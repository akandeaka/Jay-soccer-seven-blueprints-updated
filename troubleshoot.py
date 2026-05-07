"""
TROUBLESHOOTING - Check if system can access data source
"""

import os
import sys

print("="*60)
print("🔍 DATA SOURCE ACCESS DIAGNOSTIC")
print("="*60)

# 1. Check current working directory
print(f"\n1. Current working directory: {os.getcwd()}")

# 2. List all files in current directory
print(f"\n2. Files in current directory:")
files = os.listdir('.')
for f in files:
    size = os.path.getsize(f) if os.path.isfile(f) else 'DIR'
    print(f"   - {f} ({size})")

# 3. Specifically check for input_matches.txt
print(f"\n3. Looking for input_matches.txt...")
if os.path.exists("input_matches.txt"):
    print(f"   ✅ File EXISTS: input_matches.txt")
    
    # Show file size
    size = os.path.getsize("input_matches.txt")
    print(f"   File size: {size} bytes")
    
    # Show file content
    print(f"\n4. Content of input_matches.txt:")
    print("-" * 40)
    with open("input_matches.txt", 'r') as f:
        content = f.read()
        print(content)
    print("-" * 40)
    
    # Check if file has valid format
    lines = [l.strip() for l in content.split('\n') if l.strip()]
    print(f"\n5. File analysis:")
    print(f"   Total non-empty lines: {len(lines)}")
    
    # Check for 'vs' pattern
    vs_count = sum(1 for line in lines if 'vs' in line)
    print(f"   Lines containing 'vs': {vs_count}")
    
    if vs_count == 0:
        print(f"\n   ❌ PROBLEM: No 'vs' found in any line!")
        print(f"   The system cannot identify matches without 'vs' in the line.")
        print(f"\n   Expected format example:")
        print(f"   Bayern Munich vs Dortmund")
        
else:
    print(f"   ❌ File DOES NOT EXIST: input_matches.txt")
    print(f"\n   Please create this file in: {os.getcwd()}")

print("\n" + "="*60)
print("✅ DIAGNOSTIC COMPLETE")
print("="*60)
