#!/bin/bash
set -e

echo "Starting Turing Smart Screen Suite Installer"
echo "--------------------------------------------"

# Check Python 3
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed on this system."
    exit 1
fi

# Detect package manager and install Tkinter dependencies (python3-tk or tk)
echo "Checking system package dependencies..."
if command -v apt-get &> /dev/null; then
    echo "Debian/Ubuntu system detected."
    if ! dpkg -s python3-tk &> /dev/null; then
        echo "Installing python3-tk package..."
        sudo apt-get update && sudo apt-get install -y python3-tk
    fi
elif command -v pacman &> /dev/null; then
    echo "Arch Linux system detected."
    if ! pacman -Qi tk &> /dev/null; then
        echo "Installing tk package..."
        sudo pacman -S --noconfirm tk
    fi
elif command -v dnf &> /dev/null; then
    echo "Fedora system detected."
    if ! rpm -q python3-tkinter &> /dev/null; then
        echo "Installing python3-tkinter package..."
        sudo dnf install -y python3-tkinter
    fi
fi

# Install python pip requirements
echo "Installing Python dependencies from requirements.txt..."
python3 -m pip install -r /home/edopex/Documents/TURZX/turing-smart-screen-python/requirements.txt || {
    echo "Pip install failed. Retrying with --user flag..."
    python3 -m pip install --user -r /home/edopex/Documents/TURZX/turing-smart-screen-python/requirements.txt
}

# Create local applications shortcuts directory
mkdir -p ~/.local/share/applications
mkdir -p ~/.config/autostart

echo "Creating Turing Control Center desktop launcher..."
cat << 'EOF' > ~/.local/share/applications/turing-control-center.desktop
[Desktop Entry]
Type=Application
Name=Turing Control Center
Comment=Manage the Turing 8.8 Screen Dashboard and MangoHud Bridge
Exec=python3 /home/edopex/Documents/TURZX/turing-smart-screen-python/turing_control_center.py
Icon=preferences-system
Terminal=false
Categories=System;Monitor;
EOF
chmod +x ~/.local/share/applications/turing-control-center.desktop

echo "Creating autostart configuration for background services..."
cat << 'EOF' > ~/.config/autostart/turing-dashboard.desktop
[Desktop Entry]
Type=Application
Name=Turing Telemetry Dashboard (Autostart)
Comment=Start the Turing 8.8 Screen Dashboard on login
Exec=python3 /home/edopex/Documents/TURZX/turing-smart-screen-python/turing_dashboard.py
Icon=utilities-terminal
Terminal=false
X-GNOME-Autostart-enabled=true
EOF
chmod +x ~/.config/autostart/turing-dashboard.desktop

cat << 'EOF' > ~/.config/autostart/turing-fps-bridge.desktop
[Desktop Entry]
Type=Application
Name=Turing FPS Bridge (Autostart)
Comment=Start the MangoHud FPS JSON bridge on login
Exec=python3 /home/edopex/Documents/TURZX/turing-smart-screen-python/fps_bridge.py
Icon=utilities-terminal
Terminal=false
X-GNOME-Autostart-enabled=true
EOF
chmod +x ~/.config/autostart/turing-fps-bridge.desktop

# Refresh desktop database
echo "Refreshing system applications database..."
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database ~/.local/share/applications/ || true
fi

echo "--------------------------------------------"
echo "Installation completed successfully."
echo "You can now open 'Turing Control Center' from your application menu."
