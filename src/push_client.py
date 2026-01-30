"""
Push client for sending metrics to monitoring server
Agent-initiated connection (no inbound ports needed)
"""

import os
import json
import time
import logging
import urllib.request
import urllib.error
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class PushClient:
    """Client for pushing metrics to monitoring server"""
    
    def __init__(self):
        self.enabled = os.getenv('ENABLE_PUSH_MODE', 'false').lower() == 'true'
        self.api_url = os.getenv('MONITORING_API_URL', '')
        self.api_key = os.getenv('MONITORING_API_KEY', '')
        self.node_name = os.getenv('NODE_NAME', 'unknown')
        self.node_identity = os.getenv('NODE_IDENTITY', '')
        self.retry_attempts = int(os.getenv('PUSH_RETRY_ATTEMPTS', '3'))
        
        if self.enabled:
            if not self.api_url:
                logger.warning("Push mode enabled but MONITORING_API_URL not set")
                self.enabled = False
            elif not self.api_key:
                logger.warning("Push mode enabled but MONITORING_API_KEY not set")
                self.enabled = False
            else:
                logger.info(f"Push mode enabled: {self.api_url}")
    
    def push_metrics(self, metrics_data: Dict) -> bool:
        """
        Push metrics to monitoring server
        
        Args:
            metrics_data: Dictionary of metric name -> value
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False
        
        payload = {
            'node': self.node_name,
            'timestamp': int(time.time()),
            'metrics': metrics_data,
            'metadata': {
                'agent_version': '1.0.0',
                'push_time': time.time(),
                'identity': self.node_identity or None
            }
        }
        
        for attempt in range(1, self.retry_attempts + 1):
            try:
                # Prepare request
                headers = {
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json',
                    'User-Agent': 'xand-mon-agent/1.0'
                }
                
                data = json.dumps(payload).encode('utf-8')
                req = urllib.request.Request(
                    self.api_url,
                    data=data,
                    headers=headers,
                    method='POST'
                )
                
                # Send request
                with urllib.request.urlopen(req, timeout=10) as response:
                    if response.status == 200:
                        logger.debug(f"Successfully pushed metrics for {self.node_name}")
                        return True
                    else:
                        logger.warning(f"Push failed with status {response.status}")
                        
            except urllib.error.HTTPError as e:
                logger.error(f"HTTP error pushing metrics (attempt {attempt}/{self.retry_attempts}): {e.code} {e.reason}")
                if e.code == 401:
                    logger.error("Authentication failed - check MONITORING_API_KEY")
                    return False  # Don't retry auth failures
                    
            except urllib.error.URLError as e:
                logger.error(f"Network error pushing metrics (attempt {attempt}/{self.retry_attempts}): {e.reason}")
                
            except Exception as e:
                logger.error(f"Unexpected error pushing metrics (attempt {attempt}/{self.retry_attempts}): {e}")
            
            # Backoff before retry
            if attempt < self.retry_attempts:
                backoff = 2 ** attempt  # Exponential backoff: 2, 4, 8 seconds
                logger.debug(f"Retrying in {backoff} seconds...")
                time.sleep(backoff)
        
        logger.error(f"Failed to push metrics after {self.retry_attempts} attempts")
        return False
