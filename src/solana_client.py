"""
Solana CLI client wrapper for monitoring agent.
Executes solana catchup command and parses output.
"""

import subprocess
import re
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)


class SolanaClient:
    """Wrapper for Solana CLI commands."""
    
    def __init__(self, local_rpc_port: int, reference_rpc_url: str):
        """
        Initialize Solana client.
        
        Args:
            local_rpc_port: The RPC port on this node (e.g., 9887, 8899)
            reference_rpc_url: Reference RPC URL for comparison
        """
        self.local_rpc_port = local_rpc_port
        self.reference_rpc_url = reference_rpc_url
        logger.info(f"Initialized SolanaClient with local port {local_rpc_port}")
    
    def get_catchup_status(self) -> Optional[Dict[str, int]]:
        """
        Execute solana catchup command and parse the output.
        
        Returns:
            Dictionary with 'local_slot', 'reference_slot', and 'slot_lag'
            None if command fails
        """
        try:
            # Execute: solana catchup --our-localhost <port>
            cmd = ["solana", "catchup", "--our-localhost", str(self.local_rpc_port)]
            logger.debug(f"Executing command: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                logger.error(f"Catchup command failed: {result.stderr}")
                return None
            
            # Parse output to extract slot information
            # Example output:
            # "Validator is caught up. Processed slot 245678906"
            # or
            # "Validator is  behind by 5 slots. Processed slot 245678901"
            
            output = result.stdout.strip()
            logger.debug(f"Catchup output: {output}")
            
            # Extract local slot number
            slot_match = re.search(r'Processed slot (\d+)', output)
            if not slot_match:
                logger.error(f"Could not parse slot from output: {output}")
                return None
            
            local_slot = int(slot_match.group(1))
            
            # Check if behind or caught up
            behind_match = re.search(r'behind by (\d+) slots', output)
            if behind_match:
                slot_lag = int(behind_match.group(1))
                reference_slot = local_slot + slot_lag
            elif 'caught up' in output.lower():
                slot_lag = 0
                reference_slot = local_slot
            else:
                # Unknown status, assume 0 lag
                logger.warning(f"Unknown catchup status: {output}")
                slot_lag = 0
                reference_slot = local_slot
            
            return {
                'local_slot': local_slot,
                'reference_slot': reference_slot,
                'slot_lag': slot_lag
            }
            
        except subprocess.TimeoutExpired:
            logger.error("Catchup command timed out")
            return None
        except Exception as e:
            logger.error(f"Error executing catchup command: {e}")
            return None
    
    def get_node_version(self) -> Optional[str]:
        """Get Solana node version."""
        try:
            result = subprocess.run(
                ["solana", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except Exception as e:
            logger.error(f"Error getting node version: {e}")
            return None
    
    def is_healthy(self) -> bool:
        """Check if Solana node is responding."""
        try:
            result = subprocess.run(
                ["solana", "--url", f"http://localhost:{self.local_rpc_port}", "cluster-version"],
                capture_output=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False
