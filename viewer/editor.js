'use strict';

/**
 * UIエディターコアエンジン
 * キャンバス上の要素管理、選択/ドラッグ/リサイズ、Undo/Redo、JSON入出力を担当。
 */
window.Editor = (function () {

  // ========================================================
  // 状態
  // ========================================================
  const state = {
    elements: [],           // キャンバス上の全要素
    selectedId: null,       // 選択中要素のID
    canvasWidth: 1280,
    canvasHeight: 720,
    zoom: 1,
    panX: 0,
    panY: 0,
    isDirty: false,
    currentFilePath: null,
    workspaceDir: null,
    history: [],
    historyIndex: -1,
    HISTORY_MAX: 50,
  };

  // ドラッグ管理
  let drag = null;
  // リサイズ管理
  let resize = null;

  // ========================================================
  // 初期化
  // ========================================================
  function init(canvasInnerEl, selectionEl) {
    state._canvas = canvasInnerEl;
    state._selection = selectionEl;
    _setupCanvasEvents();
    renderCanvas();
  }

  // ========================================================
  // 要素の追加
  // ========================================================
  let _idCounter = 0;
  function addElement(templateId, x, y) {
    const tpl = window.getTemplate(templateId);
    if (!tpl) return;

    _pushHistory();

    const id = `${templateId.split('-').map(w => w[0]).join('')}-${++_idCounter}`;
    const el = {
      id,
      parentId: null,
      templateId,
      name: tpl.name,
      x: _snap(x),
      y: _snap(y),
      width: tpl.defaultSize.width,
      height: tpl.defaultSize.height,
      zIndex: state.elements.length,
      role: tpl.role,
      importance: tpl.importance,
      state: tpl.state,
      props: { ...tpl.defaultProps },
    };
    state.elements.push(el);
    state.isDirty = true;
    renderCanvas();
    selectElement(id);
    _notifyChange();
    return el;
  }

  // ========================================================
  // 要素の選択
  // ========================================================
  function selectElement(id) {
    state.selectedId = id;
    _updateSelectionOverlay();
    _notifySelect();
  }

  function deselect() {
    state.selectedId = null;
    _updateSelectionOverlay();
    _notifySelect();
  }

  // ========================================================
  // 要素の削除
  // ========================================================
  function deleteSelected() {
    if (!state.selectedId) return;
    _pushHistory();
    state.elements = state.elements.filter(e => e.id !== state.selectedId);
    state.selectedId = null;
    state.isDirty = true;
    renderCanvas();
    _notifyChange();
    _notifySelect();
  }

  // ========================================================
  // プロパティ更新
  // ========================================================
  function updateProp(key, value) {
    const el = _selected();
    if (!el) return;
    if (key === 'x') el.x = _snap(Number(value));
    else if (key === 'y') el.y = _snap(Number(value));
    else if (key === 'width') el.width = Math.max(8, Number(value));
    else if (key === 'height') el.height = Math.max(8, Number(value));
    else if (key === 'name') el.name = value;
    else if (key === 'role') el.role = value;
    else if (key === 'importance') el.importance = value;
    else if (key === 'state') el.state = value;
    else el.props[key] = value;
    state.isDirty = true;
    _renderElement(el);
    _updateSelectionOverlay();
    _notifyChange();
  }

  // ========================================================
  // レイヤー順変更
  // ========================================================
  function moveLayerUp(id) {
    const el = state.elements.find(e => e.id === id);
    if (!el) return;
    const siblings = state.elements.filter(e => e.parentId === el.parentId).sort((a,b)=>a.zIndex-b.zIndex);
    const idx = siblings.findIndex(e => e.id === id);
    if (idx < siblings.length - 1) {
      _pushHistory();
      const next = siblings[idx + 1];
      const temp = el.zIndex;
      el.zIndex = next.zIndex;
      next.zIndex = temp;
      state.isDirty = true;
      renderCanvas();
      _notifyChange();
    }
  }

  function moveLayerDown(id) {
    const el = state.elements.find(e => e.id === id);
    if (!el) return;
    const siblings = state.elements.filter(e => e.parentId === el.parentId).sort((a,b)=>a.zIndex-b.zIndex);
    const idx = siblings.findIndex(e => e.id === id);
    if (idx > 0) {
      _pushHistory();
      const prev = siblings[idx - 1];
      const temp = el.zIndex;
      el.zIndex = prev.zIndex;
      prev.zIndex = temp;
      state.isDirty = true;
      renderCanvas();
      _notifyChange();
    }
  }

  // ========================================================
  // 親子関係
  // ========================================================
  function setParent(childId, parentId) {
    const child = state.elements.find(e => e.id === childId);
    if (!child || childId === parentId) return;
    
    // 循環参照チェック
    let curr = parentId;
    while(curr) {
      if (curr === childId) return; // 循環するのでNG
      const p = state.elements.find(e => e.id === curr);
      curr = p ? p.parentId : null;
    }

    _pushHistory();
    const oldAbs = _getAbsoluteRect(child);
    child.parentId = parentId;
    
    // ローカル座標の再計算
    const newParentAbs = parentId ? _getAbsoluteRect(state.elements.find(e => e.id === parentId)) : {x:0, y:0};
    child.x = oldAbs.x - newParentAbs.x;
    child.y = oldAbs.y - newParentAbs.y;
    child.zIndex = state.elements.filter(e => e.parentId === parentId).length;

    state.isDirty = true;
    renderCanvas();
    _updateSelectionOverlay();
    _notifyChange();
  }

  // ========================================================
  // キャンバスサイズ変更
  // ========================================================
  function setCanvasSize(w, h) {
    state.canvasWidth = w;
    state.canvasHeight = h;
    state._canvas.style.width = w + 'px';
    state._canvas.style.height = h + 'px';
    _notifyChange();
  }

  // ========================================================
  // Undo / Redo
  // ========================================================
  function _pushHistory() {
    // 現在位置より先の履歴を破棄
    state.history = state.history.slice(0, state.historyIndex + 1);
    state.history.push(JSON.stringify(state.elements));
    if (state.history.length > state.HISTORY_MAX) {
      state.history.shift();
    }
    state.historyIndex = state.history.length - 1;
  }

  function undo() {
    if (state.historyIndex <= 0) return;
    state.historyIndex--;
    state.elements = JSON.parse(state.history[state.historyIndex]);
    state.selectedId = null;
    state.isDirty = true;
    renderCanvas();
    _notifyChange();
    _notifySelect();
  }

  function redo() {
    if (state.historyIndex >= state.history.length - 1) return;
    state.historyIndex++;
    state.elements = JSON.parse(state.history[state.historyIndex]);
    state.isDirty = true;
    renderCanvas();
    _notifyChange();
    _notifySelect();
  }

  // ========================================================
  // JSON エクスポート
  // ========================================================
  function exportJSON() {
    const compIds = new Set(state.elements.map(e => e.templateId));
    const components = [];
    for (const id of compIds) {
      const tpl = window.getTemplate(id);
      if (!tpl) continue;
      components.push({
        id: tpl.id,
        name: tpl.name,
        role: tpl.role,
        importance: tpl.importance,
        viewBox: [0, 0, tpl.defaultSize.width, tpl.defaultSize.height],
        layers: (tpl.component && tpl.component.layers) ? tpl.component.layers : [],
      });
    }

    const instancesMap = {};
    const rootInstances = [];
    state.elements.forEach(el => {
      const instance = {
        id: el.id,
        componentId: el.templateId,
        offset: { x: Math.round(el.x), y: Math.round(el.y) },
        size: { width: Math.round(el.width), height: Math.round(el.height) },
        role: el.role,
        importance: el.importance,
        state: el.state,
        zIndex: el.zIndex,
      };
      if (el.props.text) instance.overrideText = el.props.text;
      if (el.props.fillColor) instance.overrideFill = el.props.fillColor;
      if (el.props.imagePath) instance.imagePath = el.props.imagePath;
      if (el.props.imageNormal) instance.imageNormal = el.props.imageNormal;
      if (el.props.imagePressed) instance.imagePressed = el.props.imagePressed;
      
      instancesMap[el.id] = instance;
    });

    state.elements.forEach(el => {
      if (el.parentId && instancesMap[el.parentId]) {
        if (!instancesMap[el.parentId].children) instancesMap[el.parentId].children = [];
        instancesMap[el.parentId].children.push(instancesMap[el.id]);
      } else {
        rootInstances.push(instancesMap[el.id]);
      }
    });

    return {
      version: '0.4.0',
      assetType: 'screen',
      metadata: {
        name: state.currentFilePath
          ? state.currentFilePath.split('/').pop().replace('.json', '')
          : 'New Screen',
      },
      canvas: { width: state.canvasWidth, height: state.canvasHeight },
      components,
      instances: rootInstances,
    };
  }

  // ========================================================
  // JSON ロード
  // ========================================================
  function loadJSON(data) {
    _pushHistory();
    state.elements = [];
    _idCounter = 0;
    state.selectedId = null;

    if (data.canvas) {
      state.canvasWidth = data.canvas.width || 1280;
      state.canvasHeight = data.canvas.height || 720;
      state._canvas.style.width = state.canvasWidth + 'px';
      state._canvas.style.height = state.canvasHeight + 'px';
    }

    // 動的に既存JSON内の独自コンポーネントをテンポラリ登録
    if (Array.isArray(data.components)) {
      for (const comp of data.components) {
        if (!window.getTemplate(comp.id)) {
          window.TEMPLATES.push({
            id: comp.id,
            name: comp.metadata?.name || comp.id,
            category: 'コンテナ',
            icon: '📦',
            defaultSize: { 
              width: comp.viewBox ? comp.viewBox[2] : 200, 
              height: comp.viewBox ? comp.viewBox[3] : 200 
            },
            defaultProps: {
              fillColor: 'rgba(255,255,255,0.05)',
              strokeColor: '#666',
              strokeWidth: 2,
              radius: 4,
              opacity: 1
            },
            role: 'container',
            importance: 'secondary',
            state: 'default',
            propFields: ['fillColor', 'strokeColor', 'strokeWidth', 'opacity'],
            component: comp // Export時に元のlayer構造を維持するため保持
          });
        }
      }
    }

    function flatten(nodes, parentId) {
      if (!Array.isArray(nodes)) return;
      for (const inst of nodes) {
        const tpl = window.getTemplate(inst.componentId);
        if (!tpl) continue;
        const el = {
          id: inst.id || `el-${++_idCounter}`,
          parentId: parentId,
          templateId: inst.componentId,
          name: inst.name || tpl.name,
          x: inst.offset ? inst.offset.x : 0,
          y: inst.offset ? inst.offset.y : 0,
          width: inst.size ? inst.size.width : tpl.defaultSize.width,
          height: inst.size ? inst.size.height : tpl.defaultSize.height,
          zIndex: inst.zIndex || 0,
          role: inst.role || tpl.role,
          importance: inst.importance || tpl.importance,
          state: inst.state || tpl.state,
          props: { ...tpl.defaultProps },
        };
        if (inst.overrideText) el.props.text = inst.overrideText;
        if (inst.overrideFill) el.props.fillColor = inst.overrideFill;
        if (inst.imagePath) el.props.imagePath = inst.imagePath;
        if (inst.imageNormal) el.props.imageNormal = inst.imageNormal;
        if (inst.imagePressed) el.props.imagePressed = inst.imagePressed;
        
        state.elements.push(el);
        if (inst.children) flatten(inst.children, el.id);
      }
    }
    
    if (data.instances) {
      flatten(data.instances, null);
      state.elements.sort((a, b) => a.zIndex - b.zIndex);
    }

    state.isDirty = false;
    renderCanvas();
    _notifyChange();
    _notifySelect();
  }

  // ========================================================
  // レンダリング
  // ========================================================
  function renderCanvas() {
    const canvas = state._canvas;
    // 選択オーバーレイを除いた子要素を削除
    const toRemove = [...canvas.children].filter(c => !c.id.startsWith('selection-overlay'));
    toRemove.forEach(c => canvas.removeChild(c));

    // zIndex順に描画
    const sorted = [...state.elements].sort((a, b) => a.zIndex - b.zIndex);
    for (const el of sorted) {
      _renderElement(el);
    }
    _updateSelectionOverlay();
    _notifyLayerChange();
  }

  function _renderElement(el) {
    const canvas = state._canvas;
    let div = document.querySelector(`[data-id="${el.id}"]`);
    if (!div) {
      div = document.createElement('div');
      div.setAttribute('data-id', el.id);
      div.className = 'canvas-element';
      div.style.position = 'absolute';
      div.style.boxSizing = 'border-box';
      
      const visualLayer = document.createElement('div');
      visualLayer.className = 'visual-layer';
      visualLayer.style.width = '100%';
      visualLayer.style.height = '100%';
      visualLayer.style.pointerEvents = 'none';
      div.appendChild(visualLayer);

      const childrenLayer = document.createElement('div');
      childrenLayer.className = 'children-layer';
      childrenLayer.style.position = 'absolute';
      childrenLayer.style.inset = '0';
      childrenLayer.style.pointerEvents = 'none';
      div.appendChild(childrenLayer);
      
      _attachElementEvents(div);
    }
    
    // Parent resolving
    let parentNode = canvas;
    if (el.parentId) {
      const pDiv = document.querySelector(`[data-id="${el.parentId}"]`);
      if (pDiv) parentNode = pDiv.querySelector('.children-layer');
    }
    
    if (div.parentNode !== parentNode) {
      if (parentNode === canvas) {
        const sel = canvas.querySelector('#selection-overlay');
        if (sel) canvas.insertBefore(div, sel);
        else canvas.appendChild(div);
      } else {
        parentNode.appendChild(div);
      }
    }

    div.style.left = el.x + 'px';
    div.style.top = el.y + 'px';
    div.style.width = el.width + 'px';
    div.style.height = el.height + 'px';
    div.style.zIndex = el.zIndex;
    div.style.opacity = el.props.opacity ?? 1;

    const visualLayer = div.querySelector('.visual-layer');
    _applyVisual(visualLayer, el);
  }

  function _applyVisual(div, el) {
    const tpl = window.getTemplate(el.templateId);
    if (!tpl) return;
    div.innerHTML = '';
    div.style.background = '';
    div.style.border = '';
    div.style.borderRadius = '';
    div.style.display = 'flex';
    div.style.alignItems = 'center';
    div.style.justifyContent = 'center';
    div.style.boxSizing = 'border-box';
    div.style.overflow = 'hidden';

    const p = el.props;
    const vt = tpl.visualType;

    if (vt === 'image' || vt === 'sprite_button') {
      const src = p.imageNormal || p.imagePath || '';
      if (src) {
        div.style.backgroundImage = `url("file://${state.workspaceDir}/${src}")`;
        div.style.backgroundSize = p.objectFit || 'contain';
        div.style.backgroundPosition = 'center';
        div.style.backgroundRepeat = 'no-repeat';
      } else {
        div.style.background = 'rgba(0,0,0,0.5)';
        const ph = document.createElement('div');
        ph.style.cssText = 'color:#888;font-size:10px;text-align:center;';
        ph.textContent = 'No Image';
        div.appendChild(ph);
      }
      if (vt === 'sprite_button' && p.text) {
        const span = document.createElement('div');
        span.style.cssText = `font-size:${p.fontSize || 16}px;color:${p.textColor || '#fff'};font-weight:bold;z-index:1;text-shadow:0 1px 2px #000;`;
        span.textContent = p.text;
        div.appendChild(span);
      }
    } else if (vt === 'toggle') {
      // トグルスイッチ
      div.style.background = p.trackColor || '#3a3a3a';
      div.style.borderRadius = (p.radius || 20) + 'px';
      div.style.padding = '4px';
      div.style.justifyContent = p.value ? 'flex-end' : 'flex-start';
      const knob = document.createElement('div');
      knob.style.cssText = `width:${el.height - 8}px;height:${el.height - 8}px;border-radius:50%;background:${p.fillColor || '#2ecc71'};flex-shrink:0;`;
      div.appendChild(knob);
    } else if (vt === 'checkbox') {
      // チェックボックス
      div.style.background = (p.value ? (p.fillColor || '#3a86ff') : (p.trackColor || '#222'));
      div.style.borderRadius = (p.radius || 4) + 'px';
      div.style.border = `${p.strokeWidth || 2}px solid ${p.strokeColor || '#555'}`;
      if (p.value) {
        const check = document.createElement('div');
        check.style.cssText = `width:40%;height:70%;border:solid ${p.textColor || '#fff'};border-width:0 3px 3px 0;transform:rotate(45deg) translate(-10%, -20%);`;
        div.appendChild(check);
      }
    } else if (vt === 'slider') {
      // スライダー
      const v = Math.max(0, Math.min(1, p.value || 0.5));
      div.style.background = 'transparent';
      const track = document.createElement('div');
      track.style.cssText = `position:absolute;top:50%;left:0;width:100%;height:${p.strokeWidth || 4}px;background:${p.trackColor || '#333'};transform:translateY(-50%);border-radius:2px;`;
      const fill = document.createElement('div');
      fill.style.cssText = `position:absolute;top:0;left:0;width:${v*100}%;height:100%;background:${p.fillColor || '#3a86ff'};border-radius:2px;`;
      track.appendChild(fill);
      div.appendChild(track);
      
      const knob = document.createElement('div');
      const knobSize = p.radius || 20;
      knob.style.cssText = `position:absolute;top:50%;left:${v*100}%;width:${knobSize}px;height:${knobSize}px;background:${p.textColor || '#fff'};border-radius:50%;transform:translate(-50%, -50%);box-shadow:0 1px 4px rgba(0,0,0,0.5);`;
      div.appendChild(knob);
    } else if (vt === 'radial') {
      // 円形ゲージ（CSSで近似）
      const v = Math.max(0, Math.min(1, p.value || 0.3));
      div.style.borderRadius = '50%';
      div.style.background = `conic-gradient(${p.fillColor || '#a855f7'} ${v * 360}deg, ${p.trackColor || '#1a1a2a'} 0deg)`;
      div.style.border = `${p.strokeWidth || 2}px solid ${p.strokeColor || '#c084fc'}`;
      const inner = document.createElement('div');
      inner.style.cssText = `width:56%;height:56%;border-radius:50%;background:#1e1e1e;display:flex;align-items:center;justify-content:center;color:#fff;font-size:10px;`;
      inner.textContent = Math.round(v * 100) + '%';
      div.appendChild(inner);
    } else if (tpl.category === 'ゲージ') {
      // プログレスバー
      const v = Math.max(0, Math.min(1, p.value || 0.75));
      const r = p.radius || 12;
      div.style.background = p.trackColor || '#1a2a1a';
      div.style.borderRadius = r + 'px';
      div.style.padding = '0';
      div.style.justifyContent = 'flex-start';
      const fill = document.createElement('div');
      fill.style.cssText = `width:${v * 100}%;height:100%;background:${p.fillColor || '#2ecc71'};border-radius:${r}px;transition:width 0.3s;`;
      div.appendChild(fill);
    } else if (vt === 'grid') {
      // グリッドビュー（ダミーセルを描画してレイアウトを表現）
      div.style.background = p.fillColor || 'transparent';
      if (p.strokeWidth && p.strokeColor && p.strokeColor !== 'transparent') {
        div.style.border = `${p.strokeWidth}px solid ${p.strokeColor}`;
      }
      div.style.position = 'relative';
      
      const cols = Math.max(1, parseInt(p.columns || 3));
      const spX = parseInt(p.spacingX || 0);
      const spY = parseInt(p.spacingY || 0);
      const cellH = parseInt(p.cellHeight || 80);
      
      // 内側のパディングを考慮（簡易的に0とする）
      const availableW = Math.max(0, el.width - spX * (cols - 1));
      const cellW = availableW / cols;
      
      const c = p.strokeColor || '#444';
      
      // ダミーのセル枠を描画
      const gridContainer = document.createElement('div');
      gridContainer.style.cssText = `position:absolute;inset:0;pointer-events:none;display:flex;flex-wrap:wrap;gap:${spY}px ${spX}px;align-content:flex-start;padding:0;`;
      
      // 画面に収まる程度のダミー数（最大20個程度）
      const rowsToFit = Math.ceil(el.height / (cellH + spY)) + 1;
      const dummyCount = Math.min(20, cols * rowsToFit);
      
      for(let i=0; i<dummyCount; i++) {
        const cell = document.createElement('div');
        cell.style.cssText = `width:${cellW}px;height:${cellH}px;border:1px dashed ${c};box-sizing:border-box;opacity:0.3;`;
        gridContainer.appendChild(cell);
      }
      div.appendChild(gridContainer);
      
      const label = document.createElement('div');
      label.style.cssText = `position:absolute;top:8px;left:12px;font-size:11px;color:${c};font-family:sans-serif;pointer-events:none;background:rgba(0,0,0,0.5);padding:2px 4px;border-radius:2px;z-index:2;`;
      label.textContent = `Grid View (${cols} cols)`;
      div.appendChild(label);
    } else if (tpl.category === 'コンテナ') {
      // パネル系
      const r = p.radius || 0;
      div.style.background = p.fillColor || '#252526';
      div.style.borderRadius = r + 'px';
      if (p.strokeWidth && p.strokeColor && p.strokeColor !== 'transparent') {
        div.style.border = `${p.strokeWidth}px solid ${p.strokeColor}`;
      }
      // コンテナ名を薄く表示
      const label = document.createElement('div');
      label.style.cssText = `position:absolute;top:8px;left:12px;font-size:11px;color:${p.strokeColor || '#666'};font-family:sans-serif;pointer-events:none;`;
      label.textContent = tpl.name;
      div.style.position = 'relative';
      div.appendChild(label);
    } else if (tpl.category === 'テキスト') {
      // テキスト系
      div.style.background = 'transparent';
      div.style.borderRadius = '0';
      div.style.justifyContent = p.textAlign === 'left' ? 'flex-start' : p.textAlign === 'right' ? 'flex-end' : 'center';
      const span = document.createElement('div');
      span.style.cssText = `font-size:${p.fontSize || 18}px;color:${p.textColor || '#ffffff'};font-family:sans-serif;font-weight:${(p.fontSize || 18) > 20 ? 'bold' : 'normal'};width:100%;padding:0 4px;text-align:${p.textAlign || 'left'};white-space:nowrap;overflow:hidden;text-overflow:ellipsis;`;
      span.textContent = p.text || tpl.name;
      div.appendChild(span);
    } else {
      // ボタン・バッジ・フィードバック等
      const r = p.radius || 8;
      div.style.background = p.fillColor || '#3a86ff';
      div.style.borderRadius = r + 'px';
      if (p.strokeWidth && p.strokeColor && p.strokeColor !== 'transparent') {
        div.style.border = `${p.strokeWidth}px solid ${p.strokeColor}`;
      }
      const span = document.createElement('div');
      span.style.cssText = `font-size:${p.fontSize || 16}px;color:${p.textColor || '#fff'};font-family:sans-serif;font-weight:bold;text-align:center;padding:0 8px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;`;
      span.textContent = p.text || tpl.name;
      div.appendChild(span);
    }
  }

  function _getAbsoluteRect(el) {
    let x = el.x, y = el.y;
    let curr = state.elements.find(e => e.id === el.parentId);
    while (curr) {
      x += curr.x;
      y += curr.y;
      curr = state.elements.find(e => e.id === curr.parentId);
    }
    return { x, y, width: el.width, height: el.height };
  }

  // ========================================================
  // 選択オーバーレイ
  // ========================================================
  function _updateSelectionOverlay() {
    const sel = document.getElementById('selection-overlay');
    if (!sel) return;
    const el = _selected();
    if (!el) {
      sel.style.display = 'none';
      return;
    }
    const rect = _getAbsoluteRect(el);
    sel.style.display = 'block';
    sel.style.left   = (rect.x - 2) + 'px';
    sel.style.top    = (rect.y - 2) + 'px';
    sel.style.width  = (rect.width + 4) + 'px';
    sel.style.height = (rect.height + 4) + 'px';
  }

  // ========================================================
  // イベント (クリック・ドラッグ)
  // ========================================================
  function _setupCanvasEvents() {
    const canvas = state._canvas;
    // キャンバスの空白クリック → 選択解除
    canvas.addEventListener('pointerdown', (e) => {
      if (e.target === canvas) {
        deselect();
      }
    });

    // リサイズハンドル
    const sel = document.getElementById('selection-overlay');
    if (sel) {
      sel.querySelectorAll('.handle').forEach(h => {
        h.addEventListener('pointerdown', _onHandleDown);
      });
    }

    // キーボードショートカット
    document.addEventListener('keydown', (e) => {
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
      if ((e.ctrlKey || e.metaKey) && e.key === 'z') { undo(); e.preventDefault(); }
      if ((e.ctrlKey || e.metaKey) && (e.key === 'y' || (e.shiftKey && e.key === 'z'))) { redo(); e.preventDefault(); }
      if (e.key === 'Delete' || e.key === 'Backspace') { deleteSelected(); e.preventDefault(); }
      if (e.key === 'Escape') { deselect(); }
      // 矢印キーでの微調整
      const el = _selected();
      if (el) {
        const step = e.shiftKey ? 10 : 1;
        if (e.key === 'ArrowLeft')  { _pushHistory(); el.x -= step; _renderElement(el); _updateSelectionOverlay(); _notifyChange(); _notifySelect(); e.preventDefault(); }
        if (e.key === 'ArrowRight') { _pushHistory(); el.x += step; _renderElement(el); _updateSelectionOverlay(); _notifyChange(); _notifySelect(); e.preventDefault(); }
        if (e.key === 'ArrowUp')    { _pushHistory(); el.y -= step; _renderElement(el); _updateSelectionOverlay(); _notifyChange(); _notifySelect(); e.preventDefault(); }
        if (e.key === 'ArrowDown')  { _pushHistory(); el.y += step; _renderElement(el); _updateSelectionOverlay(); _notifyChange(); _notifySelect(); e.preventDefault(); }
      }
    });
  }

  function _attachElementEvents(div) {
    div.addEventListener('pointerdown', _onElementDown);
  }

  function _onElementDown(e) {
    e.stopPropagation();
    const id = e.currentTarget.getAttribute('data-id');
    selectElement(id);

    const el = _selected();
    if (!el) return;

    const oldAbs = _getAbsoluteRect(el);

    _pushHistory();

    drag = {
      id,
      startMouseX: e.clientX,
      startMouseY: e.clientY,
      startAbsX: oldAbs.x,
      startAbsY: oldAbs.y,
    };

    document.addEventListener('pointermove', _onDragMove);
    document.addEventListener('pointerup', _onDragEnd, { once: true });
    e.currentTarget.setPointerCapture(e.pointerId);
  }

  function _onDragMove(e) {
    if (!drag) return;
    const el = state.elements.find(el => el.id === drag.id);
    if (!el) return;

    const zoom = state.zoom;
    const dx = (e.clientX - drag.startMouseX) / zoom;
    const dy = (e.clientY - drag.startMouseY) / zoom;

    const newAbsX = _snap(drag.startAbsX + dx);
    const newAbsY = _snap(drag.startAbsY + dy);
    
    const parentAbs = el.parentId ? _getAbsoluteRect(state.elements.find(e => e.id === el.parentId)) : {x:0, y:0};

    el.x = newAbsX - parentAbs.x;
    el.y = newAbsY - parentAbs.y;

    _renderElement(el);
    _updateSelectionOverlay();
    _notifySelect(); // プロパティパネルのX/Y更新
  }

  function _onDragEnd() {
    drag = null;
    document.removeEventListener('pointermove', _onDragMove);
    state.isDirty = true;
    _notifyChange();
  }

  // --- リサイズ ---
  function _onHandleDown(e) {
    e.stopPropagation();
    const el = _selected();
    if (!el) return;
    _pushHistory();

    resize = {
      dir: e.currentTarget.getAttribute('data-dir'),
      startMouseX: e.clientX,
      startMouseY: e.clientY,
      startX: el.x, startY: el.y,
      startW: el.width, startH: el.height,
    };
    document.addEventListener('pointermove', _onResizeMove);
    document.addEventListener('pointerup', _onResizeEnd, { once: true });
    document.body.style.cursor = _getCursorForDir(resize.dir);
  }

  function _onResizeMove(e) {
    if (!resize) return;
    const el = _selected();
    if (!el) return;
    const zoom = state.zoom;
    const dx = (e.clientX - resize.startMouseX) / zoom;
    const dy = (e.clientY - resize.startMouseY) / zoom;

    const d = resize.dir;
    let x = resize.startX, y = resize.startY;
    let w = resize.startW, h = resize.startH;

    if (d.includes('e')) w = Math.max(8, w + dx);
    if (d.includes('s')) h = Math.max(8, h + dy);
    if (d.includes('w')) { x = _snap(resize.startX + dx); w = Math.max(8, resize.startW - dx); }
    if (d.includes('n')) { y = _snap(resize.startY + dy); h = Math.max(8, resize.startH - dy); }

    el.x = x; el.y = y; el.width = w; el.height = h;
    _renderElement(el);
    _updateSelectionOverlay();
    _notifySelect();
  }

  function _onResizeEnd() {
    resize = null;
    document.removeEventListener('pointermove', _onResizeMove);
    document.body.style.cursor = '';
    state.isDirty = true;
    _notifyChange();
  }

  function _getCursorForDir(d) {
    const cursors = { n: 'n-resize', ne: 'ne-resize', e: 'e-resize', se: 'se-resize', s: 's-resize', sw: 'sw-resize', w: 'w-resize', nw: 'nw-resize' };
    return cursors[d] || 'default';
  }

  // ========================================================
  // ズーム
  // ========================================================
  function setZoom(z) {
    state.zoom = Math.max(0.1, Math.min(4, z));
    state._canvas.parentElement.style.transform = `scale(${state.zoom})`;
    state._canvas.parentElement.style.transformOrigin = 'top left';
    _notifyChange();
  }

  function zoomIn()  { setZoom(state.zoom * 1.25); }
  function zoomOut() { setZoom(state.zoom * 0.8); }
  function fitZoom() {
    const wrapper = document.getElementById('canvas-viewport');
    if (!wrapper) return;
    const wz = (wrapper.clientWidth  - 60) / state.canvasWidth;
    const hz = (wrapper.clientHeight - 60) / state.canvasHeight;
    setZoom(Math.min(wz, hz, 1));
  }

  // ========================================================
  // ヘルパー
  // ========================================================
  function _selected() {
    return state.elements.find(e => e.id === state.selectedId) || null;
  }

  const SNAP_GRID = 4;
  function _snap(v) {
    return Math.round(v / SNAP_GRID) * SNAP_GRID;
  }

  // ========================================================
  // コールバック通知
  // ========================================================
  let _onChangeCallback   = null;
  let _onSelectCallback   = null;
  let _onLayerCallback    = null;

  function onChangeCallback(fn)  { _onChangeCallback  = fn; }
  function onSelectCallback(fn)  { _onSelectCallback  = fn; }
  function onLayerCallback(fn)   { _onLayerCallback   = fn; }

  function _notifyChange()  { if (_onChangeCallback)  _onChangeCallback(state); }
  function _notifySelect()  { if (_onSelectCallback)  _onSelectCallback(_selected()); }
  function _notifyLayerChange() { if (_onLayerCallback) _onLayerCallback([...state.elements]); }

  // ========================================================
  // 公開API
  // ========================================================
  return {
    init,
    addElement,
    selectElement,
    deselect,
    deleteSelected,
    updateProp,
    moveLayerUp,
    moveLayerDown,
    setCanvasSize,
    undo,
    redo,
    exportJSON,
    loadJSON,
    renderCanvas,
    setZoom,
    zoomIn,
    zoomOut,
    fitZoom,
    onChangeCallback,
    onSelectCallback,
    onLayerCallback,
    setParent,
    getState: () => state,
    getSelected: () => _selected(),
  };
})();
