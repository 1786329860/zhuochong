import os
import glob
from typing import List, Optional

try:
    from PIL import Image, ImageTk  # type: ignore
except Exception:
    Image = None
    ImageTk = None

class AnimationPlayer:
    def __init__(self, root, image_label, frames_dir: Optional[str] = None, fps: int = 12):
        self.root = root
        self.label = image_label
        self.fps = max(1, int(fps))
        self.frames_dir = frames_dir or os.getenv(
            "ANIMATION_FRAMES_DIR",
            r"D:\下载\selected_frames_101_1765341866824",
        )
        self.pet_size = int(os.getenv("PET_SIZE", "128"))
        self.bg_threshold = int(os.getenv("BG_THRESHOLD", "30"))
        self.use_transparent = os.getenv("USE_TRANSPARENT", "false").lower() == "true"
        self.bg_fill_color = os.getenv("BG_FILL_COLOR", "#f4f4f4")
        self.alpha_threshold = int(os.getenv("ALPHA_THRESHOLD", "24"))
        self.recursive = os.getenv("ANIMATION_RECURSIVE", "false").lower() == "true"
        self._frames: List = []
        self._frame_index = 0
        self._after_id: Optional[str] = None
        self._load_frames()

    def _load_frames(self):
        if not Image or not ImageTk:
            try:
                print("animation: pillow not available")
            except Exception:
                pass
            self._frames = []
            return
        if not self.frames_dir or not os.path.isdir(self.frames_dir):
            try:
                print("animation: dir invalid", self.frames_dir)
            except Exception:
                pass
            self._frames = []
            return
        if self.recursive:
            paths = []
            for r, _, files in os.walk(self.frames_dir):
                for f in files:
                    paths.append(os.path.join(r, f))
        else:
            paths = sorted(
                glob.glob(os.path.join(self.frames_dir, "*.png"))
                + glob.glob(os.path.join(self.frames_dir, "*.jpg"))
                + glob.glob(os.path.join(self.frames_dir, "*.jpeg"))
                + glob.glob(os.path.join(self.frames_dir, "*.webp"))
                + glob.glob(os.path.join(self.frames_dir, "*.gif"))
            )
        try:
            print("animation: loading from", self.frames_dir, "files", len(paths))
        except Exception:
            pass
        imgs = []
        for p in paths:
            try:
                img = Image.open(p).convert("RGBA")
                w, h = img.size
                if self.pet_size > 0:
                    img = img.resize((self.pet_size, int(h * self.pet_size / w)), Image.LANCZOS)
                img = self._process_bg(img)
                imgs.append(ImageTk.PhotoImage(img))
            except Exception:
                continue
        self._frames = imgs
        if not self._frames:
            self._ensure_visible_placeholder()

    def _process_bg(self, img: Image.Image) -> Image.Image:
        px = img.load()
        w, h = img.size
        # 自动检测：角点若已透明，视为素材已抠图；对 alpha 做二值化避免外缘描线
        corner_alpha = [px[1, 1][3], px[w - 2, 1][3], px[1, h - 2][3], px[w - 2, h - 2][3]]
        if self.use_transparent and sum(corner_alpha) / 4 < 10:
            for y in range(h):
                for x in range(w):
                    r0, g0, b0, a0 = px[x, y]
                    px[x, y] = (r0, g0, b0, 0 if a0 <= self.alpha_threshold else 255)
            return img

        corners = [px[1, 1], px[w - 2, 1], px[1, h - 2], px[w - 2, h - 2]]
        r = int(sum([c[0] for c in corners]) / 4)
        g = int(sum([c[1] for c in corners]) / 4)
        b = int(sum([c[2] for c in corners]) / 4)
        thr = self.bg_threshold

        def parse_hex(s: str):
            s = s.strip().lstrip('#')
            if len(s) == 6:
                return int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)
            return 244, 244, 244

        fr, fg, fb = parse_hex(self.bg_fill_color)
        for y in range(h):
            for x in range(w):
                cr, cg, cb, ca = px[x, y]
                dr = abs(cr - r)
                dg = abs(cg - g)
                db = abs(cb - b)
                d = (dr + dg + db) // 3
                if d <= thr:
                    if self.use_transparent:
                        px[x, y] = (r, g, b, 0)
                    else:
                        px[x, y] = (fr, fg, fb, 255)
                else:
                    if self.use_transparent:
                        px[x, y] = (cr, cg, cb, 0 if ca <= self.alpha_threshold else 255)
                    else:
                        px[x, y] = (cr, cg, cb, 255)
        return img

    def play(self, animation_name: str):
        # 当前仅一套帧序列，全部动画名共用
        if self._after_id:
            try:
                self.root.after_cancel(self._after_id)
            except Exception:
                pass
        self._frame_index = 0
        self._tick()

    def stop(self):
        if self._after_id:
            try:
                self.root.after_cancel(self._after_id)
            except Exception:
                pass
        self._after_id = None

    def set_pet_size(self, size: int):
        try:
            self.stop()
        except Exception:
            pass
        try:
            self.pet_size = max(32, int(size))
        except Exception:
            self.pet_size = 128
        self._load_frames()
        self._frame_index = 0
        self._tick()

    def set_use_transparent(self, use: bool):
        try:
            self.stop()
        except Exception:
            pass
        self.use_transparent = bool(use)
        self._load_frames()
        self._frame_index = 0
        self._tick()

    def set_fps(self, fps: int):
        try:
            self.stop()
        except Exception:
            pass
        self.fps = max(1, int(fps))
        self._tick()

    def set_frames_dir(self, frames_dir: Optional[str]):
        if frames_dir:
            self.frames_dir = frames_dir
        try:
            self.stop()
        except Exception:
            pass
        self._load_frames()
        self._frame_index = 0
        self._tick()

    def _tick(self):
        if not self._frames:
            return
        frame = self._frames[self._frame_index]
        self.label.configure(image=frame)
        self.label.image = frame
        self._frame_index = (self._frame_index + 1) % len(self._frames)
        interval = int(1000 / self.fps)
        self._after_id = self.root.after(interval, self._tick)

    def _ensure_visible_placeholder(self):
        try:
            self.root.configure(bg="#f4f4f4")
            self.label.configure(text=f"资源未加载：{self.frames_dir}", bg="#f4f4f4")
        except Exception:
            pass
