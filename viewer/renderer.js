const btnOpen = document.getElementById('btn-open');
const fileInfo = document.getElementById('file-info');
const statusIndicator = document.getElementById('status-indicator');
const canvasContainer = document.getElementById('canvas-container');
const errorConsole = document.getElementById('error-console');

let currentZoom = d3.zoomIdentity;
let isFirstLoad = true;

// Initialize D3 Zoom
const zoom = d3.zoom()
    .scaleExtent([0.1, 10])
    .on('zoom', (e) => {
        const svgGroup = d3.select('#canvas-container svg > g.zoom-layer');
        if (!svgGroup.empty()) {
            svgGroup.attr('transform', e.transform);
        } else {
            // Fallback if we couldn't wrap the SVG contents
            d3.select('#canvas-container svg').attr('transform', e.transform);
        }
    });

d3.select('#canvas-container').call(zoom);

btnOpen.addEventListener('click', async () => {
    await window.api.openFileDialog();
});

window.api.onFileLoaded((filePath) => {
    fileInfo.textContent = filePath;
    statusIndicator.textContent = "Loading...";
    statusIndicator.className = "status-rendering";
    errorConsole.style.display = 'none';
    isFirstLoad = true;
});

window.api.onRenderStart(() => {
    statusIndicator.textContent = "Rendering...";
    statusIndicator.className = "status-rendering";
});

window.api.onRenderSuccess((svgString) => {
    statusIndicator.textContent = "Success";
    statusIndicator.className = "status-success";
    errorConsole.style.display = 'none';

    // Inject SVG
    canvasContainer.innerHTML = svgString;

    // Wrap children in a <g class="zoom-layer">
    const svgEl = canvasContainer.querySelector('svg');
    if (svgEl) {
        const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        g.setAttribute('class', 'zoom-layer');
        
        while (svgEl.firstChild) {
            g.appendChild(svgEl.firstChild);
        }
        svgEl.appendChild(g);

        if (isFirstLoad) {
            const containerRect = canvasContainer.getBoundingClientRect();
            const svgWidth = parseFloat(svgEl.getAttribute('width')) || 720;
            const svgHeight = parseFloat(svgEl.getAttribute('height')) || 1280;
            const padding = 60; // top/bottom padding
            
            // Calculate scale to fit height
            const scale = Math.max(0.1, (containerRect.height - padding) / svgHeight);
            const tx = (containerRect.width - (svgWidth * scale)) / 2;
            const ty = padding / 2;
            
            currentZoom = d3.zoomIdentity.translate(tx, ty).scale(scale);
            d3.select('#canvas-container').call(zoom.transform, currentZoom);
            isFirstLoad = false;
        }

        // Apply current zoom state so it doesn't jump
        d3.select(g).attr('transform', currentZoom);
    }
});

window.api.onRenderError((errorMsg) => {
    statusIndicator.textContent = "Error";
    statusIndicator.className = "status-error";
    errorConsole.textContent = errorMsg;
    errorConsole.style.display = 'block';
});
