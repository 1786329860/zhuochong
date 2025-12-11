桌宠AI项目最小原型

运行步骤：
- 安装 Python 3.10+。
- 可选：创建虚拟环境。
- 安装依赖：`pip install -r requirements.txt`。
- 配置环境：复制 `.env.example` 为 `.env`，填入 `DEEPSEEK_API_KEY`（可留空以离线模式运行）。
- 设置动画路径：在 `.env` 中配置 `ANIMATION_FRAMES_DIR` 指向帧资源目录（支持 png/jpg）。
- 启动：`python app.py`。

说明：
- 无 API Key 时使用离线降级，基于规则引擎与本地回复库。
- 有 API Key 时调用 `https://api.deepseek.com/v1/chat/completions`，模型默认 `deepseek-chat`，可通过 `DEEPSEEK_MODEL` 覆盖。
- 动画播放：默认从 `ANIMATION_FRAMES_DIR` 读取帧（101 张），`ANIMATION_FPS` 控制速度。
- 桌宠形态：`PET_SIZE` 控制缩放像素大小；`BG_THRESHOLD` 控制去白背景容忍度，白边多时可调大到 40–60。
- 托盘：如需自定义托盘图标，设置 `TRAY_ICON_PATH` 指向一张 PNG/ICO；未设置会使用默认红色圆形图标。
- 防止绿色描边：透明模式下设置 `ALPHA_THRESHOLD=24`（或 32/40）以二值化透明边缘，避免与透明色混合产生外圈。
- 主菜单：点击系统托盘图标右键选择“主菜单”，可在窗口中直接切换动画目录与 FPS（无需修改 `.env`）。
电脑桌宠
