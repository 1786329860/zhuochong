import os
import threading
from typing import Optional

try:
    import pystray
    from PIL import Image, ImageDraw
except Exception:
    pystray = None
    Image = None
    ImageDraw = None

class Tray:
    def __init__(self, on_exit, on_show, on_hide, on_settings=None, icon_path: Optional[str] = None):
        self.on_exit = on_exit
        self.on_show = on_show
        self.on_hide = on_hide
        self.on_settings = on_settings
        self.icon: Optional[pystray.Icon] = None
        self.icon_path = icon_path or os.getenv("TRAY_ICON_PATH", "")

    def _default_icon(self) -> Optional[Image.Image]:
        if not Image or not ImageDraw:
            return None
        img = Image.new("RGBA", (64, 64), (255, 255, 255, 0))
        d = ImageDraw.Draw(img)
        d.ellipse((6, 6, 58, 58), fill=(255, 74, 106, 255))
        d.ellipse((20, 24, 28, 32), fill=(255, 255, 255, 255))
        d.ellipse((36, 24, 44, 32), fill=(255, 255, 255, 255))
        d.rectangle((30, 36, 34, 40), fill=(255, 255, 255, 255))
        return img

    def start(self):
        if not pystray or not Image:
            return
        img: Optional[Image.Image] = None
        try:
            if self.icon_path and os.path.isfile(self.icon_path):
                img = Image.open(self.icon_path).convert("RGBA")
        except Exception:
            img = None
        if img is None:
            img = self._default_icon()
        menu = pystray.Menu(
            pystray.MenuItem("主菜单", lambda: self.on_settings() if self.on_settings else None),
            pystray.MenuItem("显示", lambda: self.on_show()),
            pystray.MenuItem("隐藏", lambda: self.on_hide()),
            pystray.MenuItem("退出", self._exit)
        )
        self.icon = pystray.Icon("小灵桌宠", img, menu=menu)
        threading.Thread(target=self.icon.run, daemon=True).start()

    def _exit(self, *args):
        if self.icon:
            try:
                self.icon.stop()
            except Exception:
                pass
        self.on_exit()
