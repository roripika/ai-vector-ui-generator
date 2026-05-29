const fs = require('fs');
let code = fs.readFileSync('viewer/editor.js', 'utf8');

const targetStr = `} else if (tpl.category === 'コンテナ') {
      // パネル系`;

const injection = `} else if (tpl.component && tpl.component.layers && tpl.component.layers.length > 0) {
      // カスタムコンポーネントのレイヤーを解析して描画（プレビュー用）
      div.style.position = 'relative';
      div.style.background = 'transparent';
      
      tpl.component.layers.forEach(layer => {
        const shape = layer.shape || layer.type;
        const cdiv = document.createElement('div');
        cdiv.style.position = 'absolute';
        
        let x = 0, y = 0, w = 100, h = 100;
        if (layer.rect) {
          x = layer.rect.x || 0; y = layer.rect.y || 0;
          w = layer.rect.width || 0; h = layer.rect.height || 0;
        } else if (layer.position) {
          x = layer.position.x || 0; y = layer.position.y || 0;
        }
        
        cdiv.style.left = x + 'px';
        cdiv.style.top = y + 'px';
        if (layer.rect) {
          cdiv.style.width = w + 'px';
          cdiv.style.height = h + 'px';
        }
        
        if (layer.style && layer.style.fill) {
          cdiv.style.background = layer.style.fill;
        }
        if (layer.fillOpacity !== undefined) {
          cdiv.style.opacity = layer.fillOpacity / 255;
        }
        
        if (shape === 'roundedRect') {
          cdiv.style.borderRadius = (layer.cornerRadius || 0) + 'px';
        }
        
        if (shape === 'text' || layer.type === 'text') {
          cdiv.style.color = layer.color || '#fff';
          cdiv.style.fontSize = (layer.fontSize || (layer.text && layer.text.size) || 16) + 'px';
          cdiv.textContent = (layer.text && layer.text.value) || layer.text || '';
          cdiv.style.whiteSpace = 'nowrap';
          cdiv.style.background = 'transparent';
        }
        
        div.appendChild(cdiv);
      });
      
    `;

code = code.replace(targetStr, injection + targetStr);
fs.writeFileSync('viewer/editor.js', code);
