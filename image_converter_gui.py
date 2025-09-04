#!/usr/bin/env python3
"""
ESP32-S2 Image Converter - GUI Version
Graphical interface for converting PNG/JPG images to ESP32-S2 format
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import sys
import threading
from PIL import Image
import numpy as np

class ImageConverterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ESP32-S2 Image Converter - JBD013VGA Display")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="🖼️ ESP32-S2 Image Converter", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # File selection section
        file_frame = ttk.LabelFrame(main_frame, text="📁 Select Image File", padding="10")
        file_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        file_frame.columnconfigure(1, weight=1)
        
        # File path
        ttk.Label(file_frame, text="Image File:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.file_path_var = tk.StringVar()
        self.file_entry = ttk.Entry(file_frame, textvariable=self.file_path_var, width=50)
        self.file_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        
        browse_btn = ttk.Button(file_frame, text="Browse...", command=self.browse_file)
        browse_btn.grid(row=0, column=2)
        
        # Preview section
        preview_frame = ttk.LabelFrame(main_frame, text="🖼️ Image Preview", padding="10")
        preview_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.preview_label = ttk.Label(preview_frame, text="Select an image to see preview")
        self.preview_label.pack()
        
        self.info_label = ttk.Label(preview_frame, text="", foreground="blue")
        self.info_label.pack(pady=(5, 0))
        
        # Settings section
        settings_frame = ttk.LabelFrame(main_frame, text="⚙️ Conversion Settings", padding="10")
        settings_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        settings_frame.columnconfigure(1, weight=1)
        
        # Output dimensions
        ttk.Label(settings_frame, text="Width:").grid(row=0, column=0, sticky=tk.W)
        self.width_var = tk.StringVar(value="640")
        width_entry = ttk.Entry(settings_frame, textvariable=self.width_var, width=10)
        width_entry.grid(row=0, column=1, sticky=tk.W, padx=(5, 20))
        
        ttk.Label(settings_frame, text="Height:").grid(row=0, column=2, sticky=tk.W)
        self.height_var = tk.StringVar(value="480")
        height_entry = ttk.Entry(settings_frame, textvariable=self.height_var, width=10)
        height_entry.grid(row=0, column=3, sticky=tk.W, padx=(5, 0))
        
        # Output file info
        ttk.Label(settings_frame, text="Output File:").grid(row=1, column=0, sticky=tk.W, pady=(10, 0))
        output_info = ttk.Label(settings_frame, text="current_image.h (Fixed filename)", 
                               foreground="green", font=('Arial', 9, 'italic'))
        output_info.grid(row=1, column=1, columnspan=3, sticky=tk.W, padx=(5, 0), pady=(10, 0))
        
        # Convert button
        convert_btn = ttk.Button(main_frame, text="🚀 Convert Image", 
                                command=self.convert_image, style='Accent.TButton')
        convert_btn.grid(row=4, column=0, columnspan=2, pady=20, sticky=(tk.W))

        # Export .bin button
        export_btn = ttk.Button(main_frame, text="💾 Export runtime .bin", 
                                command=self.export_bin)
        export_btn.grid(row=4, column=2, pady=20, sticky=(tk.E))

        # Preview converted 4-bit button
        preview_btn = ttk.Button(main_frame, text="👁 Preview 4-bit image", 
                                 command=self.preview_converted)
        preview_btn.grid(row=4, column=1, pady=20)
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Log section
        log_frame = ttk.LabelFrame(main_frame, text="📋 Conversion Log", padding="10")
        log_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(6, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, width=80)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, 
                              relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Instructions
        self.log("🎯 ESP32-S2 Image Converter Ready!")
        self.log("📝 Instructions:")
        self.log("   1. Click 'Browse...' to select your image file (PNG, JPG, etc.)")
        self.log("   2. Adjust width/height if needed (default: 640x480)")
        self.log("   3. Click 'Convert Image' to generate current_image.h")
        self.log("   4. Compile your ESP32-S2 project to use the new image")
        self.log("")
        
    def browse_file(self):
        """Open file dialog to select image"""
        filetypes = [
            ("Image files", "*.png *.jpg *.jpeg *.bmp *.tiff *.gif"),
            ("PNG files", "*.png"),
            ("JPEG files", "*.jpg *.jpeg"),
            ("All files", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="Select Image File",
            filetypes=filetypes
        )
        
        if filename:
            self.file_path_var.set(filename)
            self.preview_image(filename)
            
    def preview_image(self, filepath):
        """Show image preview and info"""
        try:
            img = Image.open(filepath)
            
            # Update info
            mode_desc = {
                'RGB': 'RGB Color',
                'RGBA': 'RGB with Alpha',
                'L': 'Grayscale',
                'P': 'Palette'
            }
            
            info_text = f"📐 Size: {img.size[0]}x{img.size[1]} | 🎨 Mode: {mode_desc.get(img.mode, img.mode)}"
            file_size = os.path.getsize(filepath) / 1024  # KB
            info_text += f" | 💾 Size: {file_size:.1f} KB"
            
            self.info_label.config(text=info_text)
            
            # Create thumbnail for preview
            thumbnail_size = (200, 150)
            img_thumb = img.copy()
            img_thumb.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage for tkinter
            try:
                import PIL.ImageTk
                photo = PIL.ImageTk.PhotoImage(img_thumb)
                self.preview_label.config(image=photo, text="")
                self.preview_label.image = photo  # Keep a reference
            except ImportError:
                self.preview_label.config(text=f"Preview: {os.path.basename(filepath)}\n{info_text}")
                
            self.status_var.set(f"Loaded: {os.path.basename(filepath)}")
            
        except Exception as e:
            self.preview_label.config(text=f"❌ Error loading image:\n{str(e)}")
            self.status_var.set("Error loading image")
            
    def log(self, message):
        """Add message to log"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
        
    def convert_image(self):
        """Convert selected image"""
        filepath = self.file_path_var.get().strip()
        
        if not filepath:
            messagebox.showerror("Error", "Please select an image file first!")
            return
            
        if not os.path.exists(filepath):
            messagebox.showerror("Error", f"File not found: {filepath}")
            return
            
        # Validate dimensions
        try:
            width = int(self.width_var.get())
            height = int(self.height_var.get())
            
            if width <= 0 or height <= 0:
                raise ValueError("Dimensions must be positive")
                
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid dimensions: {e}")
            return
            
        # Run conversion in a separate thread
        self.progress.start()
        convert_btn = None
        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, ttk.Button) and "Convert" in child.cget("text"):
                        convert_btn = child
                        break
                        
        if convert_btn:
            convert_btn.config(state='disabled')
            
        self.status_var.set("Converting...")
        
        def convert_thread():
            try:
                self.log(f"\n🔄 Starting conversion...")
                self.log(f"📁 Input: {os.path.basename(filepath)}")
                
                result = self.convert_png_to_fixed_header(filepath, width, height)
                
                self.log(f"✅ Conversion completed successfully!")
                self.log(f"📄 Output: {result['output_path']}")
                self.log(f"📐 Final size: {result['width']}x{result['height']}")
                self.log(f"💾 Data size: {result['size']} bytes")
                self.log(f"🏷️  Variables: {result['var_prefix']}_data, {result['var_prefix']}_width, {result['var_prefix']}_height")
                self.log("")
                self.log("🎉 Ready to compile! Run 'pio run' to build your ESP32-S2 project.")
                
                self.status_var.set("Conversion completed!")
                
                messagebox.showinfo("Success", 
                    f"Image converted successfully!\n\n"
                    f"Output: current_image.h\n"
                    f"Size: {result['width']}x{result['height']}\n"
                    f"Data: {result['size']} bytes\n\n"
                    f"You can now compile your ESP32-S2 project.")
                
            except Exception as e:
                self.log(f"❌ Error: {str(e)}")
                self.status_var.set("Conversion failed!")
                messagebox.showerror("Error", f"Conversion failed:\n{str(e)}")
                
            finally:
                self.progress.stop()
                if convert_btn:
                    convert_btn.config(state='normal')
                    
        threading.Thread(target=convert_thread, daemon=True).start()

    def preview_converted(self):
        """Preview the 4-bit converted grayscale as 8-bit image in a popup window"""
        filepath = self.file_path_var.get().strip()
        if not filepath:
            messagebox.showerror("Error", "Please select an image file first!")
            return
        try:
            width = int(self.width_var.get())
            height = int(self.height_var.get())
            if width <= 0 or height <= 0:
                raise ValueError("Dimensions must be positive")
        except Exception as e:
            messagebox.showerror("Error", f"Invalid width/height: {e}")
            return

        try:
            img = Image.open(filepath)
            if img.mode != 'L':
                img = img.convert('L')
            img = img.resize((width, height), Image.Resampling.LANCZOS)
            arr = np.array(img)
            arr4 = np.round(arr / 17.0).astype(np.uint8)
            arr4 = np.clip(arr4, 0, 15)
            arr8 = (arr4 * 17).astype(np.uint8)
            preview = Image.fromarray(arr8, mode='L')

            # show in a popup window
            win = tk.Toplevel(self.root)
            win.title("4-bit Converted Preview")
            canvas = tk.Canvas(win, width=width, height=height)
            canvas.pack()
            try:
                import PIL.ImageTk
                photo = PIL.ImageTk.PhotoImage(preview)
                canvas.create_image(0, 0, anchor=tk.NW, image=photo)
                canvas.image = photo
            except ImportError:
                # fallback: save temp and notify
                tmp_path = os.path.join(os.getcwd(), "preview_converted.png")
                preview.save(tmp_path)
                ttk.Label(win, text=f"Preview saved to {tmp_path}").pack()
        except Exception as e:
            messagebox.showerror("Error", f"Preview failed: {e}")

    def export_bin(self):
        """Export 1B/px grayscale .bin for runtime upload (low 4 bits used)"""
        filepath = self.file_path_var.get().strip()
        if not filepath:
            messagebox.showerror("Error", "Please select an image file first!")
            return
        try:
            width = int(self.width_var.get())
            height = int(self.height_var.get())
            if width <= 0 or height <= 0:
                raise ValueError("Dimensions must be positive")
        except Exception as e:
            messagebox.showerror("Error", f"Invalid width/height: {e}")
            return

        try:
            img = Image.open(filepath)
            if img.mode != 'L':
                img = img.convert('L')
            img = img.resize((width, height), Image.Resampling.LANCZOS)
            arr = np.array(img)
            arr4 = np.round(arr / 17.0).astype(np.uint8)
            arr4 = np.clip(arr4, 0, 15)
            # store 1 byte per pixel with low 4 bits used
            arr1 = arr4.astype(np.uint8)
            out_path = filedialog.asksaveasfilename(
                title="Save runtime image",
                defaultextension=".bin",
                filetypes=[("Binary", "*.bin"), ("All files", "*.*")],
                initialfile="current_image.bin"
            )
            if not out_path:
                return
            with open(out_path, 'wb') as f:
                f.write(arr1.tobytes())
            self.log(f"✅ Exported runtime bin: {out_path} ({arr1.size} bytes)")
            messagebox.showinfo("Success", f"Exported runtime .bin:\n{out_path}\n{width}x{height} ({arr1.size} bytes)")
        except Exception as e:
            messagebox.showerror("Error", f"Export failed: {e}")
        
    def convert_png_to_fixed_header(self, png_path, target_width=640, target_height=480):
        """Convert PNG image to fixed C++ header file current_image.h"""
        
        # Fixed output filename and variable names
        output_path = "current_image.h"
        var_prefix = "current_image"
        
        # Open and convert image
        img = Image.open(png_path)
        self.log(f"📏 Original size: {img.size}")
        self.log(f"🎨 Original mode: {img.mode}")
        
        # Convert to grayscale if not already
        if img.mode != 'L':
            img = img.convert('L')
            self.log("✓ Converted to grayscale")
        
        # Resize to target dimensions
        img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
        self.log(f"📐 Resized to: {img.size}")
        
        # Convert to numpy array
        img_array = np.array(img)
        
        # Convert 8-bit grayscale (0-255) to 4-bit grayscale (0-15)
        img_4bit = np.round(img_array / 17.0).astype(np.uint8)
        img_4bit = np.clip(img_4bit, 0, 15)
        
        self.log(f"🔢 4-bit range: {img_4bit.min()} - {img_4bit.max()}")
        self.log(f"⚫ Non-zero pixels: {np.count_nonzero(img_4bit)}")
        
        # Flatten the array
        img_flat = img_4bit.flatten()
        actual_size = len(img_flat)
        
        # Generate header file
        original_filename = os.path.basename(png_path)
        header_content = f"""// Current display image - converted from {original_filename}
// Generated by ESP32-S2 Image Converter GUI
// Original dimensions: {img.size[0]}x{img.size[1]} 
// Target dimensions: {target_width}x{target_height}
// Format: 1 byte per pixel, only low 4 bits used (0-15)
// Compatible with packPngScaledRowsToPanel function

#ifndef CURRENT_IMAGE_H
#define CURRENT_IMAGE_H

const u16 {var_prefix}_width = {target_width};
const u16 {var_prefix}_height = {target_height};
const u32 {var_prefix}_size = {actual_size};

const u8 {var_prefix}_data[{actual_size}] = {{
"""
        
        # Add data in rows of 16 bytes
        for i in range(0, len(img_flat), 16):
            row = img_flat[i:i+16]
            hex_values = [f"0x{b:02X}" for b in row]
            header_content += "  " + ", ".join(hex_values) + ",\n"
        
        # Remove the last comma and add closing
        header_content = header_content.rstrip(',\n') + '\n};\n\n#endif // CURRENT_IMAGE_H\n'
        
        # Write header file
        with open(output_path, 'w') as f:
            f.write(header_content)
        
        return {
            'output_path': output_path,
            'var_prefix': var_prefix,
            'original_file': original_filename,
            'width': target_width,
            'height': target_height,
            'size': actual_size
        }

def main():
    # Check for required dependencies
    try:
        import PIL
        import numpy
    except ImportError as e:
        print("Missing required dependency:")
        print(f"Please install: pip install pillow numpy")
        print(f"Error: {e}")
        return
        
    root = tk.Tk()
    app = ImageConverterGUI(root)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\nGUI closed by user")

if __name__ == "__main__":
    main()
