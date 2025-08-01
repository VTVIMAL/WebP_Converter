#!/usr/bin/env python3
"""
Test script for Image Converter
Creates test images and converts them to various formats to verify functionality.
"""

import os
import tempfile
import shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from webp_converter import WebPConverter

def create_test_image(filename, size=(400, 300), format_type='PNG'):
    """Create a test image for conversion."""
    # Create a new image with a gradient background
    img = Image.new('RGB', size, color='white')
    draw = ImageDraw.Draw(img)
    
    # Draw a simple pattern
    for i in range(0, size[0], 20):
        for j in range(0, size[1], 20):
            color = (i % 255, j % 255, (i + j) % 255)
            draw.rectangle([i, j, i + 19, j + 19], fill=color)
    
    # Add some text
    try:
        font = ImageFont.load_default()
    except:
        font = None
    
    text = f"Test Image ({format_type})"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = (size[0] - text_width) // 2
    y = (size[1] - text_height) // 2
    
    draw.text((x, y), text, fill='white', font=font)
    
    # Save the test image
    img.save(filename, format=format_type)
    print(f"Created test image: {filename}")
    return filename

def create_test_directory():
    """Create a test directory with multiple images in different formats."""
    test_dir = Path("test_input_dir")
    test_dir.mkdir(exist_ok=True)
    
    # Create test images in different formats
    test_images = [
        ("test1.png", "PNG"),
        ("test2.jpg", "JPEG"),
        ("test3.bmp", "BMP"),
        ("test4.gif", "GIF"),
        ("test5.tiff", "TIFF")
    ]
    
    created_files = []
    for filename, format_type in test_images:
        filepath = test_dir / filename
        create_test_image(str(filepath), size=(400, 300), format_type=format_type)
        created_files.append(str(filepath))
    
    print(f"Created test directory with {len(created_files)} images")
    return str(test_dir), created_files

def verify_conversion(input_dir, output_dir, expected_format):
    """Verify that all images in input directory were converted to expected format."""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    if not output_path.exists():
        print(f"✗ Output directory {output_dir} does not exist!")
        return False
    
    # Get all input image files
    input_images = []
    for file in input_path.iterdir():
        if file.is_file() and file.suffix.lower() in ['.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.tif']:
            input_images.append(file)
    
    if not input_images:
        print("✗ No input images found!")
        return False
    
    # Check that each input image has a corresponding output file
    missing_files = []
    wrong_format_files = []
    skipped_files = []
    
    for input_file in input_images:
        # Expected output filename
        expected_output = output_path / f"{input_file.stem}.{expected_format.lower()}"
        
        # Check if input file is already in target format
        input_format = input_file.suffix.lower().lstrip('.')
        if input_format == expected_format.lower():
            # File is already in target format, so it's expected to be skipped
            skipped_files.append(str(input_file))
            continue
        
        if not expected_output.exists():
            missing_files.append(str(input_file))
        else:
            # Verify the file is actually in the correct format
            try:
                with Image.open(expected_output) as img:
                    actual_format = img.format
                    # Handle JPEG/JPG format name differences
                    expected_format_upper = expected_format.upper()
                    if expected_format_upper == 'JPG':
                        expected_format_upper = 'JPEG'
                    elif expected_format_upper == 'JPEG':
                        expected_format_upper = 'JPEG'
                    
                    if actual_format != expected_format_upper:
                        wrong_format_files.append((str(input_file), actual_format, expected_format_upper))
            except Exception as e:
                wrong_format_files.append((str(input_file), f"Error: {e}", expected_format.upper()))
    
    # Report results
    success = True
    
    if skipped_files:
        print(f"  Skipped files (already in target format): {skipped_files}")
    
    if missing_files:
        print(f"✗ Missing output files for: {missing_files}")
        success = False
    
    if wrong_format_files:
        print(f"✗ Files with wrong format:")
        for input_file, actual, expected in wrong_format_files:
            print(f"  {input_file}: got {actual}, expected {expected}")
        success = False
    
    if success:
        converted_count = len(input_images) - len(skipped_files)
        print(f"✓ All {converted_count} images successfully converted to {expected_format.upper()}")
        print(f"  Input directory: {input_dir}")
        print(f"  Output directory: {output_dir}")
    
    return success

def test_conversion():
    """Test the image conversion functionality."""
    print("Testing Image Converter...")
    
    # Create test directory
    test_dir, test_files = create_test_directory()
    
    # Initialize converter
    converter = WebPConverter()
    
    # Test different output formats
    test_formats = ['webp', 'png', 'jpg', 'bmp']
    
    for output_format in test_formats:
        print(f"\n{'='*50}")
        print(f"Testing conversion to {output_format.upper()}")
        print(f"{'='*50}")
        
        # Create output directory for this format
        output_dir = f"test_output_{output_format}"
        
        # Test directory conversion
        print(f"Converting {len(test_files)} images to {output_format.upper()}...")
        stats = converter.convert_directory(test_dir, output_dir, quality=80, output_format=output_format)
        
        # Print conversion statistics
        print(f"  Total files: {stats['total_files']}")
        print(f"  Converted: {stats['converted']}")
        print(f"  Failed: {stats['failed']}")
        print(f"  Skipped: {stats['skipped']}")
        
        # Verify conversion
        if stats['converted'] > 0:
            verify_conversion(test_dir, output_dir, output_format)
        else:
            print(f"✗ No files were converted to {output_format.upper()}")
    
    # Test single file conversion
    print(f"\n{'='*50}")
    print("Testing single file conversion")
    print(f"{'='*50}")
    
    test_file = test_files[0]  # Use first test file
    
    # Test conversion to different formats
    for output_format in ['webp', 'png', 'jpg']:
        output_file = f"single_test.{output_format}"
        print(f"Converting {test_file} to {output_format.upper()}...")
        
        success = converter.convert_image(test_file, output_file, quality=80, output_format=output_format)
        
        if success and os.path.exists(output_file):
            print(f"✓ Single file conversion to {output_format.upper()} successful!")
            file_size = os.path.getsize(output_file)
            print(f"  Output size: {file_size} bytes")
        else:
            print(f"✗ Single file conversion to {output_format.upper()} failed!")
    
    # Test lossless WebP conversion
    print(f"\nTesting lossless WebP conversion...")
    success = converter.convert_image(test_file, "test_lossless.webp", quality=80, lossless=True, output_format='webp')
    
    if success:
        print("✓ Lossless WebP conversion successful!")
        if os.path.exists("test_lossless.webp"):
            lossless_size = os.path.getsize("test_lossless.webp")
            print(f"  Lossless WebP size: {lossless_size} bytes")
    else:
        print("✗ Lossless WebP conversion failed!")
    
    # Test supported formats
    print(f"\n{'='*50}")
    print("Testing supported formats")
    print(f"{'='*50}")
    formats = converter.get_supported_formats()
    print(f"Supported input formats: {', '.join(formats)}")
    
    # Cleanup test files
    print(f"\n{'='*50}")
    print("Cleaning up test files")
    print(f"{'='*50}")
    
    cleanup_files = [
        "single_test.webp", "single_test.png", "single_test.jpg",
        "test_lossless.webp"
    ]
    
    # Add test directory files
    for file in test_files:
        cleanup_files.append(file)
    
    # Add output directories
    for output_format in test_formats:
        output_dir = f"test_output_{output_format}"
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
            print(f"  Removed directory: {output_dir}")
    
    # Remove test input directory
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
        print(f"  Removed directory: {test_dir}")
    
    # Remove individual files
    for file in cleanup_files:
        if os.path.exists(file):
            os.remove(file)
            print(f"  Removed: {file}")
    
    print("\n✓ All tests completed!")

if __name__ == "__main__":
    test_conversion() 