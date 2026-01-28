#!/usr/bin/env python3
"""
Solana Monitoring Agent

This agent runs on a Solana RPC or validator node and exposes metrics
about slot lag and node health in Prometheus format.
"""

import os
import sys
import time
import logging
import threading
from dotenv import load_dotenv
from prometheus_client import CollectorRegistry

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.solana_client import SolanaClient
from src.metrics_collector import MetricsCollector
from src.http_server import MetricsServer
from src.push_client import PushClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_config():
    """Load configuration from environment variables."""
    # Load .env file
    load_dotenv()
    
    config = {
        'local_rpc_port': int(os.getenv('LOCAL_RPC_PORT', '8899')),
        'helius_rpc_url': os.getenv('HELIUS_RPC_URL', 'https://api.mainnet-beta.solana.com'),
        'public_rpc_url': os.getenv('PUBLIC_RPC_URL', 'https://api.mainnet-beta.solana.com'),
        'node_name': os.getenv('NODE_NAME', 'unknown-node'),
        'metrics_port': int(os.getenv('METRICS_PORT', '9100')),
        'check_interval': int(os.getenv('CHECK_INTERVAL', '30')),
    }
    
    # Validate required config
    if config['node_name'] == 'unknown-node':
        logger.warning("NODE_NAME not set, using 'unknown-node'")
    
    logger.info(f"Configuration loaded:")
    logger.info(f"  Node Name: {config['node_name']}")
    logger.info(f"  Local RPC Port: {config['local_rpc_port']}")
    logger.info(f"  Metrics Port: {config['metrics_port']}")
    logger.info(f"  Check Interval: {config['check_interval']}s")
    
    return config


def metrics_update_loop(collector, push_client, interval):
    """Background thread to update metrics periodically."""
    logger.info(f"Starting metrics update loop (interval={interval}s)")
    
    while True:
        try:
            # Collect metrics
            collector.update_metrics()
            
            # Push metrics to monitoring server if enabled
            if push_client.enabled:
                metrics_data = collector.get_metrics_dict()
                push_client.push_metrics(metrics_data)
                
        except Exception as e:
            logger.error(f"Error in metrics update loop: {e}")
        
        time.sleep(interval)


def main():
    """Main entry point."""
    logger.info("Starting Solana Monitoring Agent...")
    
    try:
        # Load configuration
        config = load_config()
        
        # Initialize components
        registry = CollectorRegistry()
        
        # Use Helius RPC as reference, fallback to public
        reference_rpc = config['helius_rpc_url']
        if 'YOUR_API_KEY_HERE' in reference_rpc:
            logger.warning("Helius API key not configured, using public RPC")
            reference_rpc = config['public_rpc_url']
        
        solana_client = SolanaClient(
            local_rpc_port=config['local_rpc_port'],
            reference_rpc_url=reference_rpc
        )
        
        collector = MetricsCollector(
            node_name=config['node_name'],
            solana_client=solana_client,
            registry=registry
        )
        
        # Initialize push client (for agent-initiated monitoring)
        push_client = PushClient()
        
        # Do initial metrics collection
        logger.info("Performing initial metrics collection...")
        collector.update_metrics()
        
        # Push initial metrics if enabled
        if push_client.enabled:
            metrics_data = collector.get_metrics_dict()
            push_client.push_metrics(metrics_data)
        
        # Start metrics update loop in background thread
        update_thread = threading.Thread(
            target=metrics_update_loop,
            args=(collector, push_client, config['check_interval']),
            daemon=True
        )
        update_thread.start()
        
        # Start HTTP server (blocks)
        server = MetricsServer(
            port=config['metrics_port'],
            registry=registry
        )
        
        logger.info("Agent ready!")
        logger.info(f"Metrics available at http://localhost:{config['metrics_port']}/metrics")
        
        server.start()
        
    except KeyboardInterrupt:
        logger.info("Received shutdown signal, exiting...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
