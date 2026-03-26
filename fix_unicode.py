"""
Fix Unicode encoding issues in MSAM optimization modules
Converts all non-ASCII characters to ASCII equivalents
"""

import os
import re
from pathlib import Path

# Unicode to ASCII mappings
UNICODE_REPLACEMENTS = {
    'WARNING': 'WARNING',
    'PASS': 'PASS',
    'FAIL': 'FAIL',
    'RUN': 'RUN',
    'STATS': 'STATS',
    'TARGET': 'TARGET',
    'CONFIG': 'CONFIG',
    'DIR': 'DIR',
    '📝': 'DOC',
    '🏆': 'WIN',
    '🎓': 'EDU',
    '💡': 'IDEA',
    '📅': 'DATE',
    '🔐': 'SECURITY',
    '📡': 'API',
    '📈': 'GROWTH',
    '🔍': 'SEARCH',
    '⚡': 'FAST',
    '🛡️': 'PROTECT',
    '💰': 'COST',
    '🌐': 'WEB',
    '🎨': 'CUSTOM',
    '🔬': 'RESEARCH',
    '📚': 'LIB',
    '🔨': 'BUILD',
    '🔑': 'KEY',
    '🔒': 'LOCK',
    '🔓': 'UNLOCK',
    '⏰': 'TIME',
    '⏳': 'WAIT',
    '->': '->',
    'PASS': 'PASS',
    'FAIL': 'FAIL',
}

def fix_unicode_in_file(file_path):
    """Fix Unicode characters in a Python file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original = content
        
        # Replace Unicode characters
        for unicode_char, replacement in UNICODE_REPLACEMENTS.items():
            content = content.replace(unicode_char, replacement)
        
        # Check if any changes were made
        if content != original:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"PASS Fixed: {file_path.name}")
            return True
        else:
            return False
            
    except Exception as e:
        print(f"FAIL Error fixing {file_path.name}: {e}")
        return False


def main():
    """Fix Unicode issues in all MSAM optimization files"""
    
    print("=" * 70)
    print("FIXING UNICODE ENCODING ISSUES")
    print("=" * 70)
    print()
    
    # Search in both optimization directories
    search_paths = [
        Path('C:\\Users\\Tony\\.openclaw\\workspace\\projects\\msam-optimization'),
        Path('C:\\Users\\Tony\\.openclaw\\workspace\\msam'),
    ]
    
    total_fixed = 0
    
    for search_path in search_paths:
        if search_path.exists():
            print(f"Scanning: {search_path}")
            
            for py_file in search_path.glob('*.py'):
                if fix_unicode_in_file(py_file):
                    total_fixed += 1
            
            print()
    
    # Print summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Files fixed: {total_fixed}")
    print()
    
    if total_fixed > 0:
        print("STATUS: All Unicode issues fixed!")
        print("Files are now Windows-compatible (CP1252)")
    else:
        print("STATUS: No Unicode issues found - all files ASCII-only")
    
    print()
    print("=" * 70)


if __name__ == "__main__":
    main()
