"""
HTTP server to expose Prometheus metrics.
"""

import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from prometheus_client import CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST

logger = logging.getLogger(__name__)


class MetricsHandler(BaseHTTPRequestHandler):
    """HTTP request handler for metrics endpoint."""
    
    registry = None  # Will be set by server
    
    def do_GET(self):
        """Handle GET requests."""
        if self.path == '/metrics':
            self.send_response(200)
            self.send_header('Content-Type', CONTENT_TYPE_LATEST)
            self.end_headers()
            
            # Generate Prometheus metrics
            metrics = generate_latest(self.registry)
            self.wfile.write(metrics)
            
        elif self.path == '/health' or self.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
            
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found')
    
    def log_message(self, format, *args):
        """Override to use our logger."""
        logger.debug(f"{self.address_string()} - {format % args}")

    def handle(self):
        """
        Handle a single request.
        Suppress ConnectionResetError to avoid noisy logs when scanners reset connections.
        """
        try:
            super().handle()
        except ConnectionResetError:
            logger.debug("Connection reset by peer during request handling")


class MetricsServer:
    """HTTP server for exposing Prometheus metrics."""
    
    def __init__(self, port: int, registry: CollectorRegistry, bind_address: str = '0.0.0.0'):
        """
        Initialize metrics server.
        
        Args:
            port: Port to listen on
            registry: Prometheus registry
        """
        self.port = port
        self.bind_address = bind_address
        self.registry = registry
        self.server = None
        
        # Set registry for handler
        MetricsHandler.registry = registry
        
        logger.info(f"Initialized MetricsServer on {bind_address}:{port}")
    
    def start(self):
        """Start the HTTP server."""
        try:
            self.server = HTTPServer((self.bind_address, self.port), MetricsHandler)
            logger.info(
                f"Metrics server listening on http://{self.bind_address}:{self.port}/metrics"
            )
            self.server.serve_forever()
        except KeyboardInterrupt:
            logger.info("Shutting down metrics server...")
            if self.server:
                self.server.shutdown()
        except Exception as e:
            logger.error(f"Error starting metrics server: {e}")
            raise
    
    def stop(self):
        """Stop the HTTP server."""
        if self.server:
            logger.info("Stopping metrics server...")
            self.server.shutdown()
            self.server = None
