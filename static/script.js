const textInput = document.getElementById('textInput');
const wordCount = document.getElementById('wordCount');
const charCount = document.getElementById('charCount');
const fontSelect = document.getElementById('fontSelect');
const fontSize = document.getElementById('fontSize');
const fontSizeVal = document.getElementById('fontSizeVal');
const lineSpacing = document.getElementById('lineSpacing');
const lineSpacingVal = document.getElementById('lineSpacingVal');
const inkColor = document.getElementById('inkColor');
const inkColorVal = document.getElementById('inkColorVal');
const marginLeft = document.getElementById('marginLeft');
const marginLeftVal = document.getElementById('marginLeftVal');
const pageStyle = document.getElementById('pageStyle');
const pageSize = document.getElementById('pageSize');
const spacingVariation = document.getElementById('spacingVariation');
const jitter = document.getElementById('jitter');
const inkVariation = document.getElementById('inkVariation');
const generateBtn = document.getElementById('generateBtn');
const downloadBtn = document.getElementById('downloadBtn');
const downloadJpg = document.getElementById('downloadJpg');
const downloadPng = document.getElementById('downloadPng');
const previewPage = document.getElementById('previewPage');
const previewContainer = document.getElementById('previewContainer');
const pdfViewer = document.getElementById('pdfViewer');
const pdfFrame = document.getElementById('pdfFrame');
const statusBar = document.getElementById('statusBar');
const loadingOverlay = document.getElementById('loadingOverlay');

let currentFilename = null;
let previewTimeout = null;

const FONT_MAP = {
    'DancingScript': "'Dancing Script', cursive",
    'Pacifico': "'Pacifico', cursive",
    'ComicNeue': "'Comic Neue', 'Comic Sans MS', cursive"
};

function updateStats() {
    const text = textInput.value;
    const words = text.trim() ? text.trim().split(/\s+/).length : 0;
    wordCount.textContent = `${words} word${words !== 1 ? 's' : ''}`;
    charCount.textContent = `${text.length} character${text.length !== 1 ? 's' : ''}`;
}

function getSettings() {
    return {
        font: fontSelect.value,
        font_size: parseInt(fontSize.value),
        line_spacing: parseInt(lineSpacing.value),
        ink_color: inkColor.value,
        margin_left: parseInt(marginLeft.value),
        page_style: pageStyle.value,
        page_size: pageSize.value,
        spacing_variation: spacingVariation.checked,
        jitter: jitter.checked,
        ink_variation: inkVariation.checked
    };
}

function saveSettings() {
    try {
        localStorage.setItem('hw_settings', JSON.stringify(getSettings()));
    } catch(e) {}
}

function loadSettings() {
    try {
        const saved = localStorage.getItem('hw_settings');
        if (saved) {
            const s = JSON.parse(saved);
            if (s.font) fontSelect.value = s.font;
            if (s.font_size) { fontSize.value = s.font_size; fontSizeVal.textContent = s.font_size; }
            if (s.line_spacing) { lineSpacing.value = s.line_spacing; lineSpacingVal.textContent = s.line_spacing; }
            if (s.ink_color) { inkColor.value = s.ink_color; inkColorVal.textContent = s.ink_color; }
            if (s.margin_left) { marginLeft.value = s.margin_left; marginLeftVal.textContent = s.margin_left; }
            if (s.page_style) pageStyle.value = s.page_style;
            if (s.page_size) pageSize.value = s.page_size;
            if (typeof s.spacing_variation === 'boolean') spacingVariation.checked = s.spacing_variation;
            if (typeof s.jitter === 'boolean') jitter.checked = s.jitter;
            if (typeof s.ink_variation === 'boolean') inkVariation.checked = s.ink_variation;
        }
    } catch(e) {}
}

function updatePreview() {
    const text = textInput.value.trim();
    if (!text) {
        previewPage.innerHTML = `
            <div class="preview-placeholder">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                    <polyline points="14 2 14 8 20 8"></polyline>
                    <line x1="16" y1="13" x2="8" y2="13"></line>
                    <line x1="16" y1="17" x2="8" y2="17"></line>
                    <polyline points="10 9 9 9 8 9"></polyline>
                </svg>
                <p>Start typing to see a live preview of your handwritten assignment</p>
            </div>`;
        return;
    }

    fetch('/api/preview', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: textInput.value })
    })
    .then(r => r.json())
    .then(data => {
        if (data.lines) {
            const settings = getSettings();
            const fontFamily = FONT_MAP[settings.font] || "'Comic Sans MS', cursive";
            const sizeScale = settings.font_size / 18;
            const spacingScale = settings.line_spacing / 28;

            previewPage.className = `preview-page ${settings.page_style}`;

            if (settings.page_style === 'notebook') {
                previewPage.style.backgroundSize = `100% ${settings.line_spacing}px`;
            } else {
                previewPage.style.backgroundSize = '';
            }

            let html = '';
            data.lines.forEach(line => {
                const color = (line.type === 'answer' || line.type === 'answer_label') ? settings.ink_color : '';
                const style = `font-family: ${fontFamily}; font-size: ${sizeScale}em; line-height: ${spacingScale * 1.6}; ${color ? 'color:' + color + ';' : ''}`;
                html += `<div class="preview-line ${line.type}" style="${style}">${escapeHtml(line.content)}</div>`;
            });
            previewPage.innerHTML = html;
        }
    })
    .catch(() => {});
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function schedulePreview() {
    clearTimeout(previewTimeout);
    previewTimeout = setTimeout(updatePreview, 300);
}

async function generatePdf() {
    const text = textInput.value.trim();
    if (!text) {
        statusBar.textContent = 'Please enter some text first';
        return;
    }

    loadingOverlay.style.display = 'flex';
    statusBar.textContent = 'Generating PDF...';
    generateBtn.disabled = true;

    try {
        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text, ...getSettings() })
        });

        const data = await response.json();
        if (data.error) {
            statusBar.textContent = `Error: ${data.error}`;
            return;
        }

        currentFilename = data.filename;
        pdfFrame.src = `/generated/${currentFilename}`;
        previewContainer.style.display = 'none';
        pdfViewer.style.display = 'block';
        downloadBtn.disabled = false;
        downloadJpg.disabled = false;
        downloadPng.disabled = false;
        statusBar.textContent = 'PDF generated successfully! You can download it now.';
    } catch (e) {
        statusBar.textContent = 'Failed to generate PDF. Please try again.';
    } finally {
        loadingOverlay.style.display = 'none';
        generateBtn.disabled = false;
    }
}

function downloadFile(url) {
    const a = document.createElement('a');
    a.href = url;
    a.download = '';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}

textInput.addEventListener('input', () => {
    updateStats();
    schedulePreview();
    saveSettings();

    if (pdfViewer.style.display === 'block') {
        pdfViewer.style.display = 'none';
        previewContainer.style.display = 'flex';
        downloadBtn.disabled = true;
        downloadJpg.disabled = true;
        downloadPng.disabled = true;
        currentFilename = null;
    }
});

fontSize.addEventListener('input', () => {
    fontSizeVal.textContent = fontSize.value;
    schedulePreview();
    saveSettings();
});

lineSpacing.addEventListener('input', () => {
    lineSpacingVal.textContent = lineSpacing.value;
    schedulePreview();
    saveSettings();
});

inkColor.addEventListener('input', () => {
    inkColorVal.textContent = inkColor.value;
    schedulePreview();
    saveSettings();
});

marginLeft.addEventListener('input', () => {
    marginLeftVal.textContent = marginLeft.value;
    saveSettings();
});

[fontSelect, pageStyle, pageSize, spacingVariation, jitter, inkVariation].forEach(el => {
    el.addEventListener('change', () => {
        schedulePreview();
        saveSettings();
    });
});

generateBtn.addEventListener('click', generatePdf);

downloadBtn.addEventListener('click', () => {
    if (currentFilename) {
        downloadFile(`/api/download/${currentFilename}`);
    }
});

downloadJpg.addEventListener('click', () => {
    if (currentFilename) {
        downloadFile(`/api/export/${currentFilename}/jpg`);
        statusBar.textContent = 'JPG export may not be available on all servers. PDF is always available.';
    }
});

downloadPng.addEventListener('click', () => {
    if (currentFilename) {
        downloadFile(`/api/export/${currentFilename}/png`);
        statusBar.textContent = 'PNG export may not be available on all servers. PDF is always available.';
    }
});

loadSettings();
updateStats();
updatePreview();
