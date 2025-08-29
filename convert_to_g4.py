import argparse
from PIL import Image, ImageOps
import numpy as np
import os
import sys

try:
    import tkinter as tk
    from tkinter import filedialog, messagebox
except Exception:
    tk = None

def to_g4_bytes(img, gamma=None, invert=False):
    if img.mode != "L":
        img = img.convert("L")
    arr = np.asarray(img).astype(np.float32) / 255.0
    if gamma and gamma > 0:
        arr = np.power(arr, gamma)
    if invert:
        arr = 1.0 - arr
    g4 = np.clip(np.round(arr * 15.0), 0, 15).astype(np.uint8)
    return g4

def write_header(g4, width, height, name, out_path):
    total = width * height
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("#pragma once\n#include <stdint.h>\n\n")
        f.write("typedef uint8_t u8;\ntypedef uint16_t u16;\ntypedef uint32_t u32;\n\n")
        f.write(f"const u16 {name}_width = {width};\n")
        f.write(f"const u16 {name}_height = {height};\n")
        f.write(f"const u32 {name}_size = {total};\n\n")
        f.write(f"const u8 {name}_data[{total}] = {{\n")
        line = []
        for i, v in enumerate(g4.flatten()):
            line.append(f"0x{int(v):02x}")
            if len(line) >= 16:
                f.write("  " + ", ".join(line) + ",\n")
                line = []
        if line:
            f.write("  " + ", ".join(line) + ",\n")
        f.write("};\n")

def run_gui():
    if tk is None:
        print("Tkinter GUI is not available on this environment.")
        sys.exit(1)

    root = tk.Tk()
    root.title("PNG → 4-bit 灰度 转换器 (Header/BIN)")

    input_var = tk.StringVar()
    outdir_var = tk.StringVar()
    name_var = tk.StringVar(value="converted_image")
    width_var = tk.StringVar(value="640")
    height_var = tk.StringVar(value="480")
    gamma_var = tk.StringVar(value="")
    keep_aspect_var = tk.BooleanVar(value=False)
    invert_var = tk.BooleanVar(value=False)

    def choose_input():
        path = filedialog.askopenfilename(title="选择PNG文件", filetypes=[["PNG","*.png"],["All","*.*"]])
        if path:
            input_var.set(path)
            if not outdir_var.get():
                outdir_var.set(os.path.dirname(path))

    def choose_outdir():
        path = filedialog.askdirectory(title="选择输出目录")
        if path:
            outdir_var.set(path)

    def do_convert():
        try:
            in_path = input_var.get().strip()
            if not in_path or not os.path.isfile(in_path):
                messagebox.showerror("错误", "请选择有效的PNG文件")
                return
            out_dir = outdir_var.get().strip() or os.path.dirname(in_path)
            os.makedirs(out_dir, exist_ok=True)

            try:
                w = int(width_var.get().strip())
                h = int(height_var.get().strip())
            except Exception:
                messagebox.showerror("错误", "宽/高必须为整数")
                return
            if w <= 0 or h <= 0:
                messagebox.showerror("错误", "宽高必须为正数")
                return

            gtxt = gamma_var.get().strip()
            gamma = float(gtxt) if gtxt else None

            img = Image.open(in_path)
            if keep_aspect_var.get():
                img = ImageOps.pad(img.convert("L"), (w, h), method=Image.Resampling.LANCZOS, color=0)
            else:
                img = img.convert("L").resize((w, h), Image.Resampling.LANCZOS)

            g4 = to_g4_bytes(img, gamma=gamma, invert=invert_var.get())

            name = name_var.get().strip() or "converted_image"
            out_h = os.path.join(out_dir, f"{name}.h")
            out_b = os.path.join(out_dir, f"{name}.bin")

            write_header(g4, w, h, name, out_h)
            with open(out_b, "wb") as fb:
                fb.write(g4.tobytes())

            messagebox.showinfo("完成", f"已输出:\n{out_h}\n{out_b}")
        except Exception as e:
            messagebox.showerror("异常", str(e))

    pad = {'padx': 8, 'pady': 6}

    tk.Label(root, text="输入PNG").grid(row=0, column=0, sticky='e', **pad)
    tk.Entry(root, textvariable=input_var, width=48).grid(row=0, column=1, **pad)
    tk.Button(root, text="选择...", command=choose_input).grid(row=0, column=2, **pad)

    tk.Label(root, text="输出目录").grid(row=1, column=0, sticky='e', **pad)
    tk.Entry(root, textvariable=outdir_var, width=48).grid(row=1, column=1, **pad)
    tk.Button(root, text="选择...", command=choose_outdir).grid(row=1, column=2, **pad)

    tk.Label(root, text="符号名称").grid(row=2, column=0, sticky='e', **pad)
    tk.Entry(root, textvariable=name_var, width=20).grid(row=2, column=1, sticky='w', **pad)

    tk.Label(root, text="宽×高").grid(row=3, column=0, sticky='e', **pad)
    wh_frame = tk.Frame(root)
    wh_frame.grid(row=3, column=1, sticky='w')
    tk.Entry(wh_frame, textvariable=width_var, width=8).pack(side='left')
    tk.Label(wh_frame, text="×").pack(side='left')
    tk.Entry(wh_frame, textvariable=height_var, width=8).pack(side='left')

    opt_frame = tk.Frame(root)
    opt_frame.grid(row=4, column=1, sticky='w', **pad)
    tk.Checkbutton(opt_frame, text="保持比例(信箱)", variable=keep_aspect_var).pack(side='left')
    tk.Checkbutton(opt_frame, text="反转", variable=invert_var).pack(side='left')

    tk.Label(root, text="Gamma(可空)").grid(row=5, column=0, sticky='e', **pad)
    tk.Entry(root, textvariable=gamma_var, width=10).grid(row=5, column=1, sticky='w', **pad)

    tk.Button(root, text="转换", command=do_convert, width=16).grid(row=6, column=1, **pad)

    root.mainloop()

def main():
    ap = argparse.ArgumentParser(description="Convert PNG to 4-bit grayscale header/bin for AR display")
    ap.add_argument("input", nargs='?', help="input PNG")
    ap.add_argument("--out-header", default="converted_image.h", help="output .h path")
    ap.add_argument("--out-bin", default="converted_image.bin", help="output .bin path (raw 0..15 per pixel)")
    ap.add_argument("--name", default="converted_image", help="symbol prefix in header")
    ap.add_argument("--width", type=int, default=640, help="target width (default 640)")
    ap.add_argument("--height", type=int, default=480, help="target height (default 480)")
    ap.add_argument("--keep-aspect", action="store_true", help="keep aspect with letterbox (black)")
    ap.add_argument("--gamma", type=float, default=None, help="optional gamma (e.g. 0.9 or 1.2)")
    ap.add_argument("--invert", action="store_true", help="invert grayscale before quantize (optional)")
    ap.add_argument("--ui", action="store_true", help="launch GUI")
    args = ap.parse_args()

    if args.ui or args.input is None:
        return run_gui()

    img = Image.open(args.input)
    if args.keep_aspect:
        img = ImageOps.pad(img.convert("L"), (args.width, args.height), method=Image.Resampling.LANCZOS, color=0)
    else:
        img = img.convert("L").resize((args.width, args.height), Image.Resampling.LANCZOS)

    g4 = to_g4_bytes(img, gamma=args.gamma, invert=args.invert)

    write_header(g4, args.width, args.height, args.name, args.out_header)

    with open(args.out_bin, "wb") as fb:
        fb.write(g4.tobytes())

    print(f"Done. header: {os.path.abspath(args.out_header)}  bin: {os.path.abspath(args.out_bin)}")

if __name__ == "__main__":
    main()


