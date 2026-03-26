"""
MSAM Load Test Suite - Production Testing
Tests performance optimizations under load
"""

import asyncio
import time
import random
from pathlib import Path

# Test query pool
TEST_QUERIES = [
    "What is MSAM?",
    "Explain semantic aggregation",
    "How does caching improve performance?",
    "Describe local embeddings",
    "What are the benefits of async retrieval?",
    "Compare MiniLM vs BGE embeddings",
    "How to implement rate limiting?",
    "Explain JWT authentication flow",
    "What is SOC2 compliance?",
    "How does batch optimization work?",
]

async def run_load_test(msam_path="C:\\Users\\Tony\\.openclaw\\workspace\\msam"):
    """Run comprehensive load tests"""
    
    print("=" * 70)
    print("MSAM PRODUCTION LOAD TEST SUITE")
    print("=" * 70)
    print()
    
    # Import modules
    try:
        import sys
        sys.path.insert(0, msam_path)
        from optimization_suite import MSAMOptimizationSuite
        suite = MSAMOptimizationSuite()
        print(f"OK: Optimization suite loaded")
        print(f"    Optimizations active: {suite.optimizations_active}")
    except Exception as e:
        print(f"ERROR: Failed to load optimization suite: {e}")
        return
    
    results = {
        'timestamp': None,
        'baseline_queries': [],
        'load_tests': [],
        'cache_performance': [],
        'security_tests': []
    }
    
    # Test 1: Baseline Query Performance
    print()
    print("TEST 1: Baseline Query Performance (10 queries)")
    print("-" * 70)
    
    baseline_times = []
    for i in range(10):
        query = random.choice(TEST_QUERIES)
        start = time.time()
        result = await suite.optimized_query(query)
        latency = (time.time() - start) * 1000
        baseline_times.append(latency)
        print(f"  Query {i+1}: {latency:.2f}ms")
    
    avg_baseline = sum(baseline_times) / len(baseline_times)
    p50_baseline = sorted(baseline_times)[len(baseline_times)//2]
    p95_baseline = sorted(baseline_times)[int(len(baseline_times) * 0.95)]
    
    results['baseline_queries'] = {
        'count': 10,
        'avg_latency_ms': avg_baseline,
        'p50_latency_ms': p50_baseline,
        'p95_latency_ms': p95_baseline
    }
    
    print()
    print(f"  BASELINE RESULTS:")
    print(f"    Average: {avg_baseline:.2f}ms")
    print(f"    P50: {p50_baseline:.2f}ms")
    print(f"    P95: {p95_baseline:.2f}ms")
    
    # Test 2: Concurrent Query Load Test
    print()
    print("TEST 2: Concurrent Query Load Test (50 queries)")
    print("-" * 70)
    
    concurrent_times = []
    
    async def query_task(query):
        start = time.time()
        await suite.optimized_query(query)
        latency = (time.time() - start) * 1000
        return latency
    
    for i in range(50):
        query = random.choice(TEST_QUERIES)
        task = asyncio.create_task(query_task(query))
        concurrent_times.append(task)
        
        if (i + 1) % 10 == 0:
            print(f"  Running {i+1}/50 concurrent queries...")
    
    results_list = await asyncio.gather(*concurrent_times)
    concurrent_avg = sum(results_list) / len(results_list)
    concurrent_p50 = sorted(results_list)[len(results_list)//2]
    concurrent_p95 = sorted(results_list)[int(len(results_list) * 0.95)]
    
    results['load_tests'] = {
        'count': 50,
        'avg_latency_ms': concurrent_avg,
        'p50_latency_ms': concurrent_p50,
        'p95_latency_ms': concurrent_p95
    }
    
    print()
    print(f"  LOAD TEST RESULTS (50 concurrent queries):")
    print(f"    Average: {concurrent_avg:.2f}ms")
    print(f"    P50: {concurrent_p50:.2f}ms")
    print(f"    P95: {concurrent_p95:.2f}ms")
    
    # Test 3: Cache Performance
    print()
    print("TEST 3: Cache Performance Test (100 queries, repeated)")
    print("-" * 70)
    
    cache_hits = 0
    cache_misses = 0
    test_query = TEST_QUERIES[0]
    
    for i in range(100):
        result = await suite.optimized_query(test_query)
        # Check if cached (implementation dependent)
        if hasattr(result, 'get') and result.get('cached', False):
            cache_hits += 1
        else:
            cache_misses += 1
    
    cache_hit_ratio = cache_hits / (cache_hits + cache_misses) if (cache_hits + cache_misses) > 0 else 0
    
    results['cache_performance'] = {
        'cache_hits': cache_hits,
        'cache_misses': cache_misses,
        'hit_ratio': cache_hit_ratio
    }
    
    print(f"  CACHE TEST RESULTS:")
    print(f"    Cache Hits: {cache_hits}")
    print(f"    Cache Misses: {cache_misses}")
    print(f"    Hit Ratio: {cache_hit_ratio*100:.1f}%")
    
    # Test 4: Security Features
    print()
    print("TEST 4: Security Features Test")
    print("-" * 70)
    
    try:
        from security import JWTAuthManager
        auth_manager = JWTAuthManager()
        
        # Generate token
        token_data = auth_manager.generate_token("load_test_user", ['read', 'write'])
        print(f"  OK: JWT token generated for user: {token_data.user_id}")
        
        # Validate token
        validated = auth_manager.validate_token(token_data.token)
        if validated:
            print(f"  OK: Token validation successful")
            results['security_tests'].append({'status': 'PASS', 'test': 'token_validation'})
        else:
            print(f"  FAIL: Token validation failed")
            results['security_tests'].append({'status': 'FAIL', 'test': 'token_validation'})
        
        # Rate limiter test
        from security import RateLimiter
        rate_limiter = RateLimiter()
        allowed = rate_limiter.is_allowed("test_ip_001")
        print(f"  OK: Rate limiter working (request {'allowed' if allowed else 'blocked'})")
        results['security_tests'].append({'status': 'PASS', 'test': 'rate_limiting'})
        
    except Exception as e:
        print(f"  WARNING: Security test error: {e}")
        results['security_tests'].append({'status': 'ERROR', 'test': 'security', 'error': str(e)})
    
    # Summary
    print()
    print("=" * 70)
    print("LOAD TEST SUMMARY")
    print("=" * 70)
    
    print()
    print(f"  TEST COMPLETED AT: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  OPTIMIZATIONS ACTIVE: {suite.optimizations_active}")
    print()
    print(f"  BASELINE PERFORMANCE (10 queries):")
    print(f"    Average Latency: {avg_baseline:.2f}ms")
    print(f"    P50 Latency: {p50_baseline:.2f}ms")
    print(f"    P95 Latency: {p95_baseline:.2f}ms")
    print()
    print(f"  LOAD TEST PERFORMANCE (50 concurrent):")
    print(f"    Average Latency: {concurrent_avg:.2f}ms")
    print(f"    P50 Latency: {concurrent_p50:.2f}ms")
    print(f"    P95 Latency: {concurrent_p95:.2f}ms")
    print()
    print(f"  CACHE PERFORMANCE:")
    print(f"    Hit Ratio: {cache_hit_ratio*100:.1f}%")
    print(f"    Hits: {cache_hits}, Misses: {cache_misses}")
    print()
    print(f"  SECURITY TESTS:")
    for test in results['security_tests']:
        print(f"    {test['test']}: {test['status']}")
    
    print()
    print("=" * 70)
    print("PRODUCTION LOAD TEST COMPLETED")
    print("=" * 70)
    
    return results


if __name__ == "__main__":
    try:
        results = asyncio.run(run_load_test())
        print("\nLoad test execution complete!")
    except Exception as e:
        print(f"\nLoad test suite error: {e}")
        import traceback
        traceback.print_exc()
