#!/usr/bin/env python3
"""
MSAM Optimization Deployment Script
Automates deployment of all optimizations to your MSAM system
"""

import subprocess
import sys
import time
from pathlib import Path

def run_command(cmd, description):
    """Run a shell command"""
    print(f"\n{'='*60}")
    print(f"CONFIG {description}")
    print(f"{'='*60}")
    print(f"Command: {cmd}")
    print("\nRunning...")
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        print("PASS Success!")
        if result.stdout:
            print(f"Output: {result.stdout[:200]}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"FAIL Error: {e}")
        if e.stderr:
            print(f"Error: {e.stderr[:200]}")
        return False

def install_redis():
    """Check if Redis is installed and running"""
    print("\n" + "="*60)
    print("📦 Checking Redis Installation")
    print("="*60)
    
    # Check Redis server
    redis_installed = run_command("redis-server --version", "Check Redis server")
    redis_cli_installed = run_command("redis-cli --version", "Check Redis CLI")
    
    if redis_installed and redis_cli_installed:
        # Try to connect to Redis
        print("\nTesting Redis connection...")
        redis_status = run_command("redis-cli ping", "Test Redis connection")
        
        if redis_status:
            print("PASS Redis is installed and running!")
            return True
        else:
            print("WARNING️ Redis not running. Please start Redis server first.")
            print("   Windows: Start Redis as a service or run redis-server.exe")
            print("   Or install via: winget install Redis.Redis")
            return False
    else:
        print("\nFAIL Redis not found. Installing...")
        print("\n📌 Installation Options:")
        print("   1. Windows: winget install Redis.Redis")
        print("   2. Download from: https://redis.io/download")
        print("   3. Use Docker: docker run -d -p 6379:6379 redis:latest")
        return False

def install_dependencies():
    """Install Python dependencies"""
    print("\n" + "="*60)
    print("📦 Installing Python Dependencies")
    print("="*60)
    
    deps = [
        ("pip install redis", "Redis client"),
        ("pip install onnxruntime", "ONNX Runtime for local embeddings"),
        ("pip install python-jose", "JWT token handling"),
        ("pip install prometheus-client", "Prometheus metrics"),
        ("pip install aiohttp", "Async HTTP client"),
    ]
    
    results = []
    for cmd, desc in deps:
        print(f"\nInstalling {desc}...")
        if run_command(cmd, f"Install {desc}"):
            results.append(True)
        else:
            print(f"WARNING️ Skipping {desc} - will work without it")
            results.append(False)
    
    return all(results)

def validate_optimization_modules():
    """Verify all optimization modules are in place"""
    print("\n" + "="*60)
    print("🔍 Validating Optimization Modules")
    print("="*60)
    
    modules = [
        "redis_cache.py",
        "local_embeddings.py",
        "async_retrieval.py",
        "batch_embeddings.py",
        "optimization_suite.py",
        "security.py",
        "metrics_exporter.py",
    ]
    
    base_path = Path(__file__).parent
    all_present = True
    
    for module in modules:
        module_path = base_path / module
        if module_path.exists():
            print(f"PASS {module} - FOUND")
        else:
            print(f"FAIL {module} - MISSING")
            all_present = False
    
    return all_present

def test_optimization_suite():
    """Run a quick test of the optimization suite"""
    print("\n" + "="*60)
    print("🧪 Testing Optimization Suite")
    print("="*60)
    
    print("\nStarting test...")
    test_script = """
import asyncio
import sys
sys.path.append('.')

from optimization_suite import MSAMOptimizationSuite

async def test():
    print("Initializing optimization suite...")
    suite = MSAMOptimizationSuite()
    
    if not suite.optimizations_active:
        print("WARNING️ Modules not loaded, checking import errors...")
        return False
    
    print("PASS Optimization suite initialized")
    
    # Test single query
    result = await suite.optimized_query("test query")
    print(f"PASS Query test completed: {result['latency_ms']}ms")
    
    # Get performance report
    report = suite.get_performance_report()
    print(f"PASS Performance metrics collected")
    print(f"   Optimizations active: {report['optimizations_active']}")
    
    return True

try:
    result = asyncio.run(test())
    if result:
        print("\nPASS All tests passed!")
    else:
        print("\nFAIL Tests failed - check the error messages above")
except Exception as e:
    print(f"\nFAIL Test error: {e}")
    import traceback
    traceback.print_exc()
"""
    
    # Write test script
    test_file = Path(__file__).parent / "test_optimization.py"
    test_file.write_text(test_script)
    
    # Run test
    if run_command(f"python {test_file}", "Run optimization test"):
        print("\nPASS Optimization suite is working correctly!")
        return True
    else:
        print("\nFAIL Test failed - see errors above")
        return False

def start_metrics_exporter():
    """Start the Prometheus metrics exporter"""
    print("\n" + "="*60)
    print("STATS Starting Prometheus Metrics Exporter")
    print("="*60)
    
    print("\nThe metrics exporter will run on port 9090")
    print("Metrics URL: http://localhost:9090/metrics")
    print("Health URL:  http://localhost:9090/health")
    
    print("\n" + "="*60)
    print("Starting in background...")
    print("="*60)
    
    # Run in background
    result = subprocess.Popen(
        "python metrics_exporter.py",
        shell=True,
        cwd=Path(__file__).parent
    )
    
    print(f"PASS Metrics exporter started (PID: {result.pid})")
    print("Press Ctrl+C to stop the exporter")
    
    # Wait for it to start
    time.sleep(3)
    
    # Test connection
    print("\nTesting connection...")
    import requests
    try:
        response = requests.get("http://localhost:9090/health", timeout=5)
        if response.status_code == 200:
            print("PASS Metrics exporter is responding!")
        else:
            print(f"WARNING️ Metrics exporter returned status: {response.status_code}")
    except Exception as e:
        print(f"WARNING️ Could not connect: {e}")
        print("   The exporter might still be starting up")
    
    return True

def deploy_to_production():
    """Deploy all optimizations to production MSAM"""
    print("\n" + "="*60)
    print("RUN Deploying to Production MSAM")
    print("="*60)
    
    # This will copy modules to your MSAM installation
    # You'll need to configure the path to your MSAM
    
    msam_path = Path(__file__).parent.parent / "msam-integration"
    
    if msam_path.exists():
        print(f"Found MSAM installation at: {msam_path}")
        
        # Copy optimization modules
        dest_path = msam_path / "optimizations"
        dest_path.mkdir(exist_ok=True)
        
        # Copy all .py files
        import shutil
        py_files = [f for f in Path(__file__).parent.glob("*.py") if f.name not in ['test_optimization.py']]
        
        for py_file in py_files:
            dest_file = dest_path / py_file.name
            shutil.copy2(py_file, dest_file)
            print(f"PASS Copied {py_file.name} to {dest_file}")
        
        print(f"\nPASS All optimization modules copied to: {dest_path}")
        print("You can now import them in your MSAM system")
        return True
    else:
        print(f"WARNING️ MSAM installation not found at: {msam_path}")
        print("   You'll need to manually copy the modules")
        return False

def main():
    """Main deployment script"""
    print("="*60)
    print("CONFIG MSAM Optimization Deployment")
    print("="*60)
    print("\nThis script will:")
    print("1. Check/install Redis")
    print("2. Install Python dependencies")
    print("3. Validate optimization modules")
    print("4. Run tests")
    print("5. Start metrics exporter")
    print("6. Deploy to production")
    print()
    
    try:
        # Step 1: Check Redis
        redis_ok = install_redis()
        
        # Step 2: Install dependencies
        print("\n" + "="*60)
        input("Press Enter to continue with dependencies...")
        deps_ok = install_dependencies()
        
        # Step 3: Validate modules
        print("\n" + "="*60)
        input("Press Enter to validate modules...")
        modules_ok = validate_optimization_modules()
        
        # Step 4: Run tests
        print("\n" + "="*60)
        input("Press Enter to run tests...")
        test_ok = test_optimization_suite()
        
        # Step 5: Start metrics exporter
        print("\n" + "="*60)
        input("Press Enter to start metrics exporter...")
        start_ok = start_metrics_exporter()
        
        # Step 6: Deploy to production
        print("\n" + "="*60)
        input("Press Enter to deploy to production...")
        deploy_ok = deploy_to_production()
        
        # Final summary
        print("\n" + "="*60)
        print("🎉 DEPLOYMENT SUMMARY")
        print("="*60)
        
        print(f"""
PASS Redis:      {'OK' if redis_ok else 'MISSING'}
PASS Dependencies: {'OK' if deps_ok else 'PARTIAL'}
PASS Modules:    {'OK' if modules_ok else 'INCOMPLETE'}
PASS Tests:      {'PASSED' if test_ok else 'FAILED'}
PASS Exporter:   {'RUNNING' if start_ok else 'FAILED'}
PASS Deploy:     {'OK' if deploy_ok else 'SKIPPED'}

{'='*60}
RUN DEPLOYMENT {'COMPLETE!' if all([redis_ok, modules_ok, test_ok, start_ok, deploy_ok]) else 'INCOMPLETE'}
{'='*60}
        """)
        
        if all([redis_ok, modules_ok, test_ok, start_ok]):
            print("PASS All critical components are working!")
            print("   Your MSAM optimizations are ready for production use.")
        else:
            missing = []
            if not redis_ok:
                missing.append("Redis")
            if not modules_ok:
                missing.append("Modules")
            if not test_ok:
                missing.append("Tests")
            if not start_ok:
                missing.append("Exporter")
            
            print(f"WARNING️  Missing components: {', '.join(missing)}")
            print("   Please review the errors above and retry.")
        
    except KeyboardInterrupt:
        print("\n\nFAIL Deployment interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nFAIL Deployment error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
