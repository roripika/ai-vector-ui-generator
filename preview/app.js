const splitToggle = document.getElementById("split-toggle");
const canvas = document.getElementById("canvas");

const panes = {
  a: buildPane("a"),
  b: buildPane("b"),
};

const patchInput = document.getElementById("patch-input");
const patchStatus = document.getElementById("status-patch");
const applyPatchA = document.getElementById("apply-patch-a");
const applyPatchB = document.getElementById("apply-patch-b");
const savePatch = document.getElementById("save-patch");

splitToggle.addEventListener("change", () => {
  if (splitToggle.checked) {
    canvas.classList.remove("single");
    document.getElementById("pane-b").style.display = "flex";
  } else {
    canvas.classList.add("single");
    document.getElementById("pane-b").style.display = "none";
  }
});

applyPatchA.addEventListener("click", () => {
  applyPatchToPane(panes.a, panes.a);
});

applyPatchB.addEventListener("click", () => {
  applyPatchToPane(panes.a, panes.b);
});

savePatch.addEventListener("click", () => {
  savePatchToFile();
});

function buildPane(key) {
  const pane = {
    key,
    fileInput: document.getElementById(`file-${key}`),
    pathInput: document.getElementById(`path-${key}`),
    loadButton: document.getElementById(`load-${key}`),
    status: document.getElementById(`status-${key}`),
    selection: document.getElementById(`selection-${key}`),
    meta: document.getElementById(`meta-${key}`),
    container: document.getElementById(`svg-${key}`),
    asset: null,
    instanceMap: {},
    componentMap: {},
  };

  pane.fileInput.addEventListener("change", async () => {
    if (!pane.fileInput.files.length) {
      return;
    }
    const file = pane.fileInput.files[0];
    try {
      const text = await file.text();
      const asset = JSON.parse(text);
      await compileAsset(pane, { asset });
    } catch (error) {
      setStatus(pane, `Error: ${error.message}`);
    }
  });

  pane.loadButton.addEventListener("click", async () => {
    const path = pane.pathInput.value.trim();
    if (!path) {
      setStatus(pane, "Error: path is empty");
      return;
    }
    await compileAsset(pane, { path });
  });

  return pane;
}

async function compileAsset(pane, payload) {
  setStatus(pane, "Loading...");
  pane.selection.textContent = "Selected: -";
  applyMeta(pane, null);
  pane.container.innerHTML = "";

  let response;
  try {
    response = await fetch("/api/compile", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  } catch (error) {
    setStatus(pane, `Error: ${error.message}`);
    return;
  }

  let data;
  try {
    data = await response.json();
  } catch (error) {
    setStatus(pane, "Error: invalid response");
    return;
  }

  if (!response.ok) {
    setStatus(pane, `Error: ${data.error || "failed"}`);
    return;
  }

  pane.asset = data.asset;
  pane.instanceMap = buildInstanceMap(data.asset);
  pane.componentMap = buildComponentMap(data.asset);
  pane.container.innerHTML = data.svg;
  setStatus(pane, `OK: ${pane.asset.assetType || "asset"}`);

  const svg = pane.container.querySelector("svg");
  if (svg) {
    svg.addEventListener("click", (event) => {
      const group = findGroup(event.target);
      if (!group) {
        pane.selection.textContent = "Selected: -";
        applyMeta(pane, null);
        return;
      }
      const componentId = resolveComponentId(pane, group.id);
      const meta = resolveMeta(pane, group.id);
      applyMeta(pane, { id: group.id, ...(meta || {}) });
      pane.selection.textContent = componentId
        ? `Selected: ${group.id} / ${componentId}`
        : `Selected: ${group.id}`;
    });
  }
}

function setStatus(pane, message) {
  pane.status.textContent = message;
}

function findGroup(node) {
  let current = node;
  while (current) {
    if (current.tagName && current.tagName.toLowerCase() === "g" && current.id) {
      return current;
    }
    if (current.tagName && current.tagName.toLowerCase() === "svg") {
      return null;
    }
    current = current.parentNode;
  }
  return null;
}

function buildInstanceMap(asset) {
  if (!asset || asset.assetType !== "screen") {
    return {};
  }
  const map = {};
  for (const instance of asset.instances || []) {
    if (instance.id && instance.componentId) {
      map[instance.id] = instance.componentId;
    }
  }
  return map;
}

function buildComponentMap(asset) {
  if (!asset || asset.assetType !== "screen") {
    return {};
  }
  const map = {};
  for (const component of asset.components || []) {
    if (component.id) {
      map[component.id] = component;
    }
  }
  return map;
}

function resolveComponentId(pane, groupId) {
  if (!pane.asset || pane.asset.assetType !== "screen") {
    return null;
  }
  if (!groupId) {
    return null;
  }
  const instanceId = groupId.split("--")[0];
  return pane.instanceMap[instanceId] || null;
}

function resolveMeta(pane, groupId) {
  if (!pane.asset || !groupId) {
    return null;
  }
  const asset = pane.asset;
  if (asset.assetType !== "screen") {
    const layer = findLayerById(asset.layers || [], groupId);
    return layer ? extractMeta(layer) : null;
  }

  const segments = groupId.split("--");
  const instanceId = segments[0];
  const instance = (asset.instances || []).find((item) => item.id === instanceId);
  if (!instance) {
    return null;
  }
  if (segments.length === 1) {
    return extractMeta(instance);
  }

  let component = pane.componentMap[instance.componentId];
  let currentMeta = null;
  let index = 1;

  while (component && index < segments.length) {
    const layerId = segments[index];
    const layer = findLayerById(component.layers || [], layerId);
    if (!layer) {
      break;
    }
    currentMeta = layer;
    if (isLayoutLayer(layer) && index + 1 < segments.length) {
      const itemId = segments[index + 1];
      const item = (layer.items || []).find((candidate) => candidate.id === itemId);
      if (item) {
        currentMeta = item;
        component = pane.componentMap[item.componentId];
        index += 2;
        continue;
      }
    }
    index += 1;
  }

  return currentMeta ? extractMeta(currentMeta) : extractMeta(instance);
}

function findLayerById(layers, layerId) {
  return layers.find((layer) => layer.id === layerId);
}

function isLayoutLayer(layer) {
  return (
    layer &&
    (layer.shape === "layoutRow" ||
      layer.shape === "layoutColumn" ||
      layer.shape === "layoutGrid")
  );
}

function extractMeta(item) {
  if (!item || typeof item !== "object") {
    return null;
  }
  return {
    role: item.role,
    importance: item.importance,
    state: item.state,
    constraints: item.constraints,
    layout_ref: item.layout_ref,
  };
}

function applyMeta(pane, meta) {
  const container = pane.meta;
  if (!container) {
    return;
  }
  const fields = ["id", "role", "importance", "state", "constraints", "layout_ref"];
  for (const field of fields) {
    const target = container.querySelector(`[data-field=\"${field}\"]`);
    if (!target) {
      continue;
    }
    const value = meta ? meta[field] : null;
    const text = formatMetaValue(value);
    target.textContent = text;
    target.title = text === "-" ? "" : text;
  }
}

function formatMetaValue(value) {
  if (value === undefined || value === null || value === "") {
    return "-";
  }
  if (typeof value === "object") {
    try {
      return JSON.stringify(value);
    } catch (error) {
      return String(value);
    }
  }
  return String(value);
}

function applyPatchToPane(sourcePane, targetPane) {
  if (!patchInput.value.trim()) {
    setPatchStatus("Patch is empty");
    return;
  }
  if (!sourcePane.asset) {
    setPatchStatus("Load a base JSON in Panel A");
    return;
  }

  let patch;
  try {
    patch = JSON.parse(patchInput.value);
  } catch (error) {
    setPatchStatus(`Patch error: ${error.message}`);
    return;
  }

  if (!Array.isArray(patch)) {
    setPatchStatus("Patch must be an array");
    return;
  }

  let nextAsset;
  try {
    nextAsset = applyJsonPatch(sourcePane.asset, patch);
  } catch (error) {
    setPatchStatus(`Patch apply error: ${error.message}`);
    return;
  }

  setPatchStatus("Patch applied");
  compileAsset(targetPane, { asset: nextAsset });
}

function setPatchStatus(message) {
  patchStatus.textContent = message;
}

function savePatchToFile() {
  if (!patchInput.value.trim()) {
    setPatchStatus("Patch is empty");
    return;
  }
  let patch;
  try {
    patch = JSON.parse(patchInput.value);
  } catch (error) {
    setPatchStatus(`Patch error: ${error.message}`);
    return;
  }
  const data = JSON.stringify(patch, null, 2);
  const blob = new Blob([data], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "ui_patch.json";
  link.click();
  URL.revokeObjectURL(url);
  setPatchStatus("Patch saved");
}

function applyJsonPatch(asset, patchOps) {
  let output = JSON.parse(JSON.stringify(asset));
  for (const op of patchOps) {
    if (!op || typeof op !== "object") {
      throw new Error("Invalid patch operation");
    }
    output = applyPatchOperation(output, op);
  }
  return output;
}

function applyPatchOperation(target, operation) {
  const { op, path, value } = operation;
  if (typeof op !== "string" || typeof path !== "string") {
    throw new Error("Patch operation must include op and path");
  }
  const segments = parsePointer(path);
  if (segments.length === 0) {
    if (op === "add" || op === "replace") {
      return value;
    }
    if (op === "remove") {
      throw new Error("Cannot remove root");
    }
    throw new Error(`Unsupported op: ${op}`);
  }

  const { parent, key } = resolveParent(target, segments);
  if (op === "add") {
    return applyAdd(parent, key, value, target);
  }
  if (op === "replace") {
    return applyReplace(parent, key, value, target);
  }
  if (op === "remove") {
    return applyRemove(parent, key, target);
  }
  throw new Error(`Unsupported op: ${op}`);
}

function parsePointer(pointer) {
  if (pointer === "") {
    return [];
  }
  if (!pointer.startsWith("/")) {
    throw new Error("Pointer must start with '/'");
  }
  return pointer
    .slice(1)
    .split("/")
    .map((segment) => segment.replace(/~1/g, "/").replace(/~0/g, "~"));
}

function resolveParent(target, segments) {
  let parent = target;
  for (let index = 0; index < segments.length - 1; index += 1) {
    const key = segments[index];
    if (parent == null) {
      throw new Error("Invalid path");
    }
    parent = parent[key];
  }
  return { parent, key: segments[segments.length - 1] };
}

function applyAdd(parent, key, value, target) {
  if (Array.isArray(parent)) {
    if (key === "-") {
      parent.push(value);
    } else {
      const index = toIndex(key);
      parent.splice(index, 0, value);
    }
    return target;
  }
  if (typeof parent === "object" && parent !== null) {
    parent[key] = value;
    return target;
  }
  throw new Error("Cannot add to non-container");
}

function applyReplace(parent, key, value, target) {
  if (Array.isArray(parent)) {
    const index = toIndex(key);
    parent[index] = value;
    return target;
  }
  if (typeof parent === "object" && parent !== null) {
    if (!(key in parent)) {
      throw new Error("Replace target does not exist");
    }
    parent[key] = value;
    return target;
  }
  throw new Error("Cannot replace in non-container");
}

function applyRemove(parent, key, target) {
  if (Array.isArray(parent)) {
    const index = toIndex(key);
    parent.splice(index, 1);
    return target;
  }
  if (typeof parent === "object" && parent !== null) {
    if (!(key in parent)) {
      throw new Error("Remove target does not exist");
    }
    delete parent[key];
    return target;
  }
  throw new Error("Cannot remove from non-container");
}

function toIndex(key) {
  if (key === "-") {
    throw new Error("'-' is not allowed for this operation");
  }
  const index = Number.parseInt(key, 10);
  if (Number.isNaN(index)) {
    throw new Error("Array index must be a number");
  }
  return index;
}
