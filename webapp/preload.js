// 只向页面暴露窗口控制（最小化 / 最大化 / 关闭），不暴露 Node 能力
const { contextBridge, ipcRenderer } = require('electron');
contextBridge.exposeInMainWorld('desktop', {
  win: cmd => ipcRenderer.send('win', cmd),
});
