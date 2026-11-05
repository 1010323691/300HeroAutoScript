"""合成测试：把真实截图缩放/加黑边成各种窗口尺寸，检查识别与点击坐标映射。"""
import os
import cv2
import numpy as np
import vision as v

CAP = os.path.join(os.path.dirname(__file__), "captures")
SIZES = [(2560, 1600), (1920, 1200), (1280, 800), (1920, 1080), (1600, 900),
         (1366, 768), (1280, 720), (1024, 768), (2560, 1440)]

CASES = {  # 文件: (期望board, 是否星屑页, 是否0次, 选中线)
    "s1_cell5_9.png": ((0, 0, 0, 0, 0, 9, 0, 0, 0), True, False, None),
    "s4.png": ((0, 0, 5, 0, 3, 9, 0, 0, 4), True, False, None),
    "s5_full.png": ((8, 1, 5, 6, 3, 9, 2, 7, 4), True, False, "col1"),
    "end_state.png": ((0,) * 9, True, True, None),
    "fixture_rewards_tab.png": (None, False, None, None),
}


def fit(img, W, H):
    """等比缩放到能放进 WxH，居中，其余黑边（模拟不同比例窗口）。返回 (图, scale, ox, oy)。"""
    s = min(W / img.shape[1], H / img.shape[0])
    r = cv2.resize(img, (round(img.shape[1] * s), round(img.shape[0] * s)), interpolation=cv2.INTER_AREA)
    out = np.zeros((H, W, 3), np.uint8)
    ox, oy = (W - r.shape[1]) // 2, (H - r.shape[0]) // 2
    out[oy:oy + r.shape[0], ox:ox + r.shape[1]] = r
    return out, s, ox, oy


fails = 0
for W, H in SIZES:
    errs = []
    for f, (board, page, zero, sel) in CASES.items():
        img, s, ox, oy = fit(v.imread(os.path.join(CAP, f)), W, H)
        fr = v.find_window_frame(img)
        if not fr:
            errs.append(f"{f}:未找到窗口"); continue
        # 点击映射误差：开始按钮应落在 真值 位置
        ex, ey = v.MAIN_BUTTON[0] * s + ox, v.MAIN_BUTTON[1] * s + oy
        gx, gy = fr.to_img(*v.MAIN_BUTTON)
        if abs(gx - ex) > 4 or abs(gy - ey) > 4:
            errs.append(f"{f}:按钮偏差({gx-ex:.1f},{gy-ey:.1f})")
        b = fr.warp(img)
        if v.on_stardust_page(b) != page:
            errs.append(f"{f}:页面判断错")
        if page:
            got, sc = v.read_board(b)
            if got != board:
                errs.append(f"{f}:board {got}")
            if v.plays_left_is_zero(b) != zero:
                errs.append(f"{f}:0次判断错")
            if v.selected_line(b) != sel:
                errs.append(f"{f}:选中线 {v.selected_line(b)}")
    # 大厅
    for f, names in {"lobby_a.png": ["nav_changzhu.png", "nav_xingpan.png"],
                     "lobby_closed.png": ["nav_changzhu.png"]}.items():
        img, s, ox, oy = fit(v.imread(os.path.join(CAP, f)), W, H)
        for n in names:
            hit = v.find_multiscale(img, n)
            if not hit:
                errs.append(f"{f}:{n} 未找到"); continue
            bx, by = v.TEMPLATE_CENTER[n]
            if abs(hit[0] - (bx * s + ox)) > 4 or abs(hit[1] - (by * s + oy)) > 4:
                errs.append(f"{f}:{n} 位置偏差")
        if f == "lobby_closed.png" and v.find_multiscale(img, "nav_xingpan.png"):
            errs.append("lobby_closed: 误检到好运星盘")
    fails += bool(errs)
    print(f"{W}x{H}: " + ("OK" if not errs else "; ".join(errs)))
print("全部通过" if not fails else f"{fails} 个尺寸有问题")
