"""打包脚本：生成免环境的一键包 dist/300HeroAutoScript.zip

产物结构（与 AzurLaneAutoScript 一键包相同的思路）:
    300HeroAutoScript/
        300HeroAuto.exe      启动器（双击）→ 启动 toolkit/WebApp 里的 Electron 桌面壳
        gui.py               pywebio 界面，Electron 内显示
        stardust/            脚本本体
        toolkit/python/      内嵌 Python + 依赖
        toolkit/WebApp/      Electron 运行时 + resources/app (main.js)

用法（在开发机上，用任意 Python 3 运行，需要联网）:
    python build.py            # 全量构建
    python build.py --step toolkit|webapp|launcher|package
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import urllib.request
import zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(ROOT, "build")
CACHE = os.path.join(BUILD, "cache")
TOOLKIT = os.path.join(ROOT, "toolkit")
PY_DIR = os.path.join(TOOLKIT, "python")
WEBAPP_DIR = os.path.join(TOOLKIT, "WebApp")
DIST = os.path.join(ROOT, "dist")

APP_NAME = "300HeroAutoScript"
LAUNCHER_EXE = "300HeroAuto.exe"
UI_EXE = "300HeroAutoUI.exe"

PY_VER = "3.12.8"
PY_TAG = "312"
PY_URL = f"https://www.python.org/ftp/python/{PY_VER}/python-{PY_VER}-embed-amd64.zip"

ELECTRON_VER = "33.2.1"
ELECTRON_URLS = [
    f"https://npmmirror.com/mirrors/electron/{ELECTRON_VER}/electron-v{ELECTRON_VER}-win32-x64.zip",
    f"https://github.com/electron/electron/releases/download/v{ELECTRON_VER}/electron-v{ELECTRON_VER}-win32-x64.zip",
]

CSC = r"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe"

# 打进包里的源码
APP_FILES = ["gui.py", "requirements.txt", "README.md"]
APP_DIRS = ["stardust", "webui", "recorder"]
SKIP_IN_STARDUST = {"captures", "__pycache__", "stardust_log.txt", "stop.flag", "running.flag",
                    "test_scaling.py", "grab.py"}


def log(*a):
    print("[build]", *a, flush=True)


def download(urls, name):
    os.makedirs(CACHE, exist_ok=True)
    dst = os.path.join(CACHE, name)
    if os.path.exists(dst) and os.path.getsize(dst) > 0:
        return dst
    for u in ([urls] if isinstance(urls, str) else urls):
        try:
            log("下载", u)
            tmp = dst + ".part"
            with urllib.request.urlopen(u, timeout=60) as r, open(tmp, "wb") as f:
                shutil.copyfileobj(r, f, 1 << 20)
            os.replace(tmp, dst)
            return dst
        except Exception as e:
            log("  失败:", e)
    raise SystemExit(f"无法下载 {name}")


def stop_toolkit_processes():
    """结束正在使用 toolkit 的进程（否则文件被占用，删除会失败且留下半个目录）。"""
    ps = ("Get-Process | Where-Object { $_.Path -like '%s\\*' } | "
          "ForEach-Object { Stop-Process -Id $_.Id -Force; $_.ProcessName }") % TOOLKIT
    out = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True).stdout.split()
    if out:
        log("已结束占用 toolkit 的进程:", ", ".join(out))
        import time
        time.sleep(1)


# ---------------- toolkit/python ----------------
def step_toolkit():
    stop_toolkit_processes()
    z = download(PY_URL, os.path.basename(PY_URL))
    if os.path.exists(PY_DIR):
        shutil.rmtree(PY_DIR)
    os.makedirs(PY_DIR)
    zipfile.ZipFile(z).extractall(PY_DIR)

    # ._pth 决定内嵌 Python 的 sys.path：加入 site-packages、程序根目录、stardust
    pth = os.path.join(PY_DIR, f"python{PY_TAG}._pth")
    with open(pth, "w", encoding="utf-8") as f:
        f.write(f"python{PY_TAG}.zip\n.\nLib\\site-packages\n..\\..\n..\\..\\stardust\nimport site\n")

    site = os.path.join(PY_DIR, "Lib", "site-packages")
    os.makedirs(site, exist_ok=True)
    log("安装依赖到", site)
    subprocess.check_call([
        sys.executable, "-m", "pip", "install", "--no-cache-dir", "--disable-pip-version-check",
        "--target", site, "--platform", "win_amd64", "--python-version", PY_TAG,
        "--implementation", "cp", "--only-binary=:all:",
        "-r", os.path.join(ROOT, "requirements.txt"),
    ])
    # VC++ 运行库随包分发（app-local），避免目标机没装 VC++ 运行库时 “DLL load failed”
    sysdir = os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "System32")
    for dll in ["msvcp140.dll", "msvcp140_1.dll", "msvcp140_2.dll", "vcruntime140.dll",
                "vcruntime140_1.dll", "concrt140.dll"]:
        dst = os.path.join(PY_DIR, dll)
        if not os.path.exists(dst) and os.path.exists(os.path.join(sysdir, dll)):
            shutil.copy2(os.path.join(sysdir, dll), dst)
    # 冒烟测试
    out = subprocess.check_output([os.path.join(PY_DIR, "python.exe"), "-c",
                                   "import numpy, cv2, mss, tornado; print(cv2.__version__, numpy.__version__, tornado.version)"],
                                  cwd=ROOT, text=True)
    log("内嵌 Python OK:", out.strip())


# ---------------- toolkit/WebApp (Electron) ----------------
def step_webapp():
    stop_toolkit_processes()
    z = download(ELECTRON_URLS, f"electron-v{ELECTRON_VER}-win32-x64.zip")
    if os.path.exists(WEBAPP_DIR):
        shutil.rmtree(WEBAPP_DIR)
    os.makedirs(WEBAPP_DIR)
    zipfile.ZipFile(z).extractall(WEBAPP_DIR)
    os.replace(os.path.join(WEBAPP_DIR, "electron.exe"), os.path.join(WEBAPP_DIR, UI_EXE))
    # 删掉默认 app 与不需要的文件
    for p in ["resources/default_app.asar", "LICENSES.chromium.html"]:
        fp = os.path.join(WEBAPP_DIR, p)
        if os.path.exists(fp):
            os.remove(fp)
    app = os.path.join(WEBAPP_DIR, "resources", "app")
    shutil.copytree(os.path.join(ROOT, "webapp"), app)
    log("Electron OK:", WEBAPP_DIR)


# ---------------- 启动器 ----------------
def step_launcher():
    src = os.path.join(ROOT, "launcher", "Launcher.cs")
    out = os.path.join(ROOT, LAUNCHER_EXE)
    cmd = [CSC, "/nologo", "/target:winexe", "/optimize+", f"/out:{out}",
           "/r:System.Windows.Forms.dll"]
    ico = os.path.join(ROOT, "launcher", "app.ico")
    if os.path.exists(ico):
        cmd.append(f"/win32icon:{ico}")
    cmd.append(src)
    subprocess.check_call(cmd)
    log("启动器 OK:", out)


# ---------------- 打包 ----------------
def step_package():
    stage = os.path.join(BUILD, "stage", APP_NAME)
    if os.path.exists(os.path.dirname(stage)):
        shutil.rmtree(os.path.dirname(stage))
    os.makedirs(stage)
    for f in APP_FILES + [LAUNCHER_EXE]:
        shutil.copy2(os.path.join(ROOT, f), stage)
    ignore = shutil.ignore_patterns(*SKIP_IN_STARDUST)
    for d in APP_DIRS:
        shutil.copytree(os.path.join(ROOT, d), os.path.join(stage, d), ignore=ignore)
    shutil.copytree(TOOLKIT, os.path.join(stage, "toolkit"),
                    ignore=shutil.ignore_patterns("__pycache__"))
    os.makedirs(DIST, exist_ok=True)
    zpath = os.path.join(DIST, f"{APP_NAME}.zip")
    if os.path.exists(zpath):
        os.remove(zpath)
    log("压缩", zpath)
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        base = os.path.dirname(stage)
        for dp, _, fs in os.walk(stage):
            for f in fs:
                full = os.path.join(dp, f)
                zf.write(full, os.path.relpath(full, base))
    log(f"完成: {zpath}  ({os.path.getsize(zpath) / 1e6:.0f} MB)")


STEPS = {"toolkit": step_toolkit, "webapp": step_webapp, "launcher": step_launcher, "package": step_package}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--step", choices=list(STEPS), action="append")
    a = ap.parse_args()
    for name in a.step or list(STEPS):
        log("====", name)
        STEPS[name]()
