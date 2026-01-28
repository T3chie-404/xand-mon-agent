# Performance Impact Guide

## 🎯 Overview

Solana validators are **extremely performance-sensitive**. Any monitoring overhead could affect vote submission timing, which could lead to delinquency and failover events - exactly what we're trying to prevent.

This document explains the performance impact of the monitoring agent and how to minimize it.

## 📊 Current Agent (v1.0) - Baseline Impact

### Measured Overhead (from production deployment)
```
Memory:  13.5 MB (peak: 14.0 MB)
CPU:     68ms total since service start
Process: Python 3.12 with minimal dependencies
Network: ~2KB/30sec for catchup command
```

### What It Does
- Executes `solana catchup` every 30 seconds
- Parses output and exposes Prometheus metrics
- Runs lightweight HTTP server on port 9100

### Impact Assessment
```
CPU:     < 0.1% (negligible)
Memory:  ~15MB (0.001% on typical 128GB validator)
Network: ~5KB/min (0.0001% on 1Gbps link)
Disk:    None (metrics in memory only)

⚠️ VERDICT: Safe for production validators
```

## 🚨 Proposed Network Monitoring - Performance Design

### What We WON'T Do (Performance Killers)

❌ **Packet Capture/Inspection**
```bash
# These would KILL performance - we will NEVER do this
tcpdump -i any               # Copies every packet
iptraf                       # Real-time packet analysis
wireshark/tshark            # Deep packet inspection
```
**Impact if we did**: 10-30% CPU overhead ❌

❌ **Inline Traffic Filtering**
```bash
# No inline processing of validator traffic
# No eBPF probes on data path
# No traffic mirroring
```

### What We WILL Do (Zero-Impact Stats Collection)

✅ **Read Kernel Counters (Already Being Tracked)**
```bash
# The kernel is already tracking these - reading is free
cat /proc/net/netstat          # ~0.1ms to read
cat /proc/net/snmp             # ~0.1ms to read
ip -s link show                # ~0.1ms to read
ss -s                          # ~1ms to read
conntrack -C                   # ~0.1ms to read
iptables -nvxL INPUT           # ~1ms to read
```

**How it works:**
1. Linux kernel already tracks ALL network statistics
2. Reading these files just retrieves counters from memory
3. No packet inspection, no data path interaction
4. Similar to reading `/proc/cpuinfo` - zero overhead

**Collection Frequency:**
- Default: Every 30 seconds (aligned with catchup check)
- Configurable: 10-300 seconds
- Critical validators: Disable entirely

### Architecture: Offload Heavy Processing

```
┌──────────────────────────────────────────┐
│ VALIDATOR (Performance Critical)         │
│                                          │
│ Agent Overhead:                          │
│ - Read 6 kernel files (30 sec interval) │
│ - ~5ms total per collection              │
│ - Expose via HTTP (Prometheus format)   │
│                                          │
│ Total Impact: < 0.2% CPU                │
│               < 20MB RAM                 │
└──────────────────────────────────────────┘
          ↓ (Scraped via SSH tunnel)
┌──────────────────────────────────────────┐
│ MONITORING SERVER (Does All Analysis)    │
│                                          │
│ - Time-series storage (Prometheus)       │
│ - Anomaly detection algorithms           │
│ - Baseline traffic analysis              │
│ - Correlation with vote health           │
│ - Dashboard rendering (Grafana)          │
│ - Alert evaluation                       │
│                                          │
│ 100% of CPU-intensive work happens here │
└──────────────────────────────────────────┘
```

## ⚙️ Configuration Options

### Low-Impact Mode (Recommended for Critical Validators)
```bash
# .env configuration
CHECK_INTERVAL=60              # Check every 60 seconds (vs 30)
ENABLE_NETWORK_STATS=false     # Disable network monitoring
ENABLE_SYSTEM_STATS=false      # Disable CPU/mem monitoring
METRICS_PORT=9100              # Expose only slot lag metrics
```

**Impact: ~0.05% CPU, 13MB RAM**

### Standard Mode (Recommended for RPC Nodes)
```bash
CHECK_INTERVAL=30              # Default
ENABLE_NETWORK_STATS=true      # Enable network monitoring
ENABLE_SYSTEM_STATS=true       # Enable system monitoring
NETWORK_STATS_INTERVAL=30      # Collect network stats every 30s
```

**Impact: ~0.2% CPU, 20MB RAM**

### Detailed Mode (Testing/Debugging Only)
```bash
CHECK_INTERVAL=10              # More frequent checks
ENABLE_NETWORK_STATS=true
ENABLE_SYSTEM_STATS=true
NETWORK_STATS_INTERVAL=10      # Collect every 10s
LOG_LEVEL=DEBUG                # Verbose logging
```

**Impact: ~0.5% CPU, 25MB RAM**  
⚠️ **Not recommended for production validators**

## 📋 Performance Testing Checklist

Before deploying network monitoring to your validators:

### Phase 1: Test on RPC Node First
- [ ] Deploy agent with network monitoring enabled
- [ ] Monitor for 24 hours on RPC node (non-critical validator)
- [ ] Verify: CPU usage stays < 0.5%
- [ ] Verify: No impact on RPC response times
- [ ] Check: Memory stays under 25MB

### Phase 2: Test on Secondary Validator
- [ ] Deploy to Amsterdam (failover validator)
- [ ] Monitor for 72 hours
- [ ] Verify: Vote submission timing unchanged
- [ ] Verify: Slot lag not affected
- [ ] Check: No increase in delinquency risk

### Phase 3: Production Deployment
- [ ] Deploy to Madrid (primary validator)
- [ ] Use LOW-IMPACT mode initially
- [ ] Monitor for 1 week
- [ ] Gradually enable features if performance acceptable

## 🔧 Performance Monitoring Commands

### Check Agent Impact
```bash
# CPU usage of agent
ps aux | grep agent.py

# Memory usage
systemctl status xand-mon-agent | grep Memory

# Network bandwidth (agent's HTTP metrics)
ss -tn | grep :9100
```

### Check Validator Performance (Before/After Agent)
```bash
# Vote timing
solana validators --url http://localhost:8899

# Slot lag
solana catchup --our-localhost 8899

# System resources
top -b -n 1 | grep -E "Cpu|Mem"
```

### Baseline Measurements (Run BEFORE deploying network monitoring)
```bash
# Capture baseline for comparison
echo "=== Baseline Performance ===" > /tmp/baseline.txt
date >> /tmp/baseline.txt
uptime >> /tmp/baseline.txt
ps aux | grep solana >> /tmp/baseline.txt
top -b -n 1 >> /tmp/baseline.txt
```

## 🚦 Performance Thresholds

### Green Zone ✅ (Safe)
- CPU: < 0.5%
- Memory: < 50MB
- No impact on vote timing
- Slot lag unchanged

### Yellow Zone ⚠️ (Monitor Closely)
- CPU: 0.5% - 1.0%
- Memory: 50MB - 100MB
- Occasional vote delays (< 1%)
- Investigate but don't disable

### Red Zone 🚨 (Take Action)
- CPU: > 1.0%
- Memory: > 100MB
- Vote timing affected
- Slot lag increasing

**Action**: Immediately switch to LOW-IMPACT mode or disable network monitoring

## 💡 Best Practices

### 1. **Tiered Deployment**
```
Priority 1 (Critical): Madrid primary validator
  → Use LOW-IMPACT mode or disable network stats
  → Slot lag monitoring only

Priority 2 (Important): Amsterdam failover validator  
  → Use STANDARD mode
  → Full monitoring except during active voting

Priority 3 (Safe): RPC nodes (non-voting nodes)
  → Use DETAILED mode
  → Full monitoring, testing ground for new features
```

### 2. **Time-Based Adjustments**
```bash
# Reduce frequency during peak network activity
# Cron job to adjust intervals
0 * * * * echo "CHECK_INTERVAL=60" > /etc/xand-mon-agent/.env  # Hourly
30 * * * * echo "CHECK_INTERVAL=30" > /etc/xand-mon-agent/.env  # Half past
```

### 3. **Emergency Disable**
```bash
# Quick disable if performance issues detected
sudo systemctl stop xand-mon-agent

# Or just disable network stats
echo "ENABLE_NETWORK_STATS=false" >> /path/to/xand-mon-agent/.env
sudo systemctl restart xand-mon-agent
```

## 📊 Expected Impact Summary

| Feature | CPU | Memory | Network | Risk Level |
|---------|-----|--------|---------|------------|
| Slot lag monitoring (current) | < 0.1% | 13MB | ~5KB/min | ✅ Safe |
| + Network stats (planned) | < 0.2% | 20MB | ~10KB/min | ✅ Safe |
| + System stats (planned) | < 0.3% | 25MB | ~15KB/min | ✅ Safe |
| + Vote timing (planned) | < 0.4% | 30MB | ~20KB/min | ⚠️ Test First |

## 🎯 Recommendation

**For CatalysX Madrid (Primary Validator):**
1. Keep current agent (slot lag only)
2. Deploy network monitoring to **RPC node first**
3. Test for 1 week
4. If no issues, deploy to **Amsterdam (failover)**
5. If still no issues, consider **Madrid in LOW-IMPACT mode**

**You can always disable features if any performance impact is detected.**

---

**Remember**: The goal is to **prevent** voting issues, not cause them. We'll be conservative with validator deployments and aggressive with testing on RPC nodes.
