"""从大厅导航到 常驻活动 → 好运星盘 → 星屑占卜（任意窗口尺寸）。"""
import time

import vision


def lobby_find(img, name):
    """在大厅截图里多尺度找按钮，返回实际点击坐标或 None。"""
    hit = vision.find_multiscale(img, name, 0.8)
    if not hit:
        return None
    cx, cy, s, _ = hit
    bx, by = vision.TEMPLATE_CENTER[name]
    kx, ky = vision.LOBBY_CLICK[name]
    return cx + (kx - bx) * s, cy + (ky - by) * s


def goto_stardust(bot, log, timeout=60):
    """bot 需提供 state() / act() / click_img() / click_base() / wait()。"""
    end = time.time() + timeout
    warned = False
    unknown_since = None
    while time.time() < end:
        st = bot.state()
        if st.page:
            return True

        if st.frame:                                  # 好运星盘窗口已开，但在别的标签
            unknown_since = None
            log("切换到 星屑占卜 标签")
            bot.act(lambda: bot.click_base(*vision.TAB_STARDUST),
                    lambda s: s.page, "切换标签")
            continue

        pos = lobby_find(st.img, "nav_xingpan.png")
        if pos:                                       # 常驻活动面板已展开
            unknown_since = None
            log("点击 好运星盘")
            # 只点一次并耐心等窗口加载（网络慢时可能要好几秒）。不能盲目重点：
            # 窗口一旦打开，同一位置是窗口外的遮罩，再点会把刚打开的窗口关掉。
            bot.click_img(*pos)
            if not bot.wait_for(lambda s: s.frame is not None, max(10, 2 * bot.click_timeout())):
                log("    好运星盘窗口未出现，重新判断界面状态")
            continue

        pos = lobby_find(st.img, "nav_changzhu.png")
        if pos:                                       # 面板收起
            unknown_since = None
            log("点击 常驻活动")
            # 这是开关按钮：只点一次并耐心等展开；没展开就回到循环重新判断状态再决定
            bot.click_img(*pos)
            if not bot.wait_for(lambda s: lobby_find(s.img, "nav_xingpan.png") is not None,
                                max(6, bot.click_timeout())):
                log("    常驻活动面板未展开，重新判断界面状态")
            continue

        # 窗口打开/关闭动画中会短暂认不出，持续 3 秒以上才提示
        unknown_since = unknown_since or time.time()
        if not warned and time.time() - unknown_since > 3:
            log("未识别到大厅或好运星盘界面，等待中…（请回到大厅主界面）")
            warned = True
        bot.wait(0.5)                                  # 加载/过场中，稍后再看
        continue
    return False
