#!/usr/bin/env python3
"""
Test script for WebP Image Converter
Creates a test image and converts it to WebP to verify functionality.
"""

import os
from PIL import Image, ImageDraw, ImageFont
from webp_converter import WebPConverter

def create_test_image(filename="test_image.png", size=(400, 300)):
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
        # Try to use a default font
        font = ImageFont.load_default()
    except:
        font = None
    
    text = "WebP Test Image"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = (size[0] - text_width) // 2
    y = (size[1] - text_height) // 2
    
    draw.text((x, y), text, fill='white', font=font)
    
    # Save the test image
    img.save(filename)
    print(f"Created test image: {filename}")
    return filename

def test_conversion():
    """Test the WebP conversion functionality."""
    print("Testing WebP Image Converter...")
    
    # Create test image
    test_file = create_test_image()
    
    # Initialize converter
    converter = WebPConverter()
    
    # Test single file conversion
    print("\n1. Testing single file conversion...")
    success = converter.convert_image(test_file, "test_output.webp", quality=80)
    
    if success:
        print("✓ Single file conversion successful!")
        
        # Check if output file exists
        if os.path.exists("test_output.webp"):
            original_size = os.path.getsize(test_file)
            webp_size = os.path.getsize("test_output.webp")
            compression_ratio = (1 - webp_size / original_size) * 100
            
            print(f"  Original size: {original_size} bytes")
            print(f"  WebP size: {webp_size} bytes")
            print(f"  Compression: {compression_ratio:.1f}%")
        else:
            print("✗ Output file not found!")
    else:
        print("✗ Single file conversion failed!")
    
    # Test lossless conversion
    print("\n2. Testing lossless conversion...")
    success = converter.convert_image(test_file, "test_lossless.webp", quality=80, lossless=True)
    
    if success:
        print("✓ Lossless conversion successful!")
        if os.path.exists("test_lossless.webp"):
            lossless_size = os.path.getsize("test_lossless.webp")
            print(f"  Lossless WebP size: {lossless_size} bytes")
    else:
        print("✗ Lossless conversion failed!")
    
    # Test supported formats
    print("\n3. Testing supported formats...")
    formats = converter.get_supported_formats()
    print(f"Supported formats: {', '.join(formats)}")
    
    # Cleanup test files
    print("\n4. Cleaning up test files...")
    for file in [test_file, "test_output.webp", "test_lossless.webp"]:
        if os.path.exists(file):
            os.remove(file)
            print(f"  Removed: {file}")
    
    print("\n✓ All tests completed!")

if __name__ == "__main__":
    test_conversion() 