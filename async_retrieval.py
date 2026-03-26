"""
MSAM Async Retrieval System
Non-blocking I/O for high-performance query processing
"""

import asyncio
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor


@dataclass
class QueryResult:
    """Result of a query operation"""
    success: bool
    results: Dict[str, Any]
    latency_ms: float
    query_id: str


class AsyncMSAMRetriever:
    """Async-enabled MSAM retriever for non-blocking queries"""
    
    def __init__(self, max_concurrent_queries: int = 50):
        """Initialize async retriever"""
        self.max_concurrent_queries = max_concurrent_queries
        self.semaphore = asyncio.Semaphore(max_concurrent_queries)
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.query_history = []
        
        # Statistics
        self.stats = {
            'total_queries': 0,
            'success_count': 0,
            'error_count': 0,
            'total_latency_ms': 0.0
        }
    
    async def retrieve(self, query_text: str, **kwargs) -> QueryResult:
        """Async query retrieval"""
        start_time = time.time()
        query_id = f"query_{int(time.time() * 1000)}"
        
        try:
            # Limit concurrency
            async with self.semaphore:
                # Run blocking operation in thread pool
                loop = asyncio.get_event_loop()
                
                result = await loop.run_in_executor(
                    self.executor,
                    self._blocking_retrieve,
                    query_text,
                    kwargs
                )
            
            latency_ms = (time.time() - start_time) * 1000
            
            query_result = QueryResult(
                success=True,
                results=result,
                latency_ms=latency_ms,
                query_id=query_id
            )
            
            # Update stats
            self.stats['total_queries'] += 1
            self.stats['success_count'] += 1
            self.stats['total_latency_ms'] += latency_ms
            
            # Track query
            self.query_history.append({
                'query_id': query_id,
                'query_text': query_text,
                'latency_ms': latency_ms,
                'timestamp': time.time()
            })
            
            return query_result
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            
            self.stats['error_count'] += 1
            
            return QueryResult(
                success=False,
                results={'error': str(e)},
                latency_ms=latency_ms,
                query_id=query_id
            )
    
    def _blocking_retrieve(self, query_text: str, kwargs: Dict) -> Dict[str, Any]:
        """Synchronous retrieval (called from thread pool)"""
        # This would integrate with actual MSAM retrieval
        # For demonstration, we'll simulate the operation
        time.sleep(0.05)  # Simulate 50ms delay
        
        return {
            'query': query_text,
            'atoms': [
                {'id': '1', 'text': 'Sample result', 'score': 0.95},
                {'id': '2', 'text': 'Another result', 'score': 0.85}
            ],
            'confidence': 0.9,
            'latency': 'simulated'
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get query statistics"""
        if self.stats['total_queries'] == 0:
            avg_latency = 0.0
            success_rate = 0.0
        else:
            avg_latency = self.stats['total_latency_ms'] / self.stats['total_queries']
            success_rate = (self.stats['success_count'] / self.stats['total_queries']) * 100
        
        return {
            **self.stats,
            'avg_latency_ms': round(avg_latency, 2),
            'success_rate': round(success_rate, 2),
            'active_queries': self.semaphore._value,
            'max_concurrent': self.max_concurrent_queries
        }
    
    def get_query_history(self, limit: int = 10) -> List[Dict]:
        """Get recent query history"""
        return self.query_history[-limit:]


class AsyncBatchRetriever:
    """Async batch query processing"""
    
    def __init__(self, retriever: AsyncMSAMRetriever, max_batch_size: int = 50):
        """Initialize batch retriever"""
        self.retriever = retriever
        self.max_batch_size = max_batch_size
    
    async def batch_retrieve(self, queries: List[str]) -> List[QueryResult]:
        """Process multiple queries concurrently"""
        # Split into batches
        batches = [queries[i:i + self.max_batch_size] 
                  for i in range(0, len(queries), self.max_batch_size)]
        
        results = []
        
        for batch in batches:
            # Process batch concurrently
            batch_results = await asyncio.gather(
                *[self.retriever.retrieve(query) for query in batch]
            )
            results.extend(batch_results)
        
        return results


class PerformanceMonitor:
    """Monitor query performance metrics"""
    
    def __init__(self, window_seconds: int = 300):
        """Initialize performance monitor"""
        self.window_seconds = window_seconds
        self.query_log = []
        
    def record_query(self, query_id: str, latency_ms: float, success: bool):
        """Record a query"""
        self.query_log.append({
            'query_id': query_id,
            'latency_ms': latency_ms,
            'success': success,
            'timestamp': time.time()
        })
        
        # Cleanup old entries
        self._cleanup_old_entries()
    
    def _cleanup_old_entries(self):
        """Remove entries outside observation window"""
        cutoff = time.time() - self.window_seconds
        self.query_log = [q for q in self.query_log 
                         if q['timestamp'] >= cutoff]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        if not self.query_log:
            return {'message': 'No recent queries'}
        
        latencies = [q['latency_ms'] for q in self.query_log]
        successes = sum(1 for q in self.query_log if q['success'])
        total = len(self.query_log)
        
        # Calculate percentiles
        sorted_latencies = sorted(latencies)
        p50 = sorted_latencies[int(len(sorted_latencies) * 0.5)] if sorted_latencies else 0
        p95 = sorted_latencies[int(len(sorted_latencies) * 0.95)] if sorted_latencies else 0
        p99 = sorted_latencies[min(int(len(sorted_latencies) * 0.99), len(sorted_latencies)-1)] if sorted_latencies else 0
        
        return {
            'queries_per_window': total,
            'success_rate': (successes / total * 100) if total > 0 else 0,
            'avg_latency_ms': sum(latencies) / total,
            'p50_latency_ms': p50,
            'p95_latency_ms': p95,
            'p99_latency_ms': p99,
            'max_latency_ms': max(latencies),
            'min_latency_ms': min(latencies)
        }


# Example usage:
async def main():
    print("Testing MSAM Async Retrieval...")
    
    # Create retriever
    retriever = AsyncMSAMRetriever()
    
    # Single query test
    print("\n1. Single Query Test:")
    result = await retriever.retrieve("test query")
    print(f"   Query ID: {result.query_id}")
    print(f"   Latency: {result.latency_ms:.2f}ms")
    print(f"   Success: {result.success}")
    
    # Batch query test
    print("\n2. Batch Query Test:")
    queries = ["query 1", "query 2", "query 3", "query 4", "query 5"]
    batch_retriever = AsyncBatchRetriever(retriever, max_batch_size=3)
    
    start = time.time()
    batch_results = await batch_retriever.batch_retrieve(queries)
    batch_latency = (time.time() - start) * 1000
    
    print(f"   Processed {len(batch_results)} queries")
    print(f"   Batch latency: {batch_latency:.2f}ms")
    print(f"   Avg query latency: {batch_latency / len(batch_results):.2f}ms")
    
    # Performance monitoring
    print("\n3. Performance Metrics:")
    monitor = PerformanceMonitor()
    
    for result in batch_results:
        monitor.record_query(result.query_id, result.latency_ms, result.success)
    
    metrics = monitor.get_metrics()
    print(f"   Queries in window: {metrics.get('queries_per_window', 'N/A')}")
    print(f"   Success rate: {metrics.get('success_rate', 0):.1f}%")
    print(f"   P50 latency: {metrics.get('p50_latency_ms', 0):.2f}ms")
    print(f"   P95 latency: {metrics.get('p95_latency_ms', 0):.2f}ms")
    print(f"   P99 latency: {metrics.get('p99_latency_ms', 0):.2f}ms")
    
    # Stats
    print("\n4. Retriever Statistics:")
    print(f"   Total queries: {retriever.get_stats()['total_queries']}")
    print(f"   Success count: {retriever.get_stats()['success_count']}")
    print(f"   Error count: {retriever.get_stats()['error_count']}")
    print(f"   Success rate: {retriever.get_stats()['success_rate']}%")


if __name__ == "__main__":
    asyncio.run(main())
