const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('api', {
    // ワークスペース
    openWorkspaceDialog: () => ipcRenderer.invoke('open-workspace-dialog'),
    onWorkspaceOpened: (callback) => ipcRenderer.on('workspace-opened', (_event, data) => callback(data)),
    onWorkspaceFilesUpdated: (callback) => ipcRenderer.on('workspace-files-updated', (_event, files) => callback(files)),

    // ファイル操作
    readJsonFile: (filePath) => ipcRenderer.invoke('read-json-file', filePath),
    newFile: (dir, fileName) => ipcRenderer.invoke('new-file', dir, fileName),
    saveFile: (filePath, jsonData) => ipcRenderer.invoke('save-file', filePath, jsonData),
    exportJSON: (defaultDir, jsonData) => ipcRenderer.invoke('export-json', defaultDir, jsonData),
});
