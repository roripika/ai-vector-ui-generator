const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const chokidar = require('chokidar');
const { exec } = require('child_process');
const fs = require('fs');
const os = require('os');

let mainWindow;
let watcher;
let currentJsonFile = null;
const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'vector-ui-viewer-'));

// プロジェクトのルートディレクトリ (Pythonの実行場所)
const projectRoot = path.resolve(__dirname, '..');

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1280,
        height: 800,
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

    // Check command line args (skip electron binary and script path)
    const args = process.argv.slice(2);
    if (args.length > 0) {
        let target = path.resolve(args[args.length - 1]);
        if (fs.existsSync(target) && target.endsWith('.json')) {
            watchFile(target);
        }
    }
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('quit', () => {
    // クリーンアップ
    if (watcher) watcher.close();
    fs.rmSync(tempDir, { recursive: true, force: true });
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

function watchFile(filePath) {
    if (watcher) {
        watcher.close();
    }
    
    currentJsonFile = filePath;
    console.log(`Watching file: ${currentJsonFile}`);
    
    // UIをロード状態にする
    mainWindow.webContents.send('file-loaded', currentJsonFile);
    
    // 初回レンダリング
    renderSvg();

    // 監視設定
    watcher = chokidar.watch(currentJsonFile, { persistent: true });
    watcher.on('change', () => {
        console.log(`File changed: ${currentJsonFile}`);
        renderSvg();
    });
}

function renderSvg() {
    if (!currentJsonFile) return;

    mainWindow.webContents.send('render-start');

    // Python環境を使ってSVGを生成
    // 出力先を一時ディレクトリにする
    const cmd = `source .venv/bin/activate && python -m src.cli render --in "${currentJsonFile}" --out "${tempDir}" --only svg`;
    
    exec(cmd, { cwd: projectRoot, shell: '/bin/bash' }, (error, stdout, stderr) => {
        if (error) {
            console.error(`Render Error: ${error.message}`);
            mainWindow.webContents.send('render-error', stderr || error.message);
            return;
        }

        // 一時ディレクトリから生成されたSVGを読み込む
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
