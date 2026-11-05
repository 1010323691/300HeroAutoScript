// 300英雄 自动脚本 —— Electron 桌面壳
// 启动内嵌 Python 的 gui.py（pywebio），在窗口里显示；关闭窗口时先让脚本安全停止再退出。
const { app, BrowserWindow, Menu, shell, ipcMain, screen } = require('electron');
const { spawn, spawnSync } = require('child_process');
const path = require('path');
const fs = require('fs');
const net = require('net');
const http = require('http');

// 目录结构: <root>/toolkit/WebApp/resources/app/main.js
const ROOT = process.env.APP_ROOT || path.resolve(__dirname, '..', '..', '..', '..');
const PYTHON = path.join(ROOT, 'toolkit', 'python', 'python.exe');
const GUI = path.join(ROOT, 'gui.py');
const STOP_FLAG = path.join(ROOT, 'stardust', 'stop.flag');
const RUNNING_FLAG = path.join(ROOT, 'stardust', 'running.flag');   // gui.py 在脚本运行期间维护
const REC_RUNNING_FLAG = path.join(ROOT, 'recorder', 'running.flag');
const REC_STOP_FLAG = path.join(ROOT, 'recorder', 'stop.flag');
const LOG_DIR = path.join(ROOT, 'log');
const LOG_FILE = path.join(LOG_DIR, 'gui.txt');

let win = null;
let py = null;
let quitting = false;

if (!app.requestSingleInstanceLock()) {
  app.quit();
} else {
  app.on('second-instance', () => {
    if (win) { if (win.isMinimized()) win.restore(); win.focus(); }
  });
  app.whenReady().then(main);
}

// 启动中 / 出错时显示的页面（与主界面同一设计语言；无边框窗口需自带标题栏）
function page(title, body, spinning = false) {
  const html = `<!doctype html><meta charset="utf-8"><title>${title}</title>
  <style>
    body{margin:0;height:100vh;display:flex;flex-direction:column;font:13px/1.6 "Microsoft YaHei UI","Microsoft YaHei",sans-serif;color:#15171c;background:#eceef2}
    .bar{height:52px;display:flex;align-items:center;gap:10px;padding:0 10px 0 18px;-webkit-app-region:drag;font-size:14px;font-weight:700}
    .bar svg{width:24px;height:24px}
    .bar span{margin-left:auto}.bar button{-webkit-app-region:no-drag;width:40px;height:32px;border:0;background:none;border-radius:8px;font-size:15px;color:#4a505c;cursor:pointer}
    .bar button:hover{background:rgba(255,255,255,.75)}.bar button.x:hover{background:#e5484d;color:#fff}
    .box{margin:auto;width:min(720px,calc(100% - 48px));box-sizing:border-box;background:#fff;border:1px solid #e3e6eb;border-radius:14px;padding:32px 36px;box-shadow:0 1px 2px rgba(16,24,40,.05);text-align:center}
    .spin{width:40px;height:40px;margin:0 auto 18px;border-radius:50%;border:4px solid #e4e9ff;border-top-color:#3461ff;animation:s .8s linear infinite}
    @keyframes s{to{transform:rotate(360deg)}}
    h2{margin:0 0 8px;font-size:17px}p{color:#4a505c;margin:6px 0}code{font-family:Consolas,monospace;font-size:12px;background:#f0f2f5;padding:1px 6px;border-radius:4px}
    pre{text-align:left;white-space:pre-wrap;background:#f7f8fa;border:1px solid #eef0f3;border-radius:10px;padding:12px;font:12px/1.5 Consolas,monospace;max-height:300px;overflow:auto}
  </style>
  <div class="bar"><svg viewBox="0 0 40 40"><path d="M5 29c4-1 6-5 9-10s6-9 10-9 6 3 7 7" fill="none" stroke="#3461ff" stroke-width="6" stroke-linecap="round"/><path d="M15 31c4 0 6-3 8-7s5-7 9-7 4 2 4 4" fill="none" stroke="#7a5af8" stroke-width="5.5" stroke-linecap="round"/></svg>300英雄 自动脚本<span></span><button onclick="desktop.win('min')">—</button><button class="x" onclick="desktop.win('close')">✕</button></div>
  <div class="box">${spinning ? '<div class="spin"></div>' : ''}${body}</div>`;
  return 'data:text/html;charset=utf-8,' + encodeURIComponent(html);
}

// 迷你模式：窄高小窗贴到当前显示器工作区右侧；还原时回到原来的位置大小
const FULL_SIZE = [1280, 720];
const FULL_MIN = [1100, 640];
const MINI_WIDTH = 360;
const MINI_HEIGHT = 720;
let savedBounds = null;
let savedMax = false;
let compact = false;

function enterCompact() {
  if (compact) return;
  compact = true;
  savedMax = win.isMaximized();
  savedBounds = win.getNormalBounds();
  if (savedMax) win.unmaximize();
  const wa = screen.getDisplayMatching(win.getBounds()).workArea;
  win.setMinimumSize(300, 480);
  const h = Math.min(MINI_HEIGHT, wa.height);           // 屏幕太矮时不超出工作区
  win.setBounds({
    x: wa.x + wa.width - MINI_WIDTH,                      // 贴右边
    y: wa.y + Math.round((wa.height - h) / 2),            // 垂直居中
    width: MINI_WIDTH, height: h,
  });
}

function exitCompact() {
  if (!compact) return;
  compact = false;
  win.setMinimumSize(...FULL_MIN);
  if (savedBounds) win.setBounds(savedBounds);
  if (savedMax) win.maximize();
}

ipcMain.on('win', (e, cmd) => {
  if (!win) return;
  if (cmd === 'min') win.minimize();
  else if (cmd === 'max') win.isMaximized() ? win.unmaximize() : win.maximize();
  else if (cmd === 'close') win.close();
  else if (cmd === 'compact') enterCompact();
  else if (cmd === 'full') exitCompact();
});

function freePort() {
  return new Promise((resolve, reject) => {
    const s = net.createServer();
    s.listen(0, '127.0.0.1', () => { const p = s.address().port; s.close(() => resolve(p)); });
    s.on('error', reject);
  });
}

function waitHttp(url, timeoutMs) {
  const end = Date.now() + timeoutMs;
  return new Promise((resolve, reject) => {
    const tick = () => {
      if (py && py.exitCode !== null) return reject(new Error('界面服务进程已退出'));
      http.get(url, res => { res.resume(); res.statusCode === 200 ? resolve() : retry(); })
        .on('error', retry);
    };
    const retry = () => (Date.now() > end ? reject(new Error('启动超时')) : setTimeout(tick, 300));
    tick();
  });
}

function tailLog(n = 40) {
  try { return fs.readFileSync(LOG_FILE, 'utf-8').split(/\r?\n/).slice(-n).join('\n'); }
  catch (e) { return ''; }
}

async function main() {
  Menu.setApplicationMenu(null);
  win = new BrowserWindow({
    width: FULL_SIZE[0], height: FULL_SIZE[1], minWidth: FULL_MIN[0], minHeight: FULL_MIN[1],
    title: '300英雄 自动脚本', backgroundColor: '#eceef2', show: true,
    frame: false, roundedCorners: true,
    webPreferences: { contextIsolation: true, nodeIntegration: false, preload: path.join(__dirname, 'preload.js') },
  });
  win.webContents.setWindowOpenHandler(({ url }) => { shell.openExternal(url); return { action: 'deny' }; });
  win.on('page-title-updated', e => e.preventDefault());
  win.on('close', e => { if (!quitting) { e.preventDefault(); shutdown(); } });
  win.loadURL(page('启动中', '<h2>正在启动…</h2><p>首次启动可能需要十几秒。</p>', true));

  if (!fs.existsSync(PYTHON) || !fs.existsSync(GUI)) {
    win.loadURL(page('文件缺失', `<h2>文件缺失</h2><p>找不到 <code>${PYTHON}</code> 或 <code>${GUI}</code>。</p>
      <p>请完整解压压缩包后，双击根目录下的 <b>300HeroAuto.exe</b>。</p>`));
    return;
  }

  fs.mkdirSync(LOG_DIR, { recursive: true });
  const out = fs.openSync(LOG_FILE, 'w');
  const port = await freePort();
  py = spawn(PYTHON, ['-s', '-u', GUI, '--port', String(port)], {   // -s: 不加载用户目录的第三方包
    cwd: ROOT, windowsHide: true, stdio: ['ignore', out, out],
    env: Object.assign({}, process.env, { PYTHONIOENCODING: 'utf-8', PYTHONUTF8: '1' }),
  });
  py.on('exit', code => {
    if (!quitting && win) {
      win.loadURL(page('已退出', `<h2>界面服务意外退出（代码 ${code}）</h2>
        <pre>${escapeHtml(tailLog())}</pre>
        <p>日志：${LOG_FILE}</p>`));
    }
  });

  try {
    await waitHttp(`http://127.0.0.1:${port}/`, 60000);
    win.loadURL(`http://127.0.0.1:${port}/`);
  } catch (e) {
    win.loadURL(page('启动失败', `<h2>启动失败：${e.message}</h2>
      <pre>${escapeHtml(tailLog())}</pre>
      <p>日志：${LOG_FILE}</p>`));
  }
}

function escapeHtml(s) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function killTree(pid) {
  try { spawnSync('taskkill', ['/PID', String(pid), '/T', '/F'], { windowsHide: true }); } catch (e) { }
}

async function shutdown() {
  quitting = true;
  // 1) 脚本/录制正在运行时，先让它们自己停下（脚本会取消游戏置顶，录制会写完视频），最多等 10 秒
  const pairs = [[RUNNING_FLAG, STOP_FLAG], [REC_RUNNING_FLAG, REC_STOP_FLAG]].filter(([run]) => fs.existsSync(run));
  for (const [, stop] of pairs) { try { fs.writeFileSync(stop, ''); } catch (e) { } }
  const end = Date.now() + 10000;
  while (pairs.some(([run]) => fs.existsSync(run)) && Date.now() < end) await new Promise(r => setTimeout(r, 200));
  // 2) 结束界面服务及其子进程
  if (py && py.exitCode === null) killTree(py.pid);
  try { fs.unlinkSync(STOP_FLAG); } catch (e) { }
  app.exit(0);
}

app.on('window-all-closed', () => { if (!quitting) shutdown(); });
