'use strict';
const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const fs   = require('fs');
let chokidar;
try { chokidar = require('chokidar'); } catch(e) { chokidar = null; }

// ======================================================
// ウィンドウ作成
// ======================================================
function createWindow() {
  const win = new BrowserWindow({
    width: 1440,
    height: 900,
    minWidth: 900,
    minHeight: 600,
    title: 'UI Layout Editor',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });
  win.loadFile('index.html');
}

app.whenReady().then(() => {
  createWindow();
  app.on('activate', () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
});
app.on('window-all-closed', () => { if (process.platform !== 'darwin') app.quit(); });

// ======================================================
// ワークスペース管理
// ======================================================
let workspaceDir   = null;
let workspaceWatch = null;

function getJsonFiles(dirPath) {
  try {
    return fs.readdirSync(dirPath)
      .filter(f => f.endsWith('.json') && !f.startsWith('.'))
      .map(f => ({ name: f, fullPath: path.join(dirPath, f), relativePath: f }));
  } catch (e) { return []; }
}

ipcMain.handle('open-workspace-dialog', async () => {
  const { canceled, filePaths } = await dialog.showOpenDialog({ properties: ['openDirectory'] });
  if (canceled || !filePaths.length) return;
  workspaceDir = filePaths[0];

  const win = BrowserWindow.getAllWindows()[0];
  win.webContents.send('workspace-opened', { dir: workspaceDir, files: getJsonFiles(workspaceDir) });

  // ファイル監視
  if (workspaceWatch) workspaceWatch.close();
  if (chokidar) {
    workspaceWatch = chokidar.watch(workspaceDir, { depth: 0, ignoreInitial: true });
    workspaceWatch.on('all', () => {
      win.webContents.send('workspace-files-updated', getJsonFiles(workspaceDir));
    });
  }
});

// ======================================================
// ファイル操作 IPC
// ======================================================

// JSON読み込み
ipcMain.handle('read-json-file', async (_e, filePath) => {
  if (!filePath || !fs.existsSync(filePath)) return null;
  try { return JSON.parse(fs.readFileSync(filePath, 'utf8')); }
  catch (e) { return null; }
});

// 新規ファイル作成
ipcMain.handle('new-file', async (_e, dir, fileName) => {
  if (!dir || !fileName) return { success: false, error: 'invalid args' };
  const filePath = path.join(dir, fileName);
  if (fs.existsSync(filePath)) return { success: false, error: 'already exists' };
  const empty = {
    version: '0.4.0',
    assetType: 'screen',
    metadata: { name: fileName.replace('.json', '') },
    canvas: { width: 1280, height: 720 },
    components: [],
    instances: [],
  };
  try {
    fs.writeFileSync(filePath, JSON.stringify(empty, null, 2), 'utf8');
    return { success: true, filePath };
  } catch (e) { return { success: false, error: e.message }; }
});

// 上書き保存
ipcMain.handle('save-file', async (_e, filePath, jsonData) => {
  if (!filePath) return { success: false, error: 'no path' };
  try {
    fs.writeFileSync(filePath, JSON.stringify(jsonData, null, 2), 'utf8');
    return { success: true };
  } catch (e) { return { success: false, error: e.message }; }
});

// Export JSON（名前をつけて保存）
ipcMain.handle('export-json', async (_e, defaultDir, jsonData) => {
  const { canceled, filePath } = await dialog.showSaveDialog({
    title: 'JSON をエクスポート',
    defaultPath: path.join(defaultDir || app.getPath('documents'), 'ui_layout.json'),
    filters: [{ name: 'JSON', extensions: ['json'] }],
  });
  if (canceled || !filePath) return { success: false };
  try {
    fs.writeFileSync(filePath, JSON.stringify(jsonData, null, 2), 'utf8');
    return { success: true, filePath };
  } catch (e) { return { success: false, error: e.message }; }
});
