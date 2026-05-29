'use strict';
/**
 * renderer.js — エントリーポイント
 * ツールバー / 部品パネル / ワークスペース / プロパティパネル / レイヤーパネルの制御
 */

// ======================================================
// 初期化
// ======================================================
window.addEventListener('DOMContentLoaded', () => {
  Editor.init(
    document.getElementById('canvas-inner'),
    document.getElementById('selection-overlay')
  );

  _buildComponentLibrary();
  _setupToolbar();
  _setupWorkspaceIPC();
  _setupEditorCallbacks();
  _setupCanvasMouseCoords();

  // 初期キャンバスサイズ適用
  _applyCanvasSize('1280x720');
  Editor.fitZoom();
});

// ======================================================
// 部品ライブラリの描画
// ======================================================
function _buildComponentLibrary() {
  const container = document.getElementById('component-library');
  const cats = window.getTemplatesByCategory();

  for (const [cat, items] of Object.entries(cats)) {
    const catLabel = document.createElement('div');
    catLabel.className = 'category-label';
    catLabel.textContent = cat;
    container.appendChild(catLabel);

    for (const tpl of items) {
      const item = document.createElement('div');
      item.className = 'template-item';
      item.innerHTML = `<span class="template-item-icon">${tpl.icon}</span><span>${tpl.name}</span>`;
      item.addEventListener('click', () => {
        // キャンバス中央付近にドロップ
        const st = Editor.getState();
        const cx = Math.round(st.canvasWidth / 2 - tpl.defaultSize.width / 2);
        const cy = Math.round(st.canvasHeight / 2 - tpl.defaultSize.height / 2);
        Editor.addElement(tpl.id, cx, cy);
      });
      container.appendChild(item);
    }
  }
}

// ======================================================
// ツールバー
// ======================================================
function _setupToolbar() {
  document.getElementById('btn-open-workspace').addEventListener('click', () => {
    window.api.openWorkspaceDialog();
  });

  document.getElementById('btn-new-file').addEventListener('click', async () => {
    const name = prompt('新しいファイル名（.jsonなし）:', 'new_screen');
    if (!name) return;
    const st = Editor.getState();
    if (!st.workspaceDir) return;
    const result = await window.api.newFile(st.workspaceDir, name + '.json');
    if (result.success) {
      st.currentFilePath = result.filePath;
      Editor.loadJSON({ canvas: { width: st.canvasWidth, height: st.canvasHeight } });
      _setCurrentFile(result.filePath);
    }
  });

  document.getElementById('btn-save').addEventListener('click', _saveCurrentFile);

  document.getElementById('btn-export-json').addEventListener('click', async () => {
    const json = Editor.exportJSON();
    const st = Editor.getState();
    await window.api.exportJSON(st.workspaceDir || null, json);
  });

  document.getElementById('btn-undo').addEventListener('click', () => Editor.undo());
  document.getElementById('btn-redo').addEventListener('click', () => Editor.redo());
  document.getElementById('btn-delete').addEventListener('click', () => Editor.deleteSelected());

  document.getElementById('canvas-size-select').addEventListener('change', (e) => {
    _applyCanvasSize(e.target.value);
    Editor.fitZoom();
  });

  document.getElementById('btn-zoom-in').addEventListener('click', () => { Editor.zoomIn(); _updateZoomDisplay(); });
  document.getElementById('btn-zoom-out').addEventListener('click', () => { Editor.zoomOut(); _updateZoomDisplay(); });
  document.getElementById('btn-zoom-fit').addEventListener('click', () => { Editor.fitZoom(); _updateZoomDisplay(); });

  // Ctrl+S保存
  document.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 's') { e.preventDefault(); _saveCurrentFile(); }
  });

  // タブ切り替え
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
      btn.classList.add('active');
      const tabId = 'tab-' + btn.getAttribute('data-tab');
      document.getElementById(tabId).classList.add('active');
    });
  });

  // レイヤー操作
  document.getElementById('btn-layer-up').addEventListener('click', () => {
    const el = Editor.getSelected();
    if (el) Editor.moveLayerUp(el.id);
  });
  document.getElementById('btn-layer-down').addEventListener('click', () => {
    const el = Editor.getSelected();
    if (el) Editor.moveLayerDown(el.id);
  });
}

function _applyCanvasSize(sizeStr) {
  const [w, h] = sizeStr.split('x').map(Number);
  document.getElementById('canvas-inner').style.width  = w + 'px';
  document.getElementById('canvas-inner').style.height = h + 'px';
  Editor.setCanvasSize(w, h);
}

function _updateZoomDisplay() {
  const pct = Math.round(Editor.getState().zoom * 100);
  document.getElementById('zoom-display').textContent = pct + '%';
}

// ======================================================
// ワークスペース IPC
// ======================================================
function _setupWorkspaceIPC() {
  window.api.onWorkspaceOpened((data) => {
    Editor.getState().workspaceDir = data.dir;
    document.getElementById('btn-new-file').disabled = false;
    _renderWorkspaceFiles(data.files);

    // ファイルタブに自動切替
    document.querySelectorAll('.tab-btn').forEach(b => {
      b.classList.toggle('active', b.getAttribute('data-tab') === 'files');
    });
    document.querySelectorAll('.tab-content').forEach(c => {
      c.classList.toggle('active', c.id === 'tab-files');
    });
  });

  window.api.onWorkspaceFilesUpdated((files) => {
    _renderWorkspaceFiles(files);
  });
}

function _renderWorkspaceFiles(files) {
  const container = document.getElementById('workspace-file-list');
  if (!files || files.length === 0) {
    container.innerHTML = '<div class="panel-empty">JSONファイルが見つかりません</div>';
    return;
  }
  container.innerHTML = '';
  for (const f of files) {
    const item = document.createElement('div');
    item.className = 'ws-file-item';
    item.setAttribute('data-path', f.fullPath);
    item.innerHTML = `<span>📄</span><span>${f.name}</span>`;
    item.addEventListener('click', () => _openWorkspaceFile(f.fullPath));
    container.appendChild(item);
  }
}

async function _openWorkspaceFile(filePath) {
  const data = await window.api.readJsonFile(filePath);
  if (!data) return;

  Editor.loadJSON(data);
  Editor.getState().currentFilePath = filePath;
  _setCurrentFile(filePath);

  // アクティブ表示
  document.querySelectorAll('.ws-file-item').forEach(el => {
    el.classList.toggle('active', el.getAttribute('data-path') === filePath);
  });

  // canvas-size-selectを同期
  const st = Editor.getState();
  const key = `${st.canvasWidth}x${st.canvasHeight}`;
  const sel = document.getElementById('canvas-size-select');
  if ([...sel.options].some(o => o.value === key)) sel.value = key;
  Editor.fitZoom();
  _updateZoomDisplay();
}

async function _saveCurrentFile() {
  const st = Editor.getState();
  if (!st.currentFilePath) return;
  const json = Editor.exportJSON();
  const result = await window.api.saveFile(st.currentFilePath, json);
  if (result && result.success) {
    st.isDirty = false;
    document.getElementById('dirty-dot').style.display = 'none';
  }
}

function _setCurrentFile(filePath) {
  const name = filePath.split('/').pop();
  document.getElementById('current-file-name').textContent = name;
  document.getElementById('btn-save').disabled = false;
  document.getElementById('btn-export-json').disabled = false;
  document.getElementById('dirty-dot').style.display = 'none';
}

// ======================================================
// エディターコールバック
// ======================================================
function _setupEditorCallbacks() {
  Editor.onChangeCallback((state) => {
    _updateZoomDisplay();
    document.getElementById('dirty-dot').style.display = state.isDirty ? 'inline' : 'none';
  });

  Editor.onSelectCallback((el) => {
    _renderPropertiesPanel(el);
    _updateDeleteBtn(el);
    _updateLayerHighlight(el);
  });

  Editor.onLayerCallback((elements) => {
    _renderLayerList(elements);
  });
}

// ======================================================
// プロパティパネル
// ======================================================
function _renderPropertiesPanel(el) {
  const panel = document.getElementById('properties-panel');
  if (!el) {
    panel.innerHTML = '<div class="panel-empty">要素を選択してください</div>';
    return;
  }
  const tpl = window.getTemplate(el.templateId);
  if (!tpl) return;

  let html = '';

  // --- ID & 名前 ---
  html += `<div class="prop-section">`;
  html += `<div class="prop-section-title">要素</div>`;
  html += _row('ID', `<input class="prop-input" id="prop-id" value="${_esc(el.id)}" readonly style="color:#777;">`);
  html += _row('名前', `<input class="prop-input" id="prop-name" value="${_esc(el.name)}" data-prop="name">`);
  html += `</div><div class="prop-sep"></div>`;

  // --- Transform ---
  html += `<div class="prop-section">`;
  html += `<div class="prop-section-title">Transform</div>`;
  html += `<div class="prop-row">
    <span class="prop-label">X</span>
    <input class="prop-input-num" type="number" id="prop-x" value="${Math.round(el.x)}" data-prop="x" style="width:60px;">
    <span class="prop-label" style="text-align:right;width:20px;">Y</span>
    <input class="prop-input-num" type="number" id="prop-y" value="${Math.round(el.y)}" data-prop="y" style="width:60px;">
  </div>`;
  html += `<div class="prop-row">
    <span class="prop-label">W</span>
    <input class="prop-input-num" type="number" id="prop-w" value="${Math.round(el.width)}" data-prop="width" style="width:60px;">
    <span class="prop-label" style="text-align:right;width:20px;">H</span>
    <input class="prop-input-num" type="number" id="prop-h" value="${Math.round(el.height)}" data-prop="height" style="width:60px;">
  </div>`;
  html += `</div><div class="prop-sep"></div>`;

  // --- Appearance ---
  const p = el.props;
  html += `<div class="prop-section">`;
  html += `<div class="prop-section-title">外観</div>`;
  if (p.fillColor !== undefined) html += _colorRow('塗り', 'fillColor', p.fillColor);
  if (p.textColor !== undefined) html += _colorRow('文字色', 'textColor', p.textColor);
  if (p.strokeColor !== undefined && p.strokeColor !== 'transparent') html += _colorRow('枠線', 'strokeColor', p.strokeColor);
  if (p.trackColor !== undefined) html += _colorRow('トラック', 'trackColor', p.trackColor);
  if (p.radius !== undefined) html += _row('角丸', `<input class="prop-input-num" type="number" id="prop-radius" value="${p.radius}" data-prop="radius" min="0">`);
  if (p.strokeWidth !== undefined) html += _row('枠幅', `<input class="prop-input-num" type="number" id="prop-sw" value="${p.strokeWidth}" data-prop="strokeWidth" min="0">`);
  if (p.opacity !== undefined) html += _row('透明度', `<input class="prop-input-num" type="number" id="prop-opacity" value="${p.opacity}" data-prop="opacity" min="0" max="1" step="0.05">`);
  if (p.value !== undefined) html += _row('値 (0-1)', `<input class="prop-input-num" type="number" id="prop-value" value="${p.value}" data-prop="value" min="0" max="1" step="0.05">`);
  if (p.objectFit !== undefined) html += _row('Fit', `<select class="prop-select" data-prop="objectFit"><option value="contain" ${p.objectFit==='contain'?'selected':''}>contain</option><option value="cover" ${p.objectFit==='cover'?'selected':''}>cover</option><option value="fill" ${p.objectFit==='fill'?'selected':''}>fill</option></select>`);
  if (p.animation !== undefined) html += _row('アニメ', `<select class="prop-select" data-prop="animation">
    <optgroup label="None">
      <option value="none" ${p.animation==='none'?'selected':''}>なし</option>
    </optgroup>
    <optgroup label="Loop (ループ)">
      <option value="blink" ${p.animation==='blink'?'selected':''}>点滅 (Blink)</option>
      <option value="pulse" ${p.animation==='pulse'?'selected':''}>鼓動 (Pulse)</option>
      <option value="float" ${p.animation==='float'?'selected':''}>浮遊 (Float)</option>
    </optgroup>
    <optgroup label="Entrance (登場)">
      <option value="pop-in" ${p.animation==='pop-in'?'selected':''}>ポップイン (Pop-in)</option>
      <option value="slide-up" ${p.animation==='slide-up'?'selected':''}>スライドUP (Slide-Up)</option>
      <option value="slide-down" ${p.animation==='slide-down'?'selected':''}>スライドDOWN (Slide-Down)</option>
      <option value="fade-in" ${p.animation==='fade-in'?'selected':''}>フェードイン (Fade-in)</option>
    </optgroup>
    <optgroup label="Feedback (反応)">
      <option value="shake" ${p.animation==='shake'?'selected':''}>シェイク (Shake)</option>
      <option value="squash" ${p.animation==='squash'?'selected':''}>弾力 (Squash)</option>
    </optgroup>
  </select>`);
  html += `</div><div class="prop-sep"></div>`;

  // --- Layout ---
  if (p.columns !== undefined || p.spacingX !== undefined || p.scrollDirection !== undefined || p.alignment !== undefined || p.tabNames !== undefined || p.refPath !== undefined) {
    html += `<div class="prop-section">`;
    html += `<div class="prop-section-title">レイアウト / 特殊設定</div>`;
    if (p.refPath !== undefined) html += _row('Prefab参照', `<input class="prop-input" value="${_esc(p.refPath)}" data-prop="refPath" placeholder="ex: ui_common_header.json">`);
    if (p.tabNames !== undefined) html += _row('タブ名', `<input class="prop-input" value="${_esc(p.tabNames)}" data-prop="tabNames" placeholder="Tab1,Tab2...">`);
    
    if (p.columns !== undefined) html += _row('列数 (固定)', `<input class="prop-input-num" type="number" value="${p.columns}" data-prop="columns" min="1">`);
    if (p.spacingX !== undefined) html += _row('横余白', `<input class="prop-input-num" type="number" value="${p.spacingX}" data-prop="spacingX" min="0">`);
    if (p.spacingY !== undefined) html += _row('縦余白', `<input class="prop-input-num" type="number" value="${p.spacingY}" data-prop="spacingY" min="0">`);
    if (p.cellHeight !== undefined) html += _row('セル高さ', `<input class="prop-input-num" type="number" value="${p.cellHeight}" data-prop="cellHeight" min="1">`);
    
    if (p.alignment !== undefined) html += _row('揃え位置', `<select class="prop-select" data-prop="alignment">
      <option value="start" ${p.alignment==='start'?'selected':''}>start</option>
      <option value="center" ${p.alignment==='center'?'selected':''}>center</option>
      <option value="end" ${p.alignment==='end'?'selected':''}>end</option>
      <option value="space-between" ${p.alignment==='space-between'?'selected':''}>space-between</option>
    </select>`);
    
    if (p.scrollDirection !== undefined) html += _row('スクロール方向', `<select class="prop-select" data-prop="scrollDirection">
      <option value="vertical" ${p.scrollDirection==='vertical'?'selected':''}>縦 (Vertical)</option>
      <option value="horizontal" ${p.scrollDirection==='horizontal'?'selected':''}>横 (Horizontal)</option>
      <option value="both" ${p.scrollDirection==='both'?'selected':''}>両方 (Both)</option>
    </select>`);
    if (p.contentWidth !== undefined) html += _row('内包幅', `<input class="prop-input-num" type="number" value="${p.contentWidth}" data-prop="contentWidth" min="1">`);
    if (p.contentHeight !== undefined) html += _row('内包高さ', `<input class="prop-input-num" type="number" value="${p.contentHeight}" data-prop="contentHeight" min="1">`);
    
    html += `</div><div class="prop-sep"></div>`;
  }

  // --- Images ---
  if (p.imagePath !== undefined || p.imageNormal !== undefined) {
    html += `<div class="prop-section">`;
    html += `<div class="prop-section-title">画像ソース (Workspace基準)</div>`;
    if (p.imagePath !== undefined) html += _row('Path', `<input class="prop-input" id="prop-img-path" value="${_esc(p.imagePath)}" data-prop="imagePath" placeholder="ex: assets/bg.png">`);
    if (p.imageNormal !== undefined) html += _row('Normal', `<input class="prop-input" id="prop-img-n" value="${_esc(p.imageNormal)}" data-prop="imageNormal">`);
    if (p.imagePressed !== undefined) html += _row('Pressed', `<input class="prop-input" id="prop-img-p" value="${_esc(p.imagePressed)}" data-prop="imagePressed">`);
    if (p.imageDisabled !== undefined) html += _row('Disabled', `<input class="prop-input" id="prop-img-d" value="${_esc(p.imageDisabled)}" data-prop="imageDisabled">`);
    html += `</div><div class="prop-sep"></div>`;
  }

  // --- Text ---
  if (p.text !== undefined || p.fontSize !== undefined) {
    html += `<div class="prop-section">`;
    html += `<div class="prop-section-title">テキスト</div>`;
    if (p.text !== undefined) html += _row('内容', `<input class="prop-input" id="prop-text" value="${_esc(p.text)}" data-prop="text">`);
    if (p.fontSize !== undefined) html += _row('サイズ', `<input class="prop-input-num" type="number" id="prop-fs" value="${p.fontSize}" data-prop="fontSize" min="6" max="120">`);
    if (p.textAlign !== undefined) html += _row('揃え', `<select class="prop-select" id="prop-align" data-prop="textAlign">
      <option value="left" ${p.textAlign === 'left' ? 'selected' : ''}>左</option>
      <option value="center" ${p.textAlign === 'center' ? 'selected' : ''}>中央</option>
      <option value="right" ${p.textAlign === 'right' ? 'selected' : ''}>右</option>
    </select>`);
    html += `</div><div class="prop-sep"></div>`;
  }

  // --- Semantic ---
  const ROLES = ['action','navigation','container','data_display','feedback','decoration','text','icon','status','modal','overlay','header','progress','toggle','badge','input'];
  const STATES = ['default','pressed','disabled','selected','active','loading','success','error','cooldown','locked','on','off'];
  const IMPORTANCE = ['primary','secondary','tertiary','emphasis','muted','info','warning','critical','decorative'];

  html += `<div class="prop-section">`;
  html += `<div class="prop-section-title">セマンティクス</div>`;
  html += _row('Role', `<select class="prop-select" id="prop-role" data-prop="role">${ROLES.map(r => `<option value="${r}" ${el.role === r ? 'selected' : ''}>${r}</option>`).join('')}</select>`);
  html += _row('State', `<select class="prop-select" id="prop-state" data-prop="state">${STATES.map(s => `<option value="${s}" ${el.state === s ? 'selected' : ''}>${s}</option>`).join('')}</select>`);
  html += _row('Importance', `<select class="prop-select" id="prop-imp" data-prop="importance">${IMPORTANCE.map(i => `<option value="${i}" ${el.importance === i ? 'selected' : ''}>${i}</option>`).join('')}</select>`);
  html += `</div>`;

  // --- 削除ボタン ---
  html += `<button class="btn-danger" id="prop-delete">🗑 この要素を削除</button>`;

  panel.innerHTML = html;

  // イベント登録
  panel.querySelectorAll('[data-prop]').forEach(input => {
    const ev = (input.tagName === 'SELECT') ? 'change' : 'input';
    input.addEventListener(ev, (e) => {
      Editor.updateProp(input.getAttribute('data-prop'), e.target.value);
    });
  });

  // カラースウォッチ連動
  panel.querySelectorAll('.prop-color-swatch').forEach(sw => {
    const colorInput = document.getElementById('colortext-' + sw.getAttribute('data-colortarget'));
    sw.addEventListener('input', (e) => {
      const propName = sw.getAttribute('data-colortarget');
      Editor.updateProp(propName, e.target.value);
      if (colorInput) colorInput.value = e.target.value;
    });
    if (colorInput) {
      colorInput.addEventListener('input', (e) => {
        const propName = sw.getAttribute('data-colortarget');
        if (/^#[0-9a-fA-F]{6}$/.test(e.target.value)) {
          Editor.updateProp(propName, e.target.value);
          sw.value = e.target.value;
        }
      });
    }
  });

  panel.querySelector('#prop-delete')?.addEventListener('click', () => Editor.deleteSelected());
}

function _row(label, inputHtml) {
  return `<div class="prop-row"><span class="prop-label">${label}</span><div class="prop-value">${inputHtml}</div></div>`;
}

function _colorRow(label, propName, color) {
  const safeColor = /^#[0-9a-fA-F]{6}$/.test(color) ? color : '#888888';
  return `<div class="prop-color-row">
    <span class="prop-label">${label}</span>
    <input type="color" class="prop-color-swatch" value="${safeColor}" data-colortarget="${propName}">
    <input type="text" class="prop-color-input" id="colortext-${propName}" value="${safeColor}" maxlength="7" spellcheck="false">
  </div>`;
}

function _esc(s) {
  return String(s).replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;');
}

// ======================================================
// レイヤーリスト (階層ツリー & D&D)
// ======================================================
function _renderLayerList(elements) {
  const list = document.getElementById('layer-list');
  if (!elements || elements.length === 0) {
    list.innerHTML = '<div class="panel-empty">要素なし</div>';
    return;
  }
  const selected = Editor.getSelected();

  // ツリー構築
  const rootElements = [];
  const childrenMap = {};
  elements.forEach(el => {
    if (el.parentId) {
      if (!childrenMap[el.parentId]) childrenMap[el.parentId] = [];
      childrenMap[el.parentId].push(el);
    } else {
      rootElements.push(el);
    }
  });

  const sortElements = (arr) => arr.sort((a, b) => b.zIndex - a.zIndex);

  let html = '';
  function renderNode(el, depth) {
    const tpl = window.getTemplate(el.templateId);
    const icon = tpl ? tpl.icon : '▪';
    const active = selected && selected.id === el.id ? ' active' : '';
    const indent = '<span class="layer-indent"></span>'.repeat(depth);
    
    html += `<div class="layer-item${active}" data-id="${el.id}" draggable="true">
      ${indent}
      <span class="layer-item-icon">${icon}</span>
      <span class="layer-item-name">${el.name}</span>
    </div>`;

    if (childrenMap[el.id]) {
      sortElements(childrenMap[el.id]).forEach(child => renderNode(child, depth + 1));
    }
  }

  sortElements(rootElements).forEach(el => renderNode(el, 0));
  list.innerHTML = html;

  // イベント登録
  let dragSourceId = null;

  list.querySelectorAll('.layer-item').forEach(item => {
    item.addEventListener('click', () => {
      Editor.selectElement(item.getAttribute('data-id'));
    });

    item.addEventListener('dragstart', (e) => {
      dragSourceId = item.getAttribute('data-id');
      e.dataTransfer.effectAllowed = 'move';
      e.dataTransfer.setData('text/plain', dragSourceId);
      item.style.opacity = '0.5';
    });

    item.addEventListener('dragend', () => {
      item.style.opacity = '1';
      list.querySelectorAll('.layer-item').forEach(el => el.classList.remove('drag-over'));
    });

    item.addEventListener('dragover', (e) => {
      e.preventDefault();
      e.dataTransfer.dropEffect = 'move';
      item.classList.add('drag-over');
    });

    item.addEventListener('dragleave', () => {
      item.classList.remove('drag-over');
    });

    item.addEventListener('drop', (e) => {
      e.stopPropagation();
      item.classList.remove('drag-over');
      const targetId = item.getAttribute('data-id');
      if (dragSourceId && dragSourceId !== targetId) {
        Editor.setParent(dragSourceId, targetId);
      }
    });
  });
  
  // ルートへのドロップ（リスト背景へのドロップ）
  list.addEventListener('dragover', e => e.preventDefault());
  list.addEventListener('drop', e => {
    if (e.target === list && dragSourceId) {
      Editor.setParent(dragSourceId, null);
    }
  });
}

function _updateLayerHighlight(el) {
  document.querySelectorAll('.layer-item').forEach(item => {
    item.classList.toggle('active', el && item.getAttribute('data-id') === el.id);
  });
}

function _updateDeleteBtn(el) {
  document.getElementById('btn-delete').disabled = !el;
}

// ======================================================
// マウス座標表示
// ======================================================
function _setupCanvasMouseCoords() {
  const viewport = document.getElementById('canvas-viewport');
  const inner    = document.getElementById('canvas-inner');
  const coords   = document.getElementById('canvas-coords');

  viewport.addEventListener('mousemove', (e) => {
    const rect  = inner.getBoundingClientRect();
    const zoom  = Editor.getState().zoom;
    const x     = Math.round((e.clientX - rect.left) / zoom);
    const y     = Math.round((e.clientY - rect.top)  / zoom);
    coords.textContent = `X: ${x}  Y: ${y}`;
  });
}
