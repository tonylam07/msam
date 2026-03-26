"""
Simple MSAM Load Test - Quick Performance Check
"""

import asyncio
import time

TEST_QUERIES = [
    "What is MSAM?",
    "Explain caching",
    "Local embeddings benefit",
    "Async retrieval speed",
    "Batch optimization",
]

async def quick_load_test():
    """Quick load test of MSAM optimizations"""
    
    print("=" * 60)
    print("MSAM QUICK LOAD TEST")
    print("=" * 60)
    print()
    
    # Import MSAM
    try:
        from optimization_suite import MSAMOptimizationSuite
        suite = MSAMOptimizationSuite()
        print(f"OPTIMIZATION SUITE LOADED")
        print(f"Active: {suite.optimizations_active}")
    except Exception as e:
        print(f"ERROR loading suite: {e}")
        return
    
    # Run 10 baseline queries
    print()
    print("Running 10 baseline queries...")
    baseline_times = []
    
    for i in range(10):
        query = TEST_QUERIES[i % len(TEST_QUERIES)]
        start = time.time()
        await suite.optimized_query(query)
        latency = (time.time() - start) * 1000
        baseline_times.append(latency)
        print(f"  Query {i+1}: {latency:.1f}ms")
    
    avg = sum(baseline_times) / len(baseline_times)
    print()
    print(f"AVERAGE LATENCY: {avg:.1f}ms")
    print()
    
    # Run 5 concurrent queries
    print("Running 5 concurrent queries...")
    
    async def query(query_text):
        start = time.time()
        await suite.optimized_query(query_text)
        return (time.time() - start) * 1000
    
    tasks = [query(q) for q in TEST_QUERIES]
    results = await asyncio.gather(*tasks)
    
    concurrent_avg = sum(results) / len(results)
    print(f"AVERAGE CONCURRENT LATENCY: {concurrent_avg:.1f}ms")
    print()
    print("Load test completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(quick_load_test())
    except Exception as e:
        print(f"Test error: {e}")
        import traceback
        traceback.print_exc()
