#!/usr/bin/env python3
"""
Folder Checker for Image Conversion
Cross-checks input and output folders to identify missing images and files.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple
import argparse
from collections import defaultdict, Counter

SUPPORTED_FORMATS = {
    '.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif',
    '.gif', '.ico', '.ppm', '.pgm', '.pbm', '.pnm', '.webp'
}

class FolderChecker:
    """Class to check and compare folder contents."""
    
    def __init__(self, output_format=None):
        self.supported_formats = {
            '.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', 
            '.gif', '.ico', '.ppm', '.pgm', '.pbm', '.pnm', '.webp'
        }
        self.output_format = output_format.lower() if output_format else None
        self.output_extension = f'.{self.output_format}' if self.output_format else None
    
    def detect_output_format(self, output_folder: Path) -> str:
        """
        Automatically detect the most common output format in the output folder.
        
        Args:
            output_folder: Path to the output folder
            
        Returns:
            str: The detected output format (e.g., 'webp', 'png', 'jpg')
        """
        if not output_folder.exists():
            print(f"Warning: Output folder {output_folder} does not exist!")
            return 'webp'  # Default fallback
        
        format_counts = Counter()
        
        for root, dirs, files in os.walk(output_folder):
            for file in files:
                file_path = Path(root) / file
                suffix = file_path.suffix.lower()
                if suffix in self.supported_formats:
                    format_counts[suffix] += 1
        
        if not format_counts:
            print("Warning: No supported image files found in output folder!")
            return 'webp'  # Default fallback
        
        # Get the most common format
        most_common_format = format_counts.most_common(1)[0][0]
        detected_format = most_common_format.lstrip('.')  # Remove the dot
        
        print(f"🔍 Auto-detected output format: {detected_format.upper()} ({format_counts[most_common_format]} files)")
        return detected_format
    
    def scan_folder(self, folder_path: Path) -> Dict[str, Set[Path]]:
        """
        Scan a folder recursively and categorize files.
        
        Args:
            folder_path: Path to the folder to scan
            
        Returns:
            Dict with categories: 'images', 'output_files', 'other_files', 'directories'
        """
        result = {
            'images': set(),
            'output_files': set(),
            'other_files': set(),
            'directories': set()
        }
        
        if not folder_path.exists():
            print(f"Warning: Folder {folder_path} does not exist!")
            return result
        
        for root, dirs, files in os.walk(folder_path):
            root_path = Path(root)
            
            # Add directories
            for dir_name in dirs:
                result['directories'].add(root_path / dir_name)
            
            # Categorize files
            for file_name in files:
                file_path = root_path / file_name
                suffix = file_path.suffix.lower()
                
                if suffix == self.output_extension:
                    result['output_files'].add(file_path)
                elif suffix in self.supported_formats:
                    result['images'].add(file_path)
                else:
                    result['other_files'].add(file_path)
        
        return result
    
    def get_expected_output_files(self, input_images: Set[Path], input_folder: Path, output_folder: Path) -> Set[Path]:
        """
        Generate expected output file paths based on input images and naming convention.
        The converter uses a smart naming system to handle duplicates, so we need to be flexible.
        
        Args:
            input_images: Set of input image paths
            input_folder: Input folder path
            output_folder: Output folder path
            
        Returns:
            Set of expected output file paths
        """
        expected_output = set()
        
        # Group images by their stem (filename without extension) to handle duplicates
        stem_groups = {}
        for img_path in input_images:
            rel_path = img_path.relative_to(input_folder)
            stem = rel_path.stem
            if stem not in stem_groups:
                stem_groups[stem] = []
            stem_groups[stem].append(rel_path)
        
        for stem, image_paths in stem_groups.items():
            if len(image_paths) == 1:
                # Single image with this name - expect simple output extension
                rel_path = image_paths[0]
                expected_output_path = output_folder / rel_path.parent / f"{stem}{self.output_extension}"
                expected_output.add(expected_output_path)
            else:
                # Multiple images with same stem - expect with original extension suffix
                for rel_path in image_paths:
                    original_ext = rel_path.suffix.lower()[1:]  # Remove the dot
                    expected_output_path = output_folder / rel_path.parent / f"{stem}_{original_ext}{self.output_extension}"
                    expected_output.add(expected_output_path)
        
        return expected_output
    
    def debug_naming_mismatch(self, input_images: Set[Path], output_files: Set[Path], input_folder: Path, output_folder: Path):
        """
        Debug helper to understand naming mismatches between input and output.
        
        Args:
            input_images: Set of input image paths
            output_files: Set of output file paths
            input_folder: Input folder path
            output_folder: Output folder path
        """
        print(f"\n🔍 DEBUG: Analyzing naming patterns...")
        print(f"Input images ({len(input_images)}):")
        for img in sorted(input_images):
            rel_path = img.relative_to(input_folder)
            print(f"  {rel_path}")
        
        print(f"\nOutput files ({len(output_files)}):")
        for out_file in sorted(output_files):
            rel_path = out_file.relative_to(output_folder)
            print(f"  {rel_path}")
        
        # Show expected vs actual
        expected = self.get_expected_output_files(input_images, input_folder, output_folder)
        print(f"\nExpected output files ({len(expected)}):")
        for exp in sorted(expected):
            rel_path = exp.relative_to(output_folder)
            print(f"  {rel_path}")
    
    def check_conversion_completeness(self, input_folder: Path, output_folder: Path) -> Dict:
        """
        Check if all images from input folder have been converted to the specified format in output folder.
        
        Args:
            input_folder: Input folder path
            output_folder: Output folder path
            
        Returns:
            Dict with check results and statistics
        """
        # Auto-detect output format if not specified
        if not self.output_format:
            self.output_format = self.detect_output_format(output_folder)
            self.output_extension = f'.{self.output_format}'
        
        print(f"Scanning input folder: {input_folder}")
        input_contents = self.scan_folder(input_folder)
        
        print(f"Scanning output folder: {output_folder}")
        output_contents = self.scan_folder(output_folder)
        
        # Filter out files already in target format from input images - they shouldn't be converted
        convertible_images = {img for img in input_contents['images'] 
                            if img.suffix.lower() != self.output_extension}
        
        print(f"Found {len(input_contents['images'])} total images in input")
        print(f"Found {len(input_contents['output_files'])} {self.output_format.upper()} files in input (will be skipped)")
        print(f"Found {len(convertible_images)} convertible images in input")
        
        # Get expected output files (only for convertible images)
        expected_output = self.get_expected_output_files(
            convertible_images, input_folder, output_folder
        )
        
        # Find missing output files
        missing_output = expected_output - output_contents['output_files']
        
        # Find unexpected output files (not from our conversion)
        unexpected_output = output_contents['output_files'] - expected_output
        
        # Check for missing directories
        input_dirs = {d.relative_to(input_folder) for d in input_contents['directories']}
        output_dirs = {d.relative_to(output_folder) for d in output_contents['directories']}
        missing_dirs = input_dirs - output_dirs
        
        # Check for missing other files
        input_other = {f.relative_to(input_folder) for f in input_contents['other_files']}
        output_other = {f.relative_to(output_folder) for f in output_contents['other_files']}
        missing_other = input_other - output_other
        
        return {
            'input_stats': {
                'total_images': len(input_contents['images']),
                'total_output_files': len(input_contents['output_files']),
                'convertible_images': len(convertible_images),
                'total_other_files': len(input_contents['other_files']),
                'total_directories': len(input_contents['directories'])
            },
            'output_stats': {
                'total_output_files': len(output_contents['output_files']),
                'total_other_files': len(output_contents['other_files']),
                'total_directories': len(output_contents['directories'])
            },
            'missing_output': missing_output,
            'unexpected_output': unexpected_output,
            'missing_directories': missing_dirs,
            'missing_other_files': missing_other,
            'input_images': convertible_images,  # Use only convertible images
            'output_files': output_contents['output_files']
        }
    
    def print_report(self, results: Dict, input_folder: Path, output_folder: Path):
        """
        Print a detailed report of the folder comparison.
        
        Args:
            results: Results from check_conversion_completeness
            input_folder: Input folder path
            output_folder: Output folder path
        """
        print("\n" + "="*60)
        print(f"FOLDER COMPARISON REPORT ({self.output_format.upper()} CONVERSION)")
        print("="*60)
        
        # Input folder statistics
        print(f"\n📁 INPUT FOLDER: {input_folder}")
        print(f"   Total images: {results['input_stats']['total_images']}")
        print(f"   {self.output_format.upper()} files (skipped): {results['input_stats']['total_output_files']}")
        print(f"   Convertible images: {results['input_stats']['convertible_images']}")
        print(f"   Other files: {results['input_stats']['total_other_files']}")
        print(f"   Directories: {results['input_stats']['total_directories']}")
        
        # Output folder statistics
        print(f"\n📁 OUTPUT FOLDER: {output_folder}")
        print(f"   {self.output_format.upper()} files: {results['output_stats']['total_output_files']}")
        print(f"   Other files: {results['output_stats']['total_other_files']}")
        print(f"   Directories: {results['output_stats']['total_directories']}")
        
        # Detailed checklist for each input image
        print(f"\n📋 CONVERSION CHECKLIST:")
        print("-" * 60)
        
        # Get expected output files for comparison
        expected_output = self.get_expected_output_files(
            results['input_images'], input_folder, output_folder
        )
        
        # Create a mapping of input files to their expected output
        input_to_expected = {}
        for input_img in results['input_images']:
            rel_path = input_img.relative_to(input_folder)
            stem = rel_path.stem
            parent = rel_path.parent
            
            # Find the expected output file for this input
            for expected in expected_output:
                if expected.stem == stem and expected.parent == output_folder / parent:
                    input_to_expected[input_img] = expected
                    break
            else:
                # Handle multiple files with same stem
                for expected in expected_output:
                    if expected.stem.startswith(f"{stem}_") and expected.parent == output_folder / parent:
                        input_to_expected[input_img] = expected
                        break
        
        # Check each input image
        successful_conversions = 0
        skipped_conversions = 0
        missing_conversions = 0
        
        for input_img in sorted(results['input_images']):
            rel_input = input_img.relative_to(input_folder)
            
            # Check if input is already in target format
            if input_img.suffix.lower() == self.output_extension:
                print(f"⏭️  SKIPPED: {rel_input} (already {self.output_format.upper()})")
                skipped_conversions += 1
                continue
            
            # Check if expected output exists
            if input_img in input_to_expected:
                expected_output_file = input_to_expected[input_img]
                if expected_output_file in results['output_files']:
                    print(f"✅ CONVERTED: {rel_input} → {expected_output_file.relative_to(output_folder)}")
                    successful_conversions += 1
                else:
                    print(f"❌ MISSING: {rel_input} → {expected_output_file.relative_to(output_folder)}")
                    missing_conversions += 1
            else:
                print(f"❓ UNKNOWN: {rel_input} (no expected output found)")
                missing_conversions += 1
        
        # Summary statistics
        total_checked = len(results['input_images'])
        conversion_rate = (successful_conversions / total_checked * 100) if total_checked > 0 else 0
        
        print("-" * 60)
        print(f"📊 SUMMARY:")
        print(f"   Total images checked: {total_checked}")
        print(f"   ✅ Successfully converted: {successful_conversions}")
        print(f"   ⏭️  Skipped (already {self.output_format.upper()}): {skipped_conversions}")
        print(f"   ❌ Missing conversions: {missing_conversions}")
        print(f"   📈 Conversion rate: {conversion_rate:.1f}%")
        
        # Overall status
        if missing_conversions == 0:
            if successful_conversions > 0:
                print(f"\n🎉 PERFECT CONVERSION! All {successful_conversions} images converted to {self.output_format.upper()}")
            else:
                print(f"\n✅ ALL IMAGES ALREADY IN {self.output_format.upper()} FORMAT!")
        elif conversion_rate >= 90:
            print(f"\n✅ GOOD CONVERSION! {conversion_rate:.1f}% of images converted")
        elif conversion_rate >= 50:
            print(f"\n⚠️  PARTIAL CONVERSION! Only {conversion_rate:.1f}% of images converted")
        else:
            print(f"\n❌ POOR CONVERSION! Only {conversion_rate:.1f}% of images converted")
        
        # Show unexpected files if any
        if results['unexpected_output']:
            print(f"\n⚠️  UNEXPECTED {self.output_format.upper()} FILES ({len(results['unexpected_output'])}):")
            for unexpected in sorted(results['unexpected_output']):
                print(f"   {unexpected.relative_to(output_folder)}")
        
        # Show missing directories and other files
        if results['missing_directories']:
            print(f"\n❌ MISSING DIRECTORIES ({len(results['missing_directories'])}):")
            for missing_dir in sorted(results['missing_directories']):
                print(f"   {missing_dir}")
        
        if results['missing_other_files']:
            print(f"\n❌ MISSING OTHER FILES ({len(results['missing_other_files'])}):")
            for missing_file in sorted(results['missing_other_files']):
                print(f"   {missing_file}")
    
    def generate_missing_list(self, results: Dict, output_file: str = "missing_files.txt"):
        """
        Generate a text file listing all missing files.
        
        Args:
            results: Results from check_conversion_completeness
            output_file: Output file name
        """
        missing_files = []
        
        # Add missing output files
        for missing in results['missing_output']:
            missing_files.append(str(missing))
        
        # Add missing directories
        for missing_dir in results['missing_directories']:
            missing_files.append(f"DIR: {missing_dir}")
        
        # Add missing other files
        for missing_file in results['missing_other_files']:
            missing_files.append(str(missing_file))
        
        if missing_files:
            with open(output_file, 'w') as f:
                f.write(f"Missing files for {self.output_format.upper()} conversion\n")
                f.write("="*50 + "\n\n")
                for file in sorted(missing_files):
                    f.write(f"{file}\n")
            
            print(f"\n📄 Missing files list saved to: {output_file}")
        else:
            print(f"\n✅ No missing files to report!")


def get_all_files(folder: Path) -> Set[Path]:
    """
    Recursively get all files in a folder, returning their relative paths.
    """
    all_files = set()
    for root, dirs, files in os.walk(folder):
        root_path = Path(root)
        for file in files:
            rel_path = (root_path / file).relative_to(folder)
            all_files.add(rel_path)
    return all_files


def predict_output_filenames(input_path: Path, output_format='webp') -> Set[Path]:
    """
    Predict output filenames based on input files and converter logic,
    using the converter's unique naming logic for duplicates.
    Returns a set of relative output paths.
    """
    output_extension = f'.{output_format.lower()}'
    
    # Group images by (relative parent, stem)
    groups: Dict[(Path, str), List[Path]] = defaultdict(list)
    for root, dirs, files in os.walk(input_path):
        root_path = Path(root)
        for file in files:
            file_path = root_path / file
            suffix = file_path.suffix.lower()
            if suffix in SUPPORTED_FORMATS and suffix != output_extension:
                rel_path = file_path.relative_to(input_path)
                groups[(rel_path.parent, rel_path.stem)].append(rel_path)
    
    predicted = set()
    for (parent, stem), rel_paths in groups.items():
        if len(rel_paths) == 1:
            # Only one file with this stem: output is stem.output_extension
            predicted.add(parent / f"{stem}{output_extension}")
        else:
            # Multiple files with same stem: use suffix in name
            for rel_path in rel_paths:
                ext = rel_path.suffix.lower()[1:]  # without dot
                predicted.add(parent / f"{stem}_{ext}{output_extension}")
    return predicted


def get_folder_size(folder: Path) -> int:
    """
    Recursively calculate the total size of all files in a folder (in bytes).
    """
    total_size = 0
    for root, dirs, files in os.walk(folder):
        for file in files:
            fp = Path(root) / file
            if fp.is_file():
                total_size += fp.stat().st_size
    return total_size


def main():
    parser = argparse.ArgumentParser(
        description="Check that all input images are present in output, considering unique renaming.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s /path/to/input /path/to/output
  %(prog)s /path/to/input /path/to/output --output-format png
  %(prog)s /path/to/input /path/to/output --output-format jpg
        """
    )
    parser.add_argument('input_folder', help='Input folder path')
    parser.add_argument('output_folder', help='Output folder path')
    parser.add_argument('--output-format', help='Expected output format (auto-detected if not specified)')
    args = parser.parse_args()

    input_path = Path(args.input_folder)
    output_path = Path(args.output_folder)
    output_format = args.output_format.lower() if args.output_format else None

    if not input_path.exists():
        print(f"Error: Input folder '{input_path}' does not exist!")
        sys.exit(1)
    if not output_path.exists():
        print(f"Error: Output folder '{output_path}' does not exist!")
        sys.exit(1)

    # Use the FolderChecker class for comprehensive checking
    checker = FolderChecker(output_format=output_format)
    results = checker.check_conversion_completeness(input_path, output_path)
    checker.print_report(results, input_path, output_path)
    
    # Generate missing files list if there are missing files
    if results['missing_output'] or results['missing_directories'] or results['missing_other_files']:
        checker.generate_missing_list(results)

    # Calculate folder sizes
    input_size = get_folder_size(input_path)
    output_size = get_folder_size(output_path)

    print(f"\n📊 FOLDER SIZE COMPARISON:")
    print(f"Total size of input:  {input_size / (1024*1024):.2f} MB ({input_size} bytes)")
    print(f"Total size of output: {output_size / (1024*1024):.2f} MB ({output_size} bytes)")
    if input_size > 0:
        ratio = (output_size / input_size) * 100
        print(f"Size ratio (output/input): {ratio:.1f}%")
        if ratio < 100:
            print(f"Space saved: {100 - ratio:.1f}%")
        else:
            print(f"Output is {ratio - 100:.1f}% larger than input")
    else:
        print("Input folder is empty!")

    print("="*60)


if __name__ == "__main__":
    main() 