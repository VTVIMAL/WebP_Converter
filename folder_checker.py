#!/usr/bin/env python3
"""
Folder Checker for WebP Conversion
Cross-checks input and output folders to identify missing images and files.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple
import argparse
from collections import defaultdict

SUPPORTED_FORMATS = {
    '.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif',
    '.gif', '.ico', '.ppm', '.pgm', '.pbm', '.pnm', '.webp'
}

class FolderChecker:
    """Class to check and compare folder contents."""
    
    def __init__(self):
        self.supported_formats = {
            '.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', 
            '.gif', '.ico', '.ppm', '.pgm', '.pbm', '.pnm'
        }
    
    def scan_folder(self, folder_path: Path) -> Dict[str, Set[Path]]:
        """
        Scan a folder recursively and categorize files.
        
        Args:
            folder_path: Path to the folder to scan
            
        Returns:
            Dict with categories: 'images', 'webp', 'other_files', 'directories'
        """
        result = {
            'images': set(),
            'webp': set(),
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
                
                if suffix == '.webp':
                    result['webp'].add(file_path)
                elif suffix in self.supported_formats:
                    result['images'].add(file_path)
                else:
                    result['other_files'].add(file_path)
        
        return result
    
    def get_expected_webp_files(self, input_images: Set[Path], input_folder: Path, output_folder: Path) -> Set[Path]:
        """
        Generate expected WebP file paths based on input images and naming convention.
        The converter uses a smart naming system to handle duplicates, so we need to be flexible.
        
        Args:
            input_images: Set of input image paths
            input_folder: Input folder path
            output_folder: Output folder path
            
        Returns:
            Set of expected WebP file paths
        """
        expected_webp = set()
        
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
                # Single image with this name - expect simple .webp
                rel_path = image_paths[0]
                expected_webp_path = output_folder / rel_path.parent / f"{stem}.webp"
                expected_webp.add(expected_webp_path)
            else:
                # Multiple images with same name but different formats
                # The converter will create: stem.webp, stem_jpg.webp, stem_png.webp, etc.
                for rel_path in image_paths:
                    format_suffix = f"{stem}_{rel_path.suffix[1:]}.webp"
                    expected_webp_path = output_folder / rel_path.parent / format_suffix
                    expected_webp.add(expected_webp_path)
        
        return expected_webp
    
    def debug_naming_mismatch(self, input_images: Set[Path], output_webp: Set[Path], input_folder: Path, output_folder: Path):
        """
        Debug method to show the naming mismatch between expected and actual files.
        """
        print(f"\n🔍 DEBUGGING NAMING MISMATCH:")
        print(f"Input images: {len(input_images)}")
        print(f"Output WebP files: {len(output_webp)}")
        
        # Get expected files
        expected_webp = self.get_expected_webp_files(input_images, input_folder, output_folder)
        print(f"Expected WebP files: {len(expected_webp)}")
        
        # Show some examples of expected vs actual
        print(f"\n📋 SAMPLE COMPARISON (first 10 files):")
        print("-" * 60)
        
        expected_list = sorted(expected_webp)
        actual_list = sorted(output_webp)
        
        print("EXPECTED FILES:")
        for i, expected in enumerate(expected_list[:10]):
            exists = "✅" if expected in output_webp else "❌"
            print(f"  {exists} {expected}")
        
        print(f"\nACTUAL FILES:")
        for i, actual in enumerate(actual_list[:10]):
            expected = "✅" if actual in expected_webp else "❌"
            print(f"  {expected} {actual}")
        
        # Show missing files
        missing = expected_webp - output_webp
        if missing:
            print(f"\n❌ MISSING FILES (first 10):")
            for missing_file in sorted(missing)[:10]:
                print(f"  {missing_file}")
        
        # Show unexpected files
        unexpected = output_webp - expected_webp
        if unexpected:
            print(f"\n⚠️  UNEXPECTED FILES (first 10):")
            for unexpected_file in sorted(unexpected)[:10]:
                print(f"  {unexpected_file}")
        
        print("-" * 60)
    
    def check_conversion_completeness(self, input_folder: Path, output_folder: Path) -> Dict:
        """
        Check if all images from input folder have been converted to WebP in output folder.
        
        Args:
            input_folder: Input folder path
            output_folder: Output folder path
            
        Returns:
            Dict with check results and statistics
        """
        print(f"Scanning input folder: {input_folder}")
        input_contents = self.scan_folder(input_folder)
        
        print(f"Scanning output folder: {output_folder}")
        output_contents = self.scan_folder(output_folder)
        
        # Filter out WebP files from input images - they shouldn't be converted
        convertible_images = {img for img in input_contents['images'] 
                            if img.suffix.lower() != '.webp'}
        
        print(f"Found {len(input_contents['images'])} total images in input")
        print(f"Found {len(input_contents['webp'])} WebP files in input (will be skipped)")
        print(f"Found {len(convertible_images)} convertible images in input")
        
        # Get expected WebP files (only for convertible images)
        expected_webp = self.get_expected_webp_files(
            convertible_images, input_folder, output_folder
        )
        
        # Find missing WebP files
        missing_webp = expected_webp - output_contents['webp']
        
        # Find unexpected WebP files (not from our conversion)
        unexpected_webp = output_contents['webp'] - expected_webp
        
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
                'total_webp': len(input_contents['webp']),
                'convertible_images': len(convertible_images),
                'total_other_files': len(input_contents['other_files']),
                'total_directories': len(input_contents['directories'])
            },
            'output_stats': {
                'total_webp': len(output_contents['webp']),
                'total_other_files': len(output_contents['other_files']),
                'total_directories': len(output_contents['directories'])
            },
            'missing_webp': missing_webp,
            'unexpected_webp': unexpected_webp,
            'missing_directories': missing_dirs,
            'missing_other_files': missing_other,
            'input_images': convertible_images,  # Use only convertible images
            'output_webp': output_contents['webp']
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
        print("FOLDER COMPARISON REPORT")
        print("="*60)
        
        # Input folder statistics
        print(f"\n📁 INPUT FOLDER: {input_folder}")
        print(f"   Total images: {results['input_stats']['total_images']}")
        print(f"   WebP files (skipped): {results['input_stats']['total_webp']}")
        print(f"   Convertible images: {results['input_stats']['convertible_images']}")
        print(f"   Other files: {results['input_stats']['total_other_files']}")
        print(f"   Directories: {results['input_stats']['total_directories']}")
        
        # Output folder statistics
        print(f"\n📁 OUTPUT FOLDER: {output_folder}")
        print(f"   WebP files: {results['output_stats']['total_webp']}")
        print(f"   Other files: {results['output_stats']['total_other_files']}")
        print(f"   Directories: {results['output_stats']['total_directories']}")
        
        # Missing WebP files
        if results['missing_webp']:
            print(f"\n❌ MISSING WEBP FILES ({len(results['missing_webp'])}):")
            for missing in sorted(results['missing_webp']):
                print(f"   {missing}")
        else:
            print(f"\n✅ ALL IMAGES CONVERTED TO WEBP!")
        
        # Unexpected WebP files
        if results['unexpected_webp']:
            print(f"\n⚠️  UNEXPECTED WEBP FILES ({len(results['unexpected_webp'])}):")
            for unexpected in sorted(results['unexpected_webp']):
                print(f"   {unexpected}")
        
        # Missing directories
        if results['missing_directories']:
            print(f"\n❌ MISSING DIRECTORIES ({len(results['missing_directories'])}):")
            for missing_dir in sorted(results['missing_directories']):
                print(f"   {missing_dir}")
        
        # Missing other files
        if results['missing_other_files']:
            print(f"\n❌ MISSING OTHER FILES ({len(results['missing_other_files'])}):")
            for missing_file in sorted(results['missing_other_files']):
                print(f"   {missing_file}")
        
        # Summary
        print(f"\n📊 SUMMARY:")
        total_convertible_images = results['input_stats']['convertible_images']
        total_output_webp = results['output_stats']['total_webp']
        missing_count = len(results['missing_webp'])
        
        if total_convertible_images > 0:
            conversion_rate = ((total_convertible_images - missing_count) / total_convertible_images) * 100
            print(f"   Conversion rate: {conversion_rate:.1f}%")
            print(f"   Successfully converted: {total_convertible_images - missing_count}/{total_convertible_images}")
        
        if missing_count > 0:
            print(f"   Missing conversions: {missing_count}")
            print(f"   Status: ❌ INCOMPLETE")
        else:
            print(f"   Status: ✅ COMPLETE")
        
        print("="*60)
    
    def generate_missing_list(self, results: Dict, output_file: str = "missing_files.txt"):
        """
        Generate a text file listing all missing files.
        
        Args:
            results: Results from check_conversion_completeness
            output_file: Output file name
        """
        with open(output_file, 'w') as f:
            f.write("MISSING FILES REPORT\n")
            f.write("="*50 + "\n\n")
            
            if results['missing_webp']:
                f.write("MISSING WEBP FILES:\n")
                f.write("-" * 20 + "\n")
                for missing in sorted(results['missing_webp']):
                    f.write(f"{missing}\n")
                f.write("\n")
            
            if results['missing_directories']:
                f.write("MISSING DIRECTORIES:\n")
                f.write("-" * 20 + "\n")
                for missing_dir in sorted(results['missing_directories']):
                    f.write(f"{missing_dir}\n")
                f.write("\n")
            
            if results['missing_other_files']:
                f.write("MISSING OTHER FILES:\n")
                f.write("-" * 20 + "\n")
                for missing_file in sorted(results['missing_other_files']):
                    f.write(f"{missing_file}\n")
        
        print(f"\n📄 Missing files list saved to: {output_file}")


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


def predict_output_filenames(input_path: Path) -> Set[Path]:
    """
    Predict output filenames for all supported images in the input folder,
    using the converter's unique naming logic for duplicates.
    Returns a set of relative output paths.
    """
    # Group images by (relative parent, stem)
    groups: Dict[(Path, str), List[Path]] = defaultdict(list)
    for root, dirs, files in os.walk(input_path):
        root_path = Path(root)
        for file in files:
            file_path = root_path / file
            suffix = file_path.suffix.lower()
            if suffix in SUPPORTED_FORMATS and suffix != '.webp':
                rel_path = file_path.relative_to(input_path)
                groups[(rel_path.parent, rel_path.stem)].append(rel_path)
    
    predicted = set()
    for (parent, stem), rel_paths in groups.items():
        if len(rel_paths) == 1:
            # Only one file with this stem: output is stem.webp
            predicted.add(parent / f"{stem}.webp")
        else:
            # Multiple files with same stem: use suffix in name
            for rel_path in rel_paths:
                ext = rel_path.suffix.lower()[1:]  # without dot
                predicted.add(parent / f"{stem}_{ext}.webp")
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
        """
    )
    parser.add_argument('input_folder', help='Input folder path')
    parser.add_argument('output_folder', help='Output folder path')
    args = parser.parse_args()

    input_path = Path(args.input_folder)
    output_path = Path(args.output_folder)

    if not input_path.exists():
        print(f"Error: Input folder '{input_path}' does not exist!")
        sys.exit(1)
    if not output_path.exists():
        print(f"Error: Output folder '{output_path}' does not exist!")
        sys.exit(1)

    predicted_output_files = predict_output_filenames(input_path)
    actual_output_files = get_all_files(output_path)

    missing_in_output = predicted_output_files - actual_output_files

    print("\n==============================")
    print("FOLDER MIRROR CHECK (with unique renaming)")
    print("==============================")
    print(f"Input folder:  {input_path}")
    print(f"Output folder: {output_path}")
    print(f"\nPredicted output files: {len(predicted_output_files)}")
    print(f"Actual files in output: {len(actual_output_files)}")
    print(f"\nFiles missing in output: {len(missing_in_output)}")
    if missing_in_output:
        print("\nMissing files (relative paths):")
        for f in sorted(missing_in_output):
            print(f"  {f}")
    else:
        print("\n✅ All predicted output files are present!")

    input_size = get_folder_size(input_path)
    output_size = get_folder_size(output_path)

    print(f"\nTotal size of input:  {input_size / (1024*1024):.2f} MB ({input_size} bytes)")
    print(f"Total size of output: {output_size / (1024*1024):.2f} MB ({output_size} bytes)")
    if input_size > 0:
        ratio = (output_size / input_size) * 100
        print(f"\nCompression ratio (output/input): {ratio:.1f}%")
        print(f"Space saved: {100 - ratio:.1f}%")
    else:
        print("\nInput folder is empty!")

    print("==============================")


if __name__ == "__main__":
    main() 