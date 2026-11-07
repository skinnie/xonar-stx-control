"""
Xonar Essence STX Control Panel — GTK4/Adwaita GUI

Compact audio control panel using system Adwaita theme colors.
Designed to fit comfortably on 720p screens and stay out of the way.
"""

import os
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GLib, Gdk, Gio  # noqa: E402

from .backend import (  # noqa: E402
    XonarSTXBackend, OutputMode, Impedance, DACFilter,
    VOL_MIN, VOL_MAX, VOL_STEP,
)

CSS = """
.main-container {
    padding: 10px;
}

/* ── Cards ───────────────────────────────────────────── */

.app-card {
    background: @card_bg_color;
    border-radius: 10px;
    padding: 10px 12px;
    margin: 3px 0;
    border: 1px solid alpha(@borders, 0.6);
}

.app-card-accent {
    background: @card_bg_color;
    border-radius: 10px;
    padding: 10px 12px;
    margin: 3px 0;
    border: 1px solid alpha(@accent_color, 0.35);
}

/* ── Section Titles ──────────────────────────────────── */

.section-title {
    color: @accent_color;
    font-weight: 700;
    font-size: 9px;
    letter-spacing: 1.5px;
    margin-bottom: 4px;
}

/* ── Header (in headerbar) ───────────────────────────── */

.header-title {
    color: @window_fg_color;
    font-weight: 700;
    font-size: 12px;
}

.header-sub {
    color: alpha(@window_fg_color, 0.45);
    font-size: 8px;
}

/* ── Volume ──────────────────────────────────────────── */

.vol-pct {
    color: @window_fg_color;
    font-size: 28px;
    font-weight: 200;
    font-family: monospace;
}

.vol-pct-muted {
    color: alpha(@window_fg_color, 0.3);
    font-size: 28px;
    font-weight: 200;
    font-family: monospace;
    text-decoration: line-through;
    text-decoration-color: @error_color;
}

.vol-db {
    color: alpha(@window_fg_color, 0.55);
    font-size: 11px;
    font-family: monospace;
}

.vu-slider trough {
    min-height: 6px;
    border-radius: 3px;
    background: alpha(@view_bg_color, 0.8);
    border: 1px solid alpha(@borders, 0.3);
}

.vu-slider highlight {
    border-radius: 3px;
    min-height: 6px;
    background: @accent_bg_color;
}

.vu-slider slider {
    min-width: 16px;
    min-height: 16px;
    border-radius: 8px;
    background: @accent_fg_color;
    border: 2px solid @accent_color;
}

/* ── Mute ────────────────────────────────────────────── */

.mute-btn {
    border-radius: 6px;
    padding: 4px 14px;
    font-weight: 700;
    font-size: 10px;
    letter-spacing: 1px;
    min-height: 26px;
}

.mute-btn.is-muted {
    background: @error_bg_color;
    color: @error_fg_color;
}

.mute-btn.is-playing {
    background: alpha(@view_bg_color, 0.8);
    color: alpha(@window_fg_color, 0.5);
    border: 1px solid alpha(@borders, 0.4);
}

/* ── Selector Buttons (output) ───────────────────────── */

.selector-btn {
    border-radius: 6px;
    padding: 4px 4px;
    background: alpha(@view_bg_color, 0.6);
    color: alpha(@window_fg_color, 0.5);
    font-size: 10px;
    font-weight: 600;
    border: 1px solid alpha(@borders, 0.35);
    min-height: 0;
    min-width: 0;
}

.selector-btn:hover {
    background: alpha(@view_bg_color, 0.9);
    color: alpha(@window_fg_color, 0.7);
}

.selector-btn.selected {
    background: alpha(@accent_bg_color, 0.15);
    color: @window_fg_color;
    border-color: @accent_color;
}

/* ── Impedance buttons ───────────────────────────────── */

.imp-btn {
    border-radius: 6px;
    padding: 3px 2px;
    background: alpha(@view_bg_color, 0.6);
    color: alpha(@window_fg_color, 0.5);
    font-size: 9px;
    font-weight: 700;
    border: 1px solid alpha(@borders, 0.35);
    min-height: 0;
    min-width: 0;
}

.imp-btn:hover {
    background: alpha(@view_bg_color, 0.9);
    color: alpha(@window_fg_color, 0.7);
}

.imp-btn.selected {
    background: alpha(@accent_bg_color, 0.15);
    color: @window_fg_color;
    border-color: @accent_color;
}

.imp-hint {
    color: alpha(@window_fg_color, 0.4);
    font-size: 9px;
    font-style: italic;
    margin-top: 2px;
}

/* ── Toggle Rows ─────────────────────────────────────── */

.toggle-row {
    padding: 3px 0;
}

.toggle-label {
    color: @window_fg_color;
    font-size: 11px;
    font-weight: 500;
}

.toggle-desc {
    color: alpha(@window_fg_color, 0.4);
    font-size: 9px;
}

/* ── Preset Buttons ──────────────────────────────────── */

.preset-btn {
    border-radius: 6px;
    padding: 4px 4px;
    background: alpha(@view_bg_color, 0.6);
    color: alpha(@window_fg_color, 0.5);
    font-size: 10px;
    font-weight: 600;
    border: 1px solid alpha(@borders, 0.35);
    min-height: 0;
    min-width: 0;
}

.preset-btn:hover {
    background: alpha(@view_bg_color, 0.9);
    color: @window_fg_color;
}

/* ── Status ──────────────────────────────────────────── */

.status-key {
    color: alpha(@window_fg_color, 0.4);
    font-size: 9px;
    font-family: monospace;
}

.status-val {
    color: alpha(@window_fg_color, 0.65);
    font-size: 9px;
    font-family: monospace;
}

.status-dot {
    color: @success_color;
    font-size: 6px;
}

.divider {
    background: alpha(@borders, 0.3);
    min-height: 1px;
    margin: 2px 0;
}

/* FlowBox children should be transparent wrappers */
flowboxchild {
    padding: 0;
    margin: 0;
    background: transparent;
    border: none;
    outline: none;
}

flowboxchild:focus, flowboxchild:selected {
    background: transparent;
    outline: none;
}
"""


class XonarSTXWindow(Adw.ApplicationWindow):

    def __init__(self, app, backend: XonarSTXBackend):
        super().__init__(application=app, title="Xonar Essence STX")
        self.backend = backend
        self._updating = False

        # Compact default, resizable to user preference
        self.set_default_size(340, 480)
        self.set_resizable(True)
        self.set_icon_name("xonar-stx-control")

        # CSS
        css_provider = Gtk.CssProvider()
        css_provider.load_from_string(CSS)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        # Outer: headerbar + scrollable content
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(outer)

        header = Adw.HeaderBar()
        header.set_title_widget(self._build_header_title())
        outer.append(header)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)
        outer.append(scroll)

        main = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        main.add_css_class("main-container")
        scroll.set_child(main)

        main.append(self._build_volume_card())
        main.append(self._build_output_card())
        main.append(self._build_impedance_card())
        main.append(self._build_dac_card())
        main.append(self._build_presets_card())
        main.append(self._build_status_card())

        self._refresh_state()
        GLib.timeout_add_seconds(2, self._periodic_refresh)

    # ── Header ──────────────────────────────────────────────

    def _build_header_title(self):
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        icon = Gtk.Image.new_from_icon_name("xonar-stx-control")
        icon.set_pixel_size(18)
        box.append(icon)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        vbox.set_valign(Gtk.Align.CENTER)

        t = Gtk.Label(label="Xonar Essence STX")
        t.add_css_class("header-title")
        t.set_halign(Gtk.Align.START)
        vbox.append(t)

        s = Gtk.Label(label="PCM1792A \u00b7 TPA6120A2 \u00b7 CMI8788")
        s.add_css_class("header-sub")
        s.set_halign(Gtk.Align.START)
        vbox.append(s)

        box.append(vbox)
        return box

    # ── Volume ──────────────────────────────────────────────

    def _build_volume_card(self):
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        card.add_css_class("app-card-accent")

        t = Gtk.Label(label="VOLUME")
        t.add_css_class("section-title")
        t.set_halign(Gtk.Align.START)
        card.append(t)

        # Percentage + dB in one row
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        row.set_halign(Gtk.Align.CENTER)

        self.vol_pct_label = Gtk.Label(label="0%")
        self.vol_pct_label.add_css_class("vol-pct")
        row.append(self.vol_pct_label)

        self.vol_db_label = Gtk.Label(label="-60.0 dB")
        self.vol_db_label.add_css_class("vol-db")
        self.vol_db_label.set_valign(Gtk.Align.END)
        self.vol_db_label.set_margin_bottom(4)
        row.append(self.vol_db_label)

        card.append(row)

        # Slider
        self.vol_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
        self.vol_scale.set_draw_value(False)
        self.vol_scale.add_css_class("vu-slider")
        self.vol_scale.connect("value-changed", self._on_volume_changed)
        card.append(self.vol_scale)

        # Mute button
        bx = Gtk.Box()
        bx.set_halign(Gtk.Align.CENTER)
        bx.set_margin_top(2)
        self.mute_btn = Gtk.Button(label="MUTED")
        self.mute_btn.add_css_class("mute-btn")
        self.mute_btn.add_css_class("is-muted")
        self.mute_btn.connect("clicked", self._on_mute_clicked)
        bx.append(self.mute_btn)
        card.append(bx)

        return card

    # ── Output ──────────────────────────────────────────────

    def _build_output_card(self):
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        card.add_css_class("app-card")

        t = Gtk.Label(label="OUTPUT")
        t.add_css_class("section-title")
        t.set_halign(Gtk.Align.START)
        card.append(t)

        flow = Gtk.FlowBox()
        flow.set_selection_mode(Gtk.SelectionMode.NONE)
        flow.set_homogeneous(True)
        flow.set_min_children_per_line(2)
        flow.set_max_children_per_line(3)
        flow.set_row_spacing(4)
        flow.set_column_spacing(6)

        self.output_buttons = {}
        for mode in OutputMode:
            btn = Gtk.Button()
            c = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
            c.set_halign(Gtk.Align.CENTER)
            ic = Gtk.Image.new_from_icon_name(mode.icon)
            ic.set_pixel_size(14)
            c.append(ic)
            c.append(Gtk.Label(label=mode.label))
            btn.set_child(c)
            btn.add_css_class("selector-btn")
            btn.set_hexpand(True)
            btn.connect("clicked", self._on_output_clicked, mode)
            flow.insert(btn, -1)
            self.output_buttons[mode] = btn

        card.append(flow)
        return card

    # ── Impedance ───────────────────────────────────────────

    def _build_impedance_card(self):
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        card.add_css_class("app-card")

        t = Gtk.Label(label="HEADPHONE IMPEDANCE")
        t.add_css_class("section-title")
        t.set_halign(Gtk.Align.START)
        card.append(t)

        flow = Gtk.FlowBox()
        flow.set_selection_mode(Gtk.SelectionMode.NONE)
        flow.set_homogeneous(True)
        flow.set_min_children_per_line(2)
        flow.set_max_children_per_line(4)
        flow.set_row_spacing(4)
        flow.set_column_spacing(4)

        self.impedance_buttons = {}
        for imp in Impedance:
            btn = Gtk.Button(label=imp.label)
            btn.add_css_class("imp-btn")
            btn.set_hexpand(True)
            btn.set_tooltip_text(imp.description)
            btn.connect("clicked", self._on_impedance_clicked, imp)
            flow.insert(btn, -1)
            self.impedance_buttons[imp] = btn

        card.append(flow)

        self.impedance_hint = Gtk.Label()
        self.impedance_hint.add_css_class("imp-hint")
        self.impedance_hint.set_halign(Gtk.Align.START)
        self.impedance_hint.set_wrap(True)
        card.append(self.impedance_hint)

        return card

    # ── DAC Settings ────────────────────────────────────────

    def _build_dac_card(self):
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        card.add_css_class("app-card")

        t = Gtk.Label(label="DAC SETTINGS")
        t.add_css_class("section-title")
        t.set_halign(Gtk.Align.START)
        card.append(t)

        self.filter_desc = self._toggle_row(card, "DAC Filter", "Sharp Roll-off",
                                            "ON = Slow (warm)  OFF = Sharp (accurate)")
        self.filter_switch = self._last_sw
        card.append(self._div())

        self._toggle_row(card, "De-emphasis", "44.1kHz CD de-emphasis", "")
        self.deemp_switch = self._last_sw
        card.append(self._div())

        self._toggle_row(card, "S/PDIF Out", "Digital optical/coaxial", "")
        self.spdif_switch = self._last_sw

        self.filter_switch.connect("notify::active", self._on_filter_changed)
        self.deemp_switch.connect("notify::active", self._on_deemp_changed)
        self.spdif_switch.connect("notify::active", self._on_spdif_changed)

        return card

    def _toggle_row(self, parent, label, desc, tooltip):
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        row.add_css_class("toggle-row")

        tb = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        tb.set_hexpand(True)
        l = Gtk.Label(label=label)
        l.add_css_class("toggle-label")
        l.set_halign(Gtk.Align.START)
        tb.append(l)
        d = Gtk.Label(label=desc)
        d.add_css_class("toggle-desc")
        d.set_halign(Gtk.Align.START)
        tb.append(d)
        row.append(tb)

        sw = Gtk.Switch()
        sw.set_valign(Gtk.Align.CENTER)
        if tooltip:
            sw.set_tooltip_text(tooltip)
        row.append(sw)
        parent.append(row)
        self._last_sw = sw
        return d

    def _div(self):
        s = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        s.add_css_class("divider")
        return s

    # ── Presets ─────────────────────────────────────────────

    def _build_presets_card(self):
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        card.add_css_class("app-card")

        t = Gtk.Label(label="PRESETS")
        t.add_css_class("section-title")
        t.set_halign(Gtk.Align.START)
        card.append(t)

        flow = Gtk.FlowBox()
        flow.set_selection_mode(Gtk.SelectionMode.NONE)
        flow.set_homogeneous(True)
        flow.set_min_children_per_line(2)
        flow.set_max_children_per_line(4)
        flow.set_row_spacing(4)
        flow.set_column_spacing(6)

        for label, name, ic_name in [
            ("\u266b Music", "music", "media-optical-symbolic"),
            ("\u2694 Gaming", "gaming", "input-gaming-symbolic"),
            ("\u266c Spkr", "speakers", "audio-speakers-symbolic"),
            ("\u2728 Hi-Fi", "hifi", "audio-headphones-symbolic"),
        ]:
            btn = Gtk.Button(label=label)
            btn.add_css_class("preset-btn")
            btn.set_hexpand(True)
            btn.connect("clicked", self._on_preset_clicked, name)
            flow.insert(btn, -1)

        card.append(flow)
        return card

    # ── Status ──────────────────────────────────────────────

    def _build_status_card(self):
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        card.add_css_class("app-card")

        t = Gtk.Label(label="STATUS")
        t.add_css_class("section-title")
        t.set_halign(Gtk.Align.START)
        card.append(t)

        grid = Gtk.Grid()
        grid.set_column_spacing(8)
        grid.set_row_spacing(1)

        self._status_labels = {}
        for i, (key, val) in enumerate([
            ("Driver", "snd-virtuoso (AV200)"),
            ("DAC", "PCM1792A 24-bit/192kHz"),
            ("Amp", "TPA6120A2"),
            ("PipeWire", "\u2026"),
            ("Buffer", "\u2026"),
        ]):
            dot = Gtk.Label(label="\u25cf")
            dot.add_css_class("status-dot")
            grid.attach(dot, 0, i, 1, 1)

            k = Gtk.Label(label=key)
            k.add_css_class("status-key")
            k.set_halign(Gtk.Align.START)
            grid.attach(k, 1, i, 1, 1)

            v = Gtk.Label(label=val)
            v.add_css_class("status-val")
            v.set_halign(Gtk.Align.START)
            grid.attach(v, 2, i, 1, 1)
            self._status_labels[key] = v

        card.append(grid)
        return card

    # ── Signals ─────────────────────────────────────────────

    def _on_volume_changed(self, scale):
        if self._updating:
            return
        pct = int(scale.get_value())
        self.backend.set_volume(pct)
        db = ((VOL_MIN + round((pct / 100) * (VOL_MAX - VOL_MIN))) - VOL_MAX) * VOL_STEP
        self.vol_pct_label.set_label(f"{pct}%")
        self.vol_db_label.set_label(f"{db:.1f} dB")

    def _on_mute_clicked(self, _btn):
        s = self.backend.get_state()
        self.backend.set_mute(not s.muted)
        self._update_mute_ui(not s.muted)

    def _on_output_clicked(self, _btn, mode):
        self.backend.set_output_mode(mode)
        self._update_output_ui(mode)

    def _on_impedance_clicked(self, _btn, imp):
        self.backend.set_impedance(imp)
        self._update_impedance_ui(imp)

    def _on_filter_changed(self, sw, _p):
        if self._updating:
            return
        f = DACFilter.SLOW if sw.get_active() else DACFilter.SHARP
        self.backend.set_dac_filter(f)
        self.filter_desc.set_label(f.description)

    def _on_deemp_changed(self, sw, _p):
        if not self._updating:
            self.backend.set_deemphasis(sw.get_active())

    def _on_spdif_changed(self, sw, _p):
        if not self._updating:
            self.backend.set_spdif(sw.get_active())

    def _on_preset_clicked(self, _btn, name):
        self.backend.apply_preset(name)
        self._refresh_state()

    # ── UI Sync ─────────────────────────────────────────────

    def _update_mute_ui(self, muted):
        self.mute_btn.remove_css_class("is-muted")
        self.mute_btn.remove_css_class("is-playing")
        if muted:
            self.mute_btn.set_label("MUTED")
            self.mute_btn.add_css_class("is-muted")
            self.vol_pct_label.remove_css_class("vol-pct")
            self.vol_pct_label.add_css_class("vol-pct-muted")
        else:
            self.mute_btn.set_label("PLAYING")
            self.mute_btn.add_css_class("is-playing")
            self.vol_pct_label.remove_css_class("vol-pct-muted")
            self.vol_pct_label.add_css_class("vol-pct")

    def _update_output_ui(self, active):
        for mode, btn in self.output_buttons.items():
            if mode == active:
                btn.add_css_class("selected")
            else:
                btn.remove_css_class("selected")

    def _update_impedance_ui(self, active):
        for imp, btn in self.impedance_buttons.items():
            if imp == active:
                btn.add_css_class("selected")
            else:
                btn.remove_css_class("selected")
        self.impedance_hint.set_label(active.description)

    def _refresh_state(self):
        self._updating = True
        try:
            s = self.backend.get_state()
            self.vol_scale.set_value(s.volume_pct)
            self.vol_pct_label.set_label(f"{s.volume_pct}%")
            self.vol_db_label.set_label(f"{s.volume_db:.1f} dB")
            self._update_mute_ui(s.muted)
            self._update_output_ui(s.output_mode)
            self._update_impedance_ui(s.impedance)
            self.filter_switch.set_active(s.dac_filter == DACFilter.SLOW)
            self.filter_desc.set_label(s.dac_filter.description)
            self.deemp_switch.set_active(s.deemphasis)
            self.spdif_switch.set_active(s.spdif)

            rate = self.backend.get_pipewire_rate()
            if rate:
                self._status_labels["PipeWire"].set_label(f"{rate} Hz")
            quantum = self.backend.get_pipewire_quantum()
            if quantum and rate:
                ms = (quantum / rate) * 1000
                self._status_labels["Buffer"].set_label(f"{quantum} ({ms:.1f} ms)")
        except Exception as e:
            print(f"[xonar-stx] refresh error: {e}")
        finally:
            self._updating = False

    def _periodic_refresh(self):
        self._refresh_state()
        return True


class XonarSTXApp(Adw.Application):

    def __init__(self):
        super().__init__(
            application_id="com.github.xonar-stx-control",
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
        )
        self.backend = None
        self.connect("activate", self._on_activate)

    def _on_activate(self, app):
        style_mgr = Adw.StyleManager.get_default()
        style_mgr.set_color_scheme(Adw.ColorScheme.PREFER_DARK)

        # Register icon path for non-installed runs
        icon_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data", "icons", "hicolor", "scalable", "apps"
        )
        if os.path.isdir(icon_dir):
            Gtk.IconTheme.get_for_display(
                Gdk.Display.get_default()
            ).add_search_path(icon_dir)

        win = self.get_active_window()
        if win:
            win.present()
            return

        try:
            self.backend = XonarSTXBackend()
        except RuntimeError as e:
            dialog = Adw.MessageDialog(
                heading="Xonar STX Not Found",
                body=f"{e}\n\nLoad driver: sudo modprobe snd-virtuoso",
            )
            dialog.add_response("ok", "OK")
            dialog.present()
            return

        win = XonarSTXWindow(app, self.backend)
        win.present()
