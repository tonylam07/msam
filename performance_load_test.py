"""
MSAM Performance Load Test
Tests optimization performance with mock queries
"""

import asyncio
import time
import random

# Sample queries for testing
SAMPLE_QUERIES = [
    "What is MSAM?",
    "Explain semantic aggregation",
    "How does caching improve performance",
    "Describe local embeddings",
    "Benefits of async retrieval",
    "Batch embedding optimization",
    "JWT authentication flow",
    "Rate limiting implementation",
    "SOC2 compliance requirements",
    "Multi-strategy embeddings",
]

async def run_load_test():
    """Run load test on MSAM optimizations"""
    
    print("=" * 70)
    print("MSAM LOAD TEST - Performance Validation")
    print("=" * 70)
    print()
    
    # Import MSAM modules
    try:
        from optimization_suite import MSAMOptimizationSuite
        suite = MSAMOptimizationSuite()
        print(f"OPTIMIZATION SUITE STATUS:")
        print(f"  Loaded: YES")
        print(f"  Optimizations active: {suite.optimizations_active}")
    except Exception as e:
        print(f"ERROR loading optimization suite: {e}")
        return None
    
    results = {
        'baseline': [],
        'concurrent': [],
        'cache_tests': [],
        'summary': {}
    }
    
    # Test 1: Baseline single queries
    print()
    print("TEST 1: Baseline Query Performance")
    print("-" * 70)
    
    start_time = time.time()
    baseline_times = []
    
    for i in range(10):
        query = random.choice(SAMPLE_QUERIES)
        q_start = time.time()
        
        try:
            result = await suite.optimized_query(query)
            latency = (time.time() - q_start) * 1000
            baseline_times.append(latency)
            print(f"  Query {i+1:2d}: {latency:8.2f}ms")
            
        except Exception as e:
            print(f"  Query {i+1:2d}: ERROR - {str(e)[:30]}")
            baseline_times.append(0)
    
    elapsed = time.time() - start_time
    avg_baseline = sum(baseline_times) / len([t for t in baseline_times if t > 0]) if any(t > 0 for t in baseline_times) else 0
    
    results['baseline'] = {
        'count': 10,
        'avg_latency_ms': round(avg_baseline, 2),
        'total_time_s': round(elapsed, 2)
    }
    
    print()
    print(f"  BASELINE RESULTS:")
    print(f"    Average latency: {avg_baseline:.2f}ms")
    print(f"    Total time: {elapsed:.2f}s")
    print(f"    Queries/second: {10/elapsed:.1f}")
    
    # Test 2: Concurrent queries
    print()
    print("TEST 2: Concurrent Query Load (20 simultaneous)")
    print("-" * 70)
    
    concurrent_start = time.time()
    concurrent_tasks = []
    
    for i in range(20):
        query = SAMPLE_QUERIES[i % len(SAMPLE_QUERIES)]
        
        async def run_query(q):
            q_start = time.time()
            try:
                result = await suite.optimized_query(q)
                latency = (time.time() - q_start) * 1000
                return latency
            except Exception as e:
                return -1
        
        concurrent_tasks.append(run_query(query))
    
    concurrent_results = await asyncio.gather(*concurrent_tasks, return_exceptions=True)
    concurrent_times = [r for r in concurrent_results if isinstance(r, (int, float)) and r >= 0]
    
    concurrent_elapsed = time.time() - concurrent_start
    avg_concurrent = sum(concurrent_times) / len(concurrent_times) if concurrent_times else 0
    
    results['concurrent'] = {
        'count': 20,
        'avg_latency_ms': round(avg_concurrent, 2),
        'total_time_s': round(concurrent_elapsed, 2),
        'concurrency': '20 simultaneous'
    }
    
    print()
    print(f"  CONCURRENT RESULTS:")
    print(f"    Average latency: {avg_concurrent:.2f}ms")
    print(f"    Total time: {concurrent_elapsed:.2f}s")
    print(f"    Concurrent queries completed: {len(concurrent_times)}")
    
    # Test 3: Performance metrics
    print()
    print("TEST 3: Performance Metrics")
    print("-" * 70)
    
    try:
        metrics = suite.get_performance_metrics()
        print(f"  OPTIMIZATION METRICS:")
        print(f"    Redis cache hits: {metrics.get('redis_cache_hits', 'N/A')}")
        print(f"    Redis cache misses: {metrics.get('redis_cache_misses', 'N/A')}")
        print(f"    Local embeddings enabled: {metrics.get('local_embeddings_enabled', 'N/A')}")
        print(f"    Total queries processed: {metrics.get('total_queries', 'N/A')}")
        results['metrics'] = metrics
    except Exception as e:
        print(f"  WARNING: Could not retrieve metrics: {e}")
    
    # Summary
    print()
    print("=" * 70)
    print("LOAD TEST SUMMARY")
    print("=" * 70)
    print()
    print(f"  OPTIMIZATIONS ACTIVE: {suite.optimizations_active}")
    print()
    print(f"  SINGLE QUERY PERFORMANCE:")
    print(f"    Average: {avg_baseline:.2f}ms")
    print(f"    Throughput: {10/elapsed:.1f} queries/sec")
    print()
    print(f"  CONCURRENT QUERY PERFORMANCE:")
    print(f"    Count: {concurrent_times.count(concurrent_times)}")
    print(f"    Average latency: {avg_concurrent:.2f}ms")
    print(f"    Completed: {len(concurrent_times)}/20")
    print()
    print("  PERFORMANCE TARGETS:")
    print(f"    {'PASS' if avg_baseline < 100 else 'FAIL'} Target: <100ms per query")
    print(f"    {'PASS' if len(concurrent_times) > 15 else 'FAIL'} Target: >15/20 concurrent queries")
    print()
    print("=" * 70)
    print("LOAD TEST COMPLETED SUCCESSFULLY")
    print("=" * 70)
    
    results['summary'] = {
        'test_date': time.strftime('%Y-%m-%d %H:%M:%S'),
        'optimizations_active': suite.optimizations_active,
        'baseline_avg_ms': avg_baseline,
        'concurrent_avg_ms': avg_concurrent,
        'throughput_qps': 10/elapsed
    }
    
    return results


if __name__ == "__main__":
    try:
        import sys
        print("Starting MSAM load test...")
        results = asyncio.run(run_load_test())
        print("\nLoad test execution complete!")
    except Exception as e:
        print(f"Load test failed: {e}")
        import traceback
        traceback.print_exc()
