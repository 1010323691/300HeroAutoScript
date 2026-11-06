"""与 300英雄 窗口交互的底层工具：找窗口、截图客户区、点击（Win32 SendInput）。"""
import ctypes
import ctypes.wintypes as wt
import time

import mss
import numpy as np

user32 = ctypes.windll.user32
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)   # 使用物理像素坐标
except Exception:
    user32.SetProcessDPIAware()

GAME_EXE = "300.exe"


def _exe_name(pid):
    k32 = ctypes.windll.kernel32
    h = k32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
    if not h:
        return ""
    try:
        buf = ctypes.create_unicode_buffer(520)
        n = wt.DWORD(520)
        if k32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(n)):
            return buf.value.rsplit("\\", 1)[-1]
        return ""
    finally:
        k32.CloseHandle(h)


def find_game_hwnd():
    """找 300.exe 的可见主窗口。"""
    result = []

    @ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
    def cb(hwnd, _):
        pid = wt.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if (user32.IsWindowVisible(hwnd) and user32.GetWindowTextLengthW(hwnd) > 0
                and _exe_name(pid.value).lower() == GAME_EXE):
            result.append(hwnd)
        return True

    user32.EnumWindows(cb, 0)
    if not result:
        raise RuntimeError("没找到 300英雄 窗口，请先登录进大厅")
    return result[0]


_k32 = ctypes.WinDLL("kernel32", use_last_error=True)
_adv = ctypes.WinDLL("advapi32", use_last_error=True)
_k32.OpenProcess.restype = wt.HANDLE
_k32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
_k32.GetCurrentProcess.restype = wt.HANDLE
_k32.CloseHandle.argtypes = [wt.HANDLE]
_adv.OpenProcessToken.argtypes = [wt.HANDLE, wt.DWORD, ctypes.POINTER(wt.HANDLE)]
_adv.GetTokenInformation.argtypes = [wt.HANDLE, ctypes.c_int, ctypes.c_void_p, wt.DWORD, ctypes.POINTER(wt.DWORD)]


def _elevated(proc_handle):
    """令牌是否为提升权限（管理员）。无权读取对方令牌说明对方权限比我们高，按 True 处理。"""
    tok = wt.HANDLE()
    if not _adv.OpenProcessToken(proc_handle, 0x0008, ctypes.byref(tok)):   # TOKEN_QUERY
        return ctypes.get_last_error() == 5                                 # ERROR_ACCESS_DENIED
    try:
        v, n = wt.DWORD(), wt.DWORD()
        ok = _adv.GetTokenInformation(tok, 20, ctypes.byref(v), 4, ctypes.byref(n))   # TokenElevation
        return bool(ok and v.value)
    finally:
        _k32.CloseHandle(tok)


def input_blocked(hwnd):
    """游戏以管理员身份运行而本程序没有时，Windows（UIPI）会丢弃我们发给游戏的鼠标点击。"""
    pid = wt.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    h = _k32.OpenProcess(0x1000, False, pid.value)          # PROCESS_QUERY_LIMITED_INFORMATION
    if not h:
        return False
    try:
        return _elevated(h) and not _elevated(_k32.GetCurrentProcess())
    finally:
        _k32.CloseHandle(h)


ADMIN_HINT = ("游戏以管理员身份运行，Windows 会拦截本程序发给游戏的点击。"
              "请关闭本程序后右键 300HeroAuto.exe 选择“以管理员身份运行”，或以普通方式重新启动游戏")


def client_rect(hwnd):
    """客户区在屏幕上的 (left, top, width, height)，物理像素。"""
    r = wt.RECT()
    user32.GetClientRect(hwnd, ctypes.byref(r))
    pt = wt.POINT(0, 0)
    user32.ClientToScreen(hwnd, ctypes.byref(pt))
    return pt.x, pt.y, r.right, r.bottom


def focus(hwnd, tries=5):
    """把游戏窗口切到前台（只切前台，不会重启进程）。成功返回 True。
    Windows 会拒绝后台进程抢前台，所以先挂接到当前前台线程的输入队列；仍失败再用 Alt 键解锁。"""
    k32 = ctypes.windll.kernel32
    for i in range(tries):
        fg = user32.GetForegroundWindow()
        if fg == hwnd:
            return True
        if user32.IsIconic(hwnd):
            user32.ShowWindow(hwnd, 9)
        me = k32.GetCurrentThreadId()
        other = user32.GetWindowThreadProcessId(fg, None) if fg else 0
        attached = bool(other and other != me and user32.AttachThreadInput(me, other, True))
        try:
            if i >= 2:   # 前两次不行再用 Alt 解除前台锁
                user32.keybd_event(0x12, 0, 0, 0)
                user32.keybd_event(0x12, 0, 2, 0)
            user32.BringWindowToTop(hwnd)
            user32.SetForegroundWindow(hwnd)
        finally:
            if attached:
                user32.AttachThreadInput(me, other, False)
        time.sleep(0.25)
    return user32.GetForegroundWindow() == hwnd


# ---- 遮挡 / 置顶 / 屏幕内 ----
GAME_PROCS = {"300.exe", "web300r.exe"}   # 大厅 UI 和活动窗口由 web300r.exe 绘制的叠加窗口
user32.SetWindowPos.argtypes = [wt.HWND, wt.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_uint]
user32.WindowFromPoint.argtypes = [wt.POINT]
user32.WindowFromPoint.restype = wt.HWND
user32.GetAncestor.restype = wt.HWND
_SWP_KEEP = 0x0001 | 0x0002 | 0x0010   # NOSIZE | NOMOVE | NOACTIVATE


def set_topmost(hwnd, on):
    user32.SetWindowPos(hwnd, wt.HWND(-1 if on else -2), 0, 0, 0, 0, _SWP_KEEP)


def owner_exe_at(x, y):
    """屏幕坐标 (x,y) 处最上层窗口所属的 exe 名。"""
    w = user32.WindowFromPoint(wt.POINT(int(x), int(y)))
    if not w:
        return ""
    root = user32.GetAncestor(w, 2) or w
    pid = wt.DWORD()
    user32.GetWindowThreadProcessId(root, ctypes.byref(pid))
    return _exe_name(pid.value).lower()


def blockers(hwnd, grid=4):
    """在客户区均匀取点，返回挡住游戏的其他程序名集合（空=没被挡）。"""
    x, y, w, h = client_rect(hwnd)
    found = set()
    for i in range(grid):
        for j in range(grid):
            px = x + (i + 0.5) * w / grid
            py = y + (j + 0.5) * h / grid
            exe = owner_exe_at(px, py)
            if exe and exe not in GAME_PROCS:
                found.add(exe)
    return found


def ensure_on_screen(hwnd):
    """窗口超出所在显示器工作区时，只移动位置（不改大小）使其完整可见。返回是否移动。"""
    class MI(ctypes.Structure):
        _fields_ = [("cb", wt.DWORD), ("rc", wt.RECT), ("work", wt.RECT), ("f", wt.DWORD)]
    mi = MI()
    mi.cb = ctypes.sizeof(MI)
    user32.GetMonitorInfoW(user32.MonitorFromWindow(hwnd, 2), ctypes.byref(mi))
    wa = mi.work
    r = wt.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(r))
    w, h = r.right - r.left, r.bottom - r.top
    nx = min(max(r.left, wa.left), max(wa.left, wa.right - w))
    ny = min(max(r.top, wa.top), max(wa.top, wa.bottom - h))
    if (nx, ny) != (r.left, r.top):
        user32.SetWindowPos(hwnd, None, nx, ny, 0, 0, 0x0001 | 0x0004 | 0x0010)  # NOSIZE|NOZORDER|NOACTIVATE
        time.sleep(0.3)
        return True
    return False


def new_mss():
    """mss 新版把 mss.mss 改名为 mss.MSS，两种都兼容。"""
    return mss.MSS() if hasattr(mss, "MSS") else mss.mss()


def capture_client(hwnd=None):
    """返回 (BGR 图像, (left, top, w, h))。"""
    hwnd = hwnd or find_game_hwnd()
    x, y, w, h = client_rect(hwnd)
    with new_mss() as s:
        img = np.array(s.grab({"left": x, "top": y, "width": w, "height": h}))[:, :, :3]
    return np.ascontiguousarray(img), (x, y, w, h)


# ---- 鼠标 ----
MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP = 0x0002, 0x0004


def click_screen(x, y, hover=0.12, hold=0.07):
    """移动→悬停→按下→保持→抬起。悬停让按钮先进入 hover 状态，避免点击被吞。"""
    x, y = int(round(x)), int(round(y))
    user32.SetCursorPos(x - 3, y - 3)
    time.sleep(0.03)
    user32.SetCursorPos(x, y)
    time.sleep(hover)
    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(hold)
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)


def click_client(hwnd, x, y):
    """按客户区实际像素坐标点击。"""
    left, top, _, _ = client_rect(hwnd)
    click_screen(left + x, top + y)
