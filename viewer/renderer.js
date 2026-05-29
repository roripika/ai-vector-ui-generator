// ===== DOM要素 =====
const btnOpenWorkspace = document.getElementById('btn-open-workspace');
const btnOpenFile      = document.getElementById('btn-open-file');
const btnRun           = document.getElementById('btn-run');
const btnStop          = document.getElementById('btn-stop');
const btnClearLog      = document.getElementById('btn-clear-log');
const workspacePathDisplay = document.getElementById('workspace-path-display');
const statusIndicator  = document.getElementById('status-indicator');
const canvasContainer  = document.getElementById('canvas-container');
const errorConsole     = document.getElementById('error-console');
const fileInfo         = document.getElementById('file-info');
const fileList         = document.getElementById('file-list');
const fileCount        = document.getElementById('file-count');
const fileSearch       = document.getElementById('file-search');
const eventLogBody     = document.getElementById('event-log-body');
const interactionBadge = document.getElementById('interaction-badge');
const actionCountBadge = document.getElementById('action-count-badge');
const animCountBadge   = document.getElementById('anim-count-badge');

// ===== 状態 =====
let currentZoom    = d3.zoomIdentity;
let isFirstLoad    = true;
let allFiles       = [];
let activeFilePath = null;
let currentJsonData = null;   // 現在表示中のJSONデータ
let isRunning      = false;   // インタラクティブモード中か
let logEntryCount  = 0;

// ===== D3 Zoom =====
const zoom = d3.zoom()
    .scaleExtent([0.05, 20])
    .on('zoom', (e) => {
        currentZoom = e.transform;
        const svgGroup = d3.select('#canvas-container svg > g.zoom-layer');
        if (!svgGroup.empty()) svgGroup.attr('transform', e.transform);
    });

d3.select('#canvas-container').call(zoom);

// ===== ボタンイベント =====
btnOpenWorkspace.addEventListener('click', () => window.api.openWorkspaceDialog());
btnOpenFile.addEventListener('click',      () => window.api.openFileDialog());

btnRun.addEventListener('click', () => {
    isRunning = true;
    btnRun.disabled = true;
    btnStop.disabled = false;
    btnRun.classList.add('running');
    canvasContainer.classList.add('interactive-mode');
    appendLog('run', '▶ インタラクティブモード開始', '');
    injectInteractivity();
});

btnStop.addEventListener('click', () => {
    stopInteractiveMode();
    appendLog('stop', '⏹ インタラクティブモード停止', '');
});

btnClearLog.addEventListener('click', () => {
    eventLogBody.innerHTML = '<div class="log-empty">「▶ 実行」を押してインタラクティブモードを開始してください</div>';
    logEntryCount = 0;
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

window.api.onWorkspaceFilesUpdated((files) => {
    allFiles = files;
    renderFileList(allFiles, fileSearch.value.trim());
});

// ===== ファイルが選択されたとき =====
window.api.onFileLoaded((filePath) => {
    activeFilePath = filePath;
    fileInfo.textContent = filePath;
    statusIndicator.textContent = 'Loading...';
    statusIndicator.className = 'status-rendering';
    errorConsole.style.display = 'none';
    isFirstLoad = true;
    currentJsonData = null;
    stopInteractiveMode();

    // バッジを非表示に
    interactionBadge.style.display = 'none';

    // JSONも非同期でロード
    loadJsonData(filePath);

    document.querySelectorAll('.file-item').forEach(el => {
        el.classList.toggle('active', el.dataset.path === filePath);
    });
});

// ===== JSONデータのロード =====
async function loadJsonData(filePath) {
    try {
        const data = await window.api.readJsonFile(filePath);
        currentJsonData = data;
        updateInteractionBadge(data);
    } catch (e) {
        currentJsonData = null;
    }
}

function updateInteractionBadge(data) {
    if (!data) { interactionBadge.style.display = 'none'; return; }

    const actionInstances = (data.instances || []).filter(i => i.role === 'action');
    const components = (data.components || []);

    // アニメーション対象: progress, toggle, gauge, cooldown系
    const animRoles = ['progress', 'control', 'feedback', 'status'];
    let animCount = 0;
    for (const c of components) {
        for (const l of (c.layers || [])) {
            if (['progressBar','cooldownOverlay','toggle','gauge'].includes(l.shape)) {
                animCount++;
            }
            if (animRoles.includes(l.role)) animCount++;
        }
    }
    animCount = [...new Set([animCount])][0]; // dedup

    if (actionInstances.length > 0 || animCount > 0) {
        interactionBadge.style.display = 'flex';
        actionCountBadge.textContent = `🖱 アクション: ${actionInstances.length}`;
        animCountBadge.textContent   = `✨ アニメーション: ${animCount}`;
        actionCountBadge.style.display = actionInstances.length > 0 ? '' : 'none';
        animCountBadge.style.display   = animCount > 0 ? '' : 'none';
        btnRun.disabled = false;
    } else {
        interactionBadge.style.display = 'none';
        btnRun.disabled = true;
    }
}

// ===== ファイルリストの描画 =====
function renderFileList(files, searchQuery) {
    fileCount.textContent = files.length;

    if (files.length === 0) {
        fileList.innerHTML = `<div class="empty-state"><div class="empty-icon">🗂️</div><div>JSONファイルが見つかりません</div></div>`;
        return;
    }

    const lowerQuery = searchQuery.toLowerCase();
    const filtered = searchQuery ? files.filter(f => f.relativePath.toLowerCase().includes(lowerQuery)) : files;

    if (filtered.length === 0) {
        fileList.innerHTML = `<div class="empty-state"><div class="empty-icon">🔍</div><div>「${searchQuery}」に一致するファイルがありません</div></div>`;
        return;
    }

    const groups = {};
    for (const f of filtered) {
        const parts = f.relativePath.split(/[/\\]/);
        const folder = parts.length > 1 ? parts.slice(0, -1).join('/') : '';
        if (!groups[folder]) groups[folder] = [];
        groups[folder].push(f);
    }

    let html = '';
    for (const folder of Object.keys(groups).sort()) {
        if (folder) html += `<div class="folder-group-label">📁 ${folder}</div>`;
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
    fileList.querySelectorAll('.file-item').forEach(el => {
        el.addEventListener('click', () => window.api.selectFile(el.dataset.path));
    });
}

// ===== レンダリングイベント =====
window.api.onRenderStart(() => {
    statusIndicator.textContent = 'Rendering...';
    statusIndicator.className = 'status-rendering';
});

window.api.onRenderSuccess((svgString) => {
    statusIndicator.textContent = '✓ Success';
    statusIndicator.className = 'status-success';
    errorConsole.style.display = 'none';

    canvasContainer.innerHTML = svgString;
    const svgEl = canvasContainer.querySelector('svg');
    if (svgEl) {
        const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        g.setAttribute('class', 'zoom-layer');
        while (svgEl.firstChild) g.appendChild(svgEl.firstChild);
        svgEl.appendChild(g);

        if (isFirstLoad) {
            const rect    = canvasContainer.getBoundingClientRect();
            const svgW    = parseFloat(svgEl.getAttribute('width'))  || 720;
            const svgH    = parseFloat(svgEl.getAttribute('height')) || 1280;
            const padding = 60;
            const scale   = Math.max(0.05, (rect.height - padding) / svgH);
            const tx      = (rect.width - svgW * scale) / 2;
            const ty      = padding / 2;
            currentZoom   = d3.zoomIdentity.translate(tx, ty).scale(scale);
            d3.select('#canvas-container').call(zoom.transform, currentZoom);
            isFirstLoad = false;
        }
        d3.select(g).attr('transform', currentZoom);
    }

    // 実行中なら再注入
    if (isRunning) injectInteractivity();
});

window.api.onRenderError((errorMsg) => {
    statusIndicator.textContent = '✗ Error';
    statusIndicator.className = 'status-error';
    errorConsole.textContent = errorMsg;
    errorConsole.style.display = 'block';
});

// ===== インタラクティブモードの注入 =====
function injectInteractivity() {
    if (!currentJsonData) return;
    const svgEl = canvasContainer.querySelector('svg');
    if (!svgEl) return;

    const data = currentJsonData;
    const instances = data.instances || [];
    const components = data.components || [];

    // コンポーネントをIDでマップ化
    const compMap = {};
    for (const c of components) compMap[c.id] = c;

    // --- アクションボタンのホットスポット注入 ---
    const actionInstances = instances.filter(i => i.role === 'action');
    for (const inst of actionInstances) {
        const comp = compMap[inst.componentId];
        if (!comp) continue;

        // SVGのグループIDでマッチング
        const gEl = svgEl.querySelector(`#${CSS.escape(inst.id)}`) ||
                    svgEl.querySelector(`[id*="${inst.id}"]`);
        if (!gEl) continue;

        // ホットスポットとしてマーク
        gEl.classList.add('hotspot');
        gEl.setAttribute('tabindex', '0');
        gEl.setAttribute('role', 'button');
        gEl.setAttribute('aria-label', comp.name || inst.id);

        // ダッシュ枠オーバーレイを追加
        addHotspotOverlay(gEl, inst, comp);

        // クリックイベント
        gEl.addEventListener('click', (e) => {
            if (!isRunning) return;
            e.stopPropagation();

            // リップルエフェクト
            spawnRipple(svgEl, e);

            // ログ出力
            const label = comp.name || inst.id;
            const stateInfo = inst.state ? ` [state: ${inst.state}]` : '';
            appendLog('click', `🖱 タップ: ${label}`, `id="${inst.id}"${stateInfo}`);
        });
    }

    // --- アニメーション対象の識別と再生 ---
    playAnimations(svgEl, data);
}

function addHotspotOverlay(gEl, inst, comp) {
    // すでに追加済みならスキップ
    if (gEl.querySelector('.hotspot-overlay')) return;
    const layers = (comp.layers || []);
    if (layers.length === 0) return;

    // 最初のlayerのrectからサイズを取得
    const firstLayer = layers[0];
    const r = firstLayer.rect;
    if (!r) return;

    const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    rect.setAttribute('class', 'hotspot-overlay');
    rect.setAttribute('x', r.x);
    rect.setAttribute('y', r.y);
    rect.setAttribute('width', r.width);
    rect.setAttribute('height', r.height);
    if (r.radius) { rect.setAttribute('rx', r.radius); rect.setAttribute('ry', r.radius); }
    gEl.appendChild(rect);
}

function spawnRipple(svgEl, mouseEvent) {
    const svgRect = svgEl.getBoundingClientRect();
    const x = (mouseEvent.clientX - svgRect.left) / (currentZoom.k || 1) - (currentZoom.x || 0) / (currentZoom.k || 1);
    const y = (mouseEvent.clientY - svgRect.top)  / (currentZoom.k || 1) - (currentZoom.y || 0) / (currentZoom.k || 1);

    const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    circle.setAttribute('class', 'click-ripple');
    circle.setAttribute('cx', x);
    circle.setAttribute('cy', y);
    circle.setAttribute('r', 0);

    const g = svgEl.querySelector('g.zoom-layer') || svgEl;
    g.appendChild(circle);
    setTimeout(() => circle.remove(), 500);
}

// --- アニメーション再生 ---
function playAnimations(svgEl, data) {
    const components = data.components || [];
    let animsTriggered = 0;

    for (const comp of components) {
        for (const layer of (comp.layers || [])) {
            const gEl = svgEl.querySelector(`#${CSS.escape(layer.id)}`);
            if (!gEl) continue;

            const shape = layer.shape;
            const role  = layer.role || '';

            // エンターアニメーション（全要素に適用）
            const enterClass = getEnterAnimClass(role, shape);
            if (enterClass) {
                // 一度クラスを外してリセット
                gEl.classList.remove(...['anim-enter','anim-enter-slide-up','anim-enter-scale']);
                void gEl.offsetWidth; // reflow
                gEl.classList.add(enterClass);
                animsTriggered++;
            }

            // ループアニメーション
            const loopClass = getLoopAnimClass(role, shape, layer);
            if (loopClass) {
                gEl.classList.remove(...['anim-loop-bounce','anim-loop-pulse','anim-loop-spin','anim-loop-shimmer']);
                void gEl.offsetWidth;
                gEl.classList.add(loopClass);
                animsTriggered++;
            }
        }
    }

    if (animsTriggered > 0) {
        appendLog('anim', `✨ アニメーション再生: ${animsTriggered} 要素`, '');
    }
}

function getEnterAnimClass(role, shape) {
    if (role === 'modal' || role === 'overlay') return 'anim-enter-scale';
    if (role === 'header' || role === 'navigation') return 'anim-enter-slide-up';
    if (shape === 'text' && role === 'text') return 'anim-enter';
    if (role === 'container') return 'anim-enter';
    return null;
}

function getLoopAnimClass(role, shape, layer) {
    if (shape === 'progressBar') return 'anim-loop-shimmer';
    if (shape === 'cooldownOverlay') return 'anim-loop-spin';
    if (shape === 'gauge') return 'anim-loop-pulse';
    if (role === 'badge' || shape === 'badge') return 'anim-loop-bounce';
    if (role === 'status' || role === 'feedback') return 'anim-loop-pulse';
    return null;
}

// --- インタラクティブモード停止 ---
function stopInteractiveMode() {
    isRunning = false;
    btnRun.disabled = false;
    btnStop.disabled = true;
    btnRun.classList.remove('running');
    canvasContainer.classList.remove('interactive-mode');

    // SVG内アニメーションクラスを除去
    const svgEl = canvasContainer.querySelector('svg');
    if (svgEl) {
        svgEl.querySelectorAll('[class*="anim-"]').forEach(el => {
            [...el.classList].filter(c => c.startsWith('anim-')).forEach(c => el.classList.remove(c));
        });
    }
}

// ===== ログ追加 =====
function appendLog(type, msg, meta) {
    const now = new Date();
    const ts  = now.toLocaleTimeString('ja-JP', { hour12: false, hour:'2-digit', minute:'2-digit', second:'2-digit' });

    // empty state を消す
    const empty = eventLogBody.querySelector('.log-empty');
    if (empty) empty.remove();

    const entry = document.createElement('div');
    entry.className = `log-entry type-${type}`;
    entry.innerHTML = `
        <span class="log-time">${ts}</span>
        <span class="log-msg">${msg}</span>
        ${meta ? `<span class="log-meta">${meta}</span>` : ''}
    `;
    eventLogBody.appendChild(entry);
    eventLogBody.scrollTop = eventLogBody.scrollHeight;
    logEntryCount++;
}
