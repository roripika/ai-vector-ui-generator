const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('api', {
    // ワークスペース
    openWorkspaceDialog: () => ipcRenderer.invoke('open-workspace-dialog'),
    setWorkspaceDir: (dir) => ipcRenderer.invoke('set-workspace-dir', dir),
    onWorkspaceOpened: (callback) => ipcRenderer.on('workspace-opened', (_event, data) => callback(data)),
    onWorkspaceFilesUpdated: (callback) => ipcRenderer.on('workspace-files-updated', (_event, files) => callback(files)),

    // 画像アセット
    listImageAssets: (dir) => ipcRenderer.invoke('list-image-assets', dir),
    selectAssetDir: () => ipcRenderer.invoke('select-asset-dir'),

    // ファイル操作
    selectFile: (dir) => ipcRenderer.invoke('select-file', dir),
    readJsonFile: (filePath) => ipcRenderer.invoke('read-json-file', filePath),
    newFile: (dir, fileName) => ipcRenderer.invoke('new-file', dir, fileName),
    saveFile: (filePath, jsonData) => ipcRenderer.invoke('save-file', filePath, jsonData),
    exportJSON: (defaultDir, jsonData) => ipcRenderer.invoke('export-json', defaultDir, jsonData),
});
