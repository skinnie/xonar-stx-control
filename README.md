# Xonar Essence STX Control Panel

A modern GTK4 control panel for the ASUS Xonar Essence STX sound card on Linux.

Replaces the Windows Asus/UNi Xonar driver panel with a native Linux GUI
for the CMI8788 + PCM1792A DAC + TPA6120A2 headphone amplifier.

## Features

- Volume control with dB display
- Output mode switching (Speakers / Headphones / Front Panel)
- Headphone impedance/gain control with matching guide
- PCM1792A DAC digital filter selection
- S/PDIF output toggle
- PipeWire sample rate display
- System tray integration
- Dark theme optimized for audio use

## Requirements

- Python 3.10+
- GTK 4.0+ with GObject Introspection
- ALSA utilities (`alsa-utils`)
- PipeWire (optional, for sample rate display)

```bash
sudo apt install python3-gi gir1.2-gtk-4.0 gir1.2-adw-1 alsa-utils
```

## Usage

```bash
./xonar-stx-control
```

## License

GPL-3.0 — see LICENSE
