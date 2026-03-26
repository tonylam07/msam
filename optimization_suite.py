"""
MSAM Optimization Integration
Combines all optimizations into a unified system
"""

import asyncio
import time
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class OptimizationMetrics:
    """Combined metrics from all optimizations"""
    redis_cache_hits: int = 0
    redis_cache_misses: int = 0
    local_embeddings_enabled: bool = False
    async_queries_processed: int = 0
    batch_api_calls_saved: int = 0
    avg_latency_ms: float = 0.0
    success_rate: float = 0.0


class MSAMOptimizationSuite:
    """Combined optimization suite for MSAM"""
    
    def __init__(self):
        """Initialize optimization suite"""
        self.metrics = OptimizationMetrics()
        
        # Import optimization modules
        try:
            import sys
            sys.path.append(str(Path(__file__).parent))
            
            from redis_cache import MSAMCache, CachingDecorator
            self.cache = MSAMCache(host='localhost')
            self.cache_decorator = CachingDecorator(self.cache)
            
            self.metrics.redis_cache_hits = 0
            self.metrics.redis_cache_misses = 0
            
            from local_embeddings import LocalEmbeddings, HybridEmbeddings
            self.local_embeddings = LocalEmbeddings()
            self.hybrid_embeddings = HybridEmbeddings()
            self.metrics.local_embeddings_enabled = True
            
            from async_retrieval import AsyncMSAMRetriever, AsyncBatchRetriever
            self.async_retriever = AsyncMSAMRetriever()
            self.async_batch_retriever = AsyncBatchRetriever(self.async_retriever)
            
            from batch_embeddings import BatchEmbeddingOptimizer
            self.batch_optimizer = BatchEmbeddingOptimizer()
            
            self.optimizations_active = True
            
        except ImportError as e:
            print(f"WARNING Optimization modules not available: {e}")
            self.optimizations_active = False
    
    async def optimized_query(self, query_text: str) -> Dict[str, Any]:
        """Execute optimized query with all features"""
        start_time = time.time()
        
        try:
            # Try cache first
            query_id = f"query_{query_text[:20]}"
            cached = self.cache.get_cached_query(query_id)
            
            if cached:
                self.metrics.redis_cache_hits += 1
                latency = (time.time() - start_time) * 1000
                return {
                    'results': cached.results,
                    'cached': True,
                    'latency_ms': round(latency, 2)
                }
            
            self.metrics.redis_cache_misses += 1
            
            # Use local embeddings fallback
            if self.metrics.local_embeddings_enabled:
                embeddings = self.hybrid_embeddings.embed([query_text])
            else:
                # Fallback to original
                embeddings = self._default_embeddings([query_text])
            
            # Process with async retriever
            query_result = await self.async_retriever.retrieve(query_text)
            
            latency = (time.time() - start_time) * 1000
            
            # Update metrics
            self.metrics.async_queries_processed += 1
            self.metrics.avg_latency_ms = latency
            
            # Cache result
            self.cache.cache_query(
                query_id,
                query_text,
                {
                    'results': query_result.results,
                    'latency_ms': latency
                }
            )
            
            return {
                'results': query_result.results,
                'cached': False,
                'latency_ms': round(latency, 2),
                'success': query_result.success
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'cached': False,
                'latency_ms': round((time.time() - start_time) * 1000, 2),
                'success': False
            }
    
    def _default_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Default embedding fallback"""
        return [[0.1] * 384 for _ in texts]
    
    async def batch_optimized_query(self, queries: List[str]) -> List[Dict[str, Any]]:
        """Optimized batch query processing"""
        results = []
        
        for query in queries:
            result = await self.optimized_query(query)
            results.append(result)
        
        return results
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        # Redis stats
        redis_stats = self.cache.get_stats()
        
        # Async stats
        async_stats = self.async_retriever.get_stats()
        
        # Batch stats
        batch_stats = self.batch_optimizer.get_stats()
        
        return {
            'optimizations_active': self.optimizations_active,
            'timestamp': time.time(),
            'redis_cache': {
                'hits': redis_stats['hits'],
                'misses': redis_stats['misses'],
                'hit_ratio': redis_stats['hit_ratio'],
                'total_cached': redis_stats['total_cached_queries']
            },
            'async_queries': {
                'processed': self.metrics.async_queries_processed,
                'avg_latency_ms': round(async_stats.get('avg_latency_ms', 0), 2),
                'success_rate': async_stats.get('success_rate', 0)
            },
            'batch_embeddings': {
                'api_savings': batch_stats['api_savings'],
                'api_efficiency': round(batch_stats['api_efficiency'] * 100, 1),
                'cache_hit_rate': round(batch_stats['cache_hit_rate'] * 100, 1)
            },
            'total_queries_processed': (
                self.metrics.redis_cache_hits + 
                self.metrics.redis_cache_misses
            ),
            'estimated_latency_reduction': '5x (target)'
        }
    
    def save_report(self, filename: str = 'msam-optimization-report.json'):
        """Save performance report to file"""
        report = self.get_performance_report()
        
        report_path = Path(__file__).parent / filename
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"PASS Report saved: {report_path}")
    
    def reset_metrics(self):
        """Reset optimization metrics"""
        self.metrics = OptimizationMetrics()
        self.cache = MSAMCache(host='localhost')
        self.async_retriever = AsyncMSAMRetriever()
        self.batch_optimizer = BatchEmbeddingOptimizer()


# Example usage:
async def main():
    print("MSAM Optimization Suite - Testing\n")
    
    suite = MSAMOptimizationSuite()
    
    if not suite.optimizations_active:
        print("WARNING Optimization modules not loaded")
        return
    
    print("PASS Optimization suite initialized\n")
    
    # Test single query
    print("1. Single Query Test:")
    result = await suite.optimized_query("What is MSAM?")
    print(f"   Latency: {result['latency_ms']}ms")
    print(f"   Cached: {result['cached']}")
    
    # Test batch query
    print("\n2. Batch Query Test:")
    queries = ["query 1", "query 2", "query 3"]
    
    start = time.time()
    batch_results = await suite.batch_optimized_query(queries)
    batch_latency = (time.time() - start) * 1000
    
    print(f"   Processed {len(batch_results)} queries")
    print(f"   Batch latency: {batch_latency:.0f}ms")
    
    # Performance report
    print("\n3. Performance Report:")
    report = suite.get_performance_report()
    
    print(f"   Redis hit ratio: {report['redis_cache']['hit_ratio']*100:.1f}%")
    print(f"   Async queries: {report['async_queries']['processed']}")
    print(f"   API savings: {report['batch_embeddings']['api_savings']}")
    print(f"   Estimated latency reduction: {report['estimated_latency_reduction']}")
    
    # Save report
    suite.save_report()


if __name__ == "__main__":
    asyncio.run(main())
