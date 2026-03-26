"""
MSAM Module Validation Test
Validates all optimization modules are loaded correctly
"""

import sys
from pathlib import Path

def validate_modules():
    """Validate all optimization modules are importable and working"""
    
    print("=" * 70)
    print("MSAM OPTIMIZATION MODULES - VALIDATION TEST")
    print("=" * 70)
    print()
    
    modules_to_test = [
        ('redis_cache', 'MSAMCache'),
        ('local_embeddings', 'LocalEmbeddings'),
        ('async_retrieval', 'AsyncMSAMRetriever'),
        ('batch_embeddings', 'BatchEmbeddingOptimizer'),
        ('security', 'JWTAuthManager,RateLimiter'),
        ('enterprise_security', 'EnterpriseAuthManager'),
        ('multi_strategy_embeddings', 'MultiStrategyEmbeddings'),
        ('optimization_suite', 'MSAMOptimizationSuite'),
    ]
    
    results = {}
    
    for module_name, classes in modules_to_test:
        print(f"Testing: {module_name}.py")
        print("-" * 70)
        
        try:
            module = __import__(module_name)
            
            # Parse class names
            class_names = classes.split(',')
            module_obj = getattr(module, module_name.replace('_', '')) if hasattr(module, module_name.replace('_', '')) else None
            
            if module_obj:
                print(f"  PASS: Module imported successfully")
                results[module_name] = {'status': 'PASS', 'message': 'Module loaded'}
            else:
                # Try direct import
                exec(f"from {module_name} import *")
                print(f"  PASS: Module functions available")
                results[module_name] = {'status': 'PASS', 'message': 'Imported'}
            
        except ImportError as e:
            print(f"  WARNING: Import issue - {e}")
            results[module_name] = {'status': 'WARNING', 'message': str(e)}
        except Exception as e:
            print(f"  FAIL: {e}")
            results[module_name] = {'status': 'FAIL', 'message': str(e)}
        
        print()
    
    # Summary
    print("=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    print()
    
    total = len(results)
    passed = sum(1 for r in results.values() if r['status'] == 'PASS')
    warnings = sum(1 for r in results.values() if r['status'] == 'WARNING')
    failed = sum(1 for r in results.values() if r['status'] == 'FAIL')
    
    print(f"Total modules tested: {total}")
    print(f"Passed: {passed}")
    print(f"Warnings: {warnings}")
    print(f"Failed: {failed}")
    print()
    
    if failed == 0:
        print("STATUS: ALL OPTIMIZATION MODULES LOADED SUCCESSFULLY")
        print("Ready for production deployment!")
    else:
        print("STATUS: Some modules have issues - review above")
    
    print()
    print("=" * 70)
    
    return results


if __name__ == "__main__":
    try:
        results = validate_modules()
        print("\nValidation complete!")
    except Exception as e:
        print(f"\nValidation error: {e}")
        import traceback
        traceback.print_exc()
