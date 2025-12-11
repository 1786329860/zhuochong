import os
import threading
import time
try:
    from dotenv import load_dotenv
except Exception:
    def load_dotenv():
        return None
import tkinter as tk
from tkinter import filedialog
from ai_pet_brain import AIPetBrain
from ai_pet_brain import AIPetBrain
from system_monitor import get_system_status, get_user_activity
from animation_player import AnimationPlayer
from tray_icon import Tray
from settings_window import SettingsWindow
from config_store import load_config

load_dotenv()

class PetApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.brain = AIPetBrain()
        self.anim_var = tk.StringVar(value="idle_blink")
        self.transparent = "#00FF00"
        cfg0 = load_config()
        env_trans = os.getenv("USE_TRANSPARENT")
        self.use_transparent = (cfg0.get("use_transparent") if cfg0.get("use_transparent") is not None else (env_trans and env_trans.lower() == "true") )
        if self.use_transparent is None:
            self.use_transparent = True
        self.bg_fill_color = str(cfg0.get("bg_fill_color") or os.getenv("BG_FILL_COLOR", "#f4f4f4"))
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        if self.use_transparent:
            try:
                self.root.wm_attributes("-transparentcolor", self.transparent)
            except Exception:
                pass
            self.root.configure(bg=self.transparent)
            self.image_label = tk.Label(self.root, bg=self.transparent, bd=0)
        else:
            self.root.configure(bg=self.bg_fill_color)
            self.image_label = tk.Label(self.root, bg=self.bg_fill_color, bd=0)
        self.image_label.pack()
        self.image_label.bind("<Button-1>", self._on_label_click)
        self.image_label.bind("<B1-Motion>", self._on_move)
        self.image_label.bind("<ButtonRelease-1>", lambda e: None)

        self.bubble_var = tk.StringVar(value="")
        self.bubble = tk.Label(
            self.root,
            textvariable=self.bubble_var,
            bg="#ffffff",
            fg="#333333",
            font=("Microsoft YaHei", 11),
            wraplength=240,
            bd=1,
            relief="solid",
            padx=8,
            pady=6,
        )
        self.bubble.place_forget()
        self.chat_entry = tk.Entry(self.root, width=30)
        self.chat_entry.bind("<Return>", lambda e: self._on_chat_enter(self.chat_entry.get()))
        self.chat_entry.bind("<FocusOut>", lambda e: self._toggle_input(False))
        try:
            self.chat_entry.configure(bg="#ffffff")
        except Exception:
            pass
        self._input_visible = False
        self._type_after = None
        self._fade_after = None

        cfg = load_config()
        fps = int(str(cfg.get("fps") or os.getenv("ANIMATION_FPS", "12")))
        self.player = AnimationPlayer(self.root, self.image_label, fps=fps)
        size = int(str(cfg.get("pet_size") or os.getenv("PET_SIZE", "128")))
        self.player.set_pet_size(size)
        frames_dir = cfg.get("frames_dir")
        if not frames_dir:
            try:
                import sys
                base = getattr(sys, "_MEIPASS", os.path.abspath(os.path.dirname(__file__)))
                default_frames = os.path.join(base, "default_frames")
                if os.path.isdir(default_frames):
                    frames_dir = default_frames
            except Exception:
                pass
        if frames_dir:
            try:
                self.player.set_frames_dir(frames_dir)
            except Exception:
                pass
        try:
            self.player.set_use_transparent(bool(self.use_transparent))
        except Exception:
            pass
        self.player.play(self.anim_var.get())
        self._schedule_tick()
        self.tray = Tray(on_exit=self._exit, on_show=self._show, on_hide=self._hide, on_settings=self._open_settings)
        self.tray.start()
        try:
            self.root.after(500, lambda: SettingsWindow(self))
        except Exception:
            pass
        self.root.bind('<Control-o>', lambda e: self._choose_frames_dir())
        self.root.bind('<Button-1>', self._maybe_hide_input, add=True)
        self.history = []

    def _apply_ai(self, ai_text: str, anim: str, clear_entry: bool = False):
        self.anim_var.set(anim)
        self.player.play(anim)

    def _tick(self):
        threading.Thread(target=self._worker_tick, daemon=True).start()

    def _worker_tick(self):
        try:
            status = get_system_status()
            activity = get_user_activity()
            ai_text, anim = self.brain.generate_response(status, activity)
            self.root.after(0, lambda: self._apply_ai(ai_text, anim))
        finally:
            self._schedule_tick()

    def _start_move(self, event):
        self._x = event.x
        self._y = event.y

    def _on_label_click(self, event):
        self._start_move(event)
        self._toggle_input(True)
        self._layout_entry()

    def _on_move(self, event):
        x = self.root.winfo_x() + event.x - self._x
        y = self.root.winfo_y() + event.y - self._y
        self.root.geometry(f"+{x}+{y}")

    def set_transparency(self, use_transparent: bool):
        self.use_transparent = bool(use_transparent)
        try:
            if self.use_transparent:
                self.root.wm_attributes("-transparentcolor", self.transparent)
                self.root.configure(bg=self.transparent)
                self.image_label.configure(bg=self.transparent)
            else:
                self.root.configure(bg=self.bg_fill_color)
                self.image_label.configure(bg=self.bg_fill_color)
        except Exception:
            pass

    def _exit(self):
        try:
            self.root.destroy()
        except Exception:
            pass

    def _hide(self):
        try:
            self.root.withdraw()
        except Exception:
            pass

    def _show(self):
        try:
            self.root.deiconify()
        except Exception:
            pass

    def _open_settings(self):
        try:
            SettingsWindow(self)
        except Exception:
            pass

    def _choose_frames_dir(self):
        try:
            d = filedialog.askdirectory()
            if d:
                self.player.set_frames_dir(d)
                self.player.set_fps(int(os.getenv("ANIMATION_FPS", "12")))
        except Exception:
            pass

    def _schedule_tick(self):
        # 每5分钟触发一次
        self.root.after(5 * 60 * 1000, self._tick)

    def _toggle_input(self, show: bool):
        try:
            if show and not self._input_visible:
                self._layout_entry()
                self.chat_entry.focus_set()
                self._input_visible = True
            elif not show and self._input_visible:
                self.chat_entry.place_forget()
                self._input_visible = False
        except Exception:
            pass

    def _layout_entry(self):
        try:
            self.root.update_idletasks()
            x = self.image_label.winfo_x() + self.image_label.winfo_width() // 2 - 100
            y = self.image_label.winfo_y() + self.image_label.winfo_height() + 6
            h = self.chat_entry.winfo_reqheight()
            need = y + h + 6
            cur_w = max(220, self.root.winfo_width())
            cur_h = max(self.root.winfo_height(), self.image_label.winfo_height())
            if need > cur_h:
                self.root.geometry(f"{cur_w}x{need}+{self.root.winfo_x()}+{self.root.winfo_y()}")
            self.chat_entry.place(x=max(0, x), y=y, width=200)
            try:
                self.chat_entry.lift()
            except Exception:
                pass
        except Exception:
            pass

    def _layout_bubble(self):
        try:
            self.root.update_idletasks()
            bw = min(240, max(120, self.bubble.winfo_reqwidth()))
            x = self.image_label.winfo_x() + self.image_label.winfo_width() // 2 - bw // 2
            y = self.image_label.winfo_y() - self.bubble.winfo_reqheight() - 10
            self.bubble.place(x=max(0, x), y=max(0, y), width=bw)
        except Exception:
            pass

    def _on_chat_enter(self, text: str):
        if not text:
            return
        self._toggle_input(False)
        try:
            self.chat_entry.delete(0, tk.END)
        except Exception:
            pass
        self._type_bubble("思考中…")
        threading.Thread(target=self._worker_chat, args=(text,), daemon=True).start()

    def _worker_chat(self, text: str):
        status = get_system_status()
        activity = get_user_activity()
        ai_text, anim = self.brain.generate_response(status, activity, user_input=text)
        self.history.append((text, ai_text))
        self.root.after(0, lambda: self._after_chat(ai_text, anim))

    def _after_chat(self, ai_text: str, anim: str):
        self.player.play(anim)
        self._type_bubble(ai_text)

    def _type_bubble(self, text: str):
        if self._type_after:
            try:
                self.root.after_cancel(self._type_after)
            except Exception:
                pass
            self._type_after = None
        if self._fade_after:
            try:
                self.root.after_cancel(self._fade_after)
            except Exception:
                pass
            self._fade_after = None
        self._typing_index = 0
        self._typing_text = text
        def step():
            self._typing_index += 1
            self.bubble_var.set(self._typing_text[: self._typing_index])
            self._layout_bubble()
            if self._typing_index < len(self._typing_text):
                self._type_after = self.root.after(30, step)
            else:
                self._type_after = None
                self._start_fade()
        step()

    def _start_fade(self):
        self._fade_index = 0
        def fade():
            cur = self.bubble_var.get()
            if not cur:
                self._fade_after = None
                self.bubble.place_forget()
                return
            self.bubble_var.set(cur[1:])
            self._layout_bubble()
            self._fade_after = self.root.after(120, fade)
        self._fade_after = self.root.after(2000, fade)

    def _maybe_hide_input(self, event):
        try:
            w = str(event.widget)
            if event.widget not in (self.image_label, self.chat_entry) and self._input_visible:
                self._toggle_input(False)
        except Exception:
            pass


if __name__ == "__main__":
    root = tk.Tk()
    app = PetApp(root)
    root.mainloop()
