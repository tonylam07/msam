"""
MSAM Prometheus Metrics Exporter
Real-time metrics collection for monitoring dashboards
"""

import time
import asyncio
from typing import Dict, Any, List
from dataclasses import dataclass, field
from collections import defaultdict
import http.server
import socketserver
import json


@dataclass
class MetricsCollector:
    """Collects and exposes MSAM performance metrics"""
    
    # Query metrics
    query_latencies: List[float] = field(default_factory=list)
    query_success_count: int = 0
    query_error_count: int = 0
    
    # Cache metrics
    cache_hits: int = 0
    cache_misses: int = 0
    
    # API metrics
    api_calls: int = 0
    batch_api_calls_saved: int = 0
    
    # Security metrics
    auth_success: int = 0
    auth_failures: int = 0
    rate_limited_requests: int = 0
    
    # Performance tracking
    start_time: float = field(default_factory=time.time)
    max_samples: int = 1000  # Keep last N samples
    
    # Concurrency tracking
    concurrent_queries: int = 0
    max_concurrent: int = 0
    
    def record_query(self, latency_ms: float, success: bool):
        """Record query performance"""
        self.query_latencies.append(latency_ms)
        
        if len(self.query_latencies) > self.max_samples:
            self.query_latencies.pop(0)
        
        if success:
            self.query_success_count += 1
        else:
            self.query_error_count += 1
    
    def record_cache(self, hit: bool):
        """Record cache performance"""
        if hit:
            self.cache_hits += 1
        else:
            self.cache_misses += 1
    
    def record_api_call(self, saved: bool = False):
        """Record API usage"""
        self.api_calls += 1
        if saved:
            self.batch_api_calls_saved += 1
    
    def record_auth(self, success: bool):
        """Record authentication events"""
        if success:
            self.auth_success += 1
        else:
            self.auth_failures += 1
    
    def record_rate_limit(self):
        """Record rate limited request"""
        self.rate_limited_requests += 1
    
    def update_concurrent(self, count: int):
        """Track concurrent query count"""
        self.concurrent_queries = count
        if count > self.max_concurrent:
            self.max_concurrent = count
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics in Prometheus-compatible format"""
        total_queries = self.query_success_count + self.query_error_count
        total_cache = self.cache_hits + self.cache_misses
        uptime = time.time() - self.start_time
        
        # Calculate latencies
        latencies = self.query_latencies
        if latencies:
            sorted_latencies = sorted(latencies)
            p50 = sorted_latencies[int(len(sorted_latencies) * 0.5)]
            p95 = sorted_latencies[int(len(sorted_latencies) * 0.95)]
            p99 = sorted_latencies[min(int(len(sorted_latencies) * 0.99), len(sorted_latencies)-1)]
            avg_latency = sum(latencies) / len(latencies)
        else:
            p50 = p95 = p99 = avg_latency = 0.0
        
        return {
            # Query metrics
            'msam_queries_total': {
                'value': total_queries,
                'labels': {'type': 'total'}
            },
            'msam_queries_success_total': {
                'value': self.query_success_count,
                'labels': {}
            },
            'msam_queries_error_total': {
                'value': self.query_error_count,
                'labels': {}
            },
            'msam_query_latency_seconds_p50': {
                'value': p50 / 1000,
                'labels': {}
            },
            'msam_query_latency_seconds_p95': {
                'value': p95 / 1000,
                'labels': {}
            },
            'msam_query_latency_seconds_p99': {
                'value': p99 / 1000,
                'labels': {}
            },
            'msam_query_latency_seconds_avg': {
                'value': avg_latency / 1000,
                'labels': {}
            },
            
            # Cache metrics
            'msam_cache_hits_total': {
                'value': self.cache_hits,
                'labels': {}
            },
            'msam_cache_misses_total': {
                'value': self.cache_misses,
                'labels': {}
            },
            'msam_cache_hit_ratio': {
                'value': self.cache_hits / total_cache if total_cache > 0 else 0,
                'labels': {}
            },
            
            # API metrics
            'msam_api_calls_total': {
                'value': self.api_calls,
                'labels': {}
            },
            'msam_batch_api_calls_saved_total': {
                'value': self.batch_api_calls_saved,
                'labels': {}
            },
            'msam_api_efficiency_ratio': {
                'value': (self.api_calls - self.batch_api_calls_saved) / self.api_calls 
                        if self.api_calls > 0 else 0,
                'labels': {}
            },
            
            # Security metrics
            'msam_auth_success_total': {
                'value': self.auth_success,
                'labels': {}
            },
            'msam_auth_failures_total': {
                'value': self.auth_failures,
                'labels': {}
            },
            'msam_rate_limited_requests_total': {
                'value': self.rate_limited_requests,
                'labels': {}
            },
            
            # Performance metrics
            'msam_uptime_seconds': {
                'value': uptime,
                'labels': {}
            },
            'msam_concurrent_queries_current': {
                'value': self.concurrent_queries,
                'labels': {}
            },
            'msam_concurrent_queries_max': {
                'value': self.max_concurrent,
                'labels': {}
            },
            
            # Auth metrics
            'msam_auth_failure_rate': {
                'value': self.auth_failures / (self.auth_success + self.auth_failures)
                        if (self.auth_success + self.auth_failures) > 0 else 0,
                'labels': {}
            }
        }
    
    def format_prometheus(self) -> str:
        """Format metrics as Prometheus exposition format"""
        metrics = self.get_metrics()
        
        output_lines = []
        
        for metric_name, metric_data in metrics.items():
            value = metric_data['value']
            labels = metric_data['labels']
            
            # Add labels
            if labels:
                label_str = ',' + ','.join(f'{k}="{v}"' for k, v in labels.items())
            else:
                label_str = ''
            
            output_lines.append(f"{metric_name}{label_str} {value}")
        
        return '\n'.join(output_lines)


class PrometheusExporter:
    """HTTP server for Prometheus metrics scraping"""
    
    def __init__(self, metrics_collector: MetricsCollector, port: int = 9090):
        """Initialize exporter"""
        self.collector = metrics_collector
        self.port = port
        self.server = None
        
    def start_server(self):
        """Start HTTP metrics server"""
        class MetricsHandler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == '/metrics':
                    metrics_text = self.server.collector.format_prometheus()
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'text/plain; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(metrics_text.encode('utf-8'))
                elif self.path == '/health':
                    self.send_response(200)
                    self.send_header('Content-type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(b'OK')
                else:
                    self.send_response(404)
                    self.end_headers()
            
            def log_message(self, format, *args):
                # Suppress default logging
                pass
        
        self.server = socketserver.TCPServer(('', self.port), MetricsHandler)
        self.server.collector = self.collector
        
        print(f"PASS Prometheus exporter running on port {self.port}")
        print(f"  Metrics URL: http://localhost:{self.port}/metrics")
        print(f"  Health check: http://localhost:{self.port}/health")
        
        self.server.serve_forever()
    
    def stop_server(self):
        """Stop metrics server"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            print("PASS Prometheus exporter stopped")


# Example usage:
def main():
    print("Starting MSAM Prometheus Metrics Exporter...\n")
    
    # Create metrics collector
    collector = MetricsCollector()
    
    # Simulate some activity
    def simulate_activity():
        for i in range(50):
            collector.record_query(15 + (i % 10), True)
            collector.record_cache(True if i % 5 == 0 else False)
            collector.record_api_call(saved=True)
            collector.record_auth(True)
            time.sleep(0.05)
    
    # Start server in background
    exporter = PrometheusExporter(collector, port=9090)
    
    import threading
    server_thread = threading.Thread(target=exporter.start_server, daemon=True)
    server_thread.start()
    
    time.sleep(1)  # Wait for server to start
    
    # Simulate activity
    print("Simulating MSAM activity...")
    simulate_activity()
    
    # Get metrics
    metrics = collector.get_metrics()
    print(f"\nPASS Collected {len(metrics)} metrics")
    
    # Show sample metrics
    print("\nSample Metrics:")
    for key, value in list(metrics.items())[:5]:
        print(f"  {key}: {value['value']}")
    
    # Wait a moment to see metrics
    print("\nMetrics available at: http://localhost:9090/metrics")
    print("Press Ctrl+C to stop...")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        exporter.stop_server()
        print("\nPASS Exporter stopped")


if __name__ == "__main__":
    main()
