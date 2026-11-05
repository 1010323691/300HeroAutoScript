"""游戏操作录制：录游戏窗口视频，同时记录鼠标点击/按键，并为每次点击保存前后截图。

产物（recordings/<时间>/）:
    video.mp4      游戏窗口客户区视频（点击处画标记），给人回看
    events.jsonl   每个事件一行：点击（窗口内比例坐标 + 像素坐标）、按键、暂停/恢复、遮挡
    frames/        每次点击的前后截图：0001_before.jpg（标出点击位置）/ 0001_after.jpg
    steps.md       给 agent 读的操作步骤清单（时间、动作、坐标、对应截图）
    meta.json      录制参数和统计

用法:
    python recorder.py [--fps 8] [--width 1280] [--no-keys] [--out DIR]
停止：在界面点停止（创建 stop 标志文件），或按 F10。
"""
import argparse
import collections
import ctypes
import ctypes.wintypes as wt
import datetime
import json
import os
import queue
import sys
import threading
import time

import cv2
import mss
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "stardust"))
import game  # noqa: E402  （找窗口 / 客户区坐标 / 遮挡检测，与脚本共用）

STOP_FLAG = os.path.join(HERE, "stop.flag")
DEFAULT_OUT = os.path.join(ROOT, "recordings")
VK_F10 = 0x79
AFTER_DELAY = 0.8          # 点击后多久截 “after” 图
MARK_SECONDS = 0.6         # 视频里点击标记保留多久

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32


def emit(kind, **data):
    """给图形界面的结构化事件。"""
    print("@@" + json.dumps({"kind": kind, **data}, ensure_ascii=False), flush=True)


def log(msg):
    print(f"[{datetime.datetime.now():%H:%M:%S}] {msg}", flush=True)


def imwrite(path, img, quality=88):
    ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, quality])
    if ok:
        buf.tofile(path)          # 支持中文路径


# ---------------- 低级鼠标/键盘钩子 ----------------
WH_KEYBOARD_LL, WH_MOUSE_LL = 13, 14
WM_KEYDOWN, WM_SYSKEYDOWN = 0x0100, 0x0104
MOUSE_MSGS = {0x0201: "left", 0x0204: "right", 0x0207: "middle"}   # *BUTTONDOWN
WM_MOUSEWHEEL = 0x020A
LLMHF_INJECTED = 0x01      # 鼠标事件由程序注入（例如自动脚本在点击）
LLKHF_INJECTED = 0x10


class MSLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [("pt", wt.POINT), ("mouseData", wt.DWORD), ("flags", wt.DWORD),
                ("time", wt.DWORD), ("dwExtraInfo", ctypes.c_size_t)]


class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [("vkCode", wt.DWORD), ("scanCode", wt.DWORD), ("flags", wt.DWORD),
                ("time", wt.DWORD), ("dwExtraInfo", ctypes.c_size_t)]


HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_ssize_t, ctypes.c_int, wt.WPARAM, wt.LPARAM)
user32.SetWindowsHookExW.restype = wt.HHOOK
user32.SetWindowsHookExW.argtypes = [ctypes.c_int, HOOKPROC, wt.HINSTANCE, wt.DWORD]
user32.CallNextHookEx.restype = ctypes.c_ssize_t
user32.CallNextHookEx.argtypes = [wt.HHOOK, ctypes.c_int, wt.WPARAM, wt.LPARAM]
user32.GetKeyNameTextW.argtypes = [wt.LONG, wt.LPWSTR, ctypes.c_int]

SPECIAL_KEYS = {0x08: "Backspace", 0x09: "Tab", 0x0D: "Enter", 0x1B: "Esc", 0x20: "Space",
                0x25: "Left", 0x26: "Up", 0x27: "Right", 0x28: "Down", 0x2E: "Delete",
                0x10: "Shift", 0x11: "Ctrl", 0x12: "Alt", 0xA0: "Shift", 0xA1: "Shift",
                0xA2: "Ctrl", 0xA3: "Ctrl", 0xA4: "Alt", 0xA5: "Alt", 0x5B: "Win"}


def key_name(vk, scan):
    if vk in SPECIAL_KEYS:
        return SPECIAL_KEYS[vk]
    if 0x70 <= vk <= 0x87:
        return f"F{vk - 0x6F}"
    if 0x30 <= vk <= 0x39 or 0x41 <= vk <= 0x5A:
        return chr(vk)
    buf = ctypes.create_unicode_buffer(32)
    if user32.GetKeyNameTextW(scan << 16, buf, 32):
        return buf.value
    return f"VK_{vk:02X}"


class InputHooks:
    """在独立线程里装钩子并跑消息循环；事件放进队列，由主循环处理（钩子回调必须很快返回）。"""

    def __init__(self, keys=True):
        self.q = queue.Queue()
        self.keys = keys
        self.thread_id = None
        self._mouse_cb = HOOKPROC(self._on_mouse)
        self._kb_cb = HOOKPROC(self._on_kb)
        self.f10 = threading.Event()

    def _on_mouse(self, n, wparam, lparam):
        if n >= 0:
            btn = MOUSE_MSGS.get(wparam)
            if btn or wparam == WM_MOUSEWHEEL:
                m = ctypes.cast(lparam, ctypes.POINTER(MSLLHOOKSTRUCT)).contents
                ev = {"type": "click" if btn else "wheel", "button": btn,
                      "x": m.pt.x, "y": m.pt.y, "injected": bool(m.flags & LLMHF_INJECTED),
                      "t": time.time()}
                if not btn:
                    ev["delta"] = ctypes.c_short(m.mouseData >> 16).value
                self.q.put(ev)
        return user32.CallNextHookEx(None, n, wparam, lparam)

    def _on_kb(self, n, wparam, lparam):
        if n >= 0 and wparam in (WM_KEYDOWN, WM_SYSKEYDOWN):
            k = ctypes.cast(lparam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
            if k.vkCode == VK_F10:
                self.f10.set()
            elif self.keys:
                self.q.put({"type": "key", "key": key_name(k.vkCode, k.scanCode),
                            "injected": bool(k.flags & LLKHF_INJECTED), "t": time.time()})
        return user32.CallNextHookEx(None, n, wparam, lparam)

    def _run(self):
        self.thread_id = kernel32.GetCurrentThreadId()
        hm = user32.SetWindowsHookExW(WH_MOUSE_LL, self._mouse_cb, None, 0)
        hk = user32.SetWindowsHookExW(WH_KEYBOARD_LL, self._kb_cb, None, 0)
        msg = wt.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
        if hm:
            user32.UnhookWindowsHookEx(hm)
        if hk:
            user32.UnhookWindowsHookEx(hk)

    def start(self):
        threading.Thread(target=self._run, daemon=True).start()
        for _ in range(50):
            if self.thread_id:
                break
            time.sleep(0.02)

    def stop(self):
        if self.thread_id:
            user32.PostThreadMessageW(self.thread_id, 0x0012, 0, 0)   # WM_QUIT


# ---------------- 录制 ----------------
class Recorder:
    def __init__(self, out_root, fps=8, width=1280, keys=True):
        self.fps, self.width, self.keys = fps, width, keys
        self.hwnd = game.find_game_hwnd()
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.dir = os.path.join(out_root, stamp)
        self.frames_dir = os.path.join(self.dir, "frames")
        os.makedirs(self.frames_dir, exist_ok=True)
        x, y, w, h = game.client_rect(self.hwnd)
        self.src_size = (w, h)
        self.out_w = min(width, w) // 2 * 2
        self.out_h = int(round(h * self.out_w / w)) // 2 * 2
        self.writer = cv2.VideoWriter(os.path.join(self.dir, "video.mp4"),
                                      cv2.VideoWriter_fourcc(*"mp4v"), fps, (self.out_w, self.out_h))
        if not self.writer.isOpened():
            raise RuntimeError("无法创建视频文件")
        self.events = open(os.path.join(self.dir, "events.jsonl"), "w", encoding="utf-8")
        self.hooks = InputHooks(keys)
        self.t0 = None
        self.n_frames = 0
        self.n_clicks = 0
        self.n_keys = 0
        self.paused_s = 0.0
        self.steps = []             # 写 steps.md 用
        self.pending_after = []     # [(due_time, step_index)]
        self.marks = []             # [(until_time, x_out, y_out)] 视频里的点击标记
        self.ring = collections.deque(maxlen=max(4, fps * 2))   # 最近 2 秒原始帧 (时间, 图)
        self.last_rect = None
        self.state = "recording"    # recording / paused
        self._occluded_logged = False

    # ---- 工具 ----
    def rel_t(self, t=None):
        return round((t or time.time()) - self.t0, 3)

    def write_event(self, ev):
        self.events.write(json.dumps(ev, ensure_ascii=False) + "\n")
        self.events.flush()

    def grab(self, sct):
        """截游戏客户区（原分辨率 BGR）。窗口最小化/尺寸为 0 返回 None。"""
        if user32.IsIconic(self.hwnd):
            return None
        x, y, w, h = game.client_rect(self.hwnd)
        if w <= 0 or h <= 0:
            return None
        self.last_rect = (x, y, w, h)
        img = np.array(sct.grab({"left": x, "top": y, "width": w, "height": h}))[:, :, :3]
        return np.ascontiguousarray(img)

    def to_out(self, img):
        if img.shape[1] != self.out_w or img.shape[0] != self.out_h:
            img = cv2.resize(img, (self.out_w, self.out_h), interpolation=cv2.INTER_AREA)
        return img

    @staticmethod
    def draw_click(img, x, y, color=(60, 60, 255), r=None):
        r = r or max(10, img.shape[1] // 60)
        cv2.circle(img, (int(x), int(y)), r, color, 3, cv2.LINE_AA)
        cv2.circle(img, (int(x), int(y)), 3, color, -1, cv2.LINE_AA)
        return img

    # ---- 事件处理 ----
    def handle_input(self, ev, sct):
        t = self.rel_t(ev["t"])
        fg = user32.GetForegroundWindow()
        rect = self.last_rect or game.client_rect(self.hwnd)
        x, y, w, h = rect
        if ev["type"] in ("click", "wheel"):
            inside = x <= ev["x"] < x + w and y <= ev["y"] < y + h
            on_game = inside and game.owner_exe_at(ev["x"], ev["y"]) in game.GAME_PROCS
            if not on_game:
                return                       # 只记录点在游戏里的操作
            px, py = ev["x"] - x, ev["y"] - y
            rec = {"t": t, "type": ev["type"], "x_rel": round(px / w, 4), "y_rel": round(py / h, 4),
                   "x": px, "y": py, "window": [w, h], "injected": ev["injected"]}
            if ev["type"] == "wheel":
                rec["delta"] = ev["delta"]
                self.write_event(rec)
                return
            rec["button"] = ev["button"]
            self.n_clicks += 1
            idx = self.n_clicks
            rec["step"] = idx
            # “before” 图：取点击时刻之前最后一帧（不能现截：窗口可能已经响应了这次点击）
            before = self.frame_before(ev["t"])
            if before is None:
                before = self.grab(sct)
            if before is not None:
                img = before.copy()
                self.draw_click(img, px, py, r=max(14, w // 50))
                imwrite(os.path.join(self.frames_dir, f"{idx:04d}_before.jpg"), self._shrink(img))
                rec["before"] = f"frames/{idx:04d}_before.jpg"
            self.pending_after.append((time.time() + AFTER_DELAY, idx))
            sx, sy = px * self.out_w / w, py * self.out_h / h
            self.marks.append((time.time() + MARK_SECONDS, sx, sy))
            self.steps.append(rec)
            self.write_event(rec)
            emit("rec_event", clicks=self.n_clicks, keys=self.n_keys)
            who = "（脚本）" if ev["injected"] else ""
            log(f"点击{who} #{idx} {ev['button']} @ ({rec['x_rel']:.3f}, {rec['y_rel']:.3f})")
        elif ev["type"] == "key":
            if fg != self.hwnd:
                return                       # 只记录游戏在前台时的按键
            rec = {"t": t, "type": "key", "key": ev["key"], "injected": ev["injected"]}
            self.n_keys += 1
            self.steps.append(rec)
            self.write_event(rec)
            emit("rec_event", clicks=self.n_clicks, keys=self.n_keys)

    def handle_after(self, sct):
        now = time.time()
        due = [p for p in self.pending_after if p[0] <= now]
        self.pending_after = [p for p in self.pending_after if p[0] > now]
        for _, idx in due:
            img = self.grab(sct)
            if img is None:
                continue
            name = f"frames/{idx:04d}_after.jpg"
            imwrite(os.path.join(self.dir, name), self._shrink(img))
            for s in self.steps:
                if s.get("step") == idx:
                    s["after"] = name
            self.write_event({"t": self.rel_t(), "type": "after", "step": idx, "after": name})

    def frame_before(self, t):
        """环形缓冲里时间戳早于 t 的最后一帧。"""
        for ft, img in reversed(self.ring):
            if ft < t:
                return img
        return None

    def _shrink(self, img):
        """截图存成与视频同宽，体积小、agent 读起来也够清楚。"""
        return self.to_out(img)

    # ---- 主循环 ----
    def run(self):
        try:
            os.remove(STOP_FLAG)
        except FileNotFoundError:
            pass
        self.hooks.start()
        self.t0 = time.time()
        meta_start = datetime.datetime.now().isoformat(timespec="seconds")
        log(f"开始录制：{self.dir}")
        log(f"游戏窗口 {self.src_size[0]}×{self.src_size[1]} → 视频 {self.out_w}×{self.out_h} @ {self.fps}fps")
        emit("rec_start", dir=self.dir, width=self.out_w, height=self.out_h, fps=self.fps)
        self.write_event({"t": 0, "type": "start", "window": list(self.src_size)})
        interval = 1.0 / self.fps
        next_t = time.time()
        reason = None
        with game.new_mss() as sct:
            try:
                while True:
                    if os.path.exists(STOP_FLAG):
                        reason = "用户点击了停止"
                        break
                    if self.hooks.f10.is_set():
                        reason = "按下 F10"
                        break
                    if not user32.IsWindow(self.hwnd):
                        reason = "游戏窗口已关闭"
                        break
                    while not self.hooks.q.empty():
                        self.handle_input(self.hooks.q.get_nowait(), sct)
                    self.handle_after(sct)

                    now = time.time()
                    if now < next_t:
                        time.sleep(min(0.01, next_t - now))
                        continue
                    next_t += interval
                    if now - next_t > 1.0:            # 掉帧太多就重新对齐
                        next_t = now + interval

                    img = self.grab(sct)
                    if img is None:
                        if self.state != "paused":
                            self.state = "paused"
                            self.pause_t = now
                            self.write_event({"t": self.rel_t(), "type": "pause", "reason": "游戏最小化"})
                            log("游戏窗口最小化，暂停录制")
                            emit("rec_state", state="paused")
                        continue
                    if self.state == "paused":
                        self.state = "recording"
                        self.paused_s += now - self.pause_t
                        self.write_event({"t": self.rel_t(), "type": "resume"})
                        log("游戏窗口已还原，继续录制")
                        emit("rec_state", state="recording")
                    self.check_occlusion()
                    self.ring.append((time.time(), img))
                    out = self.to_out(img).copy()
                    self.marks = [m for m in self.marks if m[0] > now]
                    for _, sx, sy in self.marks:
                        self.draw_click(out, sx, sy)
                    self.writer.write(out)
                    self.n_frames += 1
            except KeyboardInterrupt:
                reason = "中断"
            finally:
                # 收尾：把还没截的 after 图补上
                self.pending_after = [(0, i) for _, i in self.pending_after]
                self.handle_after(sct)
        self.hooks.stop()
        self.writer.release()
        dur = self.rel_t()
        self.write_event({"t": dur, "type": "stop", "reason": reason})
        self.events.close()
        meta = {"start": meta_start, "duration_s": dur, "paused_s": round(self.paused_s, 1),
                "fps": self.fps, "frames": self.n_frames, "video_size": [self.out_w, self.out_h],
                "game_window": list(self.src_size), "clicks": self.n_clicks, "keys": self.n_keys,
                "stop_reason": reason}
        with open(os.path.join(self.dir, "meta.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        self.write_steps(meta)
        size = sum(os.path.getsize(os.path.join(dp, fn)) for dp, _, fs in os.walk(self.dir) for fn in fs)
        log(f"录制结束（{reason}）：{dur:.1f}s，{self.n_frames} 帧，{self.n_clicks} 次点击，{self.n_keys} 次按键，"
            f"{size / 1e6:.1f} MB")
        emit("rec_done", dir=self.dir, duration=dur, clicks=self.n_clicks, keys=self.n_keys,
             frames=self.n_frames, size=size, reason=reason)

    def check_occlusion(self):
        """被其他窗口挡住时，视频里录到的是挡在前面的窗口：记一条事件提醒（每次被挡只记一次）。"""
        if self.n_frames % self.fps:          # 每秒检查一次
            return
        b = game.blockers(self.hwnd, grid=3)
        if b and not self._occluded_logged:
            self._occluded_logged = True
            self.write_event({"t": self.rel_t(), "type": "occluded", "by": sorted(b)})
            log(f"注意：游戏窗口被 {', '.join(sorted(b))} 挡住，这段画面可能不完整")
        elif not b:
            self._occluded_logged = False

    def write_steps(self, meta):
        """给 agent 读的步骤清单。"""
        L = ["# 操作录制", "",
             f"- 开始时间：{meta['start']}",
             f"- 时长：{meta['duration_s']:.1f} 秒（暂停 {meta['paused_s']} 秒）",
             f"- 游戏窗口：{meta['game_window'][0]}×{meta['game_window'][1]}；截图/视频：{meta['video_size'][0]}×{meta['video_size'][1]}",
             f"- 点击 {meta['clicks']} 次，按键 {meta['keys']} 次", "",
             "坐标说明：`x_rel, y_rel` 是点击位置在游戏窗口客户区内的比例（0~1，左上角为原点），与分辨率无关。",
             "每次点击有两张图：`before`（点击瞬间，红圈为点击位置）和 `after`（点击约 0.8 秒后）。",
             "标注“脚本”的是自动脚本注入的点击，不是人手操作。", "",
             "| # | 时间(s) | 动作 | 位置 (x_rel, y_rel) | 点击前 | 点击后 |",
             "|---|---|---|---|---|---|"]
        keybuf = []

        def flush_keys():
            if keybuf:
                L.append(f"|  | {keybuf[0]['t']:.1f} | 按键：{' '.join(k['key'] for k in keybuf)} |  |  |  |")
                keybuf.clear()
        for s in self.steps:
            if s["type"] == "key":
                keybuf.append(s)
                continue
            flush_keys()
            who = "（脚本）" if s.get("injected") else ""
            btn = {"left": "左键", "right": "右键", "middle": "中键"}.get(s.get("button"), s.get("button"))
            before = f"![]({s['before']})" if s.get("before") else ""
            after = f"![]({s['after']})" if s.get("after") else ""
            L.append(f"| {s['step']} | {s['t']:.1f} | {btn}点击{who} | ({s['x_rel']:.3f}, {s['y_rel']:.3f}) | {before} | {after} |")
        flush_keys()
        with open(os.path.join(self.dir, "steps.md"), "w", encoding="utf-8") as f:
            f.write("\n".join(L) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fps", type=int, default=8)
    ap.add_argument("--width", type=int, default=1280)
    ap.add_argument("--no-keys", action="store_true", help="不记录按键")
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--exe", help=argparse.SUPPRESS)   # 仅测试用：录制其他程序的窗口
    a = ap.parse_args()
    if a.exe:
        game.GAME_EXE = a.exe.lower()
        game.GAME_PROCS = set(game.GAME_PROCS) | {a.exe.lower()}
    try:
        rec = Recorder(a.out, fps=max(1, min(30, a.fps)), width=a.width, keys=not a.no_keys)
    except Exception as e:
        log(f"停止: {e}")
        emit("rec_done", dir=None, duration=0, clicks=0, keys=0, frames=0, size=0, reason=str(e))
        return 1
    rec.run()
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    sys.exit(main())
