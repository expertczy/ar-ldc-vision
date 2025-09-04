#!/usr/bin/env python3
"""
Screen Streamer GUI
- Captures a 640x480 region of the desktop every N seconds
- Converts to 4-bit grayscale (1B/px low nibble used)
- Uploads to ESP32-S2 via /upload then calls /apply
"""

import os
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox

import numpy as np
from PIL import Image
import struct

try:
    import mss  # fast screen capture
except ImportError:
    mss = None

try:
    import requests
except ImportError:
    requests = None

try:
    import websockets
    import asyncio
except ImportError:
    websockets = None
    asyncio = None

class ScreenStreamerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ESP32-S2 Screen Streamer")
        self.root.geometry("700x480")

        self.running = False
        self.capture_interval = 1.0  # seconds
        self.fps_var = tk.StringVar(value="1")
        self.host = tk.StringVar(value="192.168.1.189")
        self.x_var = tk.StringVar(value="0")
        self.y_var = tk.StringVar(value="0")
        self.w_var = tk.StringVar(value="640")
        self.h_var = tk.StringVar(value="480")
        self.invert_var = tk.BooleanVar(value=False)
        self.ws_rows_var = tk.StringVar(value="10")  # rows per WS chunk (smaller avoids 1009)

        self._build_ui()

    def _build_ui(self):
        frame = ttk.Frame(self.root, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        # Connection
        ttk.Label(frame, text="Device Host (IP)").grid(row=0, column=0, sticky=tk.W)
        host_entry = ttk.Entry(frame, textvariable=self.host, width=30)
        host_entry.grid(row=0, column=1, sticky=tk.W)

        # Region
        region = ttk.LabelFrame(frame, text="Capture Region (px)", padding=10)
        region.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 10))
        ttk.Label(region, text="X").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(region, textvariable=self.x_var, width=8).grid(row=0, column=1, sticky=tk.W, padx=(5, 10))
        ttk.Label(region, text="Y").grid(row=0, column=2, sticky=tk.W)
        ttk.Entry(region, textvariable=self.y_var, width=8).grid(row=0, column=3, sticky=tk.W, padx=(5, 10))
        ttk.Label(region, text="W").grid(row=0, column=4, sticky=tk.W)
        ttk.Entry(region, textvariable=self.w_var, width=8).grid(row=0, column=5, sticky=tk.W, padx=(5, 10))
        ttk.Label(region, text="H").grid(row=0, column=6, sticky=tk.W)
        ttk.Entry(region, textvariable=self.h_var, width=8).grid(row=0, column=7, sticky=tk.W, padx=(5, 10))

        # Options + FPS + Pick Start
        options = ttk.Frame(frame)
        options.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E))
        ttk.Checkbutton(options, text="Invert (match device invert)", variable=self.invert_var).grid(row=0, column=0, sticky=tk.W)
        ttk.Label(options, text="FPS").grid(row=0, column=1, padx=(12,4), sticky=tk.W)
        ttk.Entry(options, textvariable=self.fps_var, width=6).grid(row=0, column=2, sticky=tk.W)
        ttk.Button(options, text="Pick Start (click on screen)", command=self.pick_start_point).grid(row=0, column=3, padx=(12,0))
        ttk.Label(options, text="WS rows/chunk").grid(row=0, column=4, padx=(12,4), sticky=tk.W)
        ttk.Entry(options, textvariable=self.ws_rows_var, width=6).grid(row=0, column=5, sticky=tk.W)

        # Controls
        controls = ttk.Frame(frame)
        controls.grid(row=3, column=0, columnspan=2, pady=(10, 5), sticky=(tk.W, tk.E))
        ttk.Button(controls, text="Start", command=self.start).grid(row=0, column=0, padx=5)
        ttk.Button(controls, text="Stop", command=self.stop).grid(row=0, column=1, padx=5)
        ttk.Button(controls, text="One Shot (WS)", command=self.one_shot_ws).grid(row=0, column=2, padx=5)
        ttk.Button(controls, text="Test Connect", command=self.test_connect).grid(row=0, column=3, padx=5)

        # Log
        self.log_text = tk.Text(frame, height=10)
        self.log_text.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        frame.rowconfigure(4, weight=1)
        frame.columnconfigure(1, weight=1)

        self._log("Ready. Install deps: pip install mss requests pillow numpy")

    def pick_start_point(self):
        """Show a fullscreen transparent window to pick the top-left point by click"""
        try:
            overlay = tk.Toplevel(self.root)
            overlay.attributes("-fullscreen", True)
            # Try to make it click-through transparent-ish background
            overlay.attributes("-alpha", 0.3)
            overlay.configure(bg="black")
            overlay.lift()
            overlay.focus_set()

            info = tk.Label(overlay, text="Click to set top-left (Esc to cancel)", fg="white", bg="black", font=("Arial", 18))
            info.pack(pady=20)

            def on_click(event):
                self.x_var.set(str(event.x))
                self.y_var.set(str(event.y))
                self._log(f"Pick start: x={event.x}, y={event.y}")
                overlay.destroy()

            def on_key(event):
                if event.keysym == 'Escape':
                    overlay.destroy()

            overlay.bind("<Button-1>", on_click)
            overlay.bind("<Key>", on_key)
        except Exception as e:
            messagebox.showerror("Error", f"Pick failed: {e}")
            self._log(f"Pick failed: {e}")

    def _log(self, msg):
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)

    def _capture_region(self, x, y, w, h):
        if mss is None:
            raise RuntimeError("mss not installed: pip install mss")
        with mss.mss() as sct:
            monitor = {"left": x, "top": y, "width": w, "height": h}
            raw = sct.grab(monitor)
            img = Image.frombytes("RGB", raw.size, raw.rgb)
            return img

    def _to_4bit_bytes(self, img, invert=False):
        # Ensure 640x480
        if img.size != (640, 480):
            img = img.resize((640, 480), Image.Resampling.LANCZOS)
        gray = img.convert("L")
        arr = np.array(gray)
        g4 = np.clip(np.round(arr / 17.0), 0, 15).astype(np.uint8)
        if invert:
            g4 = 15 - g4
        return g4.tobytes()

    def _pack_rows_4bit(self, g4_bytes, row_start, rows):
        """Pack 1B/px low-nibble grayscale to 4-bit per pixel (two pixels per byte) for given rows"""
        w = 640
        bytes_per_row_src = w
        bytes_per_row_dst = w // 2
        out = np.empty(bytes_per_row_dst * rows, dtype=np.uint8)
        src = np.frombuffer(g4_bytes, dtype=np.uint8).reshape(480, 640)
        block = src[row_start:row_start+rows, :]
        # pack: (p0<<4) | p1
        hi = block[:, 0::2] & 0x0F
        lo = block[:, 1::2] & 0x0F
        packed = ((hi << 4) | lo).astype(np.uint8)
        out[:] = packed.reshape(-1)
        return out.tobytes()

    def _upload_and_apply(self, host, data_bytes):
        if requests is None:
            raise RuntimeError("requests not installed: pip install requests")
        files = {"file": ("current_image.bin", data_bytes, "application/octet-stream")}
        r = requests.post(host.rstrip('/') + "/upload", files=files, timeout=10)
        r.raise_for_status()
        self._log(f"Upload: {r.text.strip()}")
        r2 = requests.post(host.rstrip('/') + "/apply", timeout=10)
        r2.raise_for_status()
        self._log(f"Apply: {r2.text.strip()}")

    def _ws_send_frame(self, host_ip, g4_bytes):
        if websockets is None or asyncio is None:
            raise RuntimeError("websockets not installed: pip install websockets")

        async def _run():
            uri = f"ws://{host_ip}:81/"
            async with websockets.connect(uri, max_size=None, ping_interval=None) as ws:
                # 以每60行一个块发送（与设备端一致），每块前加4字节小端头: rowStart(u16), rows(u16)
                try:
                    chunk_rows = int(self.ws_rows_var.get())
                except Exception:
                    chunk_rows = 10
                if chunk_rows <= 0 or chunk_rows > 60:
                    chunk_rows = 10
                for row_start in range(0, 480, chunk_rows):
                    rows = min(chunk_rows, 480 - row_start)
                    chunk = self._pack_rows_4bit(g4_bytes, row_start, rows)
                    header = struct.pack('<HH', row_start, rows)
                    await ws.send(header + chunk)
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            loop.run_until_complete(_run())
        finally:
            try:
                loop.close()
            except Exception:
                pass

    def one_shot(self):
        try:
            x = int(self.x_var.get()); y = int(self.y_var.get())
            w = int(self.w_var.get()); h = int(self.h_var.get())
            host = self.host.get().strip()
            if not host.startswith("http"):
                host = "http://" + host
            img = self._capture_region(x, y, w, h)
            g4 = self._to_4bit_bytes(img, invert=self.invert_var.get())
            # stream in chunks of 60 rows via /stream-chunk (packed=1)
            for row_start in range(0, 480, 60):
                rows = min(60, 480 - row_start)
                chunk = self._pack_rows_4bit(g4, row_start, rows)
                params = {
                    'rowStart': str(row_start),
                    'rows': str(rows),
                    'packed': '1'
                }
                files = {'file': ('chunk.bin', chunk, 'application/octet-stream')}
                if requests is None:
                    raise RuntimeError("requests not installed: pip install requests")
                r = requests.post(host.rstrip('/') + "/stream-chunk", params=params, files=files, timeout=10)
                r.raise_for_status()
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self._log(f"Error: {e}")

    def one_shot_ws(self):
        try:
            x = int(self.x_var.get()); y = int(self.y_var.get())
            w = int(self.w_var.get()); h = int(self.h_var.get())
            host_ip = self.host.get().strip()
            img = self._capture_region(x, y, w, h)
            g4 = self._to_4bit_bytes(img, invert=self.invert_var.get())
            self._ws_send_frame(host_ip, g4)
            self._log("One shot via WebSocket done")
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self._log(f"WS Error: {e}")

    def _loop(self):
        while self.running:
            t0 = time.time()
            try:
                # Prefer WebSocket streaming for performance
                self.one_shot_ws()
            except Exception as e:
                self._log(f"Loop error: {e}")
            # update interval from FPS
            try:
                fps = float(self.fps_var.get())
                if fps <= 0:
                    fps = 1.0
            except Exception:
                fps = 1.0
            self.capture_interval = 1.0 / fps
            dt = time.time() - t0
            sleep_left = max(0.0, self.capture_interval - dt)
            time.sleep(sleep_left)

    def start(self):
        if self.running:
            return
        self.running = True
        threading.Thread(target=self._loop, daemon=True).start()
        self._log("Started streaming")

    def stop(self):
        self.running = False
        self._log("Stopped")

    def test_connect(self):
        try:
            if requests is None:
                raise RuntimeError("requests not installed: pip install requests")
            host = self.host.get().strip().rstrip('/')
            if not host.startswith("http"):
                host = "http://" + host
            r = requests.get(host + "/api/fs-status", timeout=5)
            self._log(f"fs-status: {r.status_code} {r.text[:120]}")
            r2 = requests.get(host + "/api/runtime-status", timeout=5)
            self._log(f"runtime-status: {r2.status_code} {r2.text[:120]}")
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self._log(f"Conn error: {e}")


def main():
    root = tk.Tk()
    app = ScreenStreamerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()


