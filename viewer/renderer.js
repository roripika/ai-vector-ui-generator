// ===== DOM要素の取得 =====
const btnOpenWorkspace = document.getElementById('btn-open-workspace');
const btnOpenFile = document.getElementById('btn-open-file');
const workspacePathDisplay = document.getElementById('workspace-path-display');
const statusIndicator = document.getElementById('status-indicator');
const canvasContainer = document.getElementById('canvas-container');
const errorConsole = document.getElementById('error-console');
const fileInfo = document.getElementById('file-info');
const fileList = document.getElementById('file-list');
const fileCount = document.getElementById('file-count');
const fileSearch = document.getElementById('file-search');

let currentZoom = d3.zoomIdentity;
let isFirstLoad = true;
let allFiles = [];
let activeFilePath = null;

// ===== D3 Zoom 初期化 =====
const zoom = d3.zoom()
    .scaleExtent([0.05, 20])
    .on('zoom', (e) => {
        currentZoom = e.transform;
        const svgGroup = d3.select('#canvas-container svg > g.zoom-layer');
        if (!svgGroup.empty()) {
            svgGroup.attr('transform', e.transform);
        }
    });

d3.select('#canvas-container').call(zoom);

// ===== ボタンイベント =====
btnOpenWorkspace.addEventListener('click', async () => {
    await window.api.openWorkspaceDialog();
});

btnOpenFile.addEventListener('click', async () => {
    await window.api.openFileDialog();
});

// ===== ファイル検索 =====
fileSearch.addEventListener('input', () => {
    renderFileList(allFiles, fileSearch.value.trim());
});

// ===== ワークスペースが開かれたとき =====
window.api.onWorkspaceOpened((data) => {
    allFiles = data.files;
    workspacePathDisplay.textContent = data.dir;
    fileSearch.value = '';
    renderFileList(allFiles, '');
});

// ===== ワークスペース内のファイルが変わったとき =====
window.api.onWorkspaceFilesUpdated((files) => {
    allFiles = files;
    renderFileList(allFiles, fileSearch.value.trim());
});

// ===== ファイルが選択されたとき（単一ファイル開いた場合も） =====
window.api.onFileLoaded((filePath) => {
    activeFilePath = filePath;
    fileInfo.textContent = filePath;
    statusIndicator.textContent = 'Loading...';
    statusIndicator.className = 'status-rendering';
    errorConsole.style.display = 'none';
    isFirstLoad = true;

    // もしサイドバーにそのファイルがあれば選択状態に
    document.querySelectorAll('.file-item').forEach(el => {
        el.classList.toggle('active', el.dataset.path === filePath);
    });
});

// ===== ファイルリストの描画 =====
function renderFileList(files, searchQuery) {
    fileCount.textContent = files.length;

    if (files.length === 0) {
        fileList.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">🗂️</div>
                <div>JSONファイルが見つかりません</div>
            </div>`;
        return;
    }

    const lowerQuery = searchQuery.toLowerCase();
    const filtered = searchQuery
        ? files.filter(f => f.relativePath.toLowerCase().includes(lowerQuery))
        : files;

    if (filtered.length === 0) {
        fileList.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">🔍</div>
                <div>「${searchQuery}」に一致するファイルがありません</div>
            </div>`;
        return;
    }

    // フォルダごとにグループ化
    const groups = {};
    for (const f of filtered) {
        const parts = f.relativePath.split(/[/\\]/);
        const folder = parts.length > 1 ? parts.slice(0, -1).join('/') : '';
        if (!groups[folder]) groups[folder] = [];
        groups[folder].push(f);
    }

    let html = '';
    const sortedFolders = Object.keys(groups).sort();

    for (const folder of sortedFolders) {
        if (folder) {
            html += `<div class="folder-group-label">📁 ${folder}</div>`;
        }
        for (const f of groups[folder]) {
            const isActive = f.fullPath === activeFilePath ? ' active' : '';
            html += `
                <div class="file-item${isActive}" data-path="${f.fullPath}" title="${f.fullPath}">
                    <span class="file-item-icon">📄</span>
                    <div class="file-item-info">
                        <span class="file-item-name">${f.name}</span>
                        ${folder ? `<span class="file-item-path">${f.relativePath}</span>` : ''}
                    </div>
                </div>`;
        }
    }

    fileList.innerHTML = html;

    // クリックイベントを登録
    fileList.querySelectorAll('.file-item').forEach(el => {
        el.addEventListener('click', () => {
            const filePath = el.dataset.path;
            window.api.selectFile(filePath);
        });
    });
}

// ===== レンダリング：開始 =====
window.api.onRenderStart(() => {
    statusIndicator.textContent = 'Rendering...';
    statusIndicator.className = 'status-rendering';
});

// ===== レンダリング：成功 =====
window.api.onRenderSuccess((svgString) => {
    statusIndicator.textContent = '✓ Success';
    statusIndicator.className = 'status-success';
    errorConsole.style.display = 'none';

    canvasContainer.innerHTML = svgString;

    const svgEl = canvasContainer.querySelector('svg');
    if (svgEl) {
        // zoom-layer でラップ
        const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        g.setAttribute('class', 'zoom-layer');
        while (svgEl.firstChild) {
            g.appendChild(svgEl.firstChild);
        }
        svgEl.appendChild(g);

        if (isFirstLoad) {
            const containerRect = canvasContainer.getBoundingClientRect();
            const svgWidth  = parseFloat(svgEl.getAttribute('width'))  || 720;
            const svgHeight = parseFloat(svgEl.getAttribute('height')) || 1280;
            const padding = 60;
            const scale = Math.max(0.05, (containerRect.height - padding) / svgHeight);
            const tx = (containerRect.width - svgWidth * scale) / 2;
            const ty = padding / 2;

            currentZoom = d3.zoomIdentity.translate(tx, ty).scale(scale);
            d3.select('#canvas-container').call(zoom.transform, currentZoom);
            isFirstLoad = false;
        }

        d3.select(g).attr('transform', currentZoom);
    }
});

// ===== レンダリング：エラー =====
window.api.onRenderError((errorMsg) => {
    statusIndicator.textContent = '✗ Error';
    statusIndicator.className = 'status-error';
    errorConsole.textContent = errorMsg;
    errorConsole.style.display = 'block';
});
