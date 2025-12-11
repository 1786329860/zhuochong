import os
import threading
import sys
import subprocess
from typing import Tuple, List
from PIL import Image
import numpy as np

def _parse_hex(s: str) -> Tuple[int, int, int]:
    s = s.strip().lstrip('#')
    if len(s) == 6:
        return int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)
    return 244, 244, 244

def _to_transparent(img: Image.Image, bg_threshold: int, alpha_threshold: int, edge_shrink: int = 1) -> Image.Image:
    px = img.load()
    w, h = img.size
    # 检查角点是否透明
    ca = [px[0, 0][3], px[w - 1, 0][3], px[0, h - 1][3], px[w - 1, h - 1][3]]

    from collections import deque
    mask = [[False] * w for _ in range(h)]

    def near_white(r: int, g: int, b: int) -> bool:
        return (255 - (r + g + b) // 3) <= bg_threshold

    if sum(ca) / 4 < 10:
        # 角落已透明：改为从整条边缘扫描近白区域作为种子点进行泛洪
        seeds = []
        for x in range(w):
            r, g, b, a = px[x, 0]
            if a > alpha_threshold and near_white(r, g, b):
                seeds.append((x, 0))
            r, g, b, a = px[x, h - 1]
            if a > alpha_threshold and near_white(r, g, b):
                seeds.append((x, h - 1))
        for y in range(h):
            r, g, b, a = px[0, y]
            if a > alpha_threshold and near_white(r, g, b):
                seeds.append((0, y))
            r, g, b, a = px[w - 1, y]
            if a > alpha_threshold and near_white(r, g, b):
                seeds.append((w - 1, y))
        q = deque(seeds)
        for sx, sy in seeds:
            mask[sy][sx] = True
        dirs = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, -1), (-1, 1), (1, 1)]
        while q:
            x, y = q.popleft()
            for dx, dy in dirs:
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and not mask[ny][nx]:
                    r1, g1, b1, a1 = px[nx, ny]
                    if a1 > alpha_threshold and near_white(r1, g1, b1):
                        mask[ny][nx] = True
                        q.append((nx, ny))
    else:
        # 角落不透明：使用角落平均色作为背景参考
        corners = [px[0, 0], px[w - 1, 0], px[0, h - 1], px[w - 1, h - 1]]
        br = int(sum([c[0] for c in corners]) / 4)
        bg = int(sum([c[1] for c in corners]) / 4)
        bb = int(sum([c[2] for c in corners]) / 4)
        def near_bg(r, g, b):
            return (abs(r - br) + abs(g - bg) + abs(b - bb)) // 3 <= bg_threshold
        seeds = [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]
        q = deque([])
        for sx, sy in seeds:
            r0, g0, b0, _ = px[sx, sy]
            if near_bg(r0, g0, b0):
                mask[sy][sx] = True
                q.append((sx, sy))
        dirs = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, -1), (-1, 1), (1, 1)]
        while q:
            x, y = q.popleft()
            for dx, dy in dirs:
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and not mask[ny][nx]:
                    r1, g1, b1, _ = px[nx, ny]
                    if near_bg(r1, g1, b1):
                        mask[ny][nx] = True
                        q.append((nx, ny))

    # 边缘收缩，减少白边
    for _ in range(max(0, int(edge_shrink))):
        shrink = [[mask[y][x] for x in range(w)] for y in range(h)]
        for y in range(h):
            for x in range(w):
                if not mask[y][x]:
                    continue
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w and 0 <= ny < h and not mask[ny][nx]:
                        shrink[y][x] = False
                        break
        mask = shrink

    # 应用mask：仅修改alpha，不改动RGB，保留主体颜色
    for y in range(h):
        for x in range(w):
            r0, g0, b0, a0 = px[x, y]
            if mask[y][x]:
                px[x, y] = (r0, g0, b0, 0)
            else:
                px[x, y] = (r0, g0, b0, 0 if a0 <= alpha_threshold else 255)
    return img

def batch_remove_white_bg(src_dir: str, dst_dir: str, limit: int = 300, bg_threshold: int = 30, alpha_threshold: int = 24, recursive: bool = True, edge_shrink: int = 1) -> Tuple[int, int]:
    if not os.path.isdir(src_dir):
        return 0, 0
    os.makedirs(dst_dir, exist_ok=True)
    paths: List[str] = []
    if recursive:
        for r, _, files in os.walk(src_dir):
            for f in files:
                ext = os.path.splitext(f)[1].lower()
                if ext in {'.png', '.jpg', '.jpeg', '.webp', '.gif'}:
                    paths.append(os.path.join(r, f))
    else:
        for f in os.listdir(src_dir):
            fp = os.path.join(src_dir, f)
            ext = os.path.splitext(fp)[1].lower()
            if os.path.isfile(fp) and ext in {'.png', '.jpg', '.jpeg', '.webp', '.gif'}:
                paths.append(fp)
    paths = paths[:limit]
    ok = 0
    fail = 0
    for p in paths:
        try:
            img = Image.open(p).convert('RGBA')
            img = _to_transparent(img, bg_threshold, alpha_threshold, edge_shrink=edge_shrink)
            name = os.path.splitext(os.path.basename(p))[0] + '.png'
            out = os.path.join(dst_dir, name)
            img.save(out, format='PNG')
            ok += 1
        except Exception:
            fail += 1
    return ok, fail

def _ensure_cv2():
    try:
        import cv2
        return cv2
    except Exception:
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "opencv-python", "numpy"], check=True)
            import cv2
            return cv2
        except Exception:
            raise

def _detect_wm_mask_bgr(bgr: np.ndarray, strength: int = 1) -> np.ndarray:
    cv2 = _ensure_cv2()
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    s = hsv[...,1]
    v = hsv[...,2]
    m = ((s < 40) & (v > 200)).astype(np.uint8) * 255
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2*strength+1, 2*strength+1))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, kernel)
    h, w = m.shape
    border = np.zeros_like(m)
    bw = max(10, min(h,w)//20)
    border[:bw,:] = 255; border[-bw:,:] = 255; border[:, :bw] = 255; border[:, -bw:] = 255
    m &= border
    return m

def _inpaint_bgr(bgr: np.ndarray, mask: np.ndarray, radius: int = 3) -> np.ndarray:
    cv2 = _ensure_cv2()
    return cv2.inpaint(bgr, mask, radius, cv2.INPAINT_TELEA)

def batch_remove_watermark_images(src_dir: str, dst_dir: str, limit: int = 300, recursive: bool = True, strength: int = 1) -> Tuple[int, int]:
    cv2 = _ensure_cv2()
    if not os.path.isdir(src_dir):
        return 0, 0
    os.makedirs(dst_dir, exist_ok=True)
    paths: List[str] = []
    exts = {'.png', '.jpg', '.jpeg', '.webp'}
    if recursive:
        for r, _, files in os.walk(src_dir):
            for f in files:
                if os.path.splitext(f)[1].lower() in exts:
                    paths.append(os.path.join(r, f))
    else:
        for f in os.listdir(src_dir):
            fp = os.path.join(src_dir, f)
            if os.path.isfile(fp) and os.path.splitext(fp)[1].lower() in exts:
                paths.append(fp)
    paths = paths[:limit]
    ok = 0
    fail = 0
    for p in paths:
        try:
            img = cv2.imread(p, cv2.IMREAD_UNCHANGED)
            if img is None:
                raise RuntimeError("read fail")
            has_alpha = img.shape[2] == 4 if len(img.shape) == 3 else False
            if has_alpha:
                bgr = img[..., :3]
            else:
                bgr = img
            mask = _detect_wm_mask_bgr(bgr, strength=strength)
            out_bgr = _inpaint_bgr(bgr, mask, radius=3+strength)
            if has_alpha:
                out = np.concatenate([out_bgr, img[...,3:4]], axis=2)
            else:
                out = out_bgr
            name = os.path.splitext(os.path.basename(p))[0] + '.png'
            out_path = os.path.join(dst_dir, name)
            cv2.imwrite(out_path, out)
            ok += 1
        except Exception:
            fail += 1
    return ok, fail

def remove_watermark_video_file(in_path: str, out_path: str, mode: str = 'auto', sample: int = 50, strength: int = 1) -> bool:
    cv2 = _ensure_cv2()
    cap = cv2.VideoCapture(in_path)
    if not cap.isOpened():
        return False
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(out_path, fourcc, fps, (w, h))
    masks = []
    count = 0
    while count < sample:
        ret, frame = cap.read()
        if not ret:
            break
        masks.append(_detect_wm_mask_bgr(frame, strength=strength))
        count += 1
    fixed_mask = None
    if masks:
        fixed_mask = masks[0]
        for m in masks[1:]:
            fixed_mask = cv2.bitwise_or(fixed_mask, m)
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if mode == 'fixed' and fixed_mask is not None:
            mask = fixed_mask
        elif mode == 'moving':
            mask = _detect_wm_mask_bgr(frame, strength=strength)
        else:
            cur = _detect_wm_mask_bgr(frame, strength=strength)
            if fixed_mask is not None and cv2.countNonZero(cv2.bitwise_xor(cur, fixed_mask)) < 0.1 * cv2.countNonZero(fixed_mask):
                mask = fixed_mask
            else:
                mask = cur
        out = _inpaint_bgr(frame, mask, radius=3+strength)
        writer.write(out)
    cap.release()
    writer.release()
    return True
