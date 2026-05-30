const fs = require('fs');
let code = fs.readFileSync('viewer/editor.js', 'utf8');

// Fix assetType check
code = code.replace(
  /if \(!data\.assetType \|\| data\.assetType !== 'screen'\) \{[\s\S]*?return;\n\s*\}/,
  `if (!data.instances && (!data.assetType || data.assetType !== 'screen')) {
      alert("This does not look like a valid ui_asset JSON.");
      return;
    }`
);

// Fix flatten function to support legacy JSON format
code = code.replace(
  /const tpl = window\.getTemplate\(inst\.componentId\);/,
  `const compId = inst.componentId || inst.templateId;
        let tpl = window.getTemplate(compId);
        if (!tpl) {
          // If totally unknown, create a dummy
          tpl = {
            id: compId,
            name: compId,
            category: 'コンテナ',
            icon: '📦',
            defaultSize: { width: 100, height: 100 },
            defaultProps: { fillColor: 'rgba(255,255,255,0.1)', strokeColor: '#666', strokeWidth: 1 },
            role: 'container',
            importance: 'secondary',
            state: 'default',
            propFields: ['fillColor', 'strokeColor']
          };
          window.TEMPLATES.push(tpl);
        }`
);

code = code.replace(
  /templateId: inst\.componentId,/,
  `templateId: compId,`
);

code = code.replace(
  /x: inst\.offset \? inst\.offset\.x : 0,/,
  `x: inst.offset ? inst.offset.x : (inst.x !== undefined ? inst.x : 0),`
);

code = code.replace(
  /y: inst\.offset \? inst\.offset\.y : 0,/,
  `y: inst.offset ? inst.offset.y : (inst.y !== undefined ? inst.y : 0),`
);

code = code.replace(
  /width: inst\.size \? inst\.size\.width : tpl\.defaultSize\.width,/,
  `width: inst.size ? inst.size.width : (inst.width !== undefined ? inst.width : tpl.defaultSize.width),`
);

code = code.replace(
  /height: inst\.size \? inst\.size\.height : tpl\.defaultSize\.height,/,
  `height: inst.size ? inst.size.height : (inst.height !== undefined ? inst.height : tpl.defaultSize.height),`
);

fs.writeFileSync('viewer/editor.js', code);
console.log("Fixed loadJSON to support legacy formats.");
