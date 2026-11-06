/* 300英雄 自动脚本 —— 前端逻辑（无依赖，所有数据来自本地后端 /api） */
"use strict";

/* ============================ 图标 ============================ */
const S = (d, w = 1.8) => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="${w}" stroke-linecap="round" stroke-linejoin="round">${d}</svg>`;
const ICONS = {
  filetext: S('<path d="M14 3H6.5A1.5 1.5 0 0 0 5 4.5v15A1.5 1.5 0 0 0 6.5 21h11a1.5 1.5 0 0 0 1.5-1.5V8z"/><path d="M14 3v5h5M8.5 12.5h7M8.5 16.5h5"/>'),
  gear: S('<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/>'),
  star: S('<path d="M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1-4.4-4.3 6.1-.9z"/>'),
  video: S('<rect x="2.5" y="6" width="13" height="12" rx="2.5"/><path d="M15.5 10.5l6-3.5v10l-6-3.5"/>'),
  monitor: S('<rect x="2.5" y="4" width="19" height="13" rx="2"/><path d="M8 21h8M12 17v4"/>'),
  gamepad: S('<path d="M7 7h10a4.5 4.5 0 0 1 4.4 5.5l-1 4.4a2.6 2.6 0 0 1-4.6 1L14.5 16h-5l-1.3 1.9a2.6 2.6 0 0 1-4.6-1l-1-4.4A4.5 4.5 0 0 1 7 7z"/><path d="M8 10.5v3M6.5 12h3M15.5 11h.01M17.5 13h.01"/>'),
  search: S('<circle cx="11" cy="11" r="6.5"/><path d="M20 20l-4.2-4.2"/>', 2),
  bell: S('<path d="M6 16V11a6 6 0 1 1 12 0v5l1.5 2h-15z"/><path d="M10 20.5a2 2 0 0 0 4 0"/>'),
  help: S('<circle cx="12" cy="12" r="9"/><path d="M9.4 9.2a2.7 2.7 0 0 1 5.2.9c0 1.8-2.6 2.2-2.6 4"/><path d="M12 17.2h.01"/>'),
  min: S('<path d="M5 12h14"/>'), max: S('<rect x="5.5" y="5.5" width="13" height="13" rx="1.5"/>'), x: S('<path d="M6 6l12 12M18 6L6 18"/>'),
  play: `<svg viewBox="0 0 24 24"><path d="M7.5 5.2v13.6a.8.8 0 0 0 1.2.7l11-6.8a.8.8 0 0 0 0-1.4l-11-6.8a.8.8 0 0 0-1.2.7z" fill="currentColor"/></svg>`,
  stop: `<svg viewBox="0 0 24 24"><rect x="6" y="6" width="12" height="12" rx="2.2" fill="currentColor"/></svg>`,
  recdot: `<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="6.5" fill="currentColor"/></svg>`,
  more: `<svg viewBox="0 0 24 24" fill="currentColor"><circle cx="5" cy="12" r="1.8"/><circle cx="12" cy="12" r="1.8"/><circle cx="19" cy="12" r="1.8"/></svg>`,
  dock: S('<rect x="3" y="4" width="18" height="16" rx="2.5"/><path d="M15 4v16"/><path d="M17.5 8.5h1M17.5 11h1"/>'),
  expand: S('<path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7"/>'),
  download: S('<path d="M12 4v11M7.5 10.5L12 15l4.5-4.5M5 19.5h14"/>'),
  trash: S('<path d="M4 6.5h16M9 6.5V4.5h6v2M18.5 6.5l-.9 12.6a1.5 1.5 0 0 1-1.5 1.4H7.9a1.5 1.5 0 0 1-1.5-1.4L5.5 6.5"/>'),
  chevron: S('<path d="M6 9l6 6 6-6"/>', 2.2),
  external: S('<path d="M14 4h6v6M20 4l-8.5 8.5"/><path d="M18 14v4.5a1.5 1.5 0 0 1-1.5 1.5h-11A1.5 1.5 0 0 1 4 18.5v-11A1.5 1.5 0 0 1 5.5 6H10"/>'),
  info: S('<circle cx="12" cy="12" r="9"/><path d="M12 11v5.5M12 7.6h.01"/>'),
  image: S('<rect x="3" y="3.5" width="18" height="17" rx="2.5"/><circle cx="9" cy="9.5" r="1.8"/><path d="M21 15.5l-5-5L5 20.5"/>'),
  folder: S('<path d="M3 7.5A1.5 1.5 0 0 1 4.5 6H9l2 2h8.5A1.5 1.5 0 0 1 21 9.5v8a1.5 1.5 0 0 1-1.5 1.5h-15A1.5 1.5 0 0 1 3 17.5z"/>'),
  compass: S('<circle cx="12" cy="12" r="9"/><path d="M15.8 8.2l-2.1 5.5-5.5 2.1 2.1-5.5z"/>'),
  chart: S('<path d="M4 20V10M10 20V4M16 20v-7M21 20H3"/>'),
  layers: S('<path d="M12 3l9 4.5-9 4.5-9-4.5z"/><path d="M3 12l9 4.5 9-4.5M3 16.5l9 4.5 9-4.5"/>'),
  gem: S('<path d="M6 3.5h12l3.5 5.5L12 20.5 2.5 9z"/><path d="M2.5 9h19M9.5 3.5L8 9l4 11.5L16 9l-1.5-5.5"/>'),
  clock: S('<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3.2 2"/>'),
  plus: S('<path d="M12 5v14M5 12h14"/>', 2), minus: S('<path d="M5 12h14"/>', 2),
  check: S('<path d="M5 12.5l4.5 4.5L19 7.5"/>', 2.2),
  keyboard: S('<rect x="2.5" y="6" width="19" height="12" rx="2"/><path d="M6 9.5h.01M9.5 9.5h.01M13 9.5h.01M16.5 9.5h.01M7 14.5h10"/>'),
  logs: S('<rect x="3.5" y="3.5" width="17" height="17" rx="3"/><path d="M8 8.5h.01M11 8.5h5M8 12h.01M11 12h5M8 15.5h.01M11 15.5h5"/>'),
  inbox: S('<path d="M3 13.5l2.6-7.2A2 2 0 0 1 7.5 5h9a2 2 0 0 1 1.9 1.3l2.6 7.2V18a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><path d="M3 13.5h5l1.5 2.5h5l1.5-2.5h5"/>'),
};
const LV_ICON = {
  info: "",
  start: `<svg viewBox="0 0 16 16"><path d="M5 3.6v8.8l7-4.4z" fill="#fff"/></svg>`,
  success: `<svg viewBox="0 0 16 16"><path d="M4.2 8.3l2.5 2.5 5-5.1" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/></svg>`,
  warn: `<svg viewBox="0 0 16 16"><path d="M8 4.2v4.6M8 11.6h.01" stroke="#fff" stroke-width="2" stroke-linecap="round" fill="none"/></svg>`,
  error: `<svg viewBox="0 0 16 16"><path d="M5.2 5.2l5.6 5.6M10.8 5.2l-5.6 5.6" stroke="#fff" stroke-width="2" stroke-linecap="round" fill="none"/></svg>`,
};
const LV_TEXT = { info: "信息", success: "成功", warn: "警告", error: "错误" };
const lvIcon = (lv, start) => `<span class="lv ${start ? "start" : lv}" title="${LV_TEXT[lv] || ""}">${LV_ICON[start ? "start" : lv] || ""}</span>`;
function paintIcons(root = document) {
  root.querySelectorAll("i[data-ic]").forEach(el => {
    if (el.dataset.painted !== el.dataset.ic) { el.innerHTML = ICONS[el.dataset.ic] || ""; el.dataset.painted = el.dataset.ic; }
  });
}
const setIcon = (el, name) => { el.dataset.ic = name; paintIcons(el.parentElement); };

/* ============================ 工具 ============================ */
const $ = s => document.querySelector(s);
const $$ = s => [...document.querySelectorAll(s)];
const api = (path, opt = {}) => fetch("/api/" + path, {
  method: opt.method || "GET",
  headers: opt.body ? { "Content-Type": "application/json" } : {},
  body: opt.body ? JSON.stringify(opt.body) : undefined,
}).then(r => r.json());
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const pad = n => String(n).padStart(2, "0");
const fmtDur = s => { s = Math.round(s || 0); return s < 60 ? `${s} 秒` : `${Math.floor(s / 60)} 分 ${pad(s % 60)} 秒`; };
const fmtClock = s => { s = Math.floor(s || 0); const h = Math.floor(s / 3600); return h ? `${h}:${pad(Math.floor(s / 60) % 60)}:${pad(s % 60)}` : `${Math.floor(s / 60)}:${pad(s % 60)}`; };
const fmtClock2 = s => { s = Math.floor(s || 0); const h = Math.floor(s / 3600); return (h ? `${pad(h)}:` : "") + `${pad(Math.floor(s / 60) % 60)}:${pad(s % 60)}`; };
const fmtTs = ts => { if (!ts) return "—"; const d = new Date(ts * 1000); return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`; };
const fmtHms = ts => { if (!ts) return "—"; const d = new Date(ts * 1000); return `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`; };
const fmtSize = b => !b ? "0 KB" : b >= 1e9 ? (b / 1e9).toFixed(2) + " GB" : b >= 1e6 ? (b / 1e6).toFixed(1) + " MB" : Math.max(1, Math.round(b / 1e3)) + " KB";
const fmtNum = n => Number(n || 0).toLocaleString("zh-CN");
function toast(msg, level = "info") {
  const t = $("#toast");
  t.innerHTML = `${lvIcon(level)}<span>${esc(msg)}</span>`;
  t.classList.add("show");
  clearTimeout(toast.t); toast.t = setTimeout(() => t.classList.remove("show"), 2400);
}
// 只在内容变化时写 DOM（轮询每 600ms 一次，避免重复解析和动画重启）
const setHTML = (sel, html) => { const el = $(sel); if (el.innerHTML !== html) el.innerHTML = html; };
const setText = (sel, text) => { const el = $(sel); text = String(text); if (el.textContent !== text) el.textContent = text; };
const statusPill = (cls, text, sm) => `<em class="status ${cls}${sm ? " sm" : ""}">${esc(text)}</em>`;
const emptyHTML = (ic, title, sub) => `<div class="empty"><i data-ic="${ic}"></i><b>${esc(title)}</b>${sub ? `<span>${esc(sub)}</span>` : ""}</div>`;
const chipCls = v => v >= 500 ? "c500" : v >= 100 ? "c100" : "";

/* ============================ 分段选项（控制台与设置页共用一份） ============================ */
const SEG_OPTS = {
  games: [[0, "全部"], [1, "1"], [2, "2"], [3, "3"], [5, "5"], [10, "10"]],
  close: [[1, "回到大厅"], [0, "停留在占卜页"]],
  fps: [[5, "5"], [8, "8<small>推荐</small>"], [12, "12"], [20, "20"]],
};
$$("[data-opts]").forEach(el => el.innerHTML = SEG_OPTS[el.dataset.opts].map(([v, t]) => `<button data-v="${v}">${t}</button>`).join(""));

/* ============================ 窗口 ============================ */
if (window.desktop) {
  document.body.classList.add("electron");
  $$("[data-win]").forEach(b => b.onclick = () => window.desktop.win(b.dataset.win));
  $(".topbar").addEventListener("dblclick", e => { if (!e.target.closest(".nodrag")) window.desktop.win("max"); });
}

/* ============================ 确认框 ============================ */
function confirmBox(title, body, okText = "确定") {
  return new Promise(resolve => {
    const m = $("#confirmModal");
    $("#cfTitle").textContent = title; $("#cfBody").textContent = body; $("#cfOk").textContent = okText;
    m.hidden = false; $("#cfCancel").focus();
    const done = v => { m.hidden = true; m.onclick = $("#cfOk").onclick = $("#cfCancel").onclick = null; document.removeEventListener("keydown", key, true); resolve(v); };
    const key = e => { if (e.key === "Escape") { e.stopPropagation(); done(false); } };
    document.addEventListener("keydown", key, true);
    $("#cfOk").onclick = () => done(true);
    $("#cfCancel").onclick = () => done(false);
    m.onclick = e => { if (e.target === m) done(false); };
  });
}

/* ============================ 导航 / 标签页 / 菜单 ============================ */
const PAGES = {
  home: ["星屑占卜", "常驻活动 → 好运星盘 → 星屑占卜，按最优策略用完每日占卜次数后回到大厅"],
  record: ["操作录制", "录制游戏画面、点击与按键，生成给 agent 学习的步骤清单"],
  history: ["运行记录", "每次运行的局数、星砂与每局结果"],
  settings: ["设置", "修改后自动保存，下次运行生效"],
};
let curPage = "home";
function showPage(name) {
  curPage = name;
  $$(".page").forEach(p => p.classList.toggle("active", p.id === "page-" + name));
  $$(".nav-item").forEach(a => a.classList.toggle("active", a.dataset.page === name));
  $("#pageTitle").textContent = PAGES[name][0];
  $("#pageSub").textContent = PAGES[name][1];
  if (name === "history") loadHistory();
  if (name === "record") loadRecList();
}
$$(".nav-item").forEach(a => a.addEventListener("click", () => showPage(a.dataset.page)));
$$("[data-goto]").forEach(b => b.onclick = () => showPage(b.dataset.goto));

function showTab(group, tab) {
  $$(`.tabbar[data-tabs="${group}"] .tab`).forEach(t => t.classList.toggle("active", t.dataset.tab === tab));
  $$(`[data-panel^="${group}-"]`).forEach(p => p.classList.toggle("active", p.dataset.panel === `${group}-${tab}`));
  if (group === "home" && tab === "runs") loadHistory();
  if (group === "home" && tab === "log") { const b = $("#logBody"); b.scrollTop = b.scrollHeight; }
  if (group === "record" && tab === "log") { const b = $("#recLogBody"); b.scrollTop = b.scrollHeight; }
}
$$(".tabbar").forEach(g => g.querySelectorAll(".tab").forEach(t => t.onclick = () => showTab(g.dataset.tabs, t.dataset.tab)));

function closeMenus(except) { $$(".menu.open").forEach(m => { if (m !== except) m.classList.remove("open"); }); }
document.addEventListener("click", e => {
  const t = e.target.closest("[data-menu]");
  if (t) { const m = $("#" + t.dataset.menu); closeMenus(m); m.classList.toggle("open"); e.stopPropagation(); return; }
  if (!e.target.closest(".menu")) closeMenus(e.target.closest("#searchBox") ? $("#searchMenu") : null);
});
async function openTarget(what, name) {
  const r = await api("open", { method: "POST", body: { what, name } });
  if (r.ok === false) toast(r.msg, "warn");
}
document.addEventListener("click", e => {
  const o = e.target.closest("[data-open]");
  if (o) { closeMenus(); openTarget(o.dataset.open); }
  const a = e.target.closest("[data-action='help']");
  if (a) { closeMenus(); openHelp(); }
});

/* ============================ 搜索 ============================ */
const SEARCH_ITEMS = [
  { k: "星屑占卜 好运星盘 脚本 运行 占卜 开始", t: "运行星屑占卜", s: "脚本", go: () => showPage("home") },
  { k: "操作录制 录像 视频 录制", t: "操作录制", s: "脚本", go: () => showPage("record") },
  { k: "运行日志 日志 导出", t: "运行日志", s: "星屑占卜", go: () => { showPage("home"); showTab("home", "log"); } },
  { k: "运行记录 历史 统计 星砂 图表", t: "运行记录与统计", s: "页面", go: () => showPage("history") },
  { k: "策略 说明 奖励表 期望", t: "策略说明 / 奖励表", s: "星屑占卜", go: () => { showPage("home"); showTab("home", "strategy"); } },
  { k: "录像列表 录像 文件", t: "录像列表", s: "操作录制", go: () => { showPage("record"); showTab("record", "list"); } },
  { k: "设置 参数 局数 等待 帧率 按键", t: "设置", s: "页面", go: () => showPage("settings") },
  { k: "迷你模式 小窗 贴边 compact", t: "迷你模式", s: "窗口", go: () => setCompact(true) },
  { k: "异常截图 截图 captures", t: "打开异常截图", s: "文件", go: () => openTarget("captures") },
  { k: "日志文件 stardust_log", t: "打开日志文件", s: "文件", go: () => openTarget("log") },
  { k: "帮助 使用说明 教程", t: "使用说明", s: "帮助", go: () => openHelp() },
];
let searchSel = 0;
function renderSearch() {
  const q = $("#searchInput").value.trim().toLowerCase();
  const menu = $("#searchMenu");
  if (!q) { menu.classList.remove("open"); menu.hits = []; return; }
  const hits = SEARCH_ITEMS.filter(i => (i.t + " " + i.k).toLowerCase().includes(q));
  searchSel = Math.min(searchSel, Math.max(0, hits.length - 1));
  menu.innerHTML = hits.length ? hits.map((h, i) => `<button class="${i === searchSel ? "sel" : ""}" data-si="${SEARCH_ITEMS.indexOf(h)}">${esc(h.t)}<small>${esc(h.s)}</small></button>`).join("")
    : `<div class="empty" style="padding:16px"><span>没有找到“${esc(q)}”</span></div>`;
  closeMenus(menu);
  menu.classList.add("open");
  menu.hits = hits;
}
function runSearch(item) { item.go(); $("#searchInput").value = ""; renderSearch(); $("#searchInput").blur(); }
$("#searchInput").addEventListener("input", () => { searchSel = 0; renderSearch(); });
$("#searchInput").addEventListener("keydown", e => {
  const hits = $("#searchMenu").hits || [];
  if (e.key === "ArrowDown") { searchSel = Math.min(searchSel + 1, hits.length - 1); renderSearch(); e.preventDefault(); }
  else if (e.key === "ArrowUp") { searchSel = Math.max(searchSel - 1, 0); renderSearch(); e.preventDefault(); }
  else if (e.key === "Enter" && hits[searchSel]) runSearch(hits[searchSel]);
  else if (e.key === "Escape") { $("#searchInput").value = ""; renderSearch(); $("#searchInput").blur(); }
});
$("#searchMenu").addEventListener("click", e => { const b = e.target.closest("[data-si]"); if (b) runSearch(SEARCH_ITEMS[+b.dataset.si]); });
document.addEventListener("keydown", e => {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k" && !document.body.classList.contains("compact")) {
    e.preventDefault(); $("#searchInput").focus(); $("#searchInput").select();
  } else if (e.key === "Escape") {
    closeMenus();
    if (!$("#helpModal").hidden) $("#helpModal").hidden = true;
  }
});

/* ============================ 通知 ============================ */
const notices = [];
function notify(level, title, detail) {
  const d = new Date();
  notices.unshift({ level, title, detail, time: `${pad(d.getHours())}:${pad(d.getMinutes())}` });
  notices.length = Math.min(notices.length, 30);
  $("#bellDot").hidden = false;
  renderNotices();
}
function renderNotices() {
  $("#notifyList").innerHTML = notices.length ? notices.map(n => `<div class="nt">${lvIcon(n.level)}
    <div><b>${esc(n.title)}</b><small>${esc(n.time)} · ${esc(n.detail)}</small></div></div>`).join("")
    : `<div class="empty" style="padding:24px"><span>暂无通知</span></div>`;
}
$("#bellBtn").onclick = e => { e.stopPropagation(); const m = $("#notifyMenu"); closeMenus(m); m.classList.toggle("open"); $("#bellDot").hidden = true; };
$("#notifyClear").onclick = () => { notices.length = 0; renderNotices(); };
renderNotices();

/* ============================ 使用说明 ============================ */
const HELP_HTML = `
  <h3>开始之前</h3>
  <ol>
    <li>启动 <b>300英雄</b>，登录并停在 <b>大厅主界面</b>（窗口分辨率任意，脚本会自动适配）。</li>
    <li>在「星屑占卜」页点 <b>运行脚本</b>：脚本自动进入 常驻活动 → 好运星盘 → 星屑占卜，按最优策略用完次数后回到大厅。</li>
    <li>运行期间游戏窗口会临时置顶，请不要操作鼠标；结束后自动恢复。</li>
  </ol>
  <h3>停止</h3>
  <p>点 <b>停止运行</b>，或在任何界面按 <b>F12</b> 立即停止；关闭本程序也会先安全停止脚本。</p>
  <h3>迷你模式</h3>
  <p>点顶栏右侧的迷你模式按钮，窗口缩成屏幕右侧的小窗，只保留运行按钮、星盘、状态和日志；点小窗右上角的 ⤢ 还原。</p>
  <h3>操作录制</h3>
  <p>侧栏「操作录制」可以录下游戏画面、点击和按键，生成给 agent 学习用的步骤清单；按 <b>F10</b> 停止录制。</p>
  <h3>常见问题</h3>
  <p>网络差、点击经常没反应时，把“点击等待”调大；游戏以管理员身份运行时，本程序也需要以管理员身份运行。</p>`;
function openHelp() { $("#helpModalBody").innerHTML = HELP_HTML; $("#helpModal").hidden = false; $("#helpClose").focus(); }
$("#helpBtn").onclick = openHelp;
$("#helpClose").onclick = () => $("#helpModal").hidden = true;
$("#helpModal").onclick = e => { if (e.target.id === "helpModal") $("#helpModal").hidden = true; };

/* ============================ 日志格式化 ============================ */
const LINE_NAME = { row0: "第 1 行", row1: "第 2 行", row2: "第 3 行", col0: "第 1 列", col1: "第 2 列", col2: "第 3 列", diag: "左上→右下 对角线", anti: "左下→右上 对角线" };
const LINES = { row0: [0, 1, 2], row1: [3, 4, 5], row2: [6, 7, 8], col0: [0, 3, 6], col1: [1, 4, 7], col2: [2, 5, 8], diag: [0, 4, 8], anti: [6, 4, 2] };
const cellName = i => `第 ${Math.floor(i / 3) + 1} 行第 ${i % 3 + 1} 格`;
const boardText = s => s.split(" ").join(" / ");
const BTN = { left: "左键", right: "右键", middle: "中键" };
function fmtLog(l) {
  const t = l.text.trim();
  let level = { start: "info", info: "info", success: "success", warn: "warn", error: "error", "end-done": "success", "end-stopped": "warn", "end-error": "error" }[l.level] || "info";
  const hl = l.level.startsWith("end-"), start = l.level === "start";
  let m, title = t, detail = "";
  if ((m = t.match(/^开始执行：星屑占卜（局数：(.+)）$/))) { title = "开始执行脚本"; detail = `星屑占卜 · 运行局数：${m[1]}`; }
  else if ((m = t.match(/^点击 (常驻活动|好运星盘)$/))) { title = `打开 ${m[1]}`; detail = "在大厅中定位并点击"; }
  else if (t === "切换到 星屑占卜 标签") { title = "切换到 星屑占卜 标签"; detail = "好运星盘窗口"; }
  else if ((m = t.match(/^窗口定位: Frame\(scale=([\d.]+), offset=\((-?\d+),(-?\d+)\)\)$/))) { title = "定位游戏窗口"; detail = `界面缩放 ${m[1]}，偏移 (${m[2]}, ${m[3]})`; level = "success"; }
  else if ((m = t.match(/^窗口定位: None$/))) { title = "定位游戏窗口"; detail = "未找到好运星盘窗口"; }
  else if ((m = t.match(/^新一局，系统翻开: (.+)$/))) { const b = m[1].replace(/ /g, ""); const i = [...b].findIndex(c => c !== "."); title = "开始新一局"; detail = i >= 0 ? `系统翻开 ${cellName(i)}：${b[i]}` : boardText(m[1]); }
  else if ((m = t.match(/^翻格子 (\d)（期望 ([\d.]+)）$/))) { title = `翻开 ${cellName(+m[1])}`; detail = `按最优策略选择，期望 ${m[2]} 星砂`; }
  else if ((m = t.match(/^4 格可见 (.+) → 选 (\w+)（期望 ([\d.]+)）$/))) { title = `选择 ${LINE_NAME[m[2]] || m[2]}`; detail = `已翻开 4 格：${boardText(m[1])}，期望 ${m[3]} 星砂`; }
  else if ((m = t.match(/^结果 (.+?)\s+线和=(\d+)\s+获得星砂 (\d+)$/))) { title = `获得 ${m[3]} 星砂`; detail = `星盘 ${boardText(m[1])}，所选线三数之和 ${m[2]}`; level = "success"; }
  else if (t === "剩余占卜次数为 0，结束") { title = "占卜次数已用完"; detail = "剩余占卜次数：0"; }
  else if (t === "关闭好运星盘窗口，回到大厅") { title = "回到大厅"; detail = "关闭好运星盘窗口"; }
  else if ((m = t.match(/^共 (\d+) 局，获得星砂 (\d+)(?:，平均 ([\d.]+))?$/))) { title = "统计"; detail = `共 ${m[1]} 局，获得 ${m[2]} 星砂${m[3] ? `，平均 ${m[3]}` : ""}`; }
  else if ((m = t.match(/^(.+?)：(\d+)s 内无响应，重试 \((\d)\/(\d)\)$/))) { title = `${m[1]}：界面无响应，重试 ${m[3]}/${m[4]}`; detail = `${m[2]} 秒内没有出现预期变化（可能是网络延迟）`; }
  else if ((m = t.match(/^停止: (.+)$/))) { title = "脚本停止"; detail = m[1]; level = /用户/.test(m[1]) ? "warn" : "error"; }
  else if ((m = t.match(/^(脚本执行完成|已手动停止|脚本异常停止)，共 (\d+) 局，星砂 (\d+)，耗时 ([\d.]+)s$/))) {
    title = m[1] === "脚本执行完成" ? `脚本执行完成（耗时 ${m[4]}s）` : `${m[1]}（耗时 ${m[4]}s）`;
    detail = `执行状态：${m[1] === "脚本执行完成" ? "成功" : m[1] === "已手动停止" ? "已停止" : "失败"}，完成 ${m[2]} 局，获得 ${m[3]} 星砂`;
  }
  else if (t === "游戏窗口已从最小化还原，等待画面刷新") { title = "还原游戏窗口"; detail = "游戏原本是最小化状态"; }
  else if (t.startsWith("未识别到大厅或好运星盘界面")) { title = "未识别到游戏界面"; detail = "请回到大厅主界面，脚本会继续等待"; }
  // 录制日志
  else if ((m = t.match(/^开始录制：(.+)$/))) { title = "开始录制"; detail = m[1]; }
  else if ((m = t.match(/^游戏窗口 (\d+)×(\d+) → 视频 (\d+)×(\d+) @ (\d+)fps$/))) { title = "录制参数"; detail = `游戏窗口 ${m[1]}×${m[2]}，视频 ${m[3]}×${m[4]}，${m[5]} 帧/秒`; }
  else if ((m = t.match(/^点击(（脚本）)? #(\d+) (\w+) @ \(([\d.]+), ([\d.]+)\)$/))) { title = `记录点击 #${m[2]}${m[1] ? "（脚本）" : ""}`; detail = `${BTN[m[3]] || m[3]} · 位置 (${m[4]}, ${m[5]})`; }
  else if ((m = t.match(/^录制结束（(.+?)）：(.+)$/))) { title = "录制结束"; detail = `${m[1]} · ${m[2]}`; }
  else if ((m = t.match(/^录制已保存：(.+)$/))) { title = "录像已保存"; detail = m[1]; }
  else if ((m = t.match(/^录制失败：(.+)$/))) { title = "录制失败"; detail = m[1]; }
  else if (t === "开始录制") { title = "启动录制"; detail = "正在打开游戏窗口录制"; }
  else if ((m = t.match(/^注意：(.+)$/))) { title = "画面可能不完整"; detail = m[1]; }
  return { time: l.time, level, title, detail, hl, start, seq: l.seq };
}
function logRowHTML(f) {
  const cls = ["lrow", f.level, f.hl ? "hl" : "", f.start ? "start" : ""].filter(Boolean).join(" ");
  return `<div class="${cls}"><time>${esc(f.time)}</time>${lvIcon(f.level, f.start)}
    <div class="msg"><b>${esc(f.title)}</b>${f.detail ? `<small>${esc(f.detail)}</small>` : ""}</div></div>`;
}
const miniRowHTML = f => `<div class="mrow ${f.level}${f.start ? " start" : ""}"><time>${esc(f.time)}</time>${lvIcon(f.level, f.start)}<span class="t">${esc(f.title)}</span></div>`;

/* ============================ 星屑占卜：日志 ============================ */
const botLogs = [];          // 已格式化的全部日志
let botSeq = 0, lastRunSeq = 0;
function renderBotLogs(append = []) {
  const body = $("#logBody");
  const q = $("#logSearch").value.trim().toLowerCase(), lv = $("#logLevel").value, range = $("#logRange").value;
  const keep = f => (!lv || f.level === lv) && (range !== "last" || f.seq >= lastRunSeq)
    && (!q || (f.title + " " + f.detail + " " + f.time).toLowerCase().includes(q));
  const atBottom = body.scrollHeight - body.scrollTop - body.clientHeight < 40;
  if (append.length && body.dataset.filtered === "0") {
    const html = append.filter(keep).map(logRowHTML).join("");
    if (html) { body.querySelector(".empty")?.remove(); body.insertAdjacentHTML("beforeend", html); }
  } else {
    const rows = botLogs.filter(keep);
    body.innerHTML = rows.length ? rows.map(logRowHTML).join("")
      : botLogs.length ? emptyHTML("search", "没有符合条件的日志", "换个关键词或筛选条件试试")
      : emptyHTML("logs", "暂无日志", "点击左下角「运行脚本」开始，运行过程会实时显示在这里");
    body.dataset.filtered = (q || lv || range === "last") ? "1" : "0";
    paintIcons(body);
  }
  if (atBottom || !append.length) body.scrollTop = body.scrollHeight;
  // 迷你模式日志
  const ml = $("#miniLog");
  const mAt = ml.scrollHeight - ml.scrollTop - ml.clientHeight < 40;
  const src = append.length ? append : botLogs.slice(-200);
  if (!append.length) ml.innerHTML = src.length ? "" : `<div class="empty" style="padding:28px 8px"><span>暂无日志</span></div>`;
  else ml.querySelector(".empty")?.remove();
  ml.insertAdjacentHTML("beforeend", src.map(miniRowHTML).join(""));
  while (ml.children.length > 300) ml.firstChild.remove();
  if (mAt || !append.length) ml.scrollTop = ml.scrollHeight;
}
["#logSearch", "#logLevel", "#logRange"].forEach(s => $(s).addEventListener("input", () => renderBotLogs()));
$("#logClear").onclick = async () => { await api("log", { method: "DELETE" }); botLogs.length = 0; renderBotLogs(); };
$("#logExport").onclick = () => {
  if (!botLogs.length) return toast("没有可导出的日志", "warn");
  const txt = botLogs.map(f => `[${f.time}] [${LV_TEXT[f.level]}] ${f.title}${f.detail ? " — " + f.detail : ""}`).join("\r\n");
  const d = new Date(), name = `运行日志_${d.getFullYear()}${pad(d.getMonth() + 1)}${pad(d.getDate())}_${pad(d.getHours())}${pad(d.getMinutes())}${pad(d.getSeconds())}.txt`;
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob(["﻿" + txt], { type: "text/plain;charset=utf-8" }));
  a.download = name; a.click(); setTimeout(() => URL.revokeObjectURL(a.href), 3000);
};

/* ============================ 星盘 / 步骤 ============================ */
function makeBoard(el) { el.innerHTML = Array.from({ length: 9 }, () => `<span class="cell hidden"></span>`).join(""); return [...el.children]; }
const boards = [makeBoard($("#board")), makeBoard($("#miniBoard"))];
let sysCell = -1;
function renderBoard(st) {
  const res = st.result, act = st.action;
  const board = (res && res.board) || st.board || [];
  const shown = board.filter(Boolean).length;
  if (shown === 1) sysCell = board.findIndex(Boolean);
  else if (!shown) sysCell = -1;
  const live = st.running || st.status === "stopping";       // 结束后不再显示“正在翻开/正在选择”的提示
  const line = res ? (res.cells || LINES[res.line] || []) : live && act && act.action === "line" ? (LINES[act.target] || []) : [];
  const target = live && act && act.action === "reveal" ? act.target : -1;
  const idle = !shown && !st.running;
  boards.forEach((cells, k) => {
    cells[0].parentElement.classList.toggle("idle", idle);
    cells.forEach((c, i) => {
      const v = board[i] || 0;
      const cls = ["cell"];
      if (!v) cls.push("hidden");
      if (v && i === sysCell && !res) cls.push("sys");
      if (i === target) cls.push("target");
      if (line.includes(i)) cls.push(res ? "win" : "pick");
      else if (res) cls.push("dim");
      const name = cls.join(" ");
      if (c.className !== name) c.className = name;
      const txt = v ? String(v) : "";
      if (c.textContent !== txt) c.textContent = txt;
    });
  });
}
const STEPS = [["start", "启动脚本"], ["nav", "进入好运星盘"], ["page", "打开星屑占卜"], ["check", "检查剩余次数"], ["play", "按最优策略占卜"], ["back", "回到大厅"]];
let stepsKey = "";
const liveStep = { run: null, step: null };   // 前端最后一次看到的进行中步骤（check/play 会交替，steps_done 的顺序不一定是出错那步）
function renderSteps(st) {
  const done = st.steps_done || [];
  const live = st.running || st.status === "stopping";
  const ended = !live && !!st.started_at;
  if (liveStep.run !== st.started_at) { liveStep.run = st.started_at; liveStep.step = null; }
  if (live && st.step && st.step !== "end") liveStep.step = st.step;
  const last = liveStep.step || done[done.length - 1];
  const html = STEPS.map(([key, label]) => {
    let cls = "todo";
    if (live && key === st.step) cls = "cur";
    else if (ended && key === last && st.status === "error") cls = "fail";
    else if (ended && key === last && st.status === "stopped") cls = "stop";
    else if (done.includes(key)) cls = "done";
    else if (ended) cls = "skip";
    let text = label;
    if (key === "play" && cls === "cur") text = `占卜中 · 第 ${st.games + (st.result ? 0 : 1)} 局`;
    else if (key === "play" && st.games && cls !== "todo") text = `占卜 ${st.games} 局`;
    return `<li class="${cls}"><span>${text}</span></li>`;
  }).join("");
  if (html !== stepsKey) { $("#steps").innerHTML = html; stepsKey = html; }
}

/* ============================ 星屑占卜：状态 ============================ */
const STEP_TEXT = { start: "正在启动脚本", nav: "正在打开 常驻活动 → 好运星盘", page: "正在进入 星屑占卜", check: "正在检查剩余占卜次数", play: "正在按最优策略占卜", back: "正在回到大厅" };
const BOT_STATUS = { idle: ["idle", "未运行"], running: ["running", "运行中"], stopping: ["running", "正在停止"], done: ["done", "成功"], stopped: ["stopped", "已停止"], error: ["error", "失败"] };
let botState = null, lastHist = null, gameInfo = null;
function stepText(st) {
  if (st.running) {
    if (st.step === "play") {
      const n = st.games + (st.result ? 0 : 1);
      if (st.action?.action === "reveal") return `第 ${n} 局：翻开 ${cellName(st.action.target)}`;
      if (st.action?.action === "line") return `第 ${n} 局：选择 ${LINE_NAME[st.action.target]}`;
      if (st.result) return `第 ${st.games} 局完成，+${st.result.reward} 星砂`;
      return `第 ${n} 局：开始占卜`;
    }
    return STEP_TEXT[st.step] || "运行中";
  }
  if (st.status === "stopping") return "正在停止…";
  if (st.status === "done") return st.games ? `已完成 ${st.games} 局` : "已完成：没有可用次数";
  if (st.status === "stopped") return "已手动停止";
  if (st.status === "error") return st.reason || "异常停止";
  return "等待启动";
}
function captionHTML(st) {
  // 返回 [class, html]
  const live = st.running || st.status === "stopping";
  if (live && st.step === "play") {
    const n = st.games + (st.result ? 0 : 1);
    if (st.result) return ["gold", `<b>第 ${st.games} 局 +${st.result.reward} 星砂</b><span class="ev">线和 ${st.result.total ?? "—"}</span>`];
    if (st.action?.action === "reveal") return ["", `<b>第 ${n} 局</b><span>翻开 ${cellName(st.action.target)}</span><span class="ev">期望 ${st.action.ev}</span>`];
    if (st.action?.action === "line") return ["", `<b>第 ${n} 局</b><span>选择 ${LINE_NAME[st.action.target]}</span><span class="ev">期望 ${st.action.ev}</span>`];
    return ["", `<b>第 ${n} 局</b><span>开始占卜</span>`];
  }
  if (live) return ["", `<span>${esc(stepText(st))}</span>`];
  if (st.status === "error") return ["error", `<b>异常停止</b><span>${esc(st.reason || "详见运行日志")}</span>`];
  if (st.status === "stopped") return ["warn", `<b>已手动停止</b><span>完成 ${st.games} 局</span>`];
  if (st.status === "done") return st.result ? ["gold", `<b>${esc(stepText(st))}</b><span class="ev">最后一局 +${st.result.reward}</span>`] : ["", `<b>${esc(stepText(st))}</b>`];
  return ["", `<span>${lastHist ? "等待启动 · 上次运行结果见上方" : "等待启动 · 先登录游戏并停在大厅"}</span>`];
}
function setRunButtons(running) {
  [["#runBig", "停止运行", "运行脚本"], ["#miniRun", "停止运行", "运行脚本"]].forEach(([sel, on, off]) => {
    const b = $(sel); b.querySelector("span").textContent = running ? on : off; setIcon(b.querySelector("i"), running ? "stop" : "play");
  });
  $("#runSplit").classList.toggle("running", running);
  $("#miniSplit").classList.toggle("running", running);
  $("#tagBot").hidden = !running;
  setCfgDisabled(running);
}
function renderBot(st) {
  const prev = botState; botState = st;
  const running = st.running || st.status === "stopping";
  if (!prev || running !== (prev.running || prev.status === "stopping")) setRunButtons(running);
  const [cls, label] = BOT_STATUS[st.status] || ["idle", st.status];
  const games = st.started_at ? st.games : (lastHist?.games ?? 0), dust = st.started_at ? st.dust : (lastHist?.dust ?? 0);
  // 状态行：本次会话没有运行过时，显示最近一条历史记录（主界面与迷你模式一致）
  let pill, timer, meta;
  if (st.started_at) {
    pill = statusPill(cls, label); timer = fmtClock(st.elapsed);
    meta = `开始 ${fmtTs(st.started_at)}` + (running ? " · 运行中" : ` · 结束 ${fmtHms(st.ended_at)} · 用时 ${fmtDur(st.elapsed)}`);
  } else if (lastHist) {
    const [hc, hl] = BOT_STATUS[lastHist.status] || ["idle", lastHist.status];
    pill = statusPill(hc, "上次：" + hl); timer = fmtClock(lastHist.duration);
    meta = `上次运行 ${lastHist.time} · 用时 ${fmtDur(lastHist.duration)}`;
  } else {
    pill = statusPill("idle", "未运行"); timer = fmtClock(0); meta = "尚未运行过脚本";
  }
  const avg = games ? Math.round(dust / games) : "—";
  setHTML("#rStatus", pill); setText("#rTimer", timer); setText("#rMeta", meta);
  $("#rTimer").classList.toggle("dim", !running);
  setHTML("#iGames", `${games}<small>局</small>`);
  setText("#iDust", fmtNum(dust));
  setText("#iAvg", avg);
  const [ccls, chtml] = captionHTML(st);
  const cap = $("#iStep"); cap.className = "caption" + (ccls ? " " + ccls : ""); if (cap.innerHTML !== chtml) cap.innerHTML = chtml;
  renderBoard(st);
  renderSteps(st);
  renderRunHint();
  // 迷你模式
  setHTML("#miniStatus", pill); setText("#miniTime", timer);
  $("#miniTime").classList.toggle("dim", !running);
  setText("#miniStep", stepText(st));
  setText("#miniGames", games); setText("#miniDust", fmtNum(dust)); setText("#miniAvg", avg);
  // 结束通知
  if (prev && (prev.running || prev.status === "stopping") && !st.running && st.status !== "stopping") {
    if (st.status === "done") { notify("success", "脚本执行完成", `${st.games} 局，获得 ${st.dust} 星砂`); toast(`运行完成：${st.games} 局，${st.dust} 星砂`, "success"); }
    else if (st.status === "stopped") { notify("warn", "脚本已停止", `${st.games} 局，获得 ${st.dust} 星砂`); toast("已停止", "warn"); }
    else { notify("error", "脚本异常停止", st.reason || "详见运行日志"); toast("脚本异常停止，详见日志", "error"); }
    loadHistory();
  }
}
function renderRunHint() {
  const running = botState && (botState.running || botState.status === "stopping");
  const set = (el, cls, html) => { el.className = "foot-hint" + (cls ? " " + cls : ""); el.innerHTML = `<span class="dot"></span><span>${html}</span>`; };
  const g = gameInfo;
  const gameHTML = !g ? ["", "正在检测游戏…"] : !g.found ? ["bad", "未检测到游戏：请先启动 300英雄 并登录到大厅"]
    : g.admin ? ["bad", "游戏以管理员身份运行，点击会被拦截：请以管理员身份运行本程序"]
    : g.minimized ? ["warn", "游戏已最小化，运行时会自动还原"] : ["ok", `游戏已连接 · 窗口 ${g.width}×${g.height}`];
  set($("#runHint"), ...(running ? ["run", "运行中请勿操作鼠标 · 按 <kbd>F12</kbd> 立即停止"] : gameHTML));
  const recOn = recState && (recState.running || recState.status === "stopping");
  set($("#recHint"), ...(recOn ? ["run", "正在录制游戏窗口 · 按 <kbd>F10</kbd> 停止"] : gameHTML));
}

/* ============================ 运行控制 ============================ */
const segVal = el => el.querySelector("button.on")?.dataset.v;
const clampTimeout = v => { v = parseFloat(v); return Number.isFinite(v) ? Math.max(1, Math.min(60, v)) : 5; };
function cfgFromForm() {
  const g = segVal($("#cfgGames"));
  return { games: g != null ? +g : (cfg?.games ?? 0), timeout: clampTimeout($("#cfgTimeout").value),
           close_after: (segVal($("#cfgClose")) ?? (cfg?.close_after ? "1" : "0")) === "1" };
}
let runBusy = false;
async function toggleRun(override) {
  if (runBusy) return; runBusy = true;
  $("#runSplit").classList.add("busy");
  try {
    const st = await api("state");
    if (st.running) { toast("正在停止…"); await api("stop", { method: "POST" }); }
    else {
      lastRunSeq = botSeq + 1;
      // 一次性运行方式（只跑 1 局 / 只打开页面）带 once 标记，后端不会把它存成配置
      const body = { ...cfgFromForm(), ...(override || {}), once: !!override };
      const r = await api("start", { method: "POST", body });
      toast(r.ok ? "已启动，运行期间请勿操作鼠标" : "脚本已在运行", r.ok ? "info" : "warn");
    }
  } catch (e) { toast("无法连接界面服务", "error"); }
  finally { runBusy = false; $("#runSplit").classList.remove("busy"); }
  pollBot();
}
$("#runBig").onclick = () => toggleRun();
$("#miniRun").onclick = () => toggleRun();
$$("[data-run]").forEach(b => b.onclick = () => {
  closeMenus();
  toggleRun(b.dataset.run === "one" ? { games: 1 } : { games: 0, close_after: false, nav_only: true });
});

/* ============================ 配置 ============================ */
let cfg = null;
const setSeg = (el, v) => el.querySelectorAll("button[data-v]").forEach(b => b.classList.toggle("on", b.dataset.v === String(v)));
function bindSeg(el, fn) {
  el.addEventListener("click", e => {
    const b = e.target.closest("button[data-v]");
    if (!b || b.disabled || b.classList.contains("on")) return;
    setSeg(el, b.dataset.v); fn(b.dataset.v);
  });
}
function bindStepper(box, fn) {
  const input = box.querySelector("input");
  box.addEventListener("click", e => {
    const b = e.target.closest("[data-step]"); if (!b || b.disabled) return;
    input.value = clampTimeout((+input.value || 0) + +b.dataset.step); fn(+input.value);
  });
  input.addEventListener("change", () => { input.value = clampTimeout(input.value); fn(+input.value); });
}
function setCfgDisabled(on) {
  $$("#cfgGames button, #cfgClose button, [data-stepper=cfgTimeout] button, #cfgTimeout").forEach(el => el.disabled = on);
}
function setRecDisabled(on) {
  $$("#recFps button, #recKeys").forEach(el => el.disabled = on);
}
const FPS_NOTE = { 5: "每秒 5 帧，最省空间，适合长时间录制", 8: "每秒 8 帧，画面与文件大小均衡", 12: "每秒 12 帧，动作更连贯", 20: "每秒 20 帧，最流畅，文件最大" };
function writeCfg(c) {
  cfg = c;
  [$("#cfgGames"), $("#sGames")].forEach(el => setSeg(el, c.games));
  [$("#cfgClose"), $("#sClose")].forEach(el => setSeg(el, c.close_after ? "1" : "0"));
  $("#cfgTimeout").value = c.timeout; $("#sTimeout").value = c.timeout;
  [$("#recFps"), $("#sRecFps")].forEach(el => setSeg(el, c.rec_fps));
  $("#recKeys").checked = $("#sRecKeys").checked = !!c.rec_keys;
  $("#recKeysText").textContent = c.rec_keys ? "记录" : "不记录";
  $("#recFpsNote").textContent = FPS_NOTE[c.rec_fps] || `每秒 ${c.rec_fps} 帧`;
  renderViewfinder();
}
async function saveCfg(patch) {
  try { writeCfg(await api("config", { method: "POST", body: patch })); }
  catch (e) { toast("保存失败：无法连接界面服务", "error"); return; }
  $$("[data-saved]").forEach(t => t.classList.add("show"));
  clearTimeout(saveCfg.t); saveCfg.t = setTimeout(() => $$("[data-saved]").forEach(t => t.classList.remove("show")), 1500);
}
bindSeg($("#cfgGames"), v => saveCfg({ games: +v }));
bindSeg($("#sGames"), v => saveCfg({ games: +v }));
bindSeg($("#cfgClose"), v => saveCfg({ close_after: v === "1" }));
bindSeg($("#sClose"), v => saveCfg({ close_after: v === "1" }));
bindStepper($("[data-stepper=cfgTimeout]"), v => saveCfg({ timeout: v }));
bindStepper($("[data-stepper=sTimeout]"), v => saveCfg({ timeout: v }));
bindSeg($("#recFps"), v => saveCfg({ rec_fps: +v }));
bindSeg($("#sRecFps"), v => saveCfg({ rec_fps: +v }));
$("#recKeys").onchange = () => saveCfg({ rec_keys: $("#recKeys").checked });
$("#sRecKeys").onchange = () => saveCfg({ rec_keys: $("#sRecKeys").checked });

/* ============================ 运行记录 / 统计 ============================ */
const H_STATUS = s => BOT_STATUS[s] || ["idle", s];
function runRowHTML(r) {
  const [c, l] = H_STATUS(r.status);
  const res = r.results || [];
  const note = res.length ? res.join(" / ") : (r.reason || "—");
  const detail = res.length ? `<span class="chips">${res.map(v => `<span class="chip ${chipCls(v)}">${v}</span>`).join("")}</span>` : `<span class="note">${esc(r.reason || "—")}</span>`;
  return `<div class="grow-r"><span class="t-main">${esc(r.time)}</span><span>${statusPill(c, l, true)}</span><span class="t-num r">${r.games}</span>
    <span class="t-gold r">${fmtNum(r.dust)}</span><span class="c-dur">${fmtDur(r.duration)}</span><span title="${esc(note)}">${detail}</span></div>`;
}
async function loadHistory() {
  let h;
  try { h = await api("history"); } catch (e) { return; }
  lastHist = h[h.length - 1] || null;
  const games = h.reduce((a, r) => a + r.games, 0), dust = h.reduce((a, r) => a + r.dust, 0);
  const ok = h.filter(r => r.status === "done").length, bad = h.filter(r => r.status === "error").length;
  $("#metaLast").textContent = lastHist ? lastHist.time : "—";
  $("#metaRuns").textContent = h.length;
  $("#metaDust").textContent = fmtNum(dust);
  $("#runsCount").textContent = h.length;
  $("#hMetaCount").textContent = `${h.length} 条`;
  $("#clearHist").disabled = !h.length;
  const rows = h.slice().reverse().slice(0, 300).map(runRowHTML).join("");
  $("#runsBody").innerHTML = rows || emptyHTML("inbox", "还没有运行记录", "每次运行结束后都会自动记录在这里");
  $("#histBody").innerHTML = rows || emptyHTML("inbox", "还没有运行记录", "去「星屑占卜」页运行一次脚本吧");
  paintIcons($("#runsBody")); paintIcons($("#histBody"));
  const avg = games ? Math.round(dust / games) : null;
  const kpi = (ic, label, v, unit, sub, tone = "") => `<div class="kpi ${tone}"><span><i data-ic="${ic}"></i>${label}</span><b>${v}${unit ? `<small>${unit}</small>` : ""}</b><em>${sub}</em></div>`;
  $("#kpis").innerHTML =
    kpi("filetext", "累计运行", h.length, "次", h.length ? `成功 ${ok} · 失败 ${bad} · 停止 ${h.length - ok - bad}` : "暂无记录")
    + kpi("layers", "累计占卜", fmtNum(games), "局", lastHist ? `上次 ${lastHist.time.slice(5, 16)}` : "—")
    + kpi("gem", "累计星砂", fmtNum(dust), "", h.length ? `单次最多 ${fmtNum(Math.max(...h.map(r => r.dust)))}` : "—", "gold")
    + kpi("chart", "平均每局", avg ?? "—", avg != null ? "星砂" : "", avg == null ? "理论期望约 178" : `理论期望约 178 · <span class="${avg >= 178 ? "up" : "down"}">${avg >= 178 ? "高于" : "低于"}期望</span>`);
  paintIcons($("#kpis"));
  drawChart(h);
  drawDist(h);
  if (botState) renderBot(botState);
}
function drawChart(h) {
  const days = [], byDay = {}, runsDay = {};
  h.forEach(r => { const d = r.time.slice(0, 10); byDay[d] = (byDay[d] || 0) + r.dust; runsDay[d] = (runsDay[d] || 0) + 1; });
  for (let i = 13; i >= 0; i--) { const t = new Date(Date.now() - i * 864e5); days.push(`${t.getFullYear()}-${pad(t.getMonth() + 1)}-${pad(t.getDate())}`); }
  if (!days.some(d => byDay[d])) { $("#chart").innerHTML = `<div class="bars-empty">近 14 天没有运行记录</div>`; return; }
  const max = Math.max(100, ...days.map(d => byDay[d] || 0));
  $("#chart").innerHTML = `<div class="bars">${days.map((d, i) => {
    const v = byDay[d] || 0;
    return `<div class="bar-col${i === 13 ? " today" : ""}" title="${d} · ${v ? `${fmtNum(v)} 星砂 · ${runsDay[d]} 次运行` : "没有运行"}">
      <div class="bar-area">${v ? `<span class="bar-val">${v >= 10000 ? (v / 1000).toFixed(1) + "k" : v}</span>` : ""}<span class="bar" style="height:${v ? Math.max(3, v / max * 100 * .82) : 0}%"></span></div>
      <span class="bar-x">${i === 13 ? "今天" : i % 2 === 1 ? d.slice(5) : ""}</span></div>`;
  }).join("")}</div>`;
}
function drawDist(h) {
  const cnt = {};
  h.forEach(r => (r.results || []).forEach(v => cnt[v] = (cnt[v] || 0) + 1));
  const total = Object.values(cnt).reduce((a, b) => a + b, 0);
  $("#distTotal").textContent = total ? `共 ${total} 局` : "";
  if (!total) { $("#dist").innerHTML = `<div class="bars-empty">暂无数据</div>`; return; }
  const vals = Object.keys(cnt).map(Number).sort((a, b) => b - a);
  const max = Math.max(...Object.values(cnt));
  $("#dist").innerHTML = vals.map(v => `<div class="dist-row ${chipCls(v)}"><span class="chip ${chipCls(v)}">${v}</span>
    <div class="dist-track"><span style="width:${cnt[v] / max * 100}%"></span></div><span class="dn">${cnt[v]} 局<small>${Math.round(cnt[v] / total * 100)}%</small></span></div>`).join("");
}
$("#clearHist").onclick = async () => {
  if (await confirmBox("清空全部运行记录？", "运行记录和统计数据会被删除，清空后无法恢复。", "清空")) {
    await api("history", { method: "DELETE" }); loadHistory(); toast("运行记录已清空");
  }
};

/* ============================ 操作录制 ============================ */
const REC_STATUS = { idle: ["idle", "未录制"], recording: ["rec", "录制中"], paused: ["stopped", "已暂停"], stopping: ["running", "正在保存"], done: ["done", "已保存"], error: ["error", "录制失败"] };
const recLogs = [];
let recSeq = 0, recState = null, recName = null;
function renderViewfinder() {
  const r = recState, on = r && r.status === "recording", paused = r && r.status === "paused";
  const vf = $("#vf");
  vf.classList.toggle("on", !!on); vf.classList.toggle("paused", !!paused);
  $("#vfRec").textContent = on ? "REC" : paused ? "PAUSED" : r && r.status === "stopping" ? "SAVING" : "STANDBY";
  $("#vfRes").textContent = gameInfo?.found && !gameInfo.minimized ? `${gameInfo.width}×${gameInfo.height}` : gameInfo?.found ? "MINIMIZED" : "NO SIGNAL";
  if (cfg) { $("#vfFps").textContent = `${cfg.rec_fps} FPS`; $("#vfKeys").textContent = cfg.rec_keys ? "KEYS ON" : "KEYS OFF"; }
}
function renderRec(r) {
  const prev = recState; recState = r;
  const on = r.running || r.status === "stopping";
  if (!prev || on !== (prev.running || prev.status === "stopping")) {
    const b = $("#recBig");
    b.querySelector("span").textContent = on ? "停止录制" : "开始录制";
    setIcon(b.querySelector("i"), on ? "stop" : "recdot");
    $("#recSplit").classList.toggle("running", on);
    $("#tagRec").hidden = !on;
    setRecDisabled(on);
  }
  const [c, l] = REC_STATUS[r.status] || ["idle", r.status];
  $("#recStatus").innerHTML = statusPill(c, l);
  $("#recTimer").textContent = fmtClock2(r.started_at ? r.elapsed : 0);
  $("#recStart").textContent = fmtHms(r.started_at);
  $("#recStart").title = r.started_at ? fmtTs(r.started_at) : "";
  $("#recClicks").textContent = r.clicks;
  $("#recKeysN").textContent = r.keys;
  const out = $("#recOut");
  out.disabled = !r.name;
  out.innerHTML = r.name ? `${esc(r.name)}<i data-ic="external"></i>` : "—";
  paintIcons(out);
  out.onclick = () => r.name && openTarget("rec", r.name);
  renderViewfinder();
  renderRunHint();
  if (r.running && r.name && r.name !== recName) loadRecList();
  recName = r.name;
  if (prev && (prev.running || prev.status === "stopping") && !r.running && r.status !== "stopping") {
    if (r.status === "done") { notify("success", "录像已保存", `${r.clicks} 次点击，${r.keys} 次按键`); toast("录像已保存", "success"); }
    else { notify("error", "录制失败", r.reason || "详见录制日志"); toast("录制失败，详见录制日志", "error"); }
    loadRecList();
  }
}
function renderRecLogs(lines) {
  const body = $("#recLogBody");
  const f = lines.map(fmtLog); recLogs.push(...f);
  const at = body.scrollHeight - body.scrollTop - body.clientHeight < 40;
  if (!recLogs.length) { body.innerHTML = emptyHTML("logs", "暂无录制日志", "开始录制后，点击和按键会实时记录在这里"); paintIcons(body); return; }
  body.querySelector(".empty")?.remove();
  body.insertAdjacentHTML("beforeend", f.map(logRowHTML).join(""));
  if (at) body.scrollTop = body.scrollHeight;
}
async function loadRecList() {
  let list;
  try { list = await api("rec/list"); } catch (e) { return; }
  $("#recMetaCount").textContent = list.length;
  $("#recCount").textContent = list.length;
  $("#recMetaSize").textContent = fmtSize(list.reduce((a, x) => a + x.size, 0));
  $("#recBody").innerHTML = list.length ? list.map(x => {
    const when = x.start ? x.start.replace("T", " ") : x.name.replace(/^(\d{4})(\d\d)(\d\d)_(\d\d)(\d\d)(\d\d)$/, "$1-$2-$3 $4:$5:$6");
    const acts = x.live ? `<span class="acts">${statusPill("rec", "录制中", true)}</span>` : `<span class="acts">
      <button class="btn ghost" data-rec-open="rec_steps" data-name="${esc(x.name)}" title="打开 steps.md">步骤</button>
      <button class="btn ghost" data-rec-open="rec" data-name="${esc(x.name)}" title="打开录像文件夹">文件夹</button>
      <button class="btn ghost icon danger-hover" data-rec-del="${esc(x.name)}" title="删除录像"><i data-ic="trash"></i></button></span>`;
    return `<div class="grow-r ${x.live ? "live" : ""}"><span class="t-main">${esc(when)}${x.complete || x.live ? "" : `<em class="badge">未完成</em>`}</span>
      <span class="t-num">${x.duration != null ? fmtClock(x.duration) : "—"}</span><span class="t-num r">${x.clicks ?? "—"}</span><span class="t-num r">${x.keys ?? "—"}</span>
      <span class="t-num r c-size">${fmtSize(x.size)}</span>${acts}</div>`;
  }).join("") : emptyHTML("video", "还没有录像", "点击左下角「开始录制」录制游戏操作");
  paintIcons($("#recBody"));
}
$("#recBody").addEventListener("click", async e => {
  const o = e.target.closest("[data-rec-open]"), d = e.target.closest("[data-rec-del]");
  if (o) openTarget(o.dataset.recOpen, o.dataset.name);
  else if (d && await confirmBox("删除这个录像？", `录像 ${d.dataset.recDel} 的视频、截图和步骤清单会被删除，删除后无法恢复。`, "删除")) {
    const r = await api("rec/list?name=" + encodeURIComponent(d.dataset.recDel), { method: "DELETE" });
    if (r.ok === false) toast(r.msg, "warn"); else { loadRecList(); toast("录像已删除"); }
  }
});
let recBusy = false;
async function toggleRec() {
  if (recBusy) return; recBusy = true;
  $("#recSplit").classList.add("busy");
  try {
    const r = await api("rec/state");
    if (r.running) { toast("正在保存录像…"); await api("rec/stop", { method: "POST" }); }
    else {
      const x = await api("rec/start", { method: "POST", body: { rec_fps: +(segVal($("#recFps")) || cfg?.rec_fps || 8), rec_keys: $("#recKeys").checked } });
      toast(x.ok ? "开始录制游戏窗口" : "已经在录制", x.ok ? "info" : "warn");
    }
  } catch (e) { toast("无法连接界面服务", "error"); }
  finally { recBusy = false; $("#recSplit").classList.remove("busy"); }
  pollRec();
}
$("#recBig").onclick = toggleRec;

/* ============================ 游戏连接 ============================ */
async function pollGame() {
  try {
    const g = await api("game");
    gameInfo = g;
    const card = $("#gameCard");
    const tone = !g.found || g.admin ? "bad" : g.minimized ? "warn" : "ok";
    card.className = "conn " + tone;
    $("#gcSub").textContent = !g.found ? "未启动" : g.admin ? "管理员权限 · 点击会被拦截" : g.minimized ? "已最小化 · 运行时自动还原" : `已连接 · ${g.width}×${g.height}`;
    card.title = !g.found ? "请先启动 300英雄 并登录到大厅" : g.admin ? "游戏以管理员身份运行：请右键 300HeroAuto.exe 选择“以管理员身份运行”" : "已找到 300英雄 窗口";
    $("#miniGameDot").className = "dot " + tone;
    $("#miniGameText").textContent = !g.found ? "游戏未启动" : g.admin ? "游戏是管理员权限，点击会被拦截" : g.minimized ? "游戏已最小化" : `游戏已连接 · ${g.width}×${g.height}`;
    renderRunHint();
    renderViewfinder();
  } catch (e) { }
}

/* ============================ 迷你模式 ============================ */
function setCompact(on) {
  closeMenus();
  document.body.classList.toggle("compact", on);
  if (window.desktop) window.desktop.win(on ? "compact" : "full");
  requestAnimationFrame(() => { const m = $("#miniLog"); m.scrollTop = m.scrollHeight; });
}
$("#compactBtn").onclick = () => setCompact(true);
$("#expandBtn").onclick = () => setCompact(false);

/* ============================ 奖励表 ============================ */
const PAYOUT = { 6: 500, 7: 500, 8: 150, 9: 100, 10: 50, 11: 30, 12: 20, 13: 20, 14: 10, 15: 10, 16: 10, 17: 20, 18: 20, 19: 30, 20: 50, 21: 100, 22: 150, 23: 500, 24: 500 };
$("#payGrid").innerHTML = Object.entries(PAYOUT).map(([s, v]) => `<span class="${v >= 500 ? "hi" : v >= 100 ? "mid" : ""}"><b>${s}</b>${v}</span>`).join("");

/* ============================ 轮询 ============================ */
let pollingBot = false, pollingRec = false;
async function pollBot() {
  if (pollingBot) return; pollingBot = true;
  try {
    const [st, lines] = await Promise.all([api("state"), api("log?since=" + botSeq)]);
    const f = lines.map(fmtLog);
    for (const l of lines) botSeq = Math.max(botSeq, l.seq);
    botLogs.push(...f);
    if (botLogs.length > 3000) botLogs.splice(0, botLogs.length - 3000);
    if (f.length) renderBotLogs(f);
    renderBot(st);
  } catch (e) { } finally { pollingBot = false; }
}
async function pollRec() {
  if (pollingRec) return; pollingRec = true;
  try {
    const [r, lines] = await Promise.all([api("rec/state"), api("rec/log?since=" + recSeq)]);
    for (const l of lines) recSeq = Math.max(recSeq, l.seq);
    if (lines.length) renderRecLogs(lines);
    renderRec(r);
  } catch (e) { } finally { pollingRec = false; }
}

/* ============================ 启动 ============================ */
showPage("home");
paintIcons();
renderBotLogs();
renderRecLogs([]);
api("config").then(writeCfg);
loadHistory();
loadRecList();
pollBot(); pollRec(); pollGame();
setInterval(pollBot, 600);
setInterval(pollRec, 800);
setInterval(pollGame, 3000);
