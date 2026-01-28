# Xand Monitoring Agent - Roadmap

## Planned Improvements

### High Priority

- [ ] **Rename systemd service** from `solana-monitoring-agent` to `xand-mon-agent`
  - Service file: `/etc/systemd/system/xand-mon-agent.service`
  - Update installer script
  - Update documentation
  - Reason: Used to monitor Xandeum assets specifically

- [ ] **Network Anomaly Detection & DDoS Monitoring**
  - Monitor incoming network traffic patterns for DDoS indicators
  - Track: Connection rates, packet floods (SYN/UDP), unusual IPs
  - Detect bandwidth saturation and port scanning
  - Correlate network anomalies with validator delinquency/failover events
  - Integration with iptables/nftables for real-time stats
  - Alert on suspicious patterns BEFORE they cause voting issues
  - Use Case: Detect what caused Madrid failover (Jan 28, 2026 04:33 UTC)

- [ ] **Validator Vote & Delinquency Tracking**
  - Monitor vote submission timing and success rates
  - Track delinquency status and slot lag acceleration
  - Gossip protocol health monitoring
  - TPU/TVU port accessibility checks
  - Pre-failover warning indicators
  - Historical vote performance analysis

- [ ] **HA Cluster Monitoring Integration**
  - Track primary (Madrid) and failover (Amsterdam) validators
  - Log failover events with timestamps and root cause data
  - Automatic correlation: network spike → vote failure → failover
  - Post-mortem analysis: Timeline reconstruction of incidents
  - Multi-validator dashboard showing cluster health

- [ ] **Native Solana/Xandeum Metrics Integration**
  - Add InfluxDB to xand-monitoring server
  - Configure validator to export native metrics (like SOLANA_METRICS_CONFIG)
  - Support dual export: metrics.solana.com + xand-monitoring
  - Use Telegraf for metrics relay/mirroring
  - Captures: CPU, network, vote performance, block production, TPU stats
  - Integrate with Grafana dashboards
  - Combined view: Agent metrics (slot lag) + Native metrics (performance)

### Medium Priority

- [ ] Add support for multiple RPC endpoints (failover)
- [ ] Add configurable alert thresholds
- [ ] Support for monitoring multiple local validators from one agent
- [ ] Add systemd journal integration for better logging
- [ ] Prometheus Federation for multi-site monitoring

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
