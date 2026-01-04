const splitToggle = document.getElementById("split-toggle");
const canvas = document.getElementById("canvas");

const panes = {
  a: buildPane("a"),
  b: buildPane("b"),
};

splitToggle.addEventListener("change", () => {
  if (splitToggle.checked) {
    canvas.classList.remove("single");
    document.getElementById("pane-b").style.display = "flex";
  } else {
    canvas.classList.add("single");
    document.getElementById("pane-b").style.display = "none";
  }
});

function buildPane(key) {
  const pane = {
    key,
    fileInput: document.getElementById(`file-${key}`),
    pathInput: document.getElementById(`path-${key}`),
    loadButton: document.getElementById(`load-${key}`),
    status: document.getElementById(`status-${key}`),
    selection: document.getElementById(`selection-${key}`),
    container: document.getElementById(`svg-${key}`),
    asset: null,
    instanceMap: {},
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
  pane.container.innerHTML = data.svg;
  setStatus(pane, `OK: ${pane.asset.assetType || "asset"}`);

  const svg = pane.container.querySelector("svg");
  if (svg) {
    svg.addEventListener("click", (event) => {
      const group = findGroup(event.target);
      if (!group) {
        pane.selection.textContent = "Selected: -";
        return;
      }
      const componentId = resolveComponentId(pane, group.id);
      if (componentId) {
        pane.selection.textContent = `Selected: ${group.id} / ${componentId}`;
      } else {
        pane.selection.textContent = `Selected: ${group.id}`;
      }
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
