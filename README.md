# WebP Image Converter

A Python application that converts images from various formats to WebP format. Supports both command-line and GUI interfaces.

## Features

- **Multiple Input Formats**: Supports JPG, JPEG, PNG, BMP, TIFF, GIF, ICO, PPM, PGM, PBM, and PNM
- **Flexible Output**: Convert single files or entire directories
- **Quality Control**: Adjustable quality settings (0-100)
- **Lossless Option**: Option for lossless compression
- **Dual Interface**: Both command-line and GUI interfaces
- **Batch Processing**: Convert multiple images at once
- **Progress Tracking**: Real-time conversion status and logging

## Installation

### Prerequisites

- Python 3.6 or higher
- pip (Python package installer)

### Install Dependencies

```bash
pip install -r requirements.txt
```

Or install Pillow directly:

```bash
pip install Pillow
```

## Usage

### Command Line Interface

#### Basic Usage

```bash
# Convert a single image
python webp_converter.py image.jpg

# Convert with custom output name
python webp_converter.py image.jpg -o output.webp

# Convert all images in a directory
python webp_converter.py /path/to/images/

# Convert with specific quality
python webp_converter.py image.jpg -q 90

# Use lossless compression
python webp_converter.py image.jpg --lossless
```

#### Command Line Options

- `input`: Input file or directory (required)
- `-o, --output`: Output file or directory
- `-q, --quality`: WebP quality (0-100, default: 80)
- `--lossless`: Use lossless compression
- `--gui`: Start GUI interface
- `--formats`: Show supported input formats

#### Examples

```bash
# Show supported formats
python webp_converter.py --formats

# Convert with high quality
python webp_converter.py photo.png -q 95 -o high_quality.webp

# Convert directory with lossless compression
python webp_converter.py /photos/ --lossless -o /webp_photos/

# Start GUI
python webp_converter.py --gui
```

### GUI Interface

To start the graphical interface:

```bash
python webp_converter.py --gui
```

Or simply run without arguments:

```bash
python webp_converter.py
```

#### GUI Features

- **File/Directory Selection**: Browse for input files or directories
- **Output Configuration**: Choose output location
- **Quality Slider**: Adjust quality from 0-100
- **Lossless Option**: Toggle lossless compression
- **Real-time Logging**: See conversion progress and results
- **Batch Processing**: Convert multiple files at once

## Supported Formats

### Input Formats
- **JPEG**: .jpg, .jpeg
- **PNG**: .png
- **BMP**: .bmp
- **TIFF**: .tiff, .tif
- **GIF**: .gif
- **ICO**: .ico
- **PPM**: .ppm
- **PGM**: .pgm
- **PBM**: .pbm
- **PNM**: .pnm

### Output Format
- **Any format supported by Pillow**: e.g., .webp, .png, .jpg, .jpeg, .bmp, .tiff, .gif, .ico, .ppm, .pgm, .pbm, .pnm

## Technical Details

### Image Processing

The converter handles various image modes:
- **RGB images**: Converted directly to the target format
- **RGBA images**: Transparent background converted to white (for formats that do not support alpha)
- **Palette images**: Converted to RGB with transparency handling
- **Other modes**: Converted to RGB as needed

### Quality Settings

- **Quality 0-100**: Controls compression level for lossy formats (higher = better quality, larger file)
- **Lossless**: Preserves exact pixel values (for WebP only)

### Error Handling

- Graceful handling of unsupported formats
- Detailed error messages for troubleshooting
- Statistics reporting for batch operations

## Examples

### Single File Conversion

```bash
# Convert a PNG to WebP with default settings
python webp_converter.py photo.png

# Convert a PNG to JPEG
python webp_converter.py photo.png --to-format jpg

# Convert a JPEG to PNG
python webp_converter.py photo.jpg --to-format png

# Convert with high quality
python webp_converter.py photo.png --to-format jpg -q 95

# Convert with custom output name
python webp_converter.py photo.png --to-format png -o optimized_photo.png
```

### Directory Conversion

```bash
# Convert all images in current directory to PNG
python webp_converter.py . --to-format png

# Convert with specific output directory
python webp_converter.py /input_photos/ --to-format jpg -o /jpg_photos/

# Convert with lossless compression (WebP only)
python webp_converter.py /photos/ --to-format webp --lossless
```

### Batch Processing Output

When converting directories, you'll see output like:

```
✓ Converted: photo1.jpg -> photo1.webp
✓ Converted: photo2.png -> photo2.webp
✗ Failed: unsupported.txt

Conversion Summary:
Total files: 3
Converted: 2
Failed: 1
Skipped: 0
```

## Troubleshooting

### Common Issues

1. **"No module named 'PIL'"**
   - Install Pillow: `pip install Pillow`

2. **"Permission denied"**
   - Check file/directory permissions
   - Ensure write access to output location

3. **"Unsupported format"**
   - Check if the file format is supported
   - Run `python webp_converter.py --formats` to see supported formats

4. **GUI not working**
   - Ensure tkinter is installed (usually included with Python)
   - On some Linux systems: `sudo apt-get install python3-tk`

### Performance Tips

- For large directories, use command-line interface for better performance
- Use appropriate quality settings (80-90 is usually sufficient)
- Consider lossless compression only for images that require exact pixel preservation

## License

This project is open source and available under the MIT License.

## Contributing

Feel free to submit issues, feature requests, or pull requests to improve the converter. 

Updating readme