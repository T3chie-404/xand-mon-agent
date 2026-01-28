# Solana Monitoring Agent

A lightweight Python agent that monitors Solana RPC and validator nodes by tracking slot lag using the `solana catchup` command. Exposes metrics in Prometheus format for centralized monitoring.

## Features

- **Slot Lag Monitoring**: Uses `solana catchup` to track how current the node is compared to the cluster tip
- **Prometheus Metrics**: Exposes metrics on port 9100 (configurable)
- **Health Checks**: Monitors node health and responsiveness
- **Lightweight**: Minimal resource usage, runs in the background
- **Systemd Integration**: Runs as a system service with auto-restart

## Requirements

- Python 3.8 or higher
- Solana CLI tools installed and in PATH
- A running Solana RPC or validator node
- Root access for installation (or sudo)

## Installation

1. Clone this repository to the target Solana node:

```bash
git clone https://github.com/T3chie-404/xand-mon-agent.git
cd xand-mon-agent
```

2. Configure the agent:

```bash
cp env.example .env
vim .env
```

**IMPORTANT**: Set `LOCAL_RPC_PORT` to match your node's actual RPC port!

```bash
# Find your RPC port by testing:
solana --url http://localhost:8899 cluster-version   # Try 8899
solana --url http://localhost:9887 cluster-version   # Try 9887
```

3. Run the installation script:

```bash
sudo ./install.sh
```

4. Enable and start the service:

```bash
sudo systemctl enable solana-monitoring-agent
sudo systemctl start solana-monitoring-agent
```

## Configuration

All configuration is done via environment variables in the `.env` file:

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `LOCAL_RPC_PORT` | RPC port on THIS node | 8899 | Yes |
| `HELIUS_RPC_URL` | Reference RPC URL | See env.example | No |
| `PUBLIC_RPC_URL` | Fallback RPC URL | api.mainnet-beta.solana.com | No |
| `NODE_NAME` | Identifier for this node | unknown-node | Yes |
| `METRICS_PORT` | Port to expose metrics | 9100 | No |
| `CHECK_INTERVAL` | Seconds between checks | 30 | No |

### Finding Your RPC Port

Each Solana node may use a different RPC port. Common ports:

- `8899` - Default Solana RPC port
- `9887` - Alternative port
- `8900` - Alternative port

Test with:
```bash
solana --url http://localhost:<PORT> cluster-version
```

## Usage

### Check Service Status

```bash
sudo systemctl status solana-monitoring-agent
```

### View Logs

```bash
sudo journalctl -u solana-monitoring-agent -f
```

### Test Metrics Endpoint

```bash
curl http://localhost:9100/metrics
```

### Manual Run (for testing)

```bash
source venv/bin/activate
python3 agent.py
```

## Metrics

The agent exposes the following Prometheus metrics:

| Metric | Type | Description |
|--------|------|-------------|
| `solana_slot_current` | Gauge | Current slot number on this node |
| `solana_slot_cluster` | Gauge | Cluster tip slot number |
| `solana_slot_lag` | Gauge | Slots behind cluster tip |
| `solana_node_health` | Gauge | Health status (1=healthy, 0=unhealthy) |
| `solana_metrics_last_update_timestamp` | Gauge | Unix timestamp of last update |
| `solana_node_info` | Info | Node version and details |

### Example Metrics Output

```
# HELP solana_slot_current Current slot number on this node
# TYPE solana_slot_current gauge
solana_slot_current{node="my-validator"} 245678901.0

# HELP solana_slot_lag Slots behind cluster tip
# TYPE solana_slot_lag gauge
solana_slot_lag{node="my-validator"} 5.0

# HELP solana_node_health Node health status (1=healthy, 0=unhealthy)
# TYPE solana_node_health gauge
solana_node_health{node="my-validator"} 1.0
```

## Troubleshooting

### Agent won't start

1. Check configuration:
```bash
cat .env
```

2. Verify Solana CLI is accessible:
```bash
solana --version
```

3. Test catchup command manually:
```bash
solana catchup --our-localhost 9887
```

### No metrics appearing

1. Check if metrics endpoint is responding:
```bash
curl http://localhost:9100/health
```

2. Check firewall rules (agent binds to 0.0.0.0)

3. View detailed logs:
```bash
sudo journalctl -u solana-monitoring-agent -n 100
```

### Wrong RPC port

If you see "connection refused" errors, you likely have the wrong `LOCAL_RPC_PORT` configured. Find the correct port and update `.env`:

```bash
# Test ports
for port in 8899 9887 8900; do
    echo "Testing port $port..."
    solana --url http://localhost:$port cluster-version && echo "✅ Port $port works!"
done
```

## Security

This is a **PUBLIC repository**. Do NOT commit:

- Actual `.env` files (only `env.example`)
- API keys or credentials
- SSH keys
- Internal IP addresses or hostnames
- Any sensitive configuration

## License

MIT License - see LICENSE file

## Contributing

Contributions welcome! Please ensure:

1. No sensitive data in commits
2. Run security sweep before committing
3. Test on a live Solana node
4. Update documentation as needed

## Support

For issues or questions:

- Open an issue on GitHub
- Check existing issues for solutions
- Review logs with `journalctl`
