#!/usr/bin/env python3
"""
WebP Image Converter
A Python script to convert images from various formats to WebP format.
Supports both command-line and GUI interfaces.
"""

import os
import sys
import argparse
from pathlib import Path
from typing import List, Optional
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image
import threading


class WebPConverter:
    """Main class for converting images to WebP format."""
    
    def __init__(self):
        self.supported_formats = {
            '.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', 
            '.gif', '.ico', '.ppm', '.pgm', '.pbm', '.pnm'
        }
    
    def convert_image(self, input_path: str, output_path: Optional[str] = None, 
                     quality: int = 80, lossless: bool = False) -> bool:
        """
        Convert a single image to WebP format.
        
        Args:
            input_path: Path to the input image
            output_path: Path for the output WebP file (optional)
            quality: WebP quality (0-100)
            lossless: Whether to use lossless compression
            
        Returns:
            bool: True if conversion successful, False otherwise
        """
        try:
            # Open the image
            with Image.open(input_path) as img:
                # Convert to RGB if necessary (WebP doesn't support RGBA in some cases)
                if img.mode in ('RGBA', 'LA', 'P'):
                    # Create a white background for transparent images
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Generate output path if not provided
                if output_path is None:
                    input_file = Path(input_path)
                    output_path = input_file.with_suffix('.webp')
                
                # Save as WebP
                save_kwargs = {'format': 'WEBP'}
                if lossless:
                    save_kwargs['lossless'] = True
                else:
                    save_kwargs['quality'] = quality
                
                img.save(output_path, **save_kwargs)
                return True
                
        except Exception as e:
            print(f"Error converting {input_path}: {e}")
            return False
    
    def convert_directory(self, input_dir: str, output_dir: Optional[str] = None,
                         quality: int = 80, lossless: bool = False, skip_node_modules: Optional[bool] = None) -> dict:
        """
        Recursively convert all supported images in a directory (and subdirectories) to WebP format,
        preserving the folder structure in the output directory.
        If node_modules is found, alert the user and ask for confirmation to skip it.
        Images over 50MB are skipped.
        
        Args:
            input_dir: Input directory path
            output_dir: Output directory path (optional)
            quality: WebP quality (0-100)
            lossless: Whether to use lossless compression
            skip_node_modules: If True, skip node_modules without asking. If None, ask in CLI.
            
        Returns:
            dict: Statistics about the conversion process
        """
        input_path = Path(input_dir)
        if output_dir is None:
            output_path = input_path.parent / f"{input_path.name}_webp"
        else:
            output_path = Path(output_dir)
        
        # Detect node_modules folders
        node_modules_found = []
        for root, dirs, files in os.walk(input_path):
            if 'node_modules' in dirs:
                node_modules_found.append(str(Path(root) / 'node_modules'))
        
        # If node_modules found and not already handled, ask user in CLI
        if node_modules_found and skip_node_modules is None:
            print("\n⚠️  Warning: 'node_modules' folder(s) found:")
            for nm in node_modules_found:
                print(f"   {nm}")
            resp = input("\nDo you want to skip 'node_modules' and proceed with conversion? (y/n): ").strip().lower()
            if resp != 'y':
                print("Aborting conversion.")
                sys.exit(1)
            skip_node_modules = True
        
        # Enhanced statistics
        stats = {
            'total_files': 0,
            'converted': 0,
            'failed': 0,
            'skipped': 0,
            'skipped_large': 0,
            'format_counts': {},  # Count per format
            'webp_found': 0,      # WebP files already in input
            'total_output_files': 0  # Total files in output folder
        }
        
        # Initialize format counts
        for fmt in self.supported_formats:
            stats['format_counts'][fmt] = 0
        
        MAX_IMAGE_SIZE = 50 * 1024 * 1024  # 50MB
        
        for root, dirs, files in os.walk(input_path):
            # Skip node_modules if requested
            if skip_node_modules and 'node_modules' in dirs:
                dirs.remove('node_modules')
            rel_dir = os.path.relpath(root, input_path)
            out_dir = output_path / rel_dir if rel_dir != '.' else output_path
            out_dir.mkdir(parents=True, exist_ok=True)
            for file in files:
                file_path = Path(root) / file
                if file_path.suffix.lower() in self.supported_formats:
                    stats['total_files'] += 1
                    
                    # Count by format
                    suffix = file_path.suffix.lower()
                    stats['format_counts'][suffix] += 1
                    
                    if suffix == '.webp':
                        stats['skipped'] += 1
                        stats['webp_found'] += 1
                        continue
                    
                    # Check image size
                    try:
                        size = file_path.stat().st_size
                    except Exception as e:
                        print(f"✗ Failed to get size for {file_path}: {e}")
                        stats['failed'] += 1
                        continue
                    if size > MAX_IMAGE_SIZE:
                        print(f"⚠️  Skipping {file_path} (size {size / (1024*1024):.2f} MB > 50MB)")
                        stats['skipped_large'] += 1
                        continue
                    
                    # Generate unique output filename
                    base_output_path = out_dir / file_path.stem
                    output_file = self._generate_unique_filename(base_output_path, file_path.suffix.lower())
                    
                    if self.convert_image(str(file_path), str(output_file), quality, lossless):
                        stats['converted'] += 1
                        print(f"✓ Converted: {file_path} -> {output_file}")
                    else:
                        stats['failed'] += 1
                        print(f"✗ Failed: {file_path}")
        
        # Count total files in output folder
        stats['total_output_files'] = self._count_output_files(output_path)
        
        return stats
    
    def _count_output_files(self, output_path: Path) -> int:
        """Count total files in the output directory recursively."""
        count = 0
        for root, dirs, files in os.walk(output_path):
            count += len(files)
        return count
    
    def print_conversion_summary(self, stats: dict, input_dir: str, output_dir: str):
        """
        Print a detailed conversion summary.
        
        Args:
            stats: Statistics from convert_directory
            input_dir: Input directory path
            output_dir: Output directory path
        """
        print("\n" + "="*70)
        print("📊 WEBP CONVERSION SUMMARY")
        print("="*70)
        
        # Input folder analysis
        print(f"\n📁 INPUT FOLDER: {input_dir}")
        print(f"   Total supported images found: {stats['total_files']}")
        
        if stats['webp_found'] > 0:
            print(f"   WebP files found (already in WebP format): {stats['webp_found']}")
        
        # Format breakdown
        print(f"\n📋 FORMAT BREAKDOWN:")
        total_convertible = 0
        for fmt, count in sorted(stats['format_counts'].items()):
            if count > 0:
                if fmt == '.webp':
                    print(f"   {fmt.upper()}: {count} (skipped - already WebP)")
                else:
                    print(f"   {fmt.upper()}: {count}")
                    total_convertible += count
        
        # Conversion results
        print(f"\n🔄 CONVERSION RESULTS:")
        print(f"   Successfully converted: {stats['converted']}")
        print(f"   Failed conversions: {stats['failed']}")
        print(f"   Skipped (already WebP): {stats['skipped']}")
        if stats.get('skipped_large', 0) > 0:
            print(f"   Skipped (over 50MB): {stats['skipped_large']}")
        
        # Output folder summary
        print(f"\n📁 OUTPUT FOLDER: {output_dir}")
        print(f"   Total files in output: {stats['total_output_files']}")
        
        # Success rate
        if total_convertible > 0:
            success_rate = (stats['converted'] / total_convertible) * 100
            print(f"\n✅ SUCCESS RATE: {success_rate:.1f}%")
            print(f"   Converted: {stats['converted']}/{total_convertible} images")
        
        if stats['failed'] > 0:
            print(f"   Failed: {stats['failed']} images")
        
        print("="*70)
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported input formats."""
        return sorted(list(self.supported_formats))
    
    def _generate_unique_filename(self, base_path: Path, original_extension: str) -> Path:
        """
        Generate a unique filename for the output WebP file.
        If a file with the same name exists, append the original extension to make it unique.
        
        Args:
            base_path: Base path for the output file
            original_extension: Original file extension (e.g., '.jpg', '.png')
            
        Returns:
            Path: Unique filename for the output WebP file
        """
        # First try the simple name
        output_path = base_path.with_suffix('.webp')
        
        # If it doesn't exist, we can use it
        if not output_path.exists():
            return output_path
        
        # If it exists, try with original extension suffix
        stem_with_ext = f"{base_path.stem}_{original_extension[1:]}"  # Remove the dot
        output_path = base_path.parent / f"{stem_with_ext}.webp"
        
        # If that also exists, add a number
        counter = 1
        while output_path.exists():
            output_path = base_path.parent / f"{stem_with_ext}_{counter}.webp"
            counter += 1
        
        return output_path


class WebPConverterGUI:
    """GUI interface for the WebP converter."""
    
    def __init__(self):
        self.converter = WebPConverter()
        self.root = tk.Tk()
        self.root.title("WebP Image Converter")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the GUI interface."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="WebP Image Converter", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Input selection
        ttk.Label(main_frame, text="Input:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.input_var = tk.StringVar()
        input_entry = ttk.Entry(main_frame, textvariable=self.input_var, width=50)
        input_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(5, 5), pady=5)
        ttk.Button(main_frame, text="Browse", command=self.browse_input).grid(row=1, column=2, pady=5)
        
        # Output selection
        ttk.Label(main_frame, text="Output:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.output_var = tk.StringVar()
        output_entry = ttk.Entry(main_frame, textvariable=self.output_var, width=50)
        output_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(5, 5), pady=5)
        ttk.Button(main_frame, text="Browse", command=self.browse_output).grid(row=2, column=2, pady=5)
        
        # Quality settings
        quality_frame = ttk.LabelFrame(main_frame, text="Quality Settings", padding="10")
        quality_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        quality_frame.columnconfigure(1, weight=1)
        
        # Quality slider
        ttk.Label(quality_frame, text="Quality:").grid(row=0, column=0, sticky=tk.W)
        self.quality_var = tk.IntVar(value=80)
        quality_slider = ttk.Scale(quality_frame, from_=0, to=100, variable=self.quality_var, 
                                  orient=tk.HORIZONTAL)
        quality_slider.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 5))
        self.quality_label = ttk.Label(quality_frame, text="80")
        self.quality_label.grid(row=0, column=2)
        quality_slider.configure(command=self.update_quality_label)
        
        # Lossless option
        self.lossless_var = tk.BooleanVar()
        ttk.Checkbutton(quality_frame, text="Lossless compression", 
                       variable=self.lossless_var).grid(row=1, column=0, columnspan=3, pady=(10, 0))
        
        # Convert button
        self.convert_btn = ttk.Button(main_frame, text="Convert", command=self.start_conversion)
        self.convert_btn.grid(row=4, column=0, columnspan=3, pady=20)
        
        # Progress bar
        self.progress_var = tk.StringVar(value="Ready")
        ttk.Label(main_frame, textvariable=self.progress_var).grid(row=5, column=0, columnspan=3, pady=5)
        
        # Log area
        log_frame = ttk.LabelFrame(main_frame, text="Conversion Log", padding="10")
        log_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(6, weight=1)
        
        # Text widget with scrollbar
        self.log_text = tk.Text(log_frame, height=10, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Supported formats info
        formats_text = f"Supported formats: {', '.join(self.converter.get_supported_formats())}"
        ttk.Label(main_frame, text=formats_text, font=("Arial", 8)).grid(row=7, column=0, columnspan=3, pady=(10, 0))
    
    def update_quality_label(self, value):
        """Update the quality label when slider changes."""
        self.quality_label.config(text=str(int(float(value))))
    
    def browse_input(self):
        """Browse for input file or directory."""
        path = filedialog.askdirectory(title="Select Input Directory")
        if not path:
            path = filedialog.askopenfilename(
                title="Select Input File",
                filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff *.tif *.gif *.ico *.ppm *.pgm *.pbm *.pnm")]
            )
        if path:
            self.input_var.set(path)
            # Auto-generate output path
            if self.output_var.get() == "":
                input_path = Path(path)
                if input_path.is_file():
                    self.output_var.set(str(input_path.with_suffix('.webp')))
                else:
                    self.output_var.set(str(input_path / 'webp_output'))
    
    def browse_output(self):
        """Browse for output directory."""
        path = filedialog.askdirectory(title="Select Output Directory")
        if path:
            self.output_var.set(path)
    
    def log_message(self, message):
        """Add message to log area."""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def start_conversion(self):
        """Start the conversion process in a separate thread."""
        input_path = self.input_var.get().strip()
        output_path = self.output_var.get().strip()
        quality = self.quality_var.get()
        lossless = self.lossless_var.get()
        
        if not input_path:
            messagebox.showerror("Error", "Please select an input file or directory.")
            return
        
        if not output_path:
            messagebox.showerror("Error", "Please select an output location.")
            return
        
        # Disable convert button during conversion
        self.convert_btn.config(state='disabled')
        self.progress_var.set("Converting...")
        self.log_text.delete(1.0, tk.END)
        
        # Start conversion in separate thread
        thread = threading.Thread(target=self.convert_thread, 
                                args=(input_path, output_path, quality, lossless))
        thread.daemon = True
        thread.start()
    
    def convert_thread(self, input_path, output_path, quality, lossless):
        """Conversion thread to avoid blocking the GUI."""
        try:
            input_path_obj = Path(input_path)
            
            if input_path_obj.is_file():
                # Single file conversion
                MAX_IMAGE_SIZE = 50 * 1024 * 1024  # 50MB
                try:
                    file_size = input_path_obj.stat().st_size
                except Exception as e:
                    print(f"Error: Could not get file size for '{input_path}': {e}")
                    sys.exit(1)
                if file_size > MAX_IMAGE_SIZE:
                    print(f"Error: The image '{input_path}' is too large ({file_size / (1024*1024):.2f} MB). Please use an image under 50MB.")
                    sys.exit(1)
                print(f"Converting: {input_path}")
                success = self.converter.convert_image(input_path, output_path, quality, lossless)
                if success:
                    print("✓ Conversion completed successfully!")
                else:
                    print("✗ Conversion failed!")
                    sys.exit(1)
            else:
                # Directory conversion
                self.log_message(f"Converting directory: {input_path}")
                stats = self.converter.convert_directory(input_path, output_path, quality, lossless)
                
                self.log_message(f"\nConversion Summary:")
                self.log_message(f"Total files: {stats['total_files']}")
                self.log_message(f"Converted: {stats['converted']}")
                self.log_message(f"Failed: {stats['failed']}")
                self.log_message(f"Skipped: {stats['skipped']}")
                
                if stats['failed'] == 0:
                    self.progress_var.set("Conversion completed!")
                else:
                    self.progress_var.set(f"Conversion completed with {stats['failed']} errors")
                
                # Print detailed summary
                self.converter.print_conversion_summary(stats, input_path, output_path or str(Path(input_path).parent / f"{Path(input_path).name}_webp"))
        
        except Exception as e:
            self.log_message(f"Error: {e}")
            self.progress_var.set("Conversion failed!")
        
        finally:
            # Re-enable convert button
            self.convert_btn.config(state='normal')
    
    def run(self):
        """Start the GUI application."""
        self.root.mainloop()


def main():
    """Main function to handle command-line arguments and start the application."""
    parser = argparse.ArgumentParser(
        description="Convert images to WebP format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s image.jpg                    # Convert single file
  %(prog)s image.jpg -o output.webp     # Convert with custom output name
  %(prog)s /path/to/images/             # Convert all images in directory
  %(prog)s --gui                        # Start GUI interface
        """
    )
    
    parser.add_argument('input', nargs='?', help='Input file or directory')
    parser.add_argument('-o', '--output', help='Output file or directory')
    parser.add_argument('-q', '--quality', type=int, default=80, 
                       help='WebP quality (0-100, default: 80)')
    parser.add_argument('--lossless', action='store_true', 
                       help='Use lossless compression')
    parser.add_argument('--gui', action='store_true', 
                       help='Start GUI interface')
    parser.add_argument('--formats', action='store_true', 
                       help='Show supported input formats')
    
    args = parser.parse_args()
    
    converter = WebPConverter()
    
    # Show supported formats
    if args.formats:
        print("Supported input formats:")
        for fmt in converter.get_supported_formats():
            print(f"  {fmt}")
        return
    
    # Start GUI if requested or no arguments provided
    if args.gui or (not args.input and not args.formats):
        print("Starting WebP Converter GUI...")
        app = WebPConverterGUI()
        app.run()
        return
    
    # Command-line conversion
    if not args.input:
        parser.error("Input file or directory is required")
    
    input_path = args.input
    output_path = args.output
    quality = args.quality
    lossless = args.lossless
    
    # Validate quality
    if not 0 <= quality <= 100:
        print("Error: Quality must be between 0 and 100")
        return
    
    input_path_obj = Path(input_path)
    
    if not input_path_obj.exists():
        print(f"Error: Input path '{input_path}' does not exist")
        return
    
    if input_path_obj.is_file():
        # Single file conversion
        MAX_IMAGE_SIZE = 50 * 1024 * 1024  # 50MB
        try:
            file_size = input_path_obj.stat().st_size
        except Exception as e:
            print(f"Error: Could not get file size for '{input_path}': {e}")
            sys.exit(1)
        if file_size > MAX_IMAGE_SIZE:
            print(f"Error: The image '{input_path}' is too large ({file_size / (1024*1024):.2f} MB). Please use an image under 50MB.")
            sys.exit(1)
        print(f"Converting: {input_path}")
        success = converter.convert_image(input_path, output_path, quality, lossless)
        if success:
            print("✓ Conversion completed successfully!")
        else:
            print("✗ Conversion failed!")
            sys.exit(1)
    else:
        # Directory conversion
        print(f"Converting directory: {input_path}")
        stats = converter.convert_directory(input_path, output_path, quality, lossless)
        
        # Print detailed summary
        converter.print_conversion_summary(stats, input_path, output_path or str(Path(input_path).parent / f"{Path(input_path).name}_webp"))
        
        if stats['failed'] > 0:
            sys.exit(1)


if __name__ == "__main__":
    main() 