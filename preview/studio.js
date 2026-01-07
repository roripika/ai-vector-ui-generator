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
const copyButton = document.getElementById("copy-json");
const downloadButton = document.getElementById("download-json");

let currentJson = "{}";

function setStatus(message) {
  statusLabel.textContent = message;
}

function setPreview(svg) {
  preview.innerHTML = svg || '<div class="empty">ここにSVGプレビューが表示されます</div>';
}

function setJson(asset, id) {
  currentJson = JSON.stringify(asset, null, 2);
  jsonOutput.textContent = currentJson;
  templateId.textContent = `template: ${id || "-"}`;
  assetType.textContent = asset && asset.assetType ? `type: ${asset.assetType}` : "type: -";
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
}

function clearAll() {
  promptInput.value = "";
  setStatus("待機中");
  setPreview("");
  setJson({}, "-");
  setSelection(null);
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
  const name = templateId.textContent.replace("template: ", "").trim();
  link.download = name && name !== "-" ? `${name}.json` : "ui_asset.json";
  link.click();
  URL.revokeObjectURL(url);
  setStatus("JSONを保存しました");
}

clearButton.addEventListener("click", clearAll);
generateButton.addEventListener("click", generateAsset);
downloadButton.addEventListener("click", downloadJson);

for (const chip of document.querySelectorAll(".chip")) {
  chip.addEventListener("click", () => {
    promptInput.value = chip.dataset.prompt || "";
  });
}

setJson({}, "-");
setSelection(null);
