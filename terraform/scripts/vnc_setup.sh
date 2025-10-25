#!/bin/bash
set -e

# VNC Setup Script for macOS on EC2
# Installs and configures TigerVNC (open-source VNC server)

VNC_PASSWORD="${vnc_password}"

echo "=== Starting VNC Configuration ==="
echo "Timestamp: $(date)"

# Create VNC user directory
mkdir -p /Users/ec2-user/.vnc

# Install Homebrew if not present
if ! command -v brew &> /dev/null; then
    echo "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# Add Homebrew to PATH for this script
export PATH="/usr/local/bin:/opt/homebrew/bin:$PATH"

# Install TigerVNC server
echo "Installing TigerVNC..."
brew install -q tiger-vnc || echo "TigerVNC installation may have issues, trying alternative..."

# Create VNC password file
# TigerVNC uses a specific format for passwords
echo "Setting up VNC password..."
mkdir -p /Users/ec2-user/.vnc

# Create vncpasswd in the format TigerVNC expects
# We'll use vncpasswd utility if available, otherwise create config directly
if command -v vncpasswd &> /dev/null; then
    echo "$VNC_PASSWORD" | vncpasswd -f > /Users/ec2-user/.vnc/passwd || true
else
    # Alternative: create a config file for Xvnc
    cat > /Users/ec2-user/.vnc/passwd.txt <<EOF
$VNC_PASSWORD
$VNC_PASSWORD
EOF
    chmod 600 /Users/ec2-user/.vnc/passwd.txt
fi

# Create VNC startup script
cat > /Users/ec2-user/.vnc/xstartup <<'XVNC_EOF'
#!/bin/bash
unset SESSION_MANAGER
unset DBUS_SESSION_BUS_ADDRESS
exec /etc/X11/xinit/xinitrc
XVNC_EOF

chmod +x /Users/ec2-user/.vnc/xstartup

# Create a launchd plist for VNC service (macOS native approach)
cat > /Users/ec2-user/Library/LaunchAgents/com.tigervnc.vncserver.plist <<'PLIST_EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.tigervnc.vncserver</string>
    <key>ProgramArguments</key>
    <array>
        <string>/opt/homebrew/bin/Xvnc</string>
        <string>:1</string>
        <string>-geometry</string>
        <string>1920x1080</string>
        <string>-depth</string>
        <string>24</string>
        <string>-rfbport</string>
        <string>5900</string>
        <string>-passwordfile</string>
        <string>/Users/ec2-user/.vnc/passwd</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/ec2-user/.vnc/vnc.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/ec2-user/.vnc/vnc.err</string>
</dict>
</plist>
PLIST_EOF

chmod 644 /Users/ec2-user/Library/LaunchAgents/com.tigervnc.vncserver.plist

# Enable macOS Screen Sharing as alternative (native macOS VNC)
echo "Enabling macOS Screen Sharing..."
sudo /System/Library/CoreServices/RemoteManagement/ARDAgent.app/Contents/Resources/kickstart \
    -activate -configure -access -on -users ec2-user -privs -all -restart -agent -menu 2>/dev/null || true

# Create a helper script to manage VNC
cat > /Users/ec2-user/start_vnc.sh <<'VNC_START_EOF'
#!/bin/bash
# Start VNC server
launchctl load ~/Library/LaunchAgents/com.tigervnc.vncserver.plist 2>/dev/null || true
echo "VNC server starting on :1 (port 5900)"
VNC_START_EOF

chmod +x /Users/ec2-user/start_vnc.sh

# Create stop script
cat > /Users/ec2-user/stop_vnc.sh <<'VNC_STOP_EOF'
#!/bin/bash
# Stop VNC server
launchctl unload ~/Library/LaunchAgents/com.tigervnc.vncserver.plist 2>/dev/null || true
echo "VNC server stopped"
VNC_STOP_EOF

chmod +x /Users/ec2-user/stop_vnc.sh

# Set proper ownership
chown -R ec2-user:staff /Users/ec2-user/.vnc
chown -R ec2-user:staff /Users/ec2-user/Library/LaunchAgents/com.tigervnc.vncserver.plist

# Create connection info file
cat > /Users/ec2-user/VNC_CONNECTION_INFO.txt <<EOF
=== VNC Connection Information ===
VNC Server is configured and ready to use.

Connection Details:
- Host: (will be assigned Elastic IP)
- Port: 5900
- Password: Set during deployment

macOS provides two VNC options:

1. NATIVE SCREEN SHARING (Recommended):
   - Already enabled for ec2-user
   - Connect with any VNC client to port 5900
   - Uses macOS native screen sharing

2. TIGERVNC SERVER (Alternative):
   - Start with: ~/start_vnc.sh
   - Stop with: ~/stop_vnc.sh
   - Port: 5900

To connect from your local machine:
  macOS/Linux: open vnc://your-ip:5900
  or use: vncviewer your-ip:5900

Logs:
  - VNC logs: ~/.vnc/vnc.log
  - VNC errors: ~/.vnc/vnc.err

Note: First connection may require accepting the unverified certificate.
EOF

chown ec2-user:staff /Users/ec2-user/VNC_CONNECTION_INFO.txt

echo "=== VNC Configuration Complete ==="
echo "Timestamp: $(date)"
echo "VNC is available on port 5900"
echo "Connection info saved to: /Users/ec2-user/VNC_CONNECTION_INFO.txt"

# Log successful completion
echo "VNC setup completed successfully at $(date)" >> /var/log/vnc_setup.log
