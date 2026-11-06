"""星屑占卜 自动脚本

前提：300英雄 已登录，停在大厅（或已在好运星盘/星屑占卜页，或一局玩到一半）。
窗口任意尺寸/比例均可（自动定位缩放），窗口不要被其他窗口遮挡。
用法：
    python bot.py              # 用完剩余次数，结束后回大厅
    python bot.py -n 2         # 只玩 2 局
    python bot.py -n 0 --stay  # 只导航到星屑占卜页
    python bot.py --dry-run    # 只识别并打印建议，不点击
随时按 F12 停止。
"""
import argparse
import ctypes
import datetime
import os
import sys
import time

import cv2

import game
import nav
import solver
import vision

VK_F12 = 0x7B
HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "stardust_log.txt")

# 等待/重试参数（网络卡时可调大）
CLICK_TIMEOUT = 5.0   # 每次点击后等待界面响应的最长时间
CLICK_RETRIES = 3     # 没响应时最多重点几次
POLL = 0.3


class Stop(Exception):
    pass


def log(msg):
    line = f"[{datetime.datetime.now():%H:%M:%S}] {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


STOP_FLAG = os.path.join(HERE, "stop.flag")   # GUI 点“停止”时创建


def emit(kind, **data):
    """给图形界面的结构化事件（一行 @@JSON），界面据此点亮流程节点、显示星盘。"""
    import json
    print("@@" + json.dumps({"kind": kind, **data}, ensure_ascii=False), flush=True)


def check_stop():
    if ctypes.windll.user32.GetAsyncKeyState(VK_F12) & 0x8000:
        raise Stop("用户按下 F12")
    if os.path.exists(STOP_FLAG):
        raise Stop("用户点击了停止")


def sleep(t):
    end = time.time() + t
    while time.time() < end:
        check_stop()
        time.sleep(0.05)


def fmt(b):
    return " ".join("".join(str(v) if v else "." for v in b[r * 3:r * 3 + 3]) for r in range(3))


class State:
    """一次截图的识别结果。"""

    def __init__(self, img, frame):
        self.img = img            # 实际截图
        self.frame = frame        # 好运星盘窗口映射（不在则 None）
        self.base = frame.warp(img) if frame else None
        self.page = bool(self.base is not None and vision.on_stardust_page(self.base))
        self._board = None

    def board(self):
        """(board, 是否可信)。翻牌动画中会不可信。"""
        if self._board is None:
            b, sc = vision.read_board(self.base)
            self._board = (b, all(sc[i] >= 0.85 for i in range(9) if b[i]))
        return self._board

    @property
    def revealed(self):
        return sum(1 for v in self.board()[0] if v)


class Bot:
    def __init__(self, dry_run=False):
        self.dry = dry_run
        self.hwnd = game.find_game_hwnd()
        if not dry_run and game.input_blocked(self.hwnd):
            raise RuntimeError(game.ADMIN_HINT)        # 否则每次点击都被系统丢弃，只会反复“无响应”
        self.frame = None

    # ---- 观察 ----
    def prepare_window(self):
        """运行开始：窗口移到屏幕内、置顶（结束时 release_window 恢复）。"""
        was_min = bool(game.user32.IsIconic(self.hwnd))
        self._ensure_focus()                       # 最小化时会先还原
        if was_min:
            log("游戏窗口已从最小化还原，等待画面刷新")
            sleep(2.0)
        if game.ensure_on_screen(self.hwnd):
            log("游戏窗口有部分在屏幕外，已移动到屏幕内（未改变大小）")
        game.set_topmost(self.hwnd, True)
        self._ensure_focus()

    def release_window(self):
        try:
            game.set_topmost(self.hwnd, False)
        except Exception:
            pass

    def _ensure_visible(self):
        """确保游戏没被其他窗口挡住：截图和点击都依赖这一点。"""
        self._ensure_focus()
        b = game.blockers(self.hwnd)
        if b:
            game.set_topmost(self.hwnd, True)
            self._ensure_focus()
            time.sleep(0.2)
            b = game.blockers(self.hwnd)
            if b:
                raise Stop(f"游戏窗口被其他程序挡住：{', '.join(sorted(b))}。请关闭或移开它后重试")

    def state(self):
        check_stop()
        # 截图前必须保证游戏没被挡住，否则截到的是挡在前面的窗口
        self._ensure_visible()
        img, _ = game.capture_client(self.hwnd)
        self.frame = vision.find_window_frame(img, self.frame)
        return State(img, self.frame)

    def stable_board(self, timeout=4.0):
        """读到可信的星盘（等翻牌动画结束）。"""
        end = time.time() + timeout
        while True:
            st = self.state()
            if not st.page:
                self.fail(st, "当前不在 星屑占卜 页面")
            b, ok = st.board()
            if ok or time.time() > end:
                if not ok:
                    self.fail(st, f"数字识别置信度低 board={b}")
                return st
            sleep(POLL)

    def wait_for(self, cond, timeout):
        end = time.time() + timeout
        while True:
            st = self.state()
            try:
                if cond(st):
                    return st
            except Exception:
                pass
            if time.time() > end:
                return None
            sleep(POLL)

    def wait(self, t):
        sleep(t)

    def click_timeout(self):
        return CLICK_TIMEOUT

    def fail(self, st, msg):
        p = os.path.join(HERE, "captures", "unexpected.png")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        vision.imwrite(p, st.img)
        raise Stop(f"{msg}（截图已存 {p}）")

    # ---- 操作 ----
    def _ensure_focus(self):
        if not game.focus(self.hwnd):
            raise Stop("无法把游戏窗口切到前台（可能被其他窗口/系统浮层挡住）")

    def click_img(self, x, y):
        """按实际截图坐标点击。"""
        check_stop()
        if self.dry:
            return
        self._ensure_visible()
        left, top, _, _ = game.client_rect(self.hwnd)
        exe = game.owner_exe_at(left + x, top + y)
        if exe not in game.GAME_PROCS:
            raise Stop(f"点击位置被 {exe or '未知窗口'} 挡住，已停止以免误点")
        game.click_client(self.hwnd, x, y)

    def click_base(self, x, y):
        """按基准坐标点击（自动换算到当前窗口尺寸）。"""
        if self.frame is None:
            raise Stop("未定位到好运星盘窗口，无法换算坐标")
        self.click_img(*self.frame.to_img(x, y))

    def act(self, do_click, done, what, timeout=None, retries=CLICK_RETRIES):
        """点击 → 等待 done(state) 成立；没反应就重新确认状态后再点。
        timeout 为相对 CLICK_TIMEOUT 的值（None=CLICK_TIMEOUT）。"""
        timeout = CLICK_TIMEOUT if timeout is None else max(timeout, CLICK_TIMEOUT)
        for attempt in range(1, retries + 1):
            do_click()
            if self.dry:
                return None
            st = self.wait_for(done, timeout)
            if st is not None:
                return st
            log(f"    {what}：{timeout:.0f}s 内无响应，重试 ({attempt}/{retries})")
        self.fail(self.state(), f"{what} 多次点击无响应")

    # ---- 游戏流程 ----
    def play_one(self):
        """玩一局。返回获得的星砂；没有次数时返回 None。"""
        st = self.stable_board()
        n = st.revealed

        if n in (0, 9):                                   # 空闲，开始新一局
            emit("step", step="check")
            if vision.plays_left_is_zero(st.base):
                log("剩余占卜次数为 0，结束")
                emit("plays_left", zero=True)
                return None
            if self.dry:
                log("[dry] 需要点击 开始占卜")
                return None
            emit("step", step="play")
            st = self.act(lambda: self.click_base(*vision.MAIN_BUTTON),
                          lambda s: s.page and s.board()[1] and s.revealed == 1,
                          "开始占卜")
            log(f"新一局，系统翻开: {fmt(st.board()[0])}")
        emit("step", step="play")

        while True:
            st = self.stable_board()
            b = st.board()[0]
            kind, target, ev = solver.decide(b)
            emit("board", board=list(b), action=kind, target=target, ev=round(ev, 1))

            if kind == "reveal":
                log(f"  翻格子 {target}（期望 {ev:.1f}）")
                if self.dry:
                    return None
                x, y = vision.CELL_X[target % 3], vision.CELL_Y[target // 3]
                self.act(lambda: self.click_base(x, y),
                         lambda s, t=target: s.page and s.board()[1] and s.board()[0][t] != 0,
                         f"翻格子 {target}")
                continue

            log(f"  4 格可见 {fmt(b)} → 选 {target}（期望 {ev:.1f}）")
            if self.dry:
                return None
            if vision.selected_line(st.base) != target:
                self.act(lambda: self.click_base(*vision.ARROWS[target]),
                         lambda s: s.page and vision.selected_line(s.base) == target,
                         f"选择 {target}")
            st = self.act(lambda: self.click_base(*vision.MAIN_BUTTON),
                          lambda s: s.page and s.board()[1] and s.revealed == 9,
                          "确认选择", timeout=6)
            b = st.board()[0]
            total = sum(b[i] for i in solver.LINES[target])
            reward = solver.PAYOUT[total]
            log(f"  结果 {fmt(b)}  线和={total}  获得星砂 {reward}")
            emit("result", board=list(b), line=target, cells=list(solver.LINES[target]),
                 total=total, reward=reward)
            sleep(1.0)
            return reward

    def close_window(self):
        st = self.state()
        if st.frame is None:
            return
        log("关闭好运星盘窗口，回到大厅")
        emit("step", step="back")
        self.act(lambda: self.click_base(*vision.CLOSE_X),
                 lambda s: s.frame is None, "关闭窗口")


def _set_timeout(t):
    global CLICK_TIMEOUT
    CLICK_TIMEOUT = max(1.0, float(t))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", type=int, default=999, help="最多玩几局")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--stay", action="store_true", help="结束后停留在星屑占卜页，不关窗口")
    ap.add_argument("--timeout", type=float, default=CLICK_TIMEOUT, help="每次点击等待响应的秒数")
    a = ap.parse_args()
    _set_timeout(a.timeout)
    try:
        os.remove(STOP_FLAG)
    except FileNotFoundError:
        pass

    games, total, reason = 0, 0, None
    emit("step", step="start")
    try:
        bot = Bot(a.dry_run)
    except RuntimeError as e:
        log(f"停止: {e}")
        emit("done", games=0, total=0, reason=str(e))
        return 1
    try:
        if not a.dry_run:
            bot.prepare_window()
            emit("step", step="nav")
            if not nav.goto_stardust(bot, log):
                bot.fail(bot.state(), "无法从当前界面导航到 星屑占卜，请先回到大厅")
        emit("step", step="page")
        log(f"窗口定位: {bot.frame}")
        while games < a.n:
            r = bot.play_one()
            if r is None:
                break
            games += 1
            total += r
        if not a.dry_run and not a.stay:
            bot.close_window()
    except Stop as e:
        log(f"停止: {e}")
        reason = str(e)
    except Exception as e:                       # 意外错误也要恢复窗口并告知界面
        log(f"出错: {e!r}")
        reason = f"内部错误: {e!r}"
    finally:
        bot.release_window()
    log(f"共 {games} 局，获得星砂 {total}" + (f"，平均 {total/games:.1f}" if games else ""))
    emit("done", games=games, total=total, reason=reason)
    return 0 if reason is None else 1


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    sys.exit(main())
