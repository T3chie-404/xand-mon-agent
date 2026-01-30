"""
Metrics collector for Solana monitoring agent.
Collects slot lag and health metrics and exposes them in Prometheus format.
"""

import time
import logging
from prometheus_client import Gauge, Info, CollectorRegistry
from typing import Optional
from .solana_client import SolanaClient

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collects and exposes Solana node metrics."""
    
    def __init__(self, node_name: str, solana_client: SolanaClient, registry: CollectorRegistry):
        """
        Initialize metrics collector.
        
        Args:
            node_name: Identifier for this node
            solana_client: SolanaClient instance
            registry: Prometheus registry
        """
        self.node_name = node_name
        self.solana_client = solana_client
        self.registry = registry
        
        # Define metrics
        self.slot_current = Gauge(
            'solana_slot_current',
            'Current slot number on this node',
            ['node'],
            registry=registry
        )
        
        self.slot_cluster = Gauge(
            'solana_slot_cluster',
            'Cluster tip slot number from reference RPC',
            ['node', 'rpc'],
            registry=registry
        )
        
        self.slot_lag = Gauge(
            'solana_slot_lag',
            'Slots behind cluster tip',
            ['node'],
            registry=registry
        )
        
        self.node_health = Gauge(
            'solana_node_health',
            'Node health status (1=healthy, 0=unhealthy)',
            ['node'],
            registry=registry
        )
        
        self.last_update = Gauge(
            'solana_metrics_last_update_timestamp',
            'Unix timestamp of last successful metrics update',
            ['node'],
            registry=registry
        )

        self.rpc_error = Gauge(
            'solana_rpc_error',
            'RPC error while fetching catchup status (1=error, 0=ok)',
            ['node'],
            registry=registry
        )
        
        self.node_info = Info(
            'solana_node',
            'Solana node information',
            registry=registry
        )
        
        logger.info(f"Initialized MetricsCollector for node: {node_name}")
    
    def update_metrics(self) -> bool:
        """
        Update all metrics by querying the Solana node.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get catchup status
            catchup_status = self.solana_client.get_catchup_status()
            
            if catchup_status is None:
                logger.warning("Failed to get catchup status")
                self.rpc_error.labels(node=self.node_name).set(1)
                self.node_health.labels(node=self.node_name).set(0)
                return False
            
            # Update metrics
            self.slot_current.labels(node=self.node_name).set(catchup_status['local_slot'])
            self.slot_cluster.labels(node=self.node_name, rpc='catchup').set(catchup_status['reference_slot'])
            self.slot_lag.labels(node=self.node_name).set(catchup_status['slot_lag'])
            self.rpc_error.labels(node=self.node_name).set(0)
            
            # Check health
            is_healthy = self.solana_client.is_healthy()
            self.node_health.labels(node=self.node_name).set(1 if is_healthy else 0)
            
            # Update timestamp
            self.last_update.labels(node=self.node_name).set(time.time())
            
            # Update node info (only once or when changed)
            version = self.solana_client.get_node_version()
            if version:
                self.node_info.info({
                    'node_name': self.node_name,
                    'version': version
                })
            
            logger.info(
                f"Metrics updated: slot={catchup_status['local_slot']}, "
                f"lag={catchup_status['slot_lag']}, healthy={is_healthy}"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating metrics: {e}")
            self.node_health.labels(node=self.node_name).set(0)
            return False
    
    def get_current_slot_lag(self) -> Optional[int]:
        """Get current slot lag value."""
        try:
            catchup_status = self.solana_client.get_catchup_status()
            if catchup_status:
                return catchup_status['slot_lag']
            return None
        except Exception as e:
            logger.error(f"Error getting slot lag: {e}")
            return None
    
    def get_metrics_dict(self) -> dict:
        """
        Get current metrics as a dictionary for pushing to monitoring server.
        
        Returns:
            Dictionary of metric name -> value
        """
        try:
            catchup_status = self.solana_client.get_catchup_status()
            is_healthy = self.solana_client.is_healthy()
            version = self.solana_client.get_node_version()
            
            metrics = {
                'solana_node_health': 1 if is_healthy else 0,
                'solana_metrics_last_update_timestamp': time.time()
            }
            
            if catchup_status:
                metrics.update({
                    'solana_slot_current': catchup_status['local_slot'],
                    'solana_slot_cluster': catchup_status['reference_slot'],
                    'solana_slot_lag': catchup_status['slot_lag'],
                    'solana_rpc_error': 0
                })
            else:
                metrics['solana_rpc_error'] = 1
            
            if version:
                metrics['solana_version'] = version
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting metrics dict: {e}")
            return {
                'solana_node_health': 0,
                'solana_metrics_last_update_timestamp': time.time()
            }