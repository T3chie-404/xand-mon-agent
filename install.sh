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

# Check for Solana CLI and detect its path
SOLANA_PATH=""
if command -v solana &> /dev/null; then
    SOLANA_PATH=$(dirname $(which solana))
    SOLANA_VERSION=$(solana --version | head -1)
    echo "✅ Solana CLI found: $SOLANA_VERSION"
    echo "   Path: $SOLANA_PATH"
else
    # Try to find solana in common user locations
    INSTALL_USER=$(logname 2>/dev/null || echo $SUDO_USER)
    if [ -n "$INSTALL_USER" ]; then
        echo "Searching for Solana CLI in user paths..."
        POSSIBLE_PATHS=(
            "/home/$INSTALL_USER/.local/share/solana/install/active_release/bin"
            "/home/$INSTALL_USER/data/compiled/active_release"
            "/home/$INSTALL_USER/.cargo/bin"
        )
        
        for path in "${POSSIBLE_PATHS[@]}"; do
            if [ -f "$path/solana" ]; then
                SOLANA_PATH="$path"
                SOLANA_VERSION=$("$path/solana" --version 2>/dev/null | head -1)
                echo "✅ Solana CLI found: $SOLANA_VERSION"
                echo "   Path: $SOLANA_PATH"
                break
            fi
        done
    fi
    
    if [ -z "$SOLANA_PATH" ]; then
        echo "⚠️  WARNING: Solana CLI not found in common locations"
        echo "   The agent will attempt to use 'solana' from PATH at runtime"
        echo "   If the agent fails, you may need to manually add Solana to PATH"
    fi
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

# Build PATH variable including Solana if found
if [ -n "$SOLANA_PATH" ]; then
    SERVICE_PATH="$SOLANA_PATH:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
    echo "   Solana path will be added to service: $SOLANA_PATH"
else
    SERVICE_PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
fi

cat > /etc/systemd/system/xand-mon-agent.service << EOF
[Unit]
Description=Xandeum Monitoring Agent
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$SERVICE_PATH"
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
echo "   systemctl enable xand-mon-agent"
echo "   systemctl start xand-mon-agent"
echo ""
echo "3. Check status:"
echo "   systemctl status xand-mon-agent"
echo ""
echo "4. View metrics:"
echo "   curl http://localhost:9100/metrics"
echo ""
