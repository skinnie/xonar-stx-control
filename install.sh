#!/bin/bash
# Install Xonar Essence STX Control Panel

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Installing Xonar Essence STX Control Panel..."

# Check dependencies
echo "Checking dependencies..."
missing=()

python3 -c "import gi; gi.require_version('Gtk', '4.0')" 2>/dev/null || missing+=("gir1.2-gtk-4.0")
python3 -c "import gi; gi.require_version('Adw', '1')" 2>/dev/null || missing+=("gir1.2-adw-1")
command -v amixer &>/dev/null || missing+=("alsa-utils")

if [ ${#missing[@]} -gt 0 ]; then
    echo "Missing packages: ${missing[*]}"
    echo "Installing..."
    sudo apt install -y "${missing[@]}"
fi

# Make executable
chmod +x "$SCRIPT_DIR/xonar-stx-control"

# Symlink to ~/bin
mkdir -p "$HOME/bin"
ln -sf "$SCRIPT_DIR/xonar-stx-control" "$HOME/bin/xonar-stx-control"
echo "  [+] Linked to ~/bin/xonar-stx-control"

# Install icons
ICON_DIR="$HOME/.local/share/icons/hicolor"
mkdir -p "$ICON_DIR/scalable/apps"
mkdir -p "$ICON_DIR/symbolic/apps"
cp "$SCRIPT_DIR/data/icons/hicolor/scalable/apps/xonar-stx-control.svg" \
   "$ICON_DIR/scalable/apps/"
cp "$SCRIPT_DIR/data/icons/hicolor/symbolic/apps/xonar-stx-control-symbolic.svg" \
   "$ICON_DIR/symbolic/apps/"
# Update icon cache if available
gtk-update-icon-cache -f -t "$ICON_DIR" 2>/dev/null || true
echo "  [+] Icons installed"

# Install desktop entry
mkdir -p "$HOME/.local/share/applications"
cp "$SCRIPT_DIR/com.github.xonar-stx-control.desktop" \
   "$HOME/.local/share/applications/"
echo "  [+] Desktop entry installed"

# Install systemd service (reuse existing or create)
mkdir -p "$HOME/.config/systemd/user"
cat > "$HOME/.config/systemd/user/xonar-stx-init.service" << EOF
[Unit]
Description=Initialize Xonar Essence STX mixer settings
After=pipewire.service wireplumber.service sound.target
Wants=pipewire.service

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=$HOME/bin/xonar-ctl init

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable xonar-stx-init.service
echo "  [+] Systemd boot service enabled"

echo ""
echo "Done! You can now:"
echo "  - Run: xonar-stx-control"
echo "  - Find it in your application menu as 'Xonar Essence STX Control'"
echo "  - Card will auto-initialize on boot"
