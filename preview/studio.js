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

function setStatus(message) {
  statusLabel.textContent = message;
}

function setPreview(svg) {
  preview.innerHTML = svg || '<div class="empty">ここにSVGプレビューが表示されます</div>';
}

function setJson(asset, id) {
  currentAsset = asset;
  currentJson = JSON.stringify(asset, null, 2);
  jsonOutput.textContent = currentJson;
  templateId.textContent = `template: ${id || "-"}`;
  assetType.textContent = asset && asset.assetType ? `type: ${asset.assetType}` : "type: -";

  if (asset && asset.metadata && Array.isArray(asset.metadata.tags)) {
    tagsInput.value = asset.metadata.tags.join(", ");
  }
}

function setSelection(selection) {
  if (!selection) {
    selectionSummary.textContent = "template: -";
    selectionList.innerHTML = "";
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
    item.textContent = matches
      ? `${candidate.id} | match: ${matches}`
      : `${candidate.id}`;
    selectionList.appendChild(item);
  }
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
}

setJson({}, "-");
setSelection(null);
setSaveStatus("未保存");
fetchTags();
loadGeneratedList();
