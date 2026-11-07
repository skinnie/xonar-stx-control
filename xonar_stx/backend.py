"""
ALSA backend for Xonar Essence STX.

Controls the CMI8788 (snd-virtuoso / AV200) mixer via amixer.
Maps hardware ALSA controls to friendly Python properties.

Hardware: CMI8788 + PCM1792A DAC + TPA6120A2 headphone amp
Driver:   snd-virtuoso (AV200)
"""

import subprocess
import re
import shutil
from dataclasses import dataclass
from enum import IntEnum
from typing import Optional


class OutputMode(IntEnum):
    SPEAKERS = 0
    HEADPHONES = 1
    FP_HEADPHONES = 2

    @property
    def label(self):
        return {0: "Speakers", 1: "Headphones", 2: "Front Panel Headphones"}[self.value]

    @property
    def icon(self):
        return {0: "audio-speakers-symbolic", 1: "audio-headphones-symbolic",
                2: "audio-headphones-symbolic"}[self.value]


class Impedance(IntEnum):
    LOW = 0        # < 32 ohms
    MEDIUM = 1     # 32-64 ohms
    HIGH = 2       # 64-300 ohms
    VERY_HIGH = 3  # 300-600 ohms

    @property
    def label(self):
        return {0: "< 32 \u03a9", 1: "32\u201364 \u03a9", 2: "64\u2013300 \u03a9", 3: "300\u2013600 \u03a9"}[self.value]

    @property
    def description(self):
        return {
            0: "IEMs, earbuds, low-impedance headphones",
            1: "Most headphones (ATH-M50x, gaming headsets)",
            2: "High-impedance (DT770/880/990, HD580/600)",
            3: "Very high-impedance (HD650, DT990 600\u03a9)",
        }[self.value]


class DACFilter(IntEnum):
    SHARP = 0
    SLOW = 1

    @property
    def label(self):
        return {0: "Sharp Roll-off", 1: "Slow Roll-off"}[self.value]

    @property
    def description(self):
        return {
            0: "Accurate frequency response, minimal passband ripple",
            1: "Reduced pre-ringing, gentler roll-off, warmer character",
        }[self.value]


# ALSA control names for the Xonar Essence STX (snd-virtuoso driver)
ALSA_CONTROLS = {
    "master_volume": "Master Playback Volume",
    "master_switch": "Master Playback Switch",
    "output_mode": "Analog Output",
    "impedance": "Headphones Impedance Playback Enum",
    "dac_filter": "DAC Filter Playback Enum",
    "deemphasis": "De-emphasis Playback Switch",
    "spdif_switch": "IEC958 Playback Switch",
    "spdif_loopback": "IEC958 Loopback Switch",
    "mic_switch": "Mic Capture Switch",
    "mic_volume": "Mic Capture Volume",
    "mic_boost": "Mic Boost (+20dB)",
    "mic_source": "Mic Source Capture Enum",
    "line_switch": "Line Capture Switch",
    "aux_switch": "Aux Capture Switch",
    "aux_volume": "Aux Capture Volume",
    "analog_monitor_switch": "Analog Input Monitor Playback Switch",
    "analog_monitor_volume": "Analog Input Monitor Playback Volume",
    "digital_monitor_switch": "Digital Input Monitor Playback Switch",
    "digital_monitor_volume": "Digital Input Monitor Playback Volume",
}

# Volume range for PCM1792A via snd-virtuoso
VOL_MIN = 135   # -60.0 dB
VOL_MAX = 255   #   0.0 dB
VOL_STEP = 0.5  # dB per step


@dataclass
class CardState:
    """Snapshot of all card settings."""
    muted: bool = True
    volume_raw: int = 135
    volume_left: int = 135
    volume_right: int = 135
    output_mode: OutputMode = OutputMode.HEADPHONES
    impedance: Impedance = Impedance.LOW
    dac_filter: DACFilter = DACFilter.SHARP
    deemphasis: bool = False
    spdif: bool = False
    mic_enabled: bool = False
    mic_volume: int = 0
    mic_boost: bool = False

    @property
    def volume_pct(self) -> int:
        raw = (self.volume_left + self.volume_right) // 2
        return round(((raw - VOL_MIN) / (VOL_MAX - VOL_MIN)) * 100)

    @property
    def volume_db(self) -> float:
        raw = (self.volume_left + self.volume_right) // 2
        return (raw - VOL_MAX) * VOL_STEP

    @property
    def balance(self) -> float:
        """Return balance -1.0 (full left) to 1.0 (full right), 0.0 = center."""
        total = self.volume_left + self.volume_right
        if total == 0:
            return 0.0
        return (self.volume_right - self.volume_left) / (VOL_MAX - VOL_MIN)


class XonarSTXBackend:
    """Controls the Xonar Essence STX via ALSA amixer."""

    def __init__(self, card: str = "STX"):
        self.card = card
        self._amixer = shutil.which("amixer")
        if not self._amixer:
            raise RuntimeError("amixer not found. Install alsa-utils: sudo apt install alsa-utils")

    def _run(self, *args, quiet: bool = False) -> str:
        cmd = [self._amixer, "-c", self.card]
        if quiet:
            cmd.append("-q")
        cmd.extend(args)
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            return result.stdout
        except subprocess.TimeoutExpired:
            return ""
        except FileNotFoundError:
            raise RuntimeError("amixer not found")

    def _cget(self, control_name: str) -> str:
        return self._run("cget", f"name={control_name}")

    def _cset(self, control_name: str, value, quiet: bool = True) -> None:
        args = ["cset", f"name={control_name}", str(value)]
        self._run(*args, quiet=quiet)

    def _get_value(self, control_name: str) -> str:
        output = self._cget(control_name)
        match = re.search(r": values=(.+)", output)
        return match.group(1).strip() if match else ""

    def _get_bool(self, control_name: str) -> bool:
        return self._get_value(control_name) == "on"

    def _get_int(self, control_name: str) -> int:
        val = self._get_value(control_name)
        try:
            return int(val.split(",")[0])
        except (ValueError, IndexError):
            return 0

    def _get_int_pair(self, control_name: str) -> tuple:
        val = self._get_value(control_name)
        try:
            parts = val.split(",")
            return int(parts[0]), int(parts[1]) if len(parts) > 1 else int(parts[0])
        except (ValueError, IndexError):
            return 0, 0

    # --- Card detection ---

    def detect(self) -> bool:
        """Check if the Xonar STX card is present."""
        output = self._run("info")
        return "Xonar STX" in output or "AV200" in output or "Virtuoso" in output

    def get_card_info(self) -> dict:
        """Return card identification info."""
        output = self._run("info")
        return {
            "name": "ASUS Xonar Essence STX",
            "chip": "C-Media CMI8788 (Oxygen HD Audio)",
            "dac": "TI/Burr-Brown PCM1792A (24-bit/192kHz)",
            "amp": "TI TPA6120A2 Headphone Amplifier",
            "driver": "snd-virtuoso (AV200)",
            "raw_info": output,
        }

    # --- Read full state ---

    def get_state(self) -> CardState:
        """Read all mixer controls and return a CardState snapshot."""
        left, right = self._get_int_pair(ALSA_CONTROLS["master_volume"])
        return CardState(
            muted=not self._get_bool(ALSA_CONTROLS["master_switch"]),
            volume_raw=(left + right) // 2,
            volume_left=left,
            volume_right=right,
            output_mode=OutputMode(self._get_int(ALSA_CONTROLS["output_mode"])),
            impedance=Impedance(self._get_int(ALSA_CONTROLS["impedance"])),
            dac_filter=DACFilter(self._get_int(ALSA_CONTROLS["dac_filter"])),
            deemphasis=self._get_bool(ALSA_CONTROLS["deemphasis"]),
            spdif=self._get_bool(ALSA_CONTROLS["spdif_switch"]),
            mic_enabled=self._get_bool(ALSA_CONTROLS["mic_switch"]),
            mic_volume=self._get_int(ALSA_CONTROLS["mic_volume"]),
            mic_boost=self._get_bool(ALSA_CONTROLS["mic_boost"]),
        )

    # --- Volume ---

    def set_volume(self, pct: int) -> None:
        """Set volume as percentage 0-100."""
        pct = max(0, min(100, pct))
        raw = VOL_MIN + round((pct / 100) * (VOL_MAX - VOL_MIN))
        self._cset(ALSA_CONTROLS["master_volume"], f"{raw},{raw}")

    def set_volume_raw(self, left: int, right: int) -> None:
        """Set volume as raw ALSA values (135-255)."""
        left = max(VOL_MIN, min(VOL_MAX, left))
        right = max(VOL_MIN, min(VOL_MAX, right))
        self._cset(ALSA_CONTROLS["master_volume"], f"{left},{right}")

    def set_mute(self, muted: bool) -> None:
        self._cset(ALSA_CONTROLS["master_switch"], "off" if muted else "on")

    # --- Output ---

    def set_output_mode(self, mode: OutputMode) -> None:
        self._cset(ALSA_CONTROLS["output_mode"], mode.value)

    def set_impedance(self, imp: Impedance) -> None:
        self._cset(ALSA_CONTROLS["impedance"], imp.value)

    # --- DAC ---

    def set_dac_filter(self, filt: DACFilter) -> None:
        self._cset(ALSA_CONTROLS["dac_filter"], filt.value)

    def set_deemphasis(self, enabled: bool) -> None:
        self._cset(ALSA_CONTROLS["deemphasis"], "on" if enabled else "off")

    # --- S/PDIF ---

    def set_spdif(self, enabled: bool) -> None:
        self._cset(ALSA_CONTROLS["spdif_switch"], "on" if enabled else "off")

    # --- Mic ---

    def set_mic(self, enabled: bool) -> None:
        self._cset(ALSA_CONTROLS["mic_switch"], "on" if enabled else "off")

    def set_mic_volume(self, raw: int) -> None:
        raw = max(0, min(31, raw))
        self._cset(ALSA_CONTROLS["mic_volume"], raw)

    def set_mic_boost(self, enabled: bool) -> None:
        self._cset(ALSA_CONTROLS["mic_boost"], "on" if enabled else "off")

    # --- PipeWire info ---

    @staticmethod
    def get_pipewire_rate() -> Optional[int]:
        """Get current PipeWire sample rate."""
        pw = shutil.which("pw-metadata")
        if not pw:
            return None
        try:
            result = subprocess.run(
                [pw, "-n", "settings", "0", "clock.rate"],
                capture_output=True, text=True, timeout=3
            )
            match = re.search(r"value:'(\d+)'", result.stdout)
            return int(match.group(1)) if match else None
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return None

    @staticmethod
    def get_pipewire_quantum() -> Optional[int]:
        """Get current PipeWire buffer size (quantum)."""
        pw = shutil.which("pw-metadata")
        if not pw:
            return None
        try:
            result = subprocess.run(
                [pw, "-n", "settings", "0", "clock.quantum"],
                capture_output=True, text=True, timeout=3
            )
            match = re.search(r"value:'(\d+)'", result.stdout)
            return int(match.group(1)) if match else None
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return None

    # --- Presets ---

    def apply_preset(self, name: str) -> None:
        """Apply a named preset configuration."""
        presets = {
            "music": {
                "output": OutputMode.HEADPHONES,
                "impedance": Impedance.MEDIUM,
                "filter": DACFilter.SLOW,
                "deemphasis": False,
                "volume_pct": 70,
            },
            "gaming": {
                "output": OutputMode.HEADPHONES,
                "impedance": Impedance.LOW,
                "filter": DACFilter.SHARP,
                "deemphasis": False,
                "volume_pct": 65,
            },
            "speakers": {
                "output": OutputMode.SPEAKERS,
                "impedance": Impedance.LOW,
                "filter": DACFilter.SHARP,
                "deemphasis": False,
                "volume_pct": 50,
            },
            "hifi": {
                "output": OutputMode.HEADPHONES,
                "impedance": Impedance.HIGH,
                "filter": DACFilter.SLOW,
                "deemphasis": False,
                "volume_pct": 60,
            },
        }
        preset = presets.get(name)
        if not preset:
            raise ValueError(f"Unknown preset: {name}. Available: {list(presets.keys())}")

        self.set_output_mode(preset["output"])
        self.set_impedance(preset["impedance"])
        self.set_dac_filter(preset["filter"])
        self.set_deemphasis(preset["deemphasis"])
        self.set_volume(preset["volume_pct"])
        self.set_mute(False)
