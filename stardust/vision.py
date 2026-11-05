"""图像识别 + 自动适配窗口尺寸。

所有坐标都写在 “基准坐标系”（在 2560x1600 客户区下采集）里。
实际窗口可能是任意尺寸/比例（1280x720、1920x1080、带黑边……），
因此运行时用 **锚点模板多尺度匹配** 求出 基准→实际 的映射 (scale, tx, ty)：
    实际坐标 = 基准坐标 * scale + (tx, ty)
- 好运星盘窗口：锚点 = 左上角 “好运星盘” 标题（所有标签页都有）
- 大厅按钮：直接在整张截图里多尺度搜 “常驻活动” / “好运星盘” 图标
找到映射后把截图仿射变换回基准坐标系，下游识别代码就和分辨率无关了。
"""
import os

import cv2
import numpy as np

BASE_W, BASE_H = 2560, 1600
TPL_DIR = os.path.join(os.path.dirname(__file__), "templates")

# ---------- 基准坐标 ----------
CELL_X = [698, 925, 1153]
CELL_Y = [454, 691, 924]
HALF_W, HALF_H = 45, 55
ARROWS = {
    "col0": (698, 292), "col1": (925, 292), "col2": (1153, 292),
    "row0": (527, 460), "row1": (527, 693), "row2": (527, 922),
    "diag": (567, 314),   # 左上角箭头：左上→右下
    "anti": (554, 1075),  # 左下角箭头：左下→右上
}
MAIN_BUTTON = (928, 1178)          # 开始占卜 / 请选择结果 / 确认选择
TAB_STARDUST = (172, 485)          # 左侧 “星屑占卜” 标签
CLOSE_X = (2381, 147)              # 好运星盘 窗口关闭按钮

# 模板: 文件名 -> 它在基准坐标系里的中心
TEMPLATE_CENTER = {
    "win_title.png": (585, 135),
    "page_stardust.png": (920, 1084),
    "count_0.png": (1045, 1084),
    "nav_xingpan.png": (2440, 950),
    "nav_changzhu.png": (2440, 795),
}
# 大厅按钮的实际点击点（基准坐标），相对模板中心换算
LOBBY_CLICK = {
    "nav_changzhu.png": (2440, 740),   # 常驻活动 图标
    "nav_xingpan.png": (2440, 905),    # 好运星盘 图标
}

def imread(path):
    """支持中文/空格路径的 imread（cv2.imread 在 Windows 上读不了非 ASCII 路径）。"""
    try:
        data = np.fromfile(path, dtype=np.uint8)
    except (FileNotFoundError, OSError):
        return None
    return cv2.imdecode(data, cv2.IMREAD_COLOR) if data.size else None


def imwrite(path, img):
    """支持中文/空格路径的 imwrite。"""
    ok, buf = cv2.imencode(os.path.splitext(path)[1] or ".png", img)
    if ok:
        buf.tofile(path)
    return ok


_tpl_cache = {}


def tpl(name):
    if name not in _tpl_cache:
        t = imread(os.path.join(TPL_DIR, name))
        if t is None:
            raise FileNotFoundError(name)
        _tpl_cache[name] = t
    return _tpl_cache[name]


# ---------- 多尺度匹配 ----------
def _scale_range(img):
    h, w = img.shape[:2]
    a, b = w / BASE_W, h / BASE_H
    lo, hi = min(a, b) * 0.85, max(a, b) * 1.15
    n = max(8, int((hi - lo) / 0.02) + 1)
    return np.linspace(lo, hi, n)


_scale_hint = {}   # 窗口尺寸 -> 上次匹配到的缩放，优先在附近搜，快很多


def find_multiscale(img, name, thresh=0.8, scales=None):
    """在实际截图中多尺度搜模板。返回 (cx, cy, scale, score) 或 None。"""
    key = (img.shape[:2], name)
    if scales is None and key in _scale_hint:
        # 同一窗口尺寸下 UI 缩放不变：见过的模板只在上次缩放附近搜
        h = _scale_hint[key]
        return _find_multiscale(img, name, thresh, np.linspace(h * 0.98, h * 1.02, 3))
    r = _find_multiscale(img, name, thresh, scales)
    if r:
        _scale_hint[key] = r[2]
    return r


def _find_multiscale(img, name, thresh=0.8, scales=None):
    """先在缩小图上粗搜，再在原图上精修。"""
    t = tpl(name)
    scales = _scale_range(img) if scales is None else scales
    # 粗搜：图像缩到 1/2（太小则不缩）
    k = 0.5 if min(img.shape[:2]) > 900 else 1.0
    small = cv2.resize(img, None, fx=k, fy=k, interpolation=cv2.INTER_AREA) if k != 1 else img
    best = (-1, None, None)
    for s in scales:
        tw, th = int(t.shape[1] * s * k), int(t.shape[0] * s * k)
        if tw < 8 or th < 8 or tw >= small.shape[1] or th >= small.shape[0]:
            continue
        ts = cv2.resize(t, (tw, th), interpolation=cv2.INTER_AREA)
        r = cv2.matchTemplate(small, ts, cv2.TM_CCOEFF_NORMED)
        _, sc, _, loc = cv2.minMaxLoc(r)
        if sc > best[0]:
            best = (sc, s, loc)
    if best[1] is None or best[0] < thresh - 0.15:
        return None
    # 精修：在原图上、最佳尺度附近 ±3%
    s0, loc = best[1], best[2]
    cx0, cy0 = (loc[0] / k), (loc[1] / k)
    fine = (-1, None, None)
    for s in np.linspace(s0 * 0.97, s0 * 1.03, 25):
        tw, th = int(round(t.shape[1] * s)), int(round(t.shape[0] * s))
        x0, y0 = int(max(0, cx0 - 20)), int(max(0, cy0 - 20))
        roi = img[y0:y0 + th + 40, x0:x0 + tw + 40]
        if roi.shape[0] < th or roi.shape[1] < tw:
            continue
        ts = cv2.resize(t, (tw, th), interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_LINEAR)
        r = cv2.matchTemplate(roi, ts, cv2.TM_CCOEFF_NORMED)
        _, sc, _, l = cv2.minMaxLoc(r)
        if sc > fine[0]:
            fine = (sc, s, (x0 + l[0] + tw / 2, y0 + l[1] + th / 2))
    if fine[0] < thresh:
        return None
    return fine[2][0], fine[2][1], fine[1], fine[0]


class Frame:
    """基准坐标 -> 实际截图坐标 的映射。"""

    def __init__(self, scale, tx, ty):
        self.s, self.tx, self.ty = scale, tx, ty

    @classmethod
    def from_anchor(cls, name, hit):
        cx, cy, s, _ = hit
        bx, by = TEMPLATE_CENTER[name]
        return cls(s, cx - bx * s, cy - by * s)

    def to_img(self, x, y):
        return x * self.s + self.tx, y * self.s + self.ty

    def warp(self, img):
        """把实际截图变换到 2560x1600 基准坐标系。"""
        m = np.float32([[self.s, 0, self.tx], [0, self.s, self.ty]])
        return cv2.warpAffine(img, m, (BASE_W, BASE_H),
                              flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP)

    def __repr__(self):
        return f"Frame(scale={self.s:.3f}, offset=({self.tx:.0f},{self.ty:.0f}))"


def _score_at(base_img, name, pad=40):
    """在基准图里、模板应在的位置附近匹配，返回得分。"""
    t = tpl(name)
    cx, cy = TEMPLATE_CENTER[name]
    h, w = t.shape[:2]
    x0, y0 = int(cx - w / 2 - pad), int(cy - h / 2 - pad)
    roi = base_img[max(0, y0):y0 + h + 2 * pad, max(0, x0):x0 + w + 2 * pad]
    if roi.shape[0] < h or roi.shape[1] < w:
        return 0.0
    return float(cv2.matchTemplate(roi, t, cv2.TM_CCOEFF_NORMED).max())


def find_window_frame(img, cached=None):
    """定位好运星盘窗口。先用缓存的映射快速验证，失败再多尺度搜索。"""
    if cached is not None and _score_at(cached.warp(img), "win_title.png") > 0.75:
        return cached
    hit = find_multiscale(img, "win_title.png", 0.75)
    return Frame.from_anchor("win_title.png", hit) if hit else None


# ---------- 基准图上的识别 ----------
def on_stardust_page(base_img):
    return _score_at(base_img, "page_stardust.png") > 0.8


def plays_left_is_zero(base_img):
    return _score_at(base_img, "count_0.png", pad=25) > 0.9


def selected_line(base_img):
    """返回当前高亮（金色）的线箭头名，没有则 None。"""
    hsv = cv2.cvtColor(base_img, cv2.COLOR_BGR2HSV)
    best, best_n = None, 0
    for k, (x, y) in ARROWS.items():
        m = cv2.inRange(hsv[y - 30:y + 30, x - 30:x + 30], (10, 90, 150), (35, 255, 255))
        n = int(m.sum() / 255)
        if n > best_n:
            best, best_n = k, n
    return best if best_n > 100 else None


def _white_mask(crop):
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    return cv2.inRange(hsv, (0, 0, 215), (180, 70, 255))


def cell_crop(img, i):
    x, y = CELL_X[i % 3], CELL_Y[i // 3]
    return img[y - HALF_H:y + HALF_H, x - HALF_W:x + HALF_W]


def is_revealed(crop):
    b, g, r = [float(c) for c in crop.reshape(-1, 3).mean(0)]
    return b > 170 and g > 120


def classify(crop):
    if not is_revealed(crop):
        return 0, 1.0
    m = _white_mask(crop)
    pad = cv2.copyMakeBorder(m, 8, 8, 8, 8, cv2.BORDER_CONSTANT, value=0)
    best, best_s = 0, -1.0
    for d in range(1, 10):
        s = cv2.matchTemplate(pad, _white_mask(tpl(f"digit_{d}.png")), cv2.TM_CCOEFF_NORMED).max()
        if s > best_s:
            best, best_s = d, float(s)
    return best, best_s


def read_board(base_img):
    vals, scores = [], []
    for i in range(9):
        v, s = classify(cell_crop(base_img, i))
        vals.append(v)
        scores.append(s)
    return tuple(vals), scores


if __name__ == "__main__":
    import sys, glob
    for p in sys.argv[1:] or sorted(glob.glob(os.path.join(os.path.dirname(__file__), "captures", "*.png"))):
        img = imread(p)
        f = find_window_frame(img)
        if not f:
            print(os.path.basename(p), "未找到好运星盘窗口")
            continue
        b = f.warp(img)
        print(os.path.basename(p), f, "page" if on_stardust_page(b) else "other-tab",
              read_board(b)[0], "zero" if plays_left_is_zero(b) else "", selected_line(b) or "")
