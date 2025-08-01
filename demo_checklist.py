#!/usr/bin/env python3
"""
Demo script to show the new checklist format for folder checker
"""

import os
from pathlib import Path
from PIL import Image
from folder_checker import FolderChecker

def create_test_files():
    """Create test input and output files to demonstrate the checklist."""
    
    # Create directories
    input_dir = Path("demo_input")
    output_dir = Path("demo_output")
    input_dir.mkdir(exist_ok=True)
    output_dir.mkdir(exist_ok=True)
    
    # Create test images
    img1 = Image.new('RGB', (100, 100), 'red')
    img1.save(input_dir / "photo1.png")
    
    img2 = Image.new('RGB', (100, 100), 'blue')
    img2.save(input_dir / "photo2.jpg")
    
    img3 = Image.new('RGB', (100, 100), 'green')
    img3.save(input_dir / "photo3.bmp")
    
    # Create some output files (simulating partial conversion)
    img1.save(output_dir / "photo1.png")  # Converted
    img2.save(output_dir / "photo2.png")  # Converted
    # photo3.bmp is missing from output
    
    print("Created test files:")
    print(f"Input: {list(input_dir.glob('*'))}")
    print(f"Output: {list(output_dir.glob('*'))}")

def run_demo():
    """Run the folder checker demo."""
    print("=" * 60)
    print("FOLDER CHECKER CHECKLIST DEMO")
    print("=" * 60)
    
    # Create test files
    create_test_files()
    
    # Run folder checker
    print("\nRunning folder checker...")
    checker = FolderChecker()
    results = checker.check_conversion_completeness(
        Path("demo_input"), 
        Path("demo_output")
    )
    checker.print_report(results, Path("demo_input"), Path("demo_output"))
    
    # Cleanup
    import shutil
    shutil.rmtree("demo_input")
    shutil.rmtree("demo_output")
    print("\nDemo completed!")

if __name__ == "__main__":
    run_demo() 