const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('api', {
    openFileDialog: () => ipcRenderer.invoke('open-file-dialog'),
    onFileLoaded: (callback) => ipcRenderer.on('file-loaded', (_event, filePath) => callback(filePath)),
    onRenderStart: (callback) => ipcRenderer.on('render-start', () => callback()),
    onRenderSuccess: (callback) => ipcRenderer.on('render-success', (_event, svgString) => callback(svgString)),
    onRenderError: (callback) => ipcRenderer.on('render-error', (_event, errorMsg) => callback(errorMsg))
});
