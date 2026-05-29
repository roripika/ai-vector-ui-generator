const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const chokidar = require('chokidar');
const { exec } = require('child_process')
const fs = require('fs');
const os = require('os');

let mainWindow;
let watcher;
let currentJsonFile = null;
let currentWorkspaceDir = null;
const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'vector-ui-viewer-'));

// プロジェクトのルートディレクトリ (Pythonの実行場所)
const projectRoot = path.resolve(__dirname, '..');

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1400,
        height: 900,
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            contextIsolation: true,
            nodeIntegration: false
        }
    });

    mainWindow.loadFile('index.html');
    // mainWindow.webContents.openDevTools();
}

app.whenReady().then(() => {
    createWindow();

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow();
        }
    });

    // コマンドライン引数でファイル指定があれば開く
    const args = process.argv.slice(2);
    if (args.length > 0) {
        let target = path.resolve(args[args.length - 1]);
        if (fs.existsSync(target)) {
            if (fs.statSync(target).isDirectory()) {
                openWorkspace(target);
            } else if (target.endsWith('.json')) {
                watchFile(target);
            }
        }
    }
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('quit', () => {
    if (watcher) watcher.close();
    fs.rmSync(tempDir, { recursive: true, force: true });
});

// ===== ワークスペース操作 =====

ipcMain.handle('open-workspace-dialog', async () => {
    const { canceled, filePaths } = await dialog.showOpenDialog(mainWindow, {
        properties: ['openDirectory'],
        title: 'ワークスペースフォルダを選択'
    });
    if (!canceled && filePaths.length > 0) {
        openWorkspace(filePaths[0]);
        return filePaths[0];
    }
    return null;
});

ipcMain.handle('open-file-dialog', async () => {
    const { canceled, filePaths } = await dialog.showOpenDialog(mainWindow, {
        properties: ['openFile'],
        filters: [{ name: 'JSON', extensions: ['json'] }]
    });
    if (!canceled && filePaths.length > 0) {
        watchFile(filePaths[0]);
        return filePaths[0];
    }
    return null;
});

ipcMain.handle('list-json-files', async () => {
    if (!currentWorkspaceDir) return [];
    return getJsonFiles(currentWorkspaceDir);
});

ipcMain.handle('select-file', async (_event, filePath) => {
    if (fs.existsSync(filePath)) {
        watchFile(filePath);
    }
});

// ===== ワークスペース内部処理 =====

function getJsonFiles(dirPath) {
    const results = [];
    const items = fs.readdirSync(dirPath, { withFileTypes: true });
    for (const item of items) {
        if (item.isFile() && item.name.endsWith('.json')) {
            results.push({
                name: item.name,
                fullPath: path.join(dirPath, item.name),
                relativePath: item.name
            });
        } else if (item.isDirectory() && !item.name.startsWith('.') && item.name !== 'node_modules') {
            // サブフォルダも再帰的に探索
            const sub = getJsonFiles(path.join(dirPath, item.name));
            for (const s of sub) {
                results.push({
                    name: s.name,
                    fullPath: s.fullPath,
                    relativePath: path.join(item.name, s.relativePath)
                });
            }
        }
    }
    return results;
}

function openWorkspace(dirPath) {
    currentWorkspaceDir = dirPath;
    const files = getJsonFiles(dirPath);
    mainWindow.webContents.send('workspace-opened', { dir: dirPath, files });

    // ワークスペースフォルダ全体をウォッチして、ファイル追加・削除を検知
    if (watcher) watcher.close();
    watcher = chokidar.watch(dirPath, {
        persistent: true,
        ignoreInitial: true,
        ignored: /node_modules|\.git/
    });

    watcher.on('add', (fp) => {
        if (fp.endsWith('.json')) {
            const updatedFiles = getJsonFiles(dirPath);
            mainWindow.webContents.send('workspace-files-updated', updatedFiles);
        }
    });
    watcher.on('unlink', (fp) => {
        if (fp.endsWith('.json')) {
            const updatedFiles = getJsonFiles(dirPath);
            mainWindow.webContents.send('workspace-files-updated', updatedFiles);
        }
    });
    watcher.on('change', (fp) => {
        if (fp.endsWith('.json') && fp === currentJsonFile) {
            renderSvg();
        }
    });
}

function watchFile(filePath) {
    currentJsonFile = filePath;
    mainWindow.webContents.send('file-loaded', currentJsonFile);
    renderSvg();
}

function renderSvg() {
    if (!currentJsonFile) return;

    mainWindow.webContents.send('render-start');

    const cmd = `source .venv/bin/activate && python -m src.cli render --in "${currentJsonFile}" --out "${tempDir}" --only svg`;

    exec(cmd, { cwd: projectRoot, shell: '/bin/bash' }, (error, stdout, stderr) => {
        if (error) {
            console.error(`Render Error: ${error.message}`);
            mainWindow.webContents.send('render-error', stderr || error.message);
            return;
        }

        const stem = path.basename(currentJsonFile, '.json');
        const svgPath = path.join(tempDir, `${stem}.svg`);

        if (fs.existsSync(svgPath)) {
            const svgContent = fs.readFileSync(svgPath, 'utf8');
            mainWindow.webContents.send('render-success', svgContent);
        } else {
            mainWindow.webContents.send('render-error', `SVG file not found at ${svgPath}. Output: ${stdout}`);
        }
    });
}
