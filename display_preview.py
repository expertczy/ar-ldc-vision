#!/usr/bin/env python3
"""
JBD013VGA Display Preview Tool
模拟AR眼镜显示效果，在电脑上预览画面
"""

try:
    from PIL import Image, ImageTk
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
    import numpy as np
    import sys
    import os
    
    class JBD013Simulator:
        def __init__(self):
            self.root = tk.Tk()
            self.root.title("JBD013VGA Display Simulator - AR眼镜显示预览")
            self.root.geometry("800x700")
            
            # 显示参数
            self.panel_width = 640
            self.panel_height = 480
            self.brightness = 1200  # 默认中等亮度
            self.mirror_mode = True  # 水平镜像
            self.invert_colors = False  # 不反转颜色
            
            # 当前图像
            self.current_image = None
            self.processed_image = None
            
            self.setup_ui()
            self.load_default_image()
            
        def setup_ui(self):
            """设置用户界面"""
            # 主框架
            main_frame = ttk.Frame(self.root, padding="10")
            main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
            
            # 控制面板
            control_frame = ttk.LabelFrame(main_frame, text="显示控制", padding="5")
            control_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
            
            # 文件选择
            ttk.Button(control_frame, text="选择PNG文件", command=self.load_image).grid(row=0, column=0, padx=(0, 10))
            ttk.Button(control_frame, text="加载默认图像", command=self.load_default_image).grid(row=0, column=1, padx=(0, 10))
            
            # 亮度控制
            ttk.Label(control_frame, text="亮度:").grid(row=1, column=0, sticky=tk.W, pady=(10, 0))
            self.brightness_var = tk.IntVar(value=self.brightness)
            brightness_scale = ttk.Scale(control_frame, from_=0, to=2500, variable=self.brightness_var, 
                                       orient=tk.HORIZONTAL, length=200, command=self.update_brightness)
            brightness_scale.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
            self.brightness_label = ttk.Label(control_frame, text=f"{self.brightness} (50%)")
            self.brightness_label.grid(row=1, column=3, padx=(10, 0), pady=(10, 0))
            
            # 预设亮度按钮
            preset_frame = ttk.Frame(control_frame)
            preset_frame.grid(row=2, column=0, columnspan=4, pady=(5, 0))
            ttk.Button(preset_frame, text="低亮度(500)", command=lambda: self.set_brightness(500)).pack(side=tk.LEFT, padx=(0, 5))
            ttk.Button(preset_frame, text="中亮度(1200)", command=lambda: self.set_brightness(1200)).pack(side=tk.LEFT, padx=(0, 5))
            ttk.Button(preset_frame, text="高亮度(2000)", command=lambda: self.set_brightness(2000)).pack(side=tk.LEFT)
            
            # 显示选项
            options_frame = ttk.Frame(control_frame)
            options_frame.grid(row=3, column=0, columnspan=4, pady=(10, 0))
            
            self.mirror_var = tk.BooleanVar(value=self.mirror_mode)
            ttk.Checkbutton(options_frame, text="水平镜像翻转", variable=self.mirror_var, 
                          command=self.update_display).pack(side=tk.LEFT, padx=(0, 20))
            
            self.invert_var = tk.BooleanVar(value=self.invert_colors)
            ttk.Checkbutton(options_frame, text="颜色反转", variable=self.invert_var, 
                          command=self.update_display).pack(side=tk.LEFT)
            
            # 显示区域
            display_frame = ttk.LabelFrame(main_frame, text="显示预览 (640x480)", padding="5")
            display_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
            
            # 画布用于显示图像
            self.canvas = tk.Canvas(display_frame, width=640, height=480, bg='black')
            self.canvas.pack()
            
            # 信息显示
            info_frame = ttk.LabelFrame(main_frame, text="图像信息", padding="5")
            info_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
            
            self.info_label = ttk.Label(info_frame, text="等待加载图像...")
            self.info_label.pack()
            
        def load_image(self):
            """加载PNG文件"""
            file_path = filedialog.askopenfilename(
                title="选择PNG图像文件",
                filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
            )
            if file_path:
                try:
                    self.current_image = Image.open(file_path)
                    if self.current_image.mode != 'L':
                        self.current_image = self.current_image.convert('L')
                    self.update_display()
                    self.info_label.config(text=f"已加载: {os.path.basename(file_path)} ({self.current_image.size[0]}x{self.current_image.size[1]})")
                except Exception as e:
                    messagebox.showerror("错误", f"无法加载图像: {e}")
                    
        def load_default_image(self):
            """加载默认的TRANSPARENT.png"""
            try:
                if os.path.exists("TRANSPARENT.png"):
                    self.current_image = Image.open("TRANSPARENT.png")
                    if self.current_image.mode != 'L':
                        self.current_image = self.current_image.convert('L')
                    self.update_display()
                    self.info_label.config(text=f"默认图像: TRANSPARENT.png ({self.current_image.size[0]}x{self.current_image.size[1]})")
                else:
                    # 创建一个示例图像
                    self.current_image = self.create_sample_image()
                    self.update_display()
                    self.info_label.config(text="示例图像 (288x204)")
            except Exception as e:
                messagebox.showerror("错误", f"无法加载默认图像: {e}")
                
        def create_sample_image(self):
            """创建示例图像"""
            img = Image.new('L', (288, 204), color=0)  # 黑色背景
            # 添加一些示例内容
            import numpy as np
            pixels = np.array(img)
            
            # 绘制一个简单的文字框
            pixels[50:150, 50:250] = 255  # 白色矩形
            pixels[60:140, 60:240] = 0    # 黑色内框
            
            # 添加一些文字模拟
            for i in range(5):
                y_start = 70 + i * 12
                pixels[y_start:y_start+8, 70:220] = 255
                
            return Image.fromarray(pixels)
                
        def set_brightness(self, value):
            """设置预设亮度"""
            self.brightness_var.set(value)
            self.update_brightness(value)
            
        def update_brightness(self, value):
            """更新亮度"""
            self.brightness = int(float(value))
            percentage = int((self.brightness / 2500) * 100)
            self.brightness_label.config(text=f"{self.brightness} ({percentage}%)")
            self.update_display()
            
        def update_display(self):
            """更新显示"""
            if self.current_image is None:
                return
                
            # 获取当前设置
            self.mirror_mode = self.mirror_var.get()
            self.invert_colors = self.invert_var.get()
            
            # 处理图像
            self.processed_image = self.process_image(self.current_image)
            
            # 在画布上显示
            self.display_on_canvas(self.processed_image)
            
        def process_image(self, img):
            """模拟JBD013的图像处理流程"""
            # 1. 缩放到640x480
            scaled = img.resize((self.panel_width, self.panel_height), Image.Resampling.NEAREST)
            
            # 2. 转换为4位灰度 (0-15)
            pixels = np.array(scaled, dtype=np.float32)
            pixels = pixels / 255.0 * 15.0  # 转换到0-15范围
            pixels = np.round(pixels).astype(np.uint8)
            
            # 3. 颜色反转（如果启用）
            if self.invert_colors:
                pixels = 15 - pixels
                
            # 4. 应用亮度
            brightness_factor = self.brightness / 2500.0
            pixels = pixels * brightness_factor
            pixels = np.clip(pixels, 0, 15)
            
            # 5. 转换回8位显示
            display_pixels = (pixels / 15.0 * 255).astype(np.uint8)
            
            # 6. 水平镜像（如果启用）
            if self.mirror_mode:
                display_pixels = np.fliplr(display_pixels)
                
            return Image.fromarray(display_pixels, mode='L')
            
        def display_on_canvas(self, img):
            """在画布上显示图像"""
            # 转换为PhotoImage
            self.photo = ImageTk.PhotoImage(img)
            
            # 清除画布并显示新图像
            self.canvas.delete("all")
            self.canvas.create_image(320, 240, image=self.photo)
            
        def run(self):
            """运行模拟器"""
            self.root.mainloop()
            
    if __name__ == "__main__":
        simulator = JBD013Simulator()
        simulator.run()
        
except ImportError as e:
    print("缺少必要的库，正在安装...")
    import subprocess
    import sys
    
    libraries = ['Pillow', 'numpy']
    for lib in libraries:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", lib])
        except subprocess.CalledProcessError:
            print(f"安装 {lib} 失败，请手动安装")
    
    print("请重新运行脚本")
except Exception as e:
    print(f"错误: {e}")
    input("按回车键退出...")
