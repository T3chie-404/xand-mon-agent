#!/bin/bash
# Installation script for Solana Monitoring Agent

set -e

echo "===================================="
echo "Solana Monitoring Agent - Installer"
echo "===================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "ERROR: This script must be run as root (use sudo)"
    exit 1
fi

# Detect install location
INSTALL_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "Install directory: $INSTALL_DIR"

# Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo "Python version: $PYTHON_VERSION"

# Check for Solana CLI
if ! command -v solana &> /dev/null; then
    echo "WARNING: Solana CLI not found in PATH"
    echo "Make sure Solana CLI is installed and accessible"
fi

# Create virtual environment
echo ""
echo "Creating Python virtual environment..."
python3 -m venv "$INSTALL_DIR/venv"

# Activate venv and install dependencies
echo "Installing Python dependencies..."
source "$INSTALL_DIR/venv/bin/activate"
pip install --upgrade pip
pip install -r "$INSTALL_DIR/requirements.txt"
deactivate

# Check for .env file
if [ ! -f "$INSTALL_DIR/.env" ]; then
    echo ""
    echo "WARNING: .env file not found!"
    echo "Please copy env.example to .env and configure it:"
    echo "  cp $INSTALL_DIR/env.example $INSTALL_DIR/.env"
    echo "  vim $INSTALL_DIR/.env"
    echo ""
fi

# Make agent.py executable
chmod +x "$INSTALL_DIR/agent.py"

# Install systemd service
echo ""
echo "Installing systemd service..."

cat > /etc/systemd/system/solana-monitoring-agent.service << EOF
[Unit]
Description=Solana Monitoring Agent
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/venv/bin/python3 $INSTALL_DIR/agent.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
systemctl daemon-reload

echo ""
echo "===================================="
echo "Installation complete!"
echo "===================================="
echo ""
echo "Next steps:"
echo "1. Configure the agent:"
echo "   cp $INSTALL_DIR/env.example $INSTALL_DIR/.env"
echo "   vim $INSTALL_DIR/.env"
echo ""
echo "2. Enable and start the service:"
echo "   systemctl enable solana-monitoring-agent"
echo "   systemctl start solana-monitoring-agent"
echo ""
echo "3. Check status:"
echo "   systemctl status solana-monitoring-agent"
echo ""
echo "4. View metrics:"
echo "   curl http://localhost:9100/metrics"
echo ""
