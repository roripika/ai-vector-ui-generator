const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('api', {
    // ワークスペース
    openWorkspaceDialog: () => ipcRenderer.invoke('open-workspace-dialog'),
    listJsonFiles: () => ipcRenderer.invoke('list-json-files'),
    selectFile: (filePath) => ipcRenderer.invoke('select-file', filePath),
    onWorkspaceOpened: (callback) => ipcRenderer.on('workspace-opened', (_event, data) => callback(data)),
    onWorkspaceFilesUpdated: (callback) => ipcRenderer.on('workspace-files-updated', (_event, files) => callback(files)),

    // 単一ファイル
    openFileDialog: () => ipcRenderer.invoke('open-file-dialog'),
    onFileLoaded: (callback) => ipcRenderer.on('file-loaded', (_event, filePath) => callback(filePath)),

    // レンダリング
    onRenderStart: (callback) => ipcRenderer.on('render-start', () => callback()),
    onRenderSuccess: (callback) => ipcRenderer.on('render-success', (_event, svgString) => callback(svgString)),
    onRenderError: (callback) => ipcRenderer.on('render-error', (_event, errorMsg) => callback(errorMsg))
});
