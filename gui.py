"""300英雄 自动脚本 —— 图形界面后端（Tornado JSON API + 静态页面），由 Electron 桌面壳加载显示。

python gui.py [--port 22300]
前端在 webui/（纯 HTML/CSS/JS，无外部依赖，离线可用）。
"""
import argparse
import asyncio
import collections
import json
import os
import re
import subprocess
import sys
import threading
import time

import tornado.ioloop
import tornado.web

ROOT = os.path.dirname(os.path.abspath(__file__))
STARDUST = os.path.join(ROOT, "stardust")
WEBUI = os.path.join(ROOT, "webui")
CONFIG = os.path.join(ROOT, "config.json")
HISTORY = os.path.join(ROOT, "history.json")
LOG_DIR = os.path.join(ROOT, "log")
RUNNING_FLAG = os.path.join(STARDUST, "running.flag")   # Electron 关闭时据此判断是否要等脚本停下
STOP_FLAG = os.path.join(STARDUST, "stop.flag")
PYTHON = sys.executable.replace("pythonw.exe", "python.exe")

sys.path.insert(0, STARDUST)
import game  # noqa: E402  (用于检测游戏窗口状态)

DEFAULT_CONFIG = {"games": 0, "close_after": True, "timeout": 5}   # games=0 表示全部


def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def save_json(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def _num(v, default, lo, hi, cast=float):
    try:
        return max(lo, min(hi, cast(v)))
    except (TypeError, ValueError):
        return default


def load_config():
    """读配置；旧版本/手改出错的值一律回退默认值，保证界面能打开。"""
    return normalize_config(load_json(CONFIG, {}))


def normalize_config(raw):
    if not isinstance(raw, dict):
        raw = {}
    return {
        "games": _num(raw.get("games"), 0, 0, 999, int),          # 0 = 全部
        "timeout": _num(raw.get("timeout"), 5, 1, 60, float),
        "close_after": bool(raw.get("close_after", True)),
        "rec_fps": _num(raw.get("rec_fps"), 8, 2, 20, int),
        "rec_keys": bool(raw.get("rec_keys", True)),
    }


LINE_RE = re.compile(r"^\[(\d\d:\d\d:\d\d)\]\s*(.*)$")


class Runner:
    """全局唯一的脚本进程管理。"""

    def __init__(self):
        self.proc = None
        self.lines = collections.deque(maxlen=2000)
        self.seq = 0
        self.lock = threading.Lock()
        self.reset_state()
        self.status = "idle"          # idle / running / stopping / done / stopped / error

    def reset_state(self):
        self.step = None
        self.steps_done = []
        self.board = [0] * 9
        self.action = None            # {"action": "reveal"/"line", "target":..., "ev":...}
        self.result = None
        self.games = 0
        self.dust = 0
        self.results = []
        self.reason = None
        self.started_at = None
        self.ended_at = None

    @property
    def running(self):
        return self.proc is not None and self.proc.poll() is None

    # ---- 日志 ----
    def _append(self, text, level="info", t=None):
        with self.lock:
            self.seq += 1
            self.lines.append({"seq": self.seq, "time": t or time.strftime("%H:%M:%S"),
                               "text": text, "level": level})

    def _on_line(self, line):
        if line.startswith("@@"):
            try:
                self._on_event(json.loads(line[2:]))
            except Exception:
                pass
            return
        m = LINE_RE.match(line)
        t, text = (m.group(1), m.group(2)) if m else (None, line)
        level = "info"
        if text.startswith("停止") or text.startswith("出错") or "Traceback" in text:
            level = "error"
        elif "无响应" in text or "移动到屏幕内" in text or "等待中" in text:
            level = "warn"
        elif "获得星砂" in text and "结果" in text:
            level = "success"
        self._append(text.strip(), level, t)

    def _on_event(self, ev):
        k = ev.get("kind")
        if k == "step":
            s = ev["step"]
            if self.step and self.step != s and self.step not in self.steps_done:
                self.steps_done.append(self.step)
            self.step = s
        elif k == "board":
            self.board = ev["board"]
            self.action = {"action": ev["action"], "target": ev["target"], "ev": ev["ev"]}
            self.result = None
        elif k == "result":
            self.board = ev["board"]
            self.result = ev
            self.action = None
            self.games += 1
            self.dust += ev["reward"]
            self.results.append(ev["reward"])
        elif k == "done":
            self.reason = ev.get("reason")
            # 正常结束时当前步骤算完成；出错时它是出错的那一步（前端标红 steps_done 的最后一项）
            if self.step and self.step not in self.steps_done:
                self.steps_done.append(self.step)
            self.step = "end"

    # ---- 控制 ----
    def start(self, cfg):
        if self.running:
            return False
        args = [PYTHON, "-s", "-u", os.path.join(STARDUST, "bot.py"), "--timeout", str(cfg["timeout"])]
        if cfg.get("nav_only"):                       # 只导航到星屑占卜页，不玩
            args += ["-n", "0", "--stay"]
        else:
            if cfg["games"]:
                args += ["-n", str(int(cfg["games"]))]
            if not cfg["close_after"]:
                args.append("--stay")
        for f in (STOP_FLAG,):
            try:
                os.remove(f)
            except FileNotFoundError:
                pass
        self.reset_state()
        self.started_at = time.time()
        self.status = "running"
        scope = "只打开星屑占卜页" if cfg.get("nav_only") else (f"{cfg['games']} 局" if cfg["games"] else "全部")
        self._append(f"开始执行：星屑占卜（局数：{scope}）", "start")
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        self.proc = subprocess.Popen(args, cwd=STARDUST, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                     env=env, creationflags=0x08000000)  # CREATE_NO_WINDOW
        open(RUNNING_FLAG, "w").close()
        threading.Thread(target=self._pump, args=(self.proc,), daemon=True).start()
        return True

    def _pump(self, proc):
        try:
            for raw in proc.stdout:
                line = raw.decode("utf-8", "replace").rstrip()
                if line:
                    self._on_line(line)
            proc.wait()
        finally:
            self.ended_at = time.time()
            if self.status == "stopping" or (self.reason and "用户" in self.reason):
                self.status = "stopped"
            elif self.reason or proc.returncode not in (0, None):
                self.status = "error"
            else:
                self.status = "done"
            dur = self.ended_at - (self.started_at or self.ended_at)
            msg = {"done": "脚本执行完成", "stopped": "已手动停止", "error": "脚本异常停止"}[self.status]
            self._append(f"{msg}，共 {self.games} 局，星砂 {self.dust}，耗时 {dur:.1f}s",
                         "end-" + self.status)
            self._record_history(dur)
            try:
                os.remove(RUNNING_FLAG)
            except FileNotFoundError:
                pass

    def _record_history(self, dur):
        h = load_json(HISTORY, [])
        h.append({"time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.started_at or time.time())),
                  "duration": round(dur, 1), "games": self.games, "dust": self.dust,
                  "results": self.results, "status": self.status, "reason": self.reason})
        save_json(HISTORY, h[-500:])

    def stop(self):
        if not self.running:
            return
        self.status = "stopping"
        open(STOP_FLAG, "w").close()
        for _ in range(50):
            if not self.running:
                return
            time.sleep(0.1)
        self._append("脚本未在 5 秒内退出，已强制结束", "warn")
        self.proc.kill()

    def snapshot(self):
        now = self.ended_at if not self.running and self.ended_at else time.time()
        return {
            "status": self.status, "running": self.running,
            "step": self.step, "steps_done": self.steps_done,
            "board": self.board, "action": self.action, "result": self.result,
            "games": self.games, "dust": self.dust, "results": self.results[-20:],
            "elapsed": round(now - self.started_at, 1) if self.started_at else 0,
            "started_at": self.started_at, "ended_at": self.ended_at,
            "reason": self.reason, "log_seq": self.seq,
        }

    def log_since(self, seq):
        with self.lock:
            return [l for l in self.lines if l["seq"] > seq]

    def clear_log(self):
        with self.lock:
            self.lines.clear()


RUNNER = Runner()


# ---------------- 录制 ----------------
RECORDER_DIR = os.path.join(ROOT, "recorder")
RECORDINGS = os.path.join(ROOT, "recordings")
REC_STOP = os.path.join(RECORDER_DIR, "stop.flag")
REC_RUNNING = os.path.join(RECORDER_DIR, "running.flag")


class RecRunner:
    """录制进程管理：启动/停止 recorder.py，收集它的日志和事件。"""

    def __init__(self):
        self.proc = None
        self.lines = collections.deque(maxlen=1000)
        self.seq = 0
        self.lock = threading.Lock()
        self.status = "idle"          # idle / recording / paused / stopping / done / error
        self.dir = None
        self.clicks = self.keys = 0
        self.started_at = self.ended_at = None
        self.reason = None
        self.result = None

    @property
    def running(self):
        return self.proc is not None and self.proc.poll() is None

    def _append(self, text, level="info", t=None):
        with self.lock:
            self.seq += 1
            self.lines.append({"seq": self.seq, "time": t or time.strftime("%H:%M:%S"), "text": text, "level": level})

    def start(self, cfg):
        if self.running:
            return False
        try:
            os.remove(REC_STOP)
        except FileNotFoundError:
            pass
        self.status, self.dir, self.clicks, self.keys = "recording", None, 0, 0
        self.reason = self.result = None
        self.started_at, self.ended_at = time.time(), None
        args = [PYTHON, "-s", "-u", os.path.join(RECORDER_DIR, "recorder.py"),
                "--fps", str(cfg["rec_fps"]), "--out", RECORDINGS]
        if not cfg["rec_keys"]:
            args.append("--no-keys")
        if os.environ.get("RECORDER_TEST_EXE"):          # 仅开发测试：录制其他程序的窗口
            args += ["--exe", os.environ["RECORDER_TEST_EXE"]]
        self._append("开始录制", "start")
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        self.proc = subprocess.Popen(args, cwd=RECORDER_DIR, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                     env=env, creationflags=0x08000000)
        open(REC_RUNNING, "w").close()
        threading.Thread(target=self._pump, args=(self.proc,), daemon=True).start()
        return True

    def _pump(self, proc):
        try:
            for raw in proc.stdout:
                line = raw.decode("utf-8", "replace").rstrip()
                if not line:
                    continue
                if line.startswith("@@"):
                    try:
                        self._on_event(json.loads(line[2:]))
                    except Exception:
                        pass
                    continue
                m = LINE_RE.match(line)
                t, text = (m.group(1), m.group(2)) if m else (None, line)
                level = "error" if text.startswith("停止") or "Traceback" in text else \
                        "warn" if text.startswith("注意") or "暂停" in text else "info"
                self._append(text, level, t)
            proc.wait()
        finally:
            self.ended_at = time.time()
            if self.result and self.result.get("dir"):
                self.status = "done"
                r = self.result
                self._append(f"录制已保存：{r['duration']:.0f} 秒，{r['clicks']} 次点击，{r['keys']} 次按键，"
                             f"{r['size'] / 1e6:.1f} MB", "end-done")
            else:
                self.status = "error"
                self._append(f"录制失败：{self.reason or '进程异常退出'}", "end-error")
            for f in (REC_RUNNING, REC_STOP):
                try:
                    os.remove(f)
                except FileNotFoundError:
                    pass

    def _on_event(self, ev):
        k = ev.get("kind")
        if k == "rec_start":
            self.dir = ev["dir"]
        elif k == "rec_event":
            self.clicks, self.keys = ev["clicks"], ev["keys"]
        elif k == "rec_state":
            self.status = "paused" if ev["state"] == "paused" else "recording"
        elif k == "rec_done":
            self.result = ev
            self.reason = ev.get("reason")

    def stop(self):
        if not self.running:
            return
        self.status = "stopping"
        open(REC_STOP, "w").close()
        for _ in range(100):          # 录制收尾要写完视频，最多等 10 秒
            if not self.running:
                return
            time.sleep(0.1)
        self._append("录制进程未在 10 秒内退出，已强制结束（视频可能不完整）", "warn")
        self.proc.kill()

    def snapshot(self):
        now = self.ended_at if not self.running and self.ended_at else time.time()
        return {"status": self.status, "running": self.running, "dir": self.dir,
                "name": os.path.basename(self.dir) if self.dir else None,
                "clicks": self.clicks, "keys": self.keys, "reason": self.reason,
                "elapsed": round(now - self.started_at, 1) if self.started_at else 0,
                "started_at": self.started_at, "ended_at": self.ended_at, "log_seq": self.seq}

    def log_since(self, seq):
        with self.lock:
            return [l for l in self.lines if l["seq"] > seq]


REC = RecRunner()


def list_recordings():
    out = []
    if not os.path.isdir(RECORDINGS):
        return out
    for name in sorted(os.listdir(RECORDINGS), reverse=True):
        d = os.path.join(RECORDINGS, name)
        if not os.path.isdir(d):
            continue
        meta = load_json(os.path.join(d, "meta.json"), None)
        size = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(d) for f in fs)
        live = REC.running and REC.dir and os.path.normcase(REC.dir) == os.path.normcase(d)
        out.append({"name": name, "size": size, "live": bool(live),
                    "start": meta.get("start") if meta else None,
                    "duration": meta.get("duration_s") if meta else None,
                    "clicks": meta.get("clicks") if meta else None,
                    "keys": meta.get("keys") if meta else None,
                    "complete": bool(meta)})
    return out


def recording_path(name):
    """只允许 recordings/ 下的一级目录名，防止路径穿越。"""
    if not name or os.path.basename(name) != name or name in (".", ".."):
        return None
    p = os.path.join(RECORDINGS, name)
    return p if os.path.isdir(p) else None


def game_status():
    try:
        h = game.find_game_hwnd()
    except Exception:
        return {"found": False}
    if game.user32.IsIconic(h):
        return {"found": True, "minimized": True}
    x, y, w, hh = game.client_rect(h)
    return {"found": True, "minimized": False, "width": w, "height": hh}


# ---------------- HTTP ----------------
class Api(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.set_header("Cache-Control", "no-store")

    def body(self):
        try:
            return json.loads(self.request.body or b"{}")
        except Exception:
            return {}

    def ok(self, data=None):
        self.write(json.dumps(data if data is not None else {"ok": True}, ensure_ascii=False))


class StateH(Api):
    def get(self):
        self.ok(RUNNER.snapshot())


class LogH(Api):
    def get(self):
        self.ok(RUNNER.log_since(int(self.get_argument("since", "0"))))

    def delete(self):
        RUNNER.clear_log()
        self.ok()


class StartH(Api):
    def post(self):
        body = self.body()
        once = bool(body.pop("once", False))          # 一次性运行方式（只跑 1 局 / 只打开页面）不保存为配置
        nav_only = bool(body.pop("nav_only", False))
        merged = {**load_config(), **body}
        if not once:
            save_json(CONFIG, merged)
        cfg = normalize_config(merged)
        cfg["nav_only"] = nav_only
        self.ok({"ok": RUNNER.start(cfg)})


class StopH(Api):
    async def post(self):
        await asyncio.get_running_loop().run_in_executor(None, RUNNER.stop)
        self.ok()


class ConfigH(Api):
    def get(self):
        self.ok(load_config())

    def post(self):
        save_json(CONFIG, {**load_config(), **self.body()})
        self.ok(load_config())


class HistoryH(Api):
    def get(self):
        self.ok(load_json(HISTORY, []))

    def delete(self):
        save_json(HISTORY, [])
        self.ok()


class GameH(Api):
    def get(self):
        self.ok(game_status())


class RecStateH(Api):
    def get(self):
        self.ok(REC.snapshot())


class RecLogH(Api):
    def get(self):
        self.ok(REC.log_since(int(self.get_argument("since", "0"))))


class RecStartH(Api):
    def post(self):
        cfg = {**load_config(), **self.body()}
        save_json(CONFIG, cfg)
        self.ok({"ok": REC.start(load_config())})


class RecStopH(Api):
    async def post(self):
        await asyncio.get_running_loop().run_in_executor(None, REC.stop)
        self.ok()


class RecListH(Api):
    def get(self):
        self.ok(list_recordings())

    def delete(self):
        p = recording_path(self.get_argument("name", ""))
        if not p:
            return self.ok({"ok": False, "msg": "录像不存在"})
        if REC.running and REC.dir and os.path.normcase(REC.dir) == os.path.normcase(p):
            return self.ok({"ok": False, "msg": "正在录制，不能删除"})
        import shutil
        shutil.rmtree(p, ignore_errors=True)
        self.ok()


class OpenH(Api):
    def post(self):
        body = self.body()
        what = body.get("what")
        if what in ("rec", "rec_steps"):
            p = recording_path(body.get("name", ""))
            if p and what == "rec_steps" and os.path.exists(os.path.join(p, "steps.md")):
                p = os.path.join(p, "steps.md")
            if p:
                os.startfile(p)
                return self.ok()
            return self.ok({"ok": False, "msg": "录像不存在"})
        if what == "recordings":
            os.makedirs(RECORDINGS, exist_ok=True)
        path = {"log": os.path.join(STARDUST, "stardust_log.txt"),
                "captures": os.path.join(STARDUST, "captures"),
                "recordings": RECORDINGS,
                "folder": ROOT}.get(what)
        if path and os.path.exists(path):
            os.startfile(path)
            self.ok()
        else:
            self.ok({"ok": False, "msg": "文件不存在（还没有运行过？）"})


class NoCacheStatic(tornado.web.StaticFileHandler):
    def set_extra_headers(self, path):
        self.set_header("Cache-Control", "no-store")


def make_app():
    return tornado.web.Application([
        (r"/api/state", StateH), (r"/api/log", LogH), (r"/api/start", StartH),
        (r"/api/stop", StopH), (r"/api/config", ConfigH), (r"/api/history", HistoryH),
        (r"/api/game", GameH), (r"/api/open", OpenH),
        (r"/api/rec/state", RecStateH), (r"/api/rec/log", RecLogH), (r"/api/rec/start", RecStartH),
        (r"/api/rec/stop", RecStopH), (r"/api/rec/list", RecListH),
        (r"/(.*)", NoCacheStatic, {"path": WEBUI, "default_filename": "index.html"}),
    ])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=22300)
    ap.add_argument("--host", default="127.0.0.1")
    a = ap.parse_args()
    for stale in (RUNNING_FLAG, STOP_FLAG, REC_RUNNING, REC_STOP):
        try:
            os.remove(stale)
        except FileNotFoundError:
            pass
    os.makedirs(LOG_DIR, exist_ok=True)
    make_app().listen(a.port, a.host)
    print(f"Running on http://{a.host}:{a.port}/", flush=True)
    tornado.ioloop.IOLoop.current().start()
