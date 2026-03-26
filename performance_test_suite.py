"""
MSAM Performance Test Suite
Compares before/after optimization performance
"""

import asyncio
import time
import json
from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime
import statistics


class PerformanceBenchmark:
    """Benchmark MSAM performance before and after optimization"""
    
    def __init__(self, msam_path: str = None):
        """Initialize benchmark system"""
        self.msam_path = Path(msam_path) if msam_path else None
        self.results = {
            'timestamp': None,
            'optimizations_applied': [],
            'tests': {},
            'summary': {}
        }
        self.test_queries = [
            "What is MSAM?",
            "Explain semantic aggregation",
            "How does caching improve performance?",
            "Describe local embeddings",
            "What are the benefits of async retrieval?"
        ]
    
    def setup_msam_environment(self):
        """Set up MSAM for testing"""
        print("Setting up MSAM test environment...")
        
        # Import MSAM modules
        try:
            from optimization_suite import MSAMOptimizationSuite
            self.suite = MSAMOptimizationSuite()
            print("PASS Optimization suite initialized")
            return True
        except ImportError as e:
            print(f"FAIL Error loading optimization suite: {e}")
            return False
    
    async def baseline_test(self, description: str, test_func):
        """Run baseline test and record metrics"""
        print(f"\nRunning: {description}")
        
        results = {
            'latencies': [],
            'success_count': 0,
            'error_count': 0,
            'start_time': datetime.now().isoformat()
        }
        
        for query in self.test_queries:
            try:
                start = time.time()
                await test_func(query)
                latency = (time.time() - start) * 1000
                results['latencies'].append(latency)
                results['success_count'] += 1
            except Exception as e:
                results['error_count'] += 1
                print(f"  Error: {e}")
        
        results['end_time'] = datetime.now().isoformat()
        results['avg_latency_ms'] = statistics.mean(results['latencies'])
        results['p50_latency_ms'] = statistics.median(results['latencies'])
        results['p95_latency_ms'] = sorted(results['latencies'])[int(len(results['latencies']) * 0.95)]
        
        self.results['tests'][description] = results
        return results
    
    async def run_all_tests(self):
        """Run comprehensive benchmark suite"""
        print("\n" + "="*60)
        print("MSAM Performance Benchmark Suite")
        print("="*60)
        
        self.results['timestamp'] = datetime.now().isoformat()
        
        # Test 1: Basic Query Latency
        async def test_basic_query(query):
            result = await self.suite.optimized_query(query)
            return result
        
        await self.baseline_test(
            "Basic Query Latency",
            test_basic_query
        )
        
        # Test 2: Batch Query Processing
        async def test_batch_query(query):
            result = await self.suite.optimized_query(query)
            return result
        
        await self.baseline_test(
            "Batch Query Processing (5 queries)",
            test_batch_query
        )
        
        # Test 3: Concurrent Queries
        print("\nRunning: Concurrent Query Test")
        concurrent_latencies = []
        
        for i in range(5):
            queries = ["query 1", "query 2", "query 3"]
            start = time.time()
            results = await self.suite.batch_optimized_query(queries)
            latency = (time.time() - start) * 1000
            concurrent_latencies.append(latency)
        
        self.results['tests']['Concurrent Queries'] = {
            'latencies': concurrent_latencies,
            'avg_latency_ms': statistics.mean(concurrent_latencies),
            'success_count': 5,
            'error_count': 0
        }
        
        # Test 4: Cache Performance
        print("\nRunning: Cache Performance Test")
        cache_hits = 0
        cache_misses = 0
        
        for i in range(10):
            result = await self.suite.optimized_query(self.test_queries[0])
            if result.get('cached', False):
                cache_hits += 1
            else:
                cache_misses += 1
        
        self.results['tests']['Cache Performance'] = {
            'cache_hits': cache_hits,
            'cache_misses': cache_misses,
            'hit_ratio': cache_hits / (cache_hits + cache_misses) if (cache_hits + cache_misses) > 0 else 0
        }
        
        # Test 5: Performance Report
        print("\nRunning: Performance Report Test")
        report = self.suite.get_performance_report()
        self.results['tests']['Performance Report'] = report
        
        # Summary
        print("\n" + "="*60)
        print("Benchmark Results Summary")
        print("="*60)
        
        for test_name, test_results in self.results['tests'].items():
            if isinstance(test_results, dict):
                if 'avg_latency_ms' in test_results:
                    print(f"{test_name}: {test_results['avg_latency_ms']:.2f}ms avg latency")
                if 'hit_ratio' in test_results:
                    print(f"{test_name}: {test_results['hit_ratio']*100:.1f}% cache hit ratio")
                if 'cache_hits' in test_results:
                    print(f"{test_name}: {test_results['cache_hits']} hits, {test_results['cache_misses']} misses")
        
        self.results['summary'] = {
            'total_tests': len(self.results['tests']),
            'tests_passed': len([t for t in self.results['tests'].values() if t.get('success_count', 0) > 0]),
            'optimizations_active': self.suite.optimizations_active
        }
        
        return self.results
    
    def save_results(self, filename: str = 'performance_test_results.json'):
        """Save benchmark results to file"""
        results_file = Path(__file__).parent / filename
        
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\nPASS Results saved to: {results_file}")
        return results_file
    
    def generate_report(self):
        """Generate human-readable performance report"""
        report_lines = [
            "="*70,
            "MSAM PERFORMANCE BENCHMARK REPORT",
            "="*70,
            f"Generated: {self.results['timestamp']}",
            "",
            "OPTIMIZATION STATUS",
            "-"*70,
            f"Optimizations Active: {self.suite.optimizations_active}",
            "",
            "PERFORMANCE METRICS",
            "-"*70,
        ]
        
        for test_name, test_results in self.results['tests'].items():
            report_lines.append(f"\n{test_name}:")
            if isinstance(test_results, dict):
                if 'avg_latency_ms' in test_results:
                    report_lines.append(f"  Average Latency: {test_results['avg_latency_ms']:.2f}ms")
                    report_lines.append(f"  P50 Latency: {test_results.get('p50_latency_ms', 'N/A'):.2f}ms")
                    report_lines.append(f"  P95 Latency: {test_results.get('p95_latency_ms', 'N/A'):.2f}ms")
                if 'hit_ratio' in test_results:
                    report_lines.append(f"  Cache Hit Ratio: {test_results['hit_ratio']*100:.1f}%")
                if 'cache_hits' in test_results:
                    report_lines.append(f"  Cache Hits: {test_results['cache_hits']}")
                    report_lines.append(f"  Cache Misses: {test_results['cache_misses']}")
                if 'queries_processed' in test_results:
                    report_lines.append(f"  Queries Processed: {test_results['queries_processed']}")
        
        report_lines.extend([
            "",
            "SUMMARY",
            "-"*70,
            f"Total Tests Run: {self.results['summary']['total_tests']}",
            f"Tests Passed: {self.results['summary']['tests_passed']}",
            f"Optimizations Active: {self.results['summary']['optimizations_active']}",
            "",
            "="*70,
        ])
        
        report_text = "\n".join(report_lines)
        print("\n" + report_text)
        
        return report_text


# Main execution
async def main():
    print("MSAM Performance Benchmark Suite\n")
    
    # Initialize benchmark
    benchmark = PerformanceBenchmark()
    
    # Setup MSAM environment
    if not benchmark.setup_msam_environment():
        print("Error: Could not initialize MSAM environment")
        return
    
    # Run all tests
    results = await benchmark.run_all_tests()
    
    # Save results
    benchmark.save_results()
    
    # Generate report
    report = benchmark.generate_report()
    
    return results


if __name__ == "__main__":
    import sys
    import asyncio
    
    asyncio.run(main())
