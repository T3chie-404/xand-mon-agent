# Xand Monitoring Agent - Roadmap

## Planned Improvements

### High Priority

- [ ] **Rename systemd service** from `solana-monitoring-agent` to `xand-mon-agent`
  - Service file: `/etc/systemd/system/xand-mon-agent.service`
  - Update installer script
  - Update documentation
  - Reason: Used to monitor Xandeum assets specifically

### Medium Priority

- [ ] Add support for multiple RPC endpoints (failover)
- [ ] Add configurable alert thresholds
- [ ] Support for monitoring multiple local validators from one agent
- [ ] Add systemd journal integration for better logging

### Low Priority

- [ ] Add optional email notifications
- [ ] Support for custom metrics
- [ ] Web dashboard for agent status (standalone)

## Version History

### v1.0.0 (2026-01-28)
- Initial release
- Auto-detect Solana/Xandeum CLI path
- Prometheus metrics export
- Systemd service management

### v1.1.0 (Planned)
- Rename to xand-mon-agent
- Improved error handling
- Better startup messages
