const promptInput = document.getElementById("prompt-input");
const generateButton = document.getElementById("generate");
const clearButton = document.getElementById("clear");
const statusLabel = document.getElementById("status");
const preview = document.getElementById("preview");
const jsonOutput = document.getElementById("json-output");
const templateId = document.getElementById("template-id");
const assetType = document.getElementById("asset-type");
const selectionSummary = document.getElementById("selection-summary");
const selectionList = document.getElementById("selection-list");
const selectionRationale = document.getElementById("selection-rationale");
const gaugeEditor = document.getElementById("gauge-editor");
const gaugeTarget = document.getElementById("gauge-target");
const shapeProfile = document.getElementById("shape-profile");
const shapeSides = document.getElementById("shape-sides");
const shapeSegments = document.getElementById("shape-segments");
const shapeThickness = document.getElementById("shape-thickness");
const applyGauge = document.getElementById("apply-gauge");
const shapeSidesField = document.getElementById("shape-sides-field");
const shapeSegmentsField = document.getElementById("shape-segments-field");
const constraintsEditor = document.getElementById("constraints-editor");
const constraintsTarget = document.getElementById("constraints-target");
const constraintFlags = document.getElementById("constraint-flags");
const constraintParams = document.getElementById("constraint-params");
const applyConstraints = document.getElementById("apply-constraints");
const filenameInput = document.getElementById("filename-input");
const tagsInput = document.getElementById("tags-input");
const tagsHint = document.getElementById("tags-hint");
const tagsWarning = document.getElementById("tags-warning");
const saveButton = document.getElementById("save-repo");
const saveStatus = document.getElementById("save-status");
const refreshGenerated = document.getElementById("refresh-generated");
const generatedList = document.getElementById("generated-list");
const copyButton = document.getElementById("copy-json");
const downloadButton = document.getElementById("download-json");

let currentJson = "{}";
let currentAsset = null;
let allowedTags = [];
let currentTemplateId = "-";
let gaugeLayers = [];
let constraintTargets = [];
let allowedConstraintFlags = [];

function setStatus(message) {
  statusLabel.textContent = message;
}

function setPreview(svg) {
  preview.innerHTML = svg || '<div class="empty">ここにSVGプレビューが表示されます</div>';
}

function setJson(asset, id) {
  const normalized = normalizeAssetConstraints(asset || {});
  currentAsset = normalized;
  currentTemplateId = id || "-";
  currentJson = JSON.stringify(normalized, null, 2);
  jsonOutput.textContent = currentJson;
  templateId.textContent = `template: ${currentTemplateId}`;
  assetType.textContent = normalized && normalized.assetType ? `type: ${normalized.assetType}` : "type: -";

  if (normalized && normalized.metadata && Array.isArray(normalized.metadata.tags)) {
    tagsInput.value = normalized.metadata.tags.join(", ");
  }
  updateGaugeEditor(normalized);
  updateConstraintEditor(normalized);
}

function normalizeConstraintItem(item) {
  if (!item || typeof item !== "object") {
    return;
  }
  const flags = Array.isArray(item.constraint_flags) ? [...item.constraint_flags] : [];
  const params =
    item.constraint_params && typeof item.constraint_params === "object"
      ? { ...item.constraint_params }
      : {};
  const legacy = item.constraints;

  if (Array.isArray(legacy)) {
    for (const entry of legacy) {
      if (typeof entry === "string" && !flags.includes(entry)) {
        flags.push(entry);
      }
    }
  } else if (legacy && typeof legacy === "object") {
    for (const [key, value] of Object.entries(legacy)) {
      if (value === true || value === null) {
        if (!flags.includes(key)) {
          flags.push(key);
        }
      } else if (!(key in params)) {
        params[key] = value;
      }
    }
  }

  if (flags.length) {
    item.constraint_flags = flags;
  }
  if (Object.keys(params).length) {
    item.constraint_params = params;
  }
}

function normalizeAssetConstraints(asset) {
  if (!asset || typeof asset !== "object") {
    return asset;
  }

  normalizeConstraintItem(asset);

  const layers = Array.isArray(asset.layers) ? asset.layers : [];
  normalizeConstraintLayers(layers);

  const components = Array.isArray(asset.components) ? asset.components : [];
  for (const component of components) {
    normalizeConstraintItem(component);
    normalizeConstraintLayers(Array.isArray(component.layers) ? component.layers : []);
  }

  const instances = Array.isArray(asset.instances) ? asset.instances : [];
  for (const instance of instances) {
    normalizeConstraintItem(instance);
  }

  return asset;
}

function normalizeConstraintLayers(layers) {
  for (const layer of layers) {
    if (!layer || typeof layer !== "object") continue;
    normalizeConstraintItem(layer);
    if (
      layer.shape === "layoutRow" ||
      layer.shape === "layoutColumn" ||
      layer.shape === "layoutGrid"
    ) {
      for (const item of layer.items || []) {
        normalizeConstraintItem(item);
      }
    }
  }
}

function setSelection(selection) {
  if (!selection) {
    selectionSummary.textContent = "template: -";
    selectionList.innerHTML = "";
    selectionRationale.textContent = "";
    return;
  }
  const selected = selection.selected || "-";
  const reason = selection.reason ? ` (${selection.reason})` : "";
  selectionSummary.textContent = `selected: ${selected}${reason}`;

  const candidates = Array.isArray(selection.candidates) ? selection.candidates : [];
  selectionList.innerHTML = "";
  for (const candidate of candidates) {
    const item = document.createElement("li");
    const matches = Array.isArray(candidate.matches) ? candidate.matches.join(", ") : "";
    const tags = Array.isArray(candidate.tag_matches) ? candidate.tag_matches.join(", ") : "";
    const parts = [candidate.id];
    if (matches) {
      parts.push(`keyword: ${matches}`);
    }
    if (tags) {
      parts.push(`tag: ${tags}`);
    }
    item.textContent = parts.join(" | ");
    selectionList.appendChild(item);
  }

  const rationale = selection.rationale || {};
  const intent = rationale.intent || "-";
  const when = Array.isArray(rationale.when) && rationale.when.length ? rationale.when.join(" / ") : "-";
  const tagMatches =
    Array.isArray(rationale.matched_tags) && rationale.matched_tags.length
      ? rationale.matched_tags.join(", ")
      : "-";
  selectionRationale.innerHTML = `
    <div>intent: ${intent}</div>
    <div>when: ${when}</div>
    <div>tag match: ${tagMatches}</div>
  `;
}

function setSaveStatus(message, isError = false) {
  saveStatus.textContent = message;
  saveStatus.style.color = isError ? "#f07b73" : "var(--accent-2)";
}

function formatTimestamp(date) {
  const pad = (value) => String(value).padStart(2, "0");
  return `${date.getFullYear()}${pad(date.getMonth() + 1)}${pad(date.getDate())}_${pad(
    date.getHours()
  )}${pad(date.getMinutes())}${pad(date.getSeconds())}`;
}

function buildDefaultFilename(asset, template) {
  const type = asset && asset.assetType ? asset.assetType : "asset";
  const id = template || "template";
  return `${type}_${id}_${formatTimestamp(new Date())}.json`;
}

function collectSemanticTags(asset) {
  const roles = new Set();
  const importance = new Set();
  const states = new Set();

  function record(item) {
    if (!item || typeof item !== "object") return;
    if (typeof item.role === "string") roles.add(item.role);
    if (typeof item.importance === "string") importance.add(item.importance);
    if (typeof item.state === "string") states.add(item.state);
  }

  if (!asset) return { roles, importance, states };
  record(asset);
  for (const component of asset.components || []) {
    record(component);
    for (const layer of component.layers || []) {
      record(layer);
      for (const item of layer.items || []) {
        record(item);
      }
    }
  }
  for (const instance of asset.instances || []) {
    record(instance);
  }

  return { roles, importance, states };
}

function updateTagHints(asset) {
  const collected = collectSemanticTags(asset);
  const parts = [];
  if (collected.roles.size) {
    parts.push(`role: ${Array.from(collected.roles).join(", ")}`);
  }
  if (collected.importance.size) {
    parts.push(`importance: ${Array.from(collected.importance).join(", ")}`);
  }
  if (collected.states.size) {
    parts.push(`state: ${Array.from(collected.states).join(", ")}`);
  }
  tagsHint.textContent = parts.length ? `候補: ${parts.join(" | ")}` : "候補: -";
}

function findGaugeLayers(asset) {
  const layers = [];
  if (!asset || typeof asset !== "object") {
    return layers;
  }

  function record(layer, label) {
    if (!layer || typeof layer !== "object") return;
    if (layer.shape === "gauge") {
      layers.push({ label, layer });
    }
  }

  if (Array.isArray(asset.layers)) {
    for (const layer of asset.layers) {
      record(layer, layer.id || "gauge");
    }
  }

  if (Array.isArray(asset.components)) {
    for (const component of asset.components) {
      const prefix = component.id ? `${component.id} / ` : "";
      for (const layer of component.layers || []) {
        record(layer, `${prefix}${layer.id || "gauge"}`);
      }
    }
  }

  return layers;
}

function updateGaugeEditor(asset) {
  gaugeLayers = findGaugeLayers(asset);
  if (!gaugeLayers.length) {
    gaugeEditor.hidden = true;
    gaugeTarget.innerHTML = "";
    return;
  }

  gaugeEditor.hidden = false;
  const previous = gaugeTarget.value;
  gaugeTarget.innerHTML = "";
  gaugeLayers.forEach((entry, index) => {
    const option = document.createElement("option");
    option.value = String(index);
    option.textContent = entry.label;
    gaugeTarget.appendChild(option);
  });

  const nextIndex = previous && gaugeLayers[Number(previous)] ? Number(previous) : 0;
  gaugeTarget.value = String(nextIndex);
  setGaugeInputs(gaugeLayers[nextIndex].layer);
}

function findConstraintTargets(asset) {
  if (!asset || typeof asset !== "object") {
    return [];
  }
  if (Array.isArray(asset.instances)) {
    return asset.instances.map((instance) => ({
      label: `instance: ${instance.id}`,
      target: instance,
    }));
  }
  return [];
}

function updateConstraintEditor(asset) {
  constraintTargets = findConstraintTargets(asset);
  if (!constraintTargets.length) {
    constraintsEditor.hidden = true;
    constraintsTarget.innerHTML = "";
    return;
  }

  constraintsEditor.hidden = false;
  const previous = constraintsTarget.value;
  constraintsTarget.innerHTML = "";
  constraintTargets.forEach((entry, index) => {
    const option = document.createElement("option");
    option.value = String(index);
    option.textContent = entry.label;
    constraintsTarget.appendChild(option);
  });
  const nextIndex = previous && constraintTargets[Number(previous)] ? Number(previous) : 0;
  constraintsTarget.value = String(nextIndex);
  buildConstraintFlagOptions(constraintTargets[nextIndex].target);
  setConstraintInputs(constraintTargets[nextIndex].target);
}

function buildConstraintFlagOptions(target) {
  const currentFlags = Array.isArray(target.constraint_flags) ? target.constraint_flags : [];
  const flagSet = new Set(allowedConstraintFlags);
  currentFlags.forEach((flag) => flagSet.add(flag));
  const allFlags = Array.from(flagSet);

  constraintFlags.innerHTML = "";
  allFlags.forEach((flag) => {
    const label = document.createElement("label");
    const input = document.createElement("input");
    input.type = "checkbox";
    input.value = flag;
    label.appendChild(input);
    label.appendChild(document.createTextNode(flag));
    constraintFlags.appendChild(label);
  });
}

function setConstraintInputs(target) {
  const flags = Array.isArray(target.constraint_flags) ? target.constraint_flags : [];
  const params =
    target.constraint_params && typeof target.constraint_params === "object"
      ? target.constraint_params
      : {};

  for (const checkbox of constraintFlags.querySelectorAll("input[type=\"checkbox\"]")) {
    checkbox.checked = flags.includes(checkbox.value);
  }
  constraintParams.value = Object.keys(params).length ? JSON.stringify(params, null, 2) : "";
}

function setGaugeInputs(layer) {
  const allowedProfiles = new Set([
    "radial",
    "segmented",
    "polygon",
    "custom_svg",
    "unknown",
  ]);
  const rawProfile = typeof layer.shape_profile === "string" ? layer.shape_profile : "radial";
  const profile = allowedProfiles.has(rawProfile) ? rawProfile : "unknown";
  shapeProfile.value = profile;

  const params = layer.shape_params && typeof layer.shape_params === "object" ? layer.shape_params : {};
  shapeSides.value = Number.isFinite(Number(params.sides)) ? params.sides : "";
  shapeSegments.value = Number.isFinite(Number(params.segment_count)) ? params.segment_count : "";
  shapeThickness.value = Number.isFinite(Number(params.thickness)) ? params.thickness : "";
  updateGaugeParamVisibility(profile);
}

function updateGaugeParamVisibility(profile) {
  shapeSidesField.hidden = profile !== "polygon";
  shapeSegmentsField.hidden = profile !== "segmented";
}

async function compileAsset(asset) {
  setStatus("再レンダ中...");
  let response;
  try {
    response = await fetch("/api/compile", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ asset }),
    });
  } catch (error) {
    setStatus("再レンダに失敗しました");
    return;
  }

  const data = await response.json();
  if (!response.ok) {
    setStatus(`エラー: ${data.error || "failed"}`);
    return;
  }

  setPreview(data.svg);
  const selectedTemplate =
    data.asset && data.asset.metadata && data.asset.metadata.selected_templates
      ? data.asset.metadata.selected_templates[0]
      : currentTemplateId;
  setJson(data.asset, selectedTemplate);
  updateTagHints(data.asset);
  warnUnknownTags(parseTagsInput());
  setSaveStatus("未保存");
  setStatus("更新完了");
}

function parseTagsInput() {
  return tagsInput.value
    .split(",")
    .map((tag) => tag.trim())
    .filter((tag) => tag.length > 0);
}

function warnUnknownTags(tags) {
  if (!allowedTags.length) {
    tagsWarning.textContent = "";
    return;
  }
  const unknown = tags.filter((tag) => !allowedTags.includes(tag));
  tagsWarning.textContent = unknown.length ? `未登録タグ: ${unknown.join(", ")}` : "";
}

async function generateAsset() {
  const prompt = promptInput.value.trim();
  if (!prompt) {
    setStatus("プロンプトを入力してください");
    return;
  }
  setStatus("生成中...");

  let response;
  try {
    response = await fetch("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt }),
    });
  } catch (error) {
    setStatus(`通信エラー: ${error.message}`);
    return;
  }

  let data;
  try {
    data = await response.json();
  } catch (error) {
    setStatus("レスポンスが不正です");
    return;
  }

  if (!response.ok) {
    setStatus(`エラー: ${data.error || "failed"}`);
    return;
  }

  setStatus("生成完了");
  setPreview(data.svg);
  setJson(data.asset, data.templateId);
  setSelection(data.selection);
  filenameInput.value = buildDefaultFilename(data.asset, data.templateId);
  updateTagHints(data.asset);
  warnUnknownTags(parseTagsInput());
  setSaveStatus("未保存");
}

function clearAll() {
  promptInput.value = "";
  setStatus("待機中");
  setPreview("");
  setJson({}, "-");
  setSelection(null);
  filenameInput.value = "";
  tagsInput.value = "";
  tagsHint.textContent = "候補: -";
  tagsWarning.textContent = "";
  setSaveStatus("未保存");
}

function applyGaugeChanges() {
  if (!currentAsset || !gaugeLayers.length) {
    setStatus("ゲージが見つかりません");
    return;
  }

  const index = Number(gaugeTarget.value || 0);
  const entry = gaugeLayers[index];
  if (!entry) {
    setStatus("ゲージが選択されていません");
    return;
  }

  const profile = shapeProfile.value;
  entry.layer.shape_profile = profile;

  const params =
    entry.layer.shape_params && typeof entry.layer.shape_params === "object"
      ? { ...entry.layer.shape_params }
      : {};

  const thickness = Number.parseFloat(shapeThickness.value);
  if (Number.isFinite(thickness) && thickness >= 0) {
    params.thickness = thickness;
  } else {
    delete params.thickness;
  }

  if (profile === "polygon") {
    const sides = Number.parseInt(shapeSides.value, 10);
    if (Number.isFinite(sides) && sides >= 3) {
      params.sides = sides;
    } else {
      delete params.sides;
    }
  } else {
    delete params.sides;
  }

  if (profile === "segmented") {
    const segments = Number.parseInt(shapeSegments.value, 10);
    if (Number.isFinite(segments) && segments >= 1) {
      params.segment_count = segments;
    } else {
      delete params.segment_count;
    }
  } else {
    delete params.segment_count;
  }

  if (Object.keys(params).length) {
    entry.layer.shape_params = params;
  } else {
    delete entry.layer.shape_params;
  }

  compileAsset(currentAsset);
}

function applyConstraintChanges() {
  if (!currentAsset || !constraintTargets.length) {
    setStatus("constraints対象がありません");
    return;
  }

  const index = Number(constraintsTarget.value || 0);
  const entry = constraintTargets[index];
  if (!entry) {
    setStatus("constraints対象が選択されていません");
    return;
  }

  const flags = [];
  for (const checkbox of constraintFlags.querySelectorAll("input[type=\"checkbox\"]")) {
    if (checkbox.checked) {
      flags.push(checkbox.value);
    }
  }

  let params = {};
  if (constraintParams.value.trim()) {
    try {
      params = JSON.parse(constraintParams.value);
    } catch (error) {
      setStatus("constraint_params のJSONが不正です");
      return;
    }
  }

  if (flags.length) {
    entry.target.constraint_flags = flags;
  } else {
    delete entry.target.constraint_flags;
  }

  if (params && typeof params === "object" && Object.keys(params).length) {
    entry.target.constraint_params = params;
  } else {
    delete entry.target.constraint_params;
  }

  compileAsset(currentAsset);
}

copyButton.addEventListener("click", async () => {
  if (!currentJson || currentJson === "{}") {
    setStatus("JSONがありません");
    return;
  }
  try {
    await navigator.clipboard.writeText(currentJson);
    setStatus("JSONをコピーしました");
  } catch (error) {
    setStatus("コピーに失敗しました");
  }
});

function downloadJson() {
  if (!currentJson || currentJson === "{}") {
    setStatus("JSONがありません");
    return;
  }
  const blob = new Blob([currentJson], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  const filename = filenameInput.value.trim();
  link.download = filename || "ui_asset.json";
  link.click();
  URL.revokeObjectURL(url);
  setStatus("JSONを保存しました");
}

clearButton.addEventListener("click", clearAll);
generateButton.addEventListener("click", generateAsset);
downloadButton.addEventListener("click", downloadJson);
saveButton.addEventListener("click", saveToRepo);
applyGauge.addEventListener("click", applyGaugeChanges);
applyConstraints.addEventListener("click", applyConstraintChanges);
gaugeTarget.addEventListener("change", () => {
  const index = Number(gaugeTarget.value || 0);
  if (gaugeLayers[index]) {
    setGaugeInputs(gaugeLayers[index].layer);
  }
});
constraintsTarget.addEventListener("change", () => {
  const index = Number(constraintsTarget.value || 0);
  if (constraintTargets[index]) {
    buildConstraintFlagOptions(constraintTargets[index].target);
    setConstraintInputs(constraintTargets[index].target);
  }
});
shapeProfile.addEventListener("change", () => {
  updateGaugeParamVisibility(shapeProfile.value);
});
tagsInput.addEventListener("input", () => {
  warnUnknownTags(parseTagsInput());
});
refreshGenerated.addEventListener("click", loadGeneratedList);

for (const chip of document.querySelectorAll(".chip")) {
  chip.addEventListener("click", () => {
    promptInput.value = chip.dataset.prompt || "";
  });
}

async function saveToRepo() {
  if (!currentAsset || !currentAsset.assetType) {
    setSaveStatus("先に生成してください", true);
    return;
  }
  const filename = filenameInput.value.trim();
  if (!filename) {
    setSaveStatus("保存名が必要です", true);
    return;
  }

  const tags = parseTagsInput();
  warnUnknownTags(tags);

  setSaveStatus("保存中...");
  let response;
  try {
    response = await fetch("/api/save", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ asset: currentAsset, filename, tags }),
    });
  } catch (error) {
    setSaveStatus("保存に失敗しました", true);
    return;
  }

  const data = await response.json();
  if (!response.ok) {
    setSaveStatus(`保存失敗: ${data.error || "error"}`, true);
    return;
  }
  setSaveStatus(`保存完了: ${data.name}`);
  if (Array.isArray(data.warnings) && data.warnings.length) {
    tagsWarning.textContent = `未登録タグ: ${data.warnings.join(", ")}`;
  }
  loadGeneratedList();
}

async function loadGeneratedList() {
  let response;
  try {
    response = await fetch("/api/list_generated");
  } catch (error) {
    return;
  }
  if (!response.ok) {
    return;
  }
  const data = await response.json();
  const files = Array.isArray(data.files) ? data.files : [];
  generatedList.innerHTML = "";
  for (const file of files.slice(0, 10)) {
    const item = document.createElement("li");
    const name = document.createElement("span");
    name.textContent = file.name;
    const open = document.createElement("button");
    open.textContent = "開く";
    open.className = "ghost";
    open.addEventListener("click", () => loadGeneratedAsset(file.path));
    item.appendChild(name);
    item.appendChild(open);
    generatedList.appendChild(item);
  }
}

async function loadGeneratedAsset(path) {
  setStatus("読み込み中...");
  let response;
  try {
    response = await fetch("/api/compile", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path }),
    });
  } catch (error) {
    setStatus("読み込みに失敗しました");
    return;
  }

  const data = await response.json();
  if (!response.ok) {
    setStatus(`エラー: ${data.error || "failed"}`);
    return;
  }
  setStatus("読み込み完了");
  setPreview(data.svg);
  const selectedTemplate =
    data.asset && data.asset.metadata && data.asset.metadata.selected_templates
      ? data.asset.metadata.selected_templates[0]
      : "-";
  setJson(data.asset, selectedTemplate);
  setSelection(null);
  updateTagHints(data.asset);
  if (!data.asset || !data.asset.metadata || !Array.isArray(data.asset.metadata.tags)) {
    tagsInput.value = "";
  }
  warnUnknownTags(parseTagsInput());
  filenameInput.value = path.split("/").pop() || "";
}

async function fetchTags() {
  let response;
  try {
    response = await fetch("/api/tags");
  } catch (error) {
    return;
  }
  if (!response.ok) {
    return;
  }
  const data = await response.json();
  if (Array.isArray(data.tags)) {
    allowedTags = data.tags;
  }
  if (data.vocab && Array.isArray(data.vocab.constraints)) {
    allowedConstraintFlags = data.vocab.constraints;
  }
}

setJson({}, "-");
setSelection(null);
setSaveStatus("未保存");
fetchTags();
loadGeneratedList();
