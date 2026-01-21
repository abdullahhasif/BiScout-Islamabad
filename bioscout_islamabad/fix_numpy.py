#!/usr/bin/env python3
"""
Utility script to fix numpy compatibility issues with LlamaIndex.

This script handles the common error:
"numpy.dtype size changed, may indicate binary incompatibility. Expected 96 from C header, got 88 from PyObject"

Run this script before starting the application if you encounter this error.
"""

import os
import sys
import subprocess
import importlib

def check_numpy():
    """Check if numpy is installed and report version"""
    try:
        import numpy
        print(f"✓ Current numpy version: {numpy.__version__}")
        return True
    except ImportError:
        print("✗ Numpy is not installed")
        return False
    except Exception as e:
        print(f"✗ Error importing numpy: {e}")
        return False

def check_llamaindex():
    """Check if llama_index is installed and report version"""
    try:
        import llama_index
        print(f"✓ Current llama_index version: {llama_index.__version__}")
        return True
    except ImportError:
        print("✗ llama_index is not installed")
        return False
    except Exception as e:
        print(f"✗ Error importing llama_index: {e}")
        return False

def reinstall_numpy():
    """Reinstall numpy to fix compatibility issues"""
    print("\nReinstalling numpy to fix compatibility issues...")
    try:
        # Uninstall numpy first
        subprocess.check_call([sys.executable, "-m", "pip", "uninstall", "-y", "numpy"])
        print("✓ Successfully uninstalled numpy")
        
        # Install latest numpy
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--force-reinstall", "numpy"])
        print("✓ Successfully reinstalled numpy")
        
        # Verify the new installation
        import numpy
        print(f"✓ New numpy version: {numpy.__version__}")
        return True
    except Exception as e:
        print(f"✗ Error reinstalling numpy: {e}")
        return False

def fix_llamaindex_compatibility():
    """Fix compatibility issues with llama_index"""
    print("\nFixing llama_index compatibility issues...")
    try:
        # First, try to reinstall numpy
        if reinstall_numpy():
            print("✓ Numpy reinstalled successfully")
        else:
            print("✗ Failed to reinstall numpy")
            return False
        
        # Reinstall llama_index dependencies
        print("\nReinstalling llama_index dependencies...")
        packages = [
            "llama-index-core",
            "llama-index-embeddings-openai",
            "llama-index-llms-openai"
        ]
        
        for package in packages:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "--force-reinstall", package])
                print(f"✓ Successfully reinstalled {package}")
            except Exception as e:
                print(f"✗ Error reinstalling {package}: {e}")
        
        print("\nCompatibility fix completed.")
        return True
    except Exception as e:
        print(f"✗ Error fixing compatibility: {e}")
        return False

def main():
    print("=" * 60)
    print("BioScout LlamaIndex Numpy Compatibility Fix")
    print("=" * 60)
    print("This utility will fix numpy compatibility issues with LlamaIndex.")
    
    # Check current status
    print("\nChecking current environment:")
    numpy_ok = check_numpy()
    llamaindex_ok = check_llamaindex()
    
    if numpy_ok and llamaindex_ok:
        print("\nBoth numpy and llama_index are installed, but you may still have compatibility issues.")
        choice = input("Would you like to proceed with the fix anyway? [y/N]: ")
        if choice.lower() != 'y':
            print("Exiting without changes.")
            return
    
    # Run the fix
    success = fix_llamaindex_compatibility()
    
    if success:
        print("\n✓ Compatibility issues fixed successfully!")
        print("You should now be able to use BioScout with LlamaIndex without numpy errors.")
    else:
        print("\n✗ Failed to completely fix compatibility issues.")
        print("Try manually reinstalling the following packages:")
        print("  pip uninstall -y numpy")
        print("  pip install numpy")
        print("  pip install --force-reinstall llama-index-core llama-index-embeddings-openai llama-index-llms-openai")
    
    print("\nRestart the BioScout application after this fix.")

if __name__ == "__main__":
    main() 