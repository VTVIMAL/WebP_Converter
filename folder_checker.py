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
        
        Args:
            input_images: Set of input image paths
            input_folder: Input folder path
            output_folder: Output folder path
            
        Returns:
            Set of expected WebP file paths
        """
        expected_webp = set()
        
        for img_path in input_images:
            # Get relative path from input folder
            rel_path = img_path.relative_to(input_folder)
            
            # Generate expected WebP path
            expected_webp_path = output_folder / rel_path.parent / f"{rel_path.stem}.webp"
            expected_webp.add(expected_webp_path)
            
            # Also check for format-suffixed versions
            format_suffix = f"{rel_path.stem}_{rel_path.suffix[1:]}.webp"
            expected_webp_path_suffix = output_folder / rel_path.parent / format_suffix
            expected_webp.add(expected_webp_path_suffix)
        
        return expected_webp
    
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
        
        # Get expected WebP files
        expected_webp = self.get_expected_webp_files(
            input_contents['images'], input_folder, output_folder
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
            'input_images': input_contents['images'],
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
        print(f"   Images: {results['input_stats']['total_images']}")
        print(f"   WebP files: {results['input_stats']['total_webp']}")
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
        total_input_images = results['input_stats']['total_images']
        total_output_webp = results['output_stats']['total_webp']
        missing_count = len(results['missing_webp'])
        
        if total_input_images > 0:
            conversion_rate = ((total_input_images - missing_count) / total_input_images) * 100
            print(f"   Conversion rate: {conversion_rate:.1f}%")
            print(f"   Successfully converted: {total_input_images - missing_count}/{total_input_images}")
        
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


def main():
    """Main function to handle command-line arguments and run the checker."""
    parser = argparse.ArgumentParser(
        description="Check WebP conversion completeness between input and output folders",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s /path/to/input /path/to/output
  %(prog)s /photos /photos_webp --save-report
  %(prog)s /input_folder /output_folder --detailed
        """
    )
    
    parser.add_argument('input_folder', help='Input folder path')
    parser.add_argument('output_folder', help='Output folder path')
    parser.add_argument('--save-report', action='store_true', 
                       help='Save missing files list to missing_files.txt')
    parser.add_argument('--detailed', action='store_true',
                       help='Show detailed file-by-file comparison')
    
    args = parser.parse_args()
    
    input_path = Path(args.input_folder)
    output_path = Path(args.output_folder)
    
    # Validate input paths
    if not input_path.exists():
        print(f"Error: Input folder '{input_path}' does not exist!")
        sys.exit(1)
    
    if not output_path.exists():
        print(f"Error: Output folder '{output_path}' does not exist!")
        sys.exit(1)
    
    # Run the checker
    checker = FolderChecker()
    results = checker.check_conversion_completeness(input_path, output_path)
    
    # Print report
    checker.print_report(results, input_path, output_path)
    
    # Save report if requested
    if args.save_report:
        checker.generate_missing_list(results)
    
    # Show detailed comparison if requested
    if args.detailed:
        print(f"\n📋 DETAILED COMPARISON:")
        print("-" * 40)
        
        input_images = sorted(results['input_images'])
        output_webp = sorted(results['output_webp'])
        
        print(f"Input images ({len(input_images)}):")
        for img in input_images:
            print(f"  {img}")
        
        print(f"\nOutput WebP files ({len(output_webp)}):")
        for webp in output_webp:
            print(f"  {webp}")
    
    # Exit with error code if there are missing files
    if results['missing_webp'] or results['missing_directories']:
        sys.exit(1)


if __name__ == "__main__":
    main() 