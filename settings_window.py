import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from animation_player import AnimationPlayer
from config_store import load_config, save_config
from tools_bg_remove import batch_remove_white_bg

class SettingsWindow:
    def __init__(self, app, active_tab: str = None):
        self.app = app
        self.root = app.root
        self.top = tk.Toplevel(self.root)
        self.top.title("桌宠设置中心")
        self.top.attributes("-topmost", True)
        self.top.geometry("560x640")
        try:
            self.top.minsize(440, 520)
        except Exception:
            pass

        # Set style
        style = ttk.Style()
        style.theme_use('vista') if 'vista' in style.theme_names() else style.theme_use('default')
        style.configure("TButton", padding=4)
        style.configure("TLabel", padding=2)
        style.configure("TEntry", padding=2)

        # Main container
        main_frame = ttk.Frame(self.top, padding=10)
        main_frame.pack(fill="both", expand=True)

        # Tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill="both", expand=True, pady=(0, 10))

        # --- Tab 1: 基础设置 ---
        self.tab_basic = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(self.tab_basic, text=" 基础设置 ")
        self._init_basic_tab()

        # --- Tab 2: AI设置 ---
        self.tab_ai = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(self.tab_ai, text=" AI大脑 ")
        self._init_ai_tab()

        # --- Tab 3: 工具箱 ---
        self.tab_tools = ttk.Frame(self.notebook, padding=0)
        self.notebook.add(self.tab_tools, text=" 工具箱 ")
        self.tools_canvas = tk.Canvas(self.tab_tools, highlightthickness=0)
        self.tools_vsb = ttk.Scrollbar(self.tab_tools, orient="vertical", command=self.tools_canvas.yview)
        self.tools_canvas.configure(yscrollcommand=self.tools_vsb.set)
        self.tools_vsb.pack(side="right", fill="y")
        self.tools_canvas.pack(side="left", fill="both", expand=True)
        self.tools_body = ttk.Frame(self.tools_canvas, padding=15)
        self.tools_canvas.create_window((0,0), window=self.tools_body, anchor="nw")
        self.tools_body.bind("<Configure>", lambda e: self.tools_canvas.configure(scrollregion=self.tools_canvas.bbox("all")))
        self.tools_canvas.bind_all("<MouseWheel>", lambda e: self.tools_canvas.yview_scroll(-1*(e.delta//120), "units"))
        self._init_tools_tab()

        # --- Bottom Buttons ---
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill="x", side="bottom")
        
        ttk.Button(btn_frame, text="查看历史对话", command=self._open_history).pack(side="left", fill="x", expand=True, padx=(0, 5))
        ttk.Button(btn_frame, text="关闭窗口", command=self.top.destroy).pack(side="right", fill="x", expand=True, padx=(5, 0))

        if active_tab == "ai":
            try:
                self.notebook.select(self.tab_ai)
            except Exception:
                pass

    def _init_basic_tab(self):
        # Group: Appearance
        grp_look = ttk.LabelFrame(self.tab_basic, text="外观与动画", padding=10)
        grp_look.pack(fill="x", pady=(0, 10))

        # Animation Dir
        ttk.Label(grp_look, text="动画目录:").grid(row=0, column=0, sticky="w", pady=5)
        init_cfg = load_config()
        default_dir = init_cfg.get("frames_dir") or os.path.join(os.path.abspath(os.path.dirname(__file__)), "default_frames")
        self.dir_var = tk.StringVar(value=str(default_dir))
        ttk.Entry(grp_look, textvariable=self.dir_var).grid(row=0, column=1, sticky="we", padx=5)
        ttk.Button(grp_look, text="浏览...", command=self._choose_dir, width=8).grid(row=0, column=2, sticky="e")

        # FPS
        ttk.Label(grp_look, text="帧速 (FPS):").grid(row=1, column=0, sticky="w", pady=5)
        self.fps_var = tk.StringVar(value=os.getenv("ANIMATION_FPS", "12"))
        ttk.Entry(grp_look, textvariable=self.fps_var, width=10).grid(row=1, column=1, sticky="w", padx=5)

        # Size
        ttk.Label(grp_look, text="尺寸 (PX):").grid(row=2, column=0, sticky="w", pady=5)
        self.size_var = tk.StringVar(value=str(getattr(self.app.player, "pet_size", int(os.getenv("PET_SIZE", "128")))))
        ttk.Entry(grp_look, textvariable=self.size_var, width=10).grid(row=2, column=1, sticky="w", padx=5)

        # Transparency toggle
        cfg_init = load_config()
        self.transparent_var = tk.BooleanVar(value=bool(cfg_init.get("use_transparent", True)))
        ttk.Checkbutton(grp_look, text="启用透明背景", variable=self.transparent_var).grid(row=3, column=0, columnspan=2, sticky="w", pady=5)

        grp_look.columnconfigure(1, weight=1)

        # Group: Identity
        grp_id = ttk.LabelFrame(self.tab_basic, text="角色设定", padding=10)
        grp_id.pack(fill="x", pady=(0, 10))
        
        cfg = load_config()
        ttk.Label(grp_id, text="宠物昵称:").grid(row=0, column=0, sticky="w", pady=5)
        self.name_var = tk.StringVar(value=str(cfg.get("pet_name") or os.getenv("PET_NAME", "小灵")))
        ttk.Entry(grp_id, textvariable=self.name_var, width=20).grid(row=0, column=1, sticky="w", padx=5)

        # Apply Button
        ttk.Button(self.tab_basic, text="应用基础设置", command=self._apply).pack(fill="x", pady=10)

    def _init_ai_tab(self):
        cfg = load_config()
        
        # Group: Configuration
        grp_ai = ttk.LabelFrame(self.tab_ai, text="模型配置", padding=10)
        grp_ai.pack(fill="x", pady=(0, 10))

        # Provider
        ttk.Label(grp_ai, text="服务商:").grid(row=0, column=0, sticky="w", pady=5)
        self.provider_var = tk.StringVar(value=str(cfg.get("provider") or os.getenv("AI_PROVIDER", "deepseek")))
        cb = ttk.Combobox(grp_ai, textvariable=self.provider_var, values=["deepseek", "openai", "doubao"], state="readonly", width=15)
        cb.grid(row=0, column=1, sticky="w", padx=5)

        # Model
        ttk.Label(grp_ai, text="模型名称:").grid(row=1, column=0, sticky="w", pady=5)
        self.model_var = tk.StringVar(value=str(cfg.get("model") or os.getenv("DEEPSEEK_MODEL", "deepseek-chat")))
        ttk.Entry(grp_ai, textvariable=self.model_var, width=25).grid(row=1, column=1, sticky="w", padx=5)

        # API Key
        ttk.Label(grp_ai, text="API Key:").grid(row=2, column=0, sticky="w", pady=5)
        self.key_var = tk.StringVar(value=str(cfg.get("api_key") or ""))
        ttk.Entry(grp_ai, textvariable=self.key_var, show="*", width=30).grid(row=2, column=1, sticky="we", padx=5)

        ttk.Label(grp_ai, text="API地址(可选):").grid(row=3, column=0, sticky="w", pady=5)
        self.api_url_var = tk.StringVar(value=str(cfg.get("api_url") or ""))
        ttk.Entry(grp_ai, textvariable=self.api_url_var, width=40).grid(row=3, column=1, sticky="we", padx=5)
        
        grp_ai.columnconfigure(1, weight=1)

        # Save Button
        ttk.Button(self.tab_ai, text="保存并重新加载AI", command=self._save_ai).pack(fill="x", pady=10)
        
        # Note
        lbl_note = ttk.Label(self.tab_ai, text="注：API Key 将安全存储在本地配置文件中，\n不会随程序分享给他人。", foreground="gray", justify="center")
        lbl_note.pack(pady=20)

    def _init_tools_tab(self):
        # Group: Batch Remove BG
        grp_tool = ttk.LabelFrame(self.tools_body, text="批量去白底工具", padding=10)
        grp_tool.pack(fill="both", expand=True)

        # Source
        ttk.Label(grp_tool, text="源文件夹:").grid(row=0, column=0, sticky="w", pady=5)
        self.batch_src = tk.StringVar(value=os.getenv("ANIMATION_FRAMES_DIR", ""))
        entry_src = ttk.Entry(grp_tool, textvariable=self.batch_src)
        entry_src.grid(row=0, column=1, sticky="we", padx=5)
        ttk.Button(grp_tool, text="浏览...", command=self._pick_batch_src, width=8).grid(row=0, column=2, sticky="e")

        # Dest
        ttk.Label(grp_tool, text="保存位置:").grid(row=1, column=0, sticky="w", pady=5)
        self.batch_dst = tk.StringVar(value="")
        entry_dst = ttk.Entry(grp_tool, textvariable=self.batch_dst)
        entry_dst.grid(row=1, column=1, sticky="we", padx=5)
        ttk.Button(grp_tool, text="浏览...", command=self._pick_batch_dst, width=8).grid(row=1, column=2, sticky="e")

        # Parameters
        param_frame = ttk.Frame(grp_tool)
        param_frame.grid(row=2, column=0, columnspan=3, pady=10, sticky="w")
        
        ttk.Label(param_frame, text="处理上限:").pack(side="left")
        self.batch_limit = tk.StringVar(value="300")
        ttk.Entry(param_frame, textvariable=self.batch_limit, width=5).pack(side="left", padx=(5, 15))

        ttk.Label(param_frame, text="背景阈值:").pack(side="left")
        self.batch_bg = tk.StringVar(value=os.getenv("BG_THRESHOLD", "30"))
        ttk.Entry(param_frame, textvariable=self.batch_bg, width=5).pack(side="left", padx=(5, 15))

        ttk.Label(param_frame, text="Alpha阈值:").pack(side="left")
        self.batch_alpha = tk.StringVar(value=os.getenv("ALPHA_THRESHOLD", "24"))
        ttk.Entry(param_frame, textvariable=self.batch_alpha, width=5).pack(side="left", padx=(5, 15))
        
        ttk.Label(param_frame, text="边缘收缩:").pack(side="left")
        self.batch_shrink = tk.StringVar(value="1")
        ttk.Entry(param_frame, textvariable=self.batch_shrink, width=5).pack(side="left", padx=(5, 0))

        grp_tool.columnconfigure(1, weight=1)

        # Action
        ttk.Button(grp_tool, text="开始执行处理", command=self._run_batch).grid(row=3, column=0, columnspan=3, sticky="we", pady=10)

        # Status
        self.batch_status = tk.StringVar(value="准备就绪")
        lbl_status = ttk.Label(grp_tool, textvariable=self.batch_status, foreground="blue")
        lbl_status.grid(row=4, column=0, columnspan=3, pady=5)

        # Group: Share Packager
        grp_share = ttk.LabelFrame(self.tools_body, text="分享打包", padding=10)
        grp_share.pack(fill="x", expand=False, pady=10)
        self.pack_status = tk.StringVar(value="生成一个可直接运行的包，不会包含你的API密钥")
        ttk.Button(grp_share, text="一键打包分享", command=self._package_app).grid(row=0, column=0, sticky="we")
        ttk.Label(grp_share, textvariable=self.pack_status).grid(row=1, column=0, sticky="w")

        grp_wm_img = ttk.LabelFrame(self.tools_body, text="批量图片去水印", padding=10)
        grp_wm_img.pack(fill="x", expand=False, pady=10)
        self.wm_img_src = tk.StringVar(value="")
        self.wm_img_dst = tk.StringVar(value="")
        self.wm_img_limit = tk.StringVar(value="200")
        self.wm_img_strength = tk.StringVar(value="1")
        ttk.Label(grp_wm_img, text="源文件夹").grid(row=0, column=0, sticky="w")
        ttk.Entry(grp_wm_img, textvariable=self.wm_img_src).grid(row=0, column=1, sticky="we")
        ttk.Button(grp_wm_img, text="选择", command=self._pick_wm_img_src).grid(row=0, column=2)
        ttk.Label(grp_wm_img, text="保存到").grid(row=1, column=0, sticky="w")
        ttk.Entry(grp_wm_img, textvariable=self.wm_img_dst).grid(row=1, column=1, sticky="we")
        ttk.Button(grp_wm_img, text="选择", command=self._pick_wm_img_dst).grid(row=1, column=2)
        ttk.Label(grp_wm_img, text="上限").grid(row=2, column=0, sticky="w")
        ttk.Entry(grp_wm_img, textvariable=self.wm_img_limit, width=6).grid(row=2, column=1, sticky="w")
        ttk.Label(grp_wm_img, text="强度").grid(row=2, column=2, sticky="w")
        ttk.Entry(grp_wm_img, textvariable=self.wm_img_strength, width=6).grid(row=2, column=3, sticky="w")
        ttk.Button(grp_wm_img, text="开始去水印", command=self._run_wm_images).grid(row=3, column=0, columnspan=4, sticky="we", pady=6)
        self.wm_img_status = tk.StringVar(value="")
        ttk.Label(grp_wm_img, textvariable=self.wm_img_status).grid(row=4, column=0, columnspan=4, sticky="w")
        grp_wm_img.columnconfigure(1, weight=1)

        grp_wm_vid = ttk.LabelFrame(self.tools_body, text="视频去水印", padding=10)
        grp_wm_vid.pack(fill="x", expand=False, pady=10)
        self.wm_vid_src = tk.StringVar(value="")
        self.wm_vid_outdir = tk.StringVar(value="")
        self.wm_vid_mode = tk.StringVar(value="auto")
        self.wm_vid_strength = tk.StringVar(value="1")
        ttk.Label(grp_wm_vid, text="源视频").grid(row=0, column=0, sticky="w")
        ttk.Entry(grp_wm_vid, textvariable=self.wm_vid_src).grid(row=0, column=1, sticky="we")
        ttk.Button(grp_wm_vid, text="选择", command=self._pick_wm_vid_src).grid(row=0, column=2)
        ttk.Label(grp_wm_vid, text="保存到").grid(row=1, column=0, sticky="w")
        ttk.Entry(grp_wm_vid, textvariable=self.wm_vid_outdir).grid(row=1, column=1, sticky="we")
        ttk.Button(grp_wm_vid, text="选择", command=self._pick_wm_vid_outdir).grid(row=1, column=2)
        ttk.Label(grp_wm_vid, text="模式").grid(row=2, column=0, sticky="w")
        ttk.Combobox(grp_wm_vid, textvariable=self.wm_vid_mode, values=["auto","fixed","moving"], state="readonly", width=10).grid(row=2, column=1, sticky="w")
        ttk.Label(grp_wm_vid, text="强度").grid(row=2, column=2, sticky="w")
        ttk.Entry(grp_wm_vid, textvariable=self.wm_vid_strength, width=6).grid(row=2, column=3, sticky="w")
        ttk.Button(grp_wm_vid, text="开始去水印", command=self._run_wm_video).grid(row=3, column=0, columnspan=4, sticky="we", pady=6)
        self.wm_vid_status = tk.StringVar(value="")
        ttk.Label(grp_wm_vid, textvariable=self.wm_vid_status).grid(row=4, column=0, columnspan=4, sticky="w")
        grp_wm_vid.columnconfigure(1, weight=1)

    def _choose_dir(self):
        d = filedialog.askdirectory()
        if d:
            self.dir_var.set(d)
            # Optional: auto apply or wait for user? 
            # Original code auto applied. Let's stick to manual apply for better UX in settings window, 
            # OR keep original behavior. Original called _apply().
            # But in new UI, we have an "Apply" button. 
            # Let's NOT auto apply to avoid jarring changes while browsing.
            # But the user might expect it. Let's keep it safe: just set var.

    def _apply(self):
        d = self.dir_var.get().strip()
        fps = int(self.fps_var.get().strip() or "12")
        size = int(self.size_var.get().strip() or "128")
        
        # Save Basic Settings
        if d:
            os.environ["ANIMATION_FRAMES_DIR"] = d
        os.environ["ANIMATION_FPS"] = str(fps)
        os.environ["PET_SIZE"] = str(size)
        
        # Persist to config for sharing and next runs
        cfg = load_config()
        if d:
            cfg["frames_dir"] = d
        cfg["fps"] = fps
        cfg["pet_size"] = size
        cfg["pet_name"] = self.name_var.get().strip()
        cfg["use_transparent"] = bool(self.transparent_var.get())
        save_config(cfg)

        # Update Player
        self.app.player.set_fps(fps)
        if d:
            self.app.player.set_frames_dir(d)
        self.app.player.set_pet_size(size)
        try:
            use_t = bool(self.transparent_var.get())
            self.app.set_transparency(use_t)
            self.app.player.set_use_transparent(use_t)
        except Exception:
            pass
        
        # Reload brain to update name if needed
        self._reload_brain()
        
        messagebox.showinfo("提示", "基础设置已应用！")

    def _open_history(self):
        t = tk.Toplevel(self.top)
        t.title("历史对话")
        t.geometry("400x500")
        
        frame = ttk.Frame(t, padding=10)
        frame.pack(fill="both", expand=True)
        
        # Use Text widget with scrollbar for better history viewing
        txt = tk.Text(frame, wrap="word", font=("微软雅黑", 10))
        scroll = ttk.Scrollbar(frame, orient="vertical", command=txt.yview)
        txt.configure(yscrollcommand=scroll.set)
        
        scroll.pack(side="right", fill="y")
        txt.pack(side="left", fill="both", expand=True)
        
        for q, a in getattr(self.app, "history", []):
            txt.insert("end", f"你: {q}\n", "user")
            txt.insert("end", f"小灵: {a}\n\n", "bot")
            
        txt.tag_config("user", foreground="blue")
        txt.tag_config("bot", foreground="black")
        txt.config(state="disabled")

    def _save_ai(self):
        cfg = load_config()
        cfg["provider"] = self.provider_var.get().strip()
        cfg["model"] = self.model_var.get().strip()
        key = self.key_var.get().strip()
        if key:
            cfg["api_key"] = key
        url = self.api_url_var.get().strip()
        if url:
            cfg["api_url"] = url
        # Also save name here just in case
        cfg["pet_name"] = self.name_var.get().strip()
        
        save_config(cfg)
        self._reload_brain()
        messagebox.showinfo("提示", "AI配置已保存并重载！")

    def _reload_brain(self):
        try:
            from ai_pet_brain import AIPetBrain
            self.app.brain = AIPetBrain()
        except Exception as e:
            print(f"Reload brain error: {e}")

    def _pick_batch_src(self):
        d = filedialog.askdirectory()
        if d:
            self.batch_src.set(d)

    def _pick_batch_dst(self):
        d = filedialog.askdirectory()
        if d:
            self.batch_dst.set(d)

    def _run_batch(self):
        src = self.batch_src.get().strip()
        dst = self.batch_dst.get().strip()
        
        if not src or not dst:
            messagebox.showwarning("警告", "请先选择源目录和保存目录！")
            return

        try:
            limit = int(self.batch_limit.get().strip() or "300")
            bg = int(self.batch_bg.get().strip() or "30")
            alpha = int(self.batch_alpha.get().strip() or "24")
            shrink = int(self.batch_shrink.get().strip() or "1")
        except ValueError:
             messagebox.showwarning("错误", "参数必须是整数！")
             return

        self.batch_status.set("正在处理中，请稍候...")
        import threading
        def work():
            try:
                ok, fail = batch_remove_white_bg(src, dst, limit, bg, alpha, True, edge_shrink=shrink)
                self.top.after(0, lambda: self.batch_status.set(f"处理完成：{ok} 张成功，{fail} 张失败"))
                self.top.after(0, lambda: messagebox.showinfo("完成", f"处理完成！\n成功: {ok}\n失败: {fail}\n位置: {dst}"))
            except Exception as e:
                self.top.after(0, lambda: self.batch_status.set(f"处理出错: {str(e)}"))

        threading.Thread(target=work, daemon=True).start()

    def _pick_icon(self):
        pass

    def _ensure_app_icon(self):
        import os
        from PIL import Image
        from collections import deque
        proj_dir = os.path.abspath(os.path.dirname(__file__))
        dest_png = os.path.join(proj_dir, "app_icon.png")
        dest_ico = os.path.join(proj_dir, "app_icon.ico")
        source_paths = [
            os.path.join(proj_dir, "app_icon.jpeg"),
            os.path.join(proj_dir, "app_icon.jpg"),
            os.path.join(proj_dir, "assets", "app_icon.jpeg"),
            os.path.join(proj_dir, "assets", "app_icon.jpg"),
            r"D:\\下载\\洛宠.jpeg",
        ]
        src = next((p for p in source_paths if os.path.isfile(p)), None)
        if not src:
            return
        im = Image.open(src).convert("RGBA")
        w, h = im.size
        px = im.load()
        def near_white(r, g, b, thr=30):
            return (255 - (r + g + b) // 3) <= thr
        mask = [[False] * w for _ in range(h)]
        seeds = []
        for x in range(w):
            r, g, b, a = px[x, 0]
            if near_white(r, g, b):
                seeds.append((x, 0))
            r, g, b, a = px[x, h - 1]
            if near_white(r, g, b):
                seeds.append((x, h - 1))
        for y in range(h):
            r, g, b, a = px[0, y]
            if near_white(r, g, b):
                seeds.append((0, y))
            r, g, b, a = px[w - 1, y]
            if near_white(r, g, b):
                seeds.append((w - 1, y))
        q = deque([])
        for sx, sy in seeds:
            mask[sy][sx] = True
            q.append((sx, sy))
        dirs = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, -1), (-1, 1), (1, 1)]
        while q:
            x, y = q.popleft()
            for dx, dy in dirs:
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and not mask[ny][nx]:
                    r1, g1, b1, a1 = px[nx, ny]
                    if a1 > 16 and near_white(r1, g1, b1):
                        mask[ny][nx] = True
                        q.append((nx, ny))
        for y in range(h):
            for x in range(w):
                r0, g0, b0, a0 = px[x, y]
                if mask[y][x]:
                    px[x, y] = (r0, g0, b0, 0)
                else:
                    px[x, y] = (r0, g0, b0, 255 if a0 > 16 else 0)
        ratio = min(900 / w, 900 / h)
        new_w = int(w * ratio)
        new_h = int(h * ratio)
        im_resized = im.resize((new_w, new_h), Image.LANCZOS)
        canvas = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
        cx = (1024 - new_w) // 2
        cy = (1024 - new_h) // 2
        canvas.paste(im_resized, (cx, cy), im_resized)
        canvas.save(dest_png, format="PNG")
        canvas.save(dest_ico, format="ICO", sizes=[(256,256),(128,128),(64,64),(32,32),(16,16)])

    def _package_app(self):
        import threading
        self.pack_status.set("正在打包…首次可能需要安装依赖，请稍候")
        def work():
            try:
                import sys, subprocess, shutil, os
                # Ensure build deps
                subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pyinstaller", "opencv-python", "numpy", "pillow"], check=True)
                # Build onefile exe
                proj_dir = os.path.abspath(os.path.dirname(__file__))
                try:
                    self._ensure_app_icon()
                except Exception:
                    pass
                spec_name = "XiaoLingPet"
                app_py = os.path.join(proj_dir, "app.py")
                from PIL import Image
                candidates = [
                    os.path.join(proj_dir, "app_icon.ico"),
                    os.path.join(proj_dir, "app_icon.png"),
                    os.path.join(proj_dir, "app_icon.jpg"),
                    os.path.join(proj_dir, "app_icon.jpeg"),
                    os.path.join(proj_dir, "assets", "app_icon.ico"),
                    os.path.join(proj_dir, "assets", "app_icon.png"),
                    os.path.join(proj_dir, "assets", "app_icon.jpg"),
                    os.path.join(proj_dir, "assets", "app_icon.jpeg"),
                ]
                icon_src = next((p for p in candidates if os.path.isfile(p)), None)
                icon_ico = os.path.join(proj_dir, "build_icon.ico")
                use_icon = None
                if icon_src and icon_src.lower().endswith(".ico"):
                    use_icon = icon_src
                elif icon_src:
                    try:
                        im = Image.open(icon_src).convert("RGBA")
                        im.save(icon_ico, format="ICO", sizes=[(256,256),(128,128),(64,64),(32,32),(16,16)])
                        use_icon = icon_ico
                    except Exception:
                        use_icon = None
                cmd = [sys.executable, "-m", "PyInstaller", "-F", "-w", "-n", spec_name,
                       "--hidden-import", "cv2", "--hidden-import", "numpy",
                       "--add-data", f"{os.path.join(proj_dir,'default_frames')};default_frames"]
                if use_icon:
                    cmd += ["-i", use_icon]
                cmd.append(app_py)
                subprocess.run(cmd, cwd=proj_dir, check=True)
                dist_dir = os.path.join(proj_dir, "dist")
                exe_path = os.path.join(dist_dir, f"{spec_name}.exe")
                # Zip to Desktop
                desktop = os.path.join(os.path.expanduser("~"), "Desktop")
                out_root = desktop if os.path.isdir(desktop) else dist_dir
                out_zip = os.path.join(out_root, f"{spec_name}_Share")
                # Create a temp folder containing exe only (no .env or configs)
                temp_out = os.path.join(dist_dir, f"{spec_name}_share")
                if os.path.isdir(temp_out):
                    shutil.rmtree(temp_out, ignore_errors=True)
                os.makedirs(temp_out, exist_ok=True)
                shutil.copy2(exe_path, os.path.join(temp_out, f"{spec_name}.exe"))
                shutil.make_archive(out_zip, 'zip', temp_out)
                msg = f"打包完成：{out_zip}.zip（双击运行，无终端窗口；不含你的API密钥）"
                if use_icon:
                    msg += "，已应用内置图标"
                self.top.after(0, lambda: self.pack_status.set(msg))
            except Exception as e:
                self.top.after(0, lambda: self.pack_status.set(f"打包失败：{e}"))
        threading.Thread(target=work, daemon=True).start()

    def _pick_wm_img_src(self):
        d = filedialog.askdirectory()
        if d:
            self.wm_img_src.set(d)

    def _pick_wm_img_dst(self):
        d = filedialog.askdirectory()
        if d:
            self.wm_img_dst.set(d)

    def _run_wm_images(self):
        from tools_bg_remove import batch_remove_watermark_images
        src = self.wm_img_src.get().strip()
        dst = self.wm_img_dst.get().strip()
        try:
            limit = int(self.wm_img_limit.get().strip() or "200")
            strength = int(self.wm_img_strength.get().strip() or "1")
        except Exception:
            self.wm_img_status.set("参数错误")
            return
        if not src or not dst:
            self.wm_img_status.set("请选择源/保存路径")
            return
        self.wm_img_status.set("处理中…")
        import threading
        def work():
            ok, fail = batch_remove_watermark_images(src, dst, limit=limit, recursive=True, strength=strength)
            self.top.after(0, lambda: self.wm_img_status.set(f"完成：{ok} 成功，{fail} 失败，保存到 {dst}"))
        threading.Thread(target=work, daemon=True).start()

    def _pick_wm_vid_src(self):
        p = filedialog.askopenfilename(filetypes=[("视频", ".mp4 .mov .avi .mkv")])
        if p:
            self.wm_vid_src.set(p)

    def _pick_wm_vid_outdir(self):
        d = filedialog.askdirectory()
        if d:
            self.wm_vid_outdir.set(d)

    def _run_wm_video(self):
        from tools_bg_remove import remove_watermark_video_file
        src = self.wm_vid_src.get().strip()
        outdir = self.wm_vid_outdir.get().strip()
        mode = self.wm_vid_mode.get().strip() or "auto"
        try:
            strength = int(self.wm_vid_strength.get().strip() or "1")
        except Exception:
            self.wm_vid_status.set("参数错误")
            return
        if not src or not outdir:
            self.wm_vid_status.set("请选择源视频与保存目录")
            return
        import os
        name = os.path.splitext(os.path.basename(src))[0] + "_clean.mp4"
        out = os.path.join(outdir, name)
        self.wm_vid_status.set("处理中…")
        import threading
        def work():
            ok = remove_watermark_video_file(src, out, mode=mode, strength=strength)
            self.top.after(0, lambda: self.wm_vid_status.set("完成：" + (out if ok else "失败")))
        threading.Thread(target=work, daemon=True).start()
