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
const wordSizeVariation = document.getElementById('wordSizeVariation');
const baselineShift = document.getElementById('baselineShift');
const inkFlow = document.getElementById('inkFlow');
const gelPen = document.getElementById('gelPen');
const jitterStrength = document.getElementById('jitterStrength');
const jitterStrengthVal = document.getElementById('jitterStrengthVal');
const marginRule = document.getElementById('marginRule');
const doubleMargin = document.getElementById('doubleMargin');
const newQuestionOnNewPage = document.getElementById('newQuestionOnNewPage');
const boldQuestion = document.getElementById('boldQuestion');
const underlineHeadings = document.getElementById('underlineHeadings');
const signatureFile = document.getElementById('signatureFile');
const scanEffect = document.getElementById('scanEffect');
const darkMode = document.getElementById('darkMode');
const generateBtn = document.getElementById('generateBtn');
const downloadBtn = document.getElementById('downloadBtn');
const downloadJpg = document.getElementById('downloadJpg');
const downloadPng = document.getElementById('downloadPng');
const printBtn = document.getElementById('printBtn');
const clearTextBtn = document.getElementById('clearTextBtn');
const copySampleBtn = document.getElementById('copySampleBtn');
const copyTextBtn = document.getElementById('copyTextBtn');
const pasteBtn = document.getElementById('pasteBtn');
const autoStructureBtn = document.getElementById('autoStructureBtn');
const importFileBtn = document.getElementById('importFileBtn');
const importFileInput = document.getElementById('importFileInput');
const undoBtn = document.getElementById('undoBtn');
const redoBtn = document.getElementById('redoBtn');
const afterGenerate = document.getElementById('afterGenerate');
const newPdfBtn = document.getElementById('newPdfBtn');
const resetSettingsBtn = document.getElementById('resetSettingsBtn');
const clearSignatureBtn = document.getElementById('clearSignatureBtn');
const fullscreenPreviewBtn = document.getElementById('fullscreenPreviewBtn');
const fullscreenModal = document.getElementById('fullscreenModal');
const fullscreenContent = document.getElementById('fullscreenContent');
const closeFullscreen = document.getElementById('closeFullscreen');
const previewPage = document.getElementById('previewPage');
const previewContainer = document.getElementById('previewContainer');
const pdfViewer = document.getElementById('pdfViewer');
const pdfFrame = document.getElementById('pdfFrame');
const statusBar = document.getElementById('statusBar');
const loadingOverlay = document.getElementById('loadingOverlay');
const pageNumbers = document.getElementById('pageNumbers');
const headerText = document.getElementById('headerText');
const footerText = document.getElementById('footerText');
const watermarkText = document.getElementById('watermarkText');

// Force overlays closed on load (fixes stuck modal/loading after refresh)
(function () {
    const lo = document.getElementById('loadingOverlay');
    const fm = document.getElementById('fullscreenModal');
    const hm = document.getElementById('historyModal');
    const pm = document.getElementById('presetModal');
    const findM = document.getElementById('findModal');
    if (lo) lo.hidden = true;
    if (fm) fm.hidden = true;
    if (hm) hm.hidden = true;
    if (pm) pm.hidden = true;
    if (findM) findM.remove(); // Remove find modal completely
    document.body.style.overflow = '';
})();

let currentFilename = null;
let previewTimeout = null;
let signatureBase64 = null;
let undoStack = [];
let redoStack = [];
let maxUndoHistory = 50;

const TEMPLATES = {
    assignment: `HOME ASSIGNMENT

Name: 
ID: 
Date: 
Subject: 

1. 
Ans: 

2. 
Ans: `,
    lab: `LAB RECORD

Name: 
Roll No: 
Date: 
Subject: 
Experiment: 

Aim: 


Procedure: 


Observation: 


Result: `,
    seminar: `SEMINAR REPORT

Title: 

Name: 
Department: 
Date: 

Abstract: 


Introduction: 


Conclusion: `,
    internal: `INTERNAL ASSIGNMENT

Name: 
Roll No: 
Date: 
Subject: 

Q1. 
Ans: 

Q2. 
Ans: `
};

const PRESETS = {
    neat: { font_size: 16, line_spacing: 30, jitter_strength: 0.4, jitter: true, word_size_variation: false, baseline_shift: false },
    natural: { font_size: 18, line_spacing: 28, jitter_strength: 1, jitter: true, word_size_variation: true, baseline_shift: true },
    fast: { font_size: 16, line_spacing: 24, jitter_strength: 1.5, jitter: true, word_size_variation: true, baseline_shift: true }
};

const FONT_MAP = {
    'DancingScript': "'Dancing Script', cursive",
    'Pacifico': "'Pacifico', cursive",
    'ComicNeue': "'Comic Neue', 'Comic Sans MS', cursive"
};

// Generic fallback for external fonts
function getFontFamily(fontName) {
    if (FONT_MAP[fontName]) return FONT_MAP[fontName];
    return `'${fontName}', cursive, sans-serif`;
}

function updateStats() {
    const text = textInput.value;
    const words = text.trim() ? text.trim().split(/\s+/).length : 0;
    wordCount.textContent = `${words} word${words !== 1 ? 's' : ''}`;
    charCount.textContent = `${text.length} character${text.length !== 1 ? 's' : ''}`;
}

function getSettings() {
    var get = function(id, def) { var el = document.getElementById(id); return el ? el.checked : (def !== undefined ? def : false); };
    var getVal = function(id, def) { var el = document.getElementById(id); return el ? el.value : def; };
    return {
        font: fontSelect ? fontSelect.value : 'Helvetica',
        font_size: parseInt(fontSize && fontSize.value ? fontSize.value : 18, 10),
        line_spacing: parseInt(lineSpacing && lineSpacing.value ? lineSpacing.value : 28, 10),
        ink_color: inkColor ? inkColor.value : '#0A1F5C',
        margin_left: parseInt(marginLeft && marginLeft.value ? marginLeft.value : 60, 10),
        page_style: pageStyle ? pageStyle.value : 'blank',
        page_size: pageSize ? pageSize.value : 'A4',
        spacing_variation: get('spacingVariation', true),
        jitter: get('jitter', true),
        ink_variation: get('inkVariation', true),
        word_size_variation: get('wordSizeVariation', true),
        baseline_shift: get('baselineShift', true),
        jitter_strength: parseFloat(getVal('jitterStrength', '1') || '1') || 1,
        ink_flow: get('inkFlow', true),
        gel_pen: get('gelPen', false),
        margin_rule: get('marginRule', true),
        double_margin: get('doubleMargin', false),
        new_question_on_new_page: get('newQuestionOnNewPage', false),
        bold_question: get('boldQuestion', false),
        underline_headings: get('underlineHeadings', false),
        signature_base64: signatureBase64 || undefined,
        scan_effect: get('scanEffect', false),
        page_numbers: get('pageNumbers', false),
        header_text: headerText ? headerText.value : '',
        footer_text: footerText ? footerText.value : '',
        watermark_text: watermarkText ? watermarkText.value : ''
    };
}

function saveSettings() {
    try {
        const s = getSettings();
        delete s.signature_base64;
        delete s.scan_effect;
        localStorage.setItem('hw_settings', JSON.stringify(s));
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
            if (wordSizeVariation && typeof s.word_size_variation === 'boolean') wordSizeVariation.checked = s.word_size_variation;
            if (baselineShift && typeof s.baseline_shift === 'boolean') baselineShift.checked = s.baseline_shift;
            if (jitterStrength) { jitterStrength.value = s.jitter_strength || 1; if (jitterStrengthVal) jitterStrengthVal.textContent = jitterStrength.value; }
            if (inkFlow && typeof s.ink_flow === 'boolean') inkFlow.checked = s.ink_flow;
            if (gelPen && typeof s.gel_pen === 'boolean') gelPen.checked = s.gel_pen;
            if (marginRule && typeof s.margin_rule === 'boolean') marginRule.checked = s.margin_rule;
            if (doubleMargin && typeof s.double_margin === 'boolean') doubleMargin.checked = s.double_margin;
            if (newQuestionOnNewPage && typeof s.new_question_on_new_page === 'boolean') newQuestionOnNewPage.checked = s.new_question_on_new_page;
            if (boldQuestion && typeof s.bold_question === 'boolean') boldQuestion.checked = s.bold_question;
            if (underlineHeadings && typeof s.underline_headings === 'boolean') underlineHeadings.checked = s.underline_headings;
        }
        if (darkMode && localStorage.getItem('hw_dark') === '1') { darkMode.checked = true; document.body.classList.add('dark'); }
    } catch(e) {}
}

function updatePreview() {
    const text = textInput.value.trim();
    if (!text) {
        previewPage.innerHTML = '<div class="preview-placeholder"><p>Type or paste text to see preview</p></div>';
        previewPage.className = 'preview-page blank a4-preview';
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
            const fontFamily = getFontFamily(settings.font);
            const sizeScale = settings.font_size / 18;
            const spacingScale = settings.line_spacing / 28;

            previewPage.className = `preview-page ${settings.page_style}`;
            const marginPx = settings.margin_left || 60;
            previewPage.style.paddingLeft = marginPx + 'px';
            if (settings.page_style === 'notebook' || settings.page_style === 'legal_yellow') {
                previewPage.style.backgroundSize = `100% ${settings.line_spacing}px`;
            } else {
                previewPage.style.backgroundSize = '';
            }

            var underlineHeadings = !!settings.underline_headings;
            var marginRule = !!settings.margin_rule;
            var doubleMargin = !!settings.double_margin;
            var boldQuestion = !!settings.bold_question;
            previewPage.style.borderLeft = marginRule ? (doubleMargin ? '4px solid #ff9999' : '3px solid #ff9999') : 'none';
            if (doubleMargin && marginRule) {
                previewPage.style.paddingLeft = (marginPx + 14) + 'px';
            }

            var html = '';
            data.lines.forEach(function(line) {
                var color = (line.type === 'answer' || line.type === 'answer_label') ? settings.ink_color : '';
                var style = 'font-family: ' + fontFamily + '; font-size: ' + sizeScale + 'em; line-height: ' + (spacingScale * 1.6) + '; ' + (color ? 'color:' + color + ';' : '');
                var extraClass = '';
                if (underlineHeadings && (line.type === 'title' || line.type === 'heading')) extraClass += ' preview-underline';
                if (boldQuestion && line.type === 'question') extraClass += ' preview-bold';
                html += '<div class="preview-line ' + line.type + extraClass + '" style="' + style + '">' + escapeHtml(line.content) + '</div>';
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

const GENERATE_TIMEOUT_MS = 90000;

async function generatePdf() {
    const text = textInput.value.trim();
    if (!text) {
        statusBar.textContent = 'Please enter some text first';
        return;
    }

    if (loadingOverlay) loadingOverlay.hidden = false;
    statusBar.textContent = 'Generating PDF…';
    generateBtn.disabled = true;

    let timedOut = false;
    const timeoutId = setTimeout(() => {
        timedOut = true;
        if (loadingOverlay) loadingOverlay.hidden = true;
        generateBtn.disabled = false;
        statusBar.textContent = 'Request took too long. Check your connection and try again.';
    }, GENERATE_TIMEOUT_MS);

    try {
        const controller = new AbortController();
        const timeoutAbort = setTimeout(() => controller.abort(), GENERATE_TIMEOUT_MS - 500);
        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text, ...getSettings() }),
            signal: controller.signal
        });
        clearTimeout(timeoutAbort);

        if (timedOut) return;

        const data = await response.json();
        if (data.error) {
            statusBar.textContent = `Error: ${data.error}`;
            return;
        }

        currentFilename = data.filename;
        pdfFrame.src = `/generated/${currentFilename}`;
        previewContainer.hidden = true;
        pdfViewer.hidden = false;
        if (afterGenerate) afterGenerate.hidden = false;
        const wrapper = document.getElementById('previewWrapper');
        if (wrapper) wrapper.scrollTop = 0;
        if (downloadBtn) downloadBtn.disabled = false;
        if (downloadJpg) downloadJpg.disabled = false;
        if (downloadPng) downloadPng.disabled = false;
        statusBar.textContent = 'PDF ready. Download or export below.';
    } catch (e) {
        if (timedOut) return;
        statusBar.textContent = e.name === 'AbortError' ? 'Request timed out. Try again.' : 'Failed to generate PDF. Try again.';
    } finally {
        clearTimeout(timeoutId);
        if (loadingOverlay) loadingOverlay.hidden = true;
        generateBtn.disabled = false;
    }
}

function showEditorState() {
    currentFilename = null;
    pdfFrame.src = '';
    previewContainer.hidden = false;
    pdfViewer.hidden = true;
    if (afterGenerate) afterGenerate.hidden = true;
    if (downloadBtn) downloadBtn.disabled = true;
    if (downloadJpg) downloadJpg.disabled = true;
    if (downloadPng) downloadPng.disabled = true;
}

var downloadInProgress = false;

async function downloadFile(url, filename) {
    if (downloadInProgress) return;
    downloadInProgress = true;
    if (downloadJpg) downloadJpg.disabled = true;
    if (downloadPng) downloadPng.disabled = true;
    try {
        const response = await fetch(url);
        const contentType = response.headers.get('content-type') || '';
        if (!response.ok || contentType.includes('application/json')) {
            const error = await response.json().catch(() => ({ error: 'Export failed' }));
            statusBar.textContent = 'Error: ' + (error.error || 'Export failed.');
            return;
        }
        const blob = await response.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = filename || '';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(downloadUrl);
        statusBar.textContent = 'Downloaded (all pages as ZIP).';
    } catch (e) {
        statusBar.textContent = 'Export failed: ' + (e.message || 'Network error');
    } finally {
        downloadInProgress = false;
        if (downloadJpg) downloadJpg.disabled = false;
        if (downloadPng) downloadPng.disabled = false;
    }
}

// Undo/Redo functionality
function saveToUndoStack() {
    const currentText = textInput.value;
    if (undoStack.length === 0 || undoStack[undoStack.length - 1] !== currentText) {
        undoStack.push(currentText);
        if (undoStack.length > maxUndoHistory) {
            undoStack.shift();
        }
        redoStack = [];
        updateUndoRedoButtons();
    }
}

function updateUndoRedoButtons() {
    if (undoBtn) undoBtn.disabled = undoStack.length <= 1;
    if (redoBtn) redoBtn.disabled = redoStack.length === 0;
}

function performUndo() {
    if (undoStack.length <= 1) return;
    const current = undoStack.pop();
    redoStack.push(current);
    textInput.value = undoStack[undoStack.length - 1] || '';
    updateStats();
    schedulePreview();
    updateUndoRedoButtons();
    statusBar.textContent = 'Undone.';
}

function performRedo() {
    if (redoStack.length === 0) return;
    const next = redoStack.pop();
    undoStack.push(textInput.value);
    textInput.value = next;
    updateStats();
    schedulePreview();
    updateUndoRedoButtons();
    statusBar.textContent = 'Redone.';
}

if (undoBtn) undoBtn.addEventListener('click', performUndo);
if (redoBtn) redoBtn.addEventListener('click', performRedo);

// Initialize undo stack
if (textInput) {
    undoStack.push(textInput.value);
    updateUndoRedoButtons();
}

textInput.addEventListener('input', () => {
    saveToUndoStack();
    updateStats();
    schedulePreview();
    saveSettings();
    if (!pdfViewer.hidden) showEditorState();
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
    schedulePreview();
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
        downloadFile(`/api/download/${currentFilename}`, 'handwritten_assignment.pdf');
    }
});

downloadJpg.addEventListener('click', async () => {
    if (currentFilename) {
        const scan = getSettings().scan_effect ? '?scan=1' : '';
        await downloadFile(`/api/export/${currentFilename}/jpg${scan}`, 'handwritten_assignment_all_pages.zip');
    }
});

downloadPng.addEventListener('click', async () => {
    if (currentFilename) {
        const scan = getSettings().scan_effect ? '?scan=1' : '';
        await downloadFile(`/api/export/${currentFilename}/png${scan}`, 'handwritten_assignment_all_pages.zip');
    }
});

if (pasteBtn) {
    pasteBtn.addEventListener('click', async () => {
        try {
            const t = await navigator.clipboard.readText();
            textInput.value = t;
            updateStats();
            schedulePreview();
            statusBar.textContent = 'Pasted from clipboard.';
        } catch (e) {
            statusBar.textContent = 'Paste failed. Try Ctrl+V in the text box.';
        }
    });
}

if (copyTextBtn) {
    copyTextBtn.addEventListener('click', () => {
        const t = textInput.value;
        if (!t) { statusBar.textContent = 'Nothing to copy.'; return; }
        navigator.clipboard.writeText(t).then(() => {
            statusBar.textContent = 'Text copied to clipboard.';
        }).catch(() => { statusBar.textContent = 'Copy failed.'; });
    });
}

clearTextBtn.addEventListener('click', () => {
    if (!textInput.value.trim()) return;
    if (confirm('Clear all text?')) {
        textInput.value = '';
        updateStats();
        schedulePreview();
        statusBar.textContent = 'Text cleared.';
    }
});

copySampleBtn.addEventListener('click', () => {
    textInput.value = `HOME ASSIGNMENT

Name: Jane Smith
ID: 987654321
Date: February 16, 2026
Subject: Physics - Thermodynamics

Q1. State the First Law of Thermodynamics?
Ans: The first law states that energy can neither be created nor destroyed, only transformed from one form to another.

Q2. What is an isothermal process?
Ans: An isothermal process is one where the temperature of the system remains constant (ΔT = 0).`;
    updateStats();
    schedulePreview();
    statusBar.textContent = 'Sample loaded.';
});

['templateAssignment', 'templateLab', 'templateSeminar', 'templateInternal'].forEach((id, i) => {
    const key = ['assignment', 'lab', 'seminar', 'internal'][i];
    document.getElementById(id)?.addEventListener('click', () => {
        textInput.value = TEMPLATES[key];
        updateStats();
        schedulePreview();
        statusBar.textContent = `Template "${key}" loaded.`;
    });
});

function applyPreset(name) {
    const p = PRESETS[name];
    if (!p) return;
    if (fontSize) { fontSize.value = p.font_size; if (fontSizeVal) fontSizeVal.textContent = p.font_size; }
    if (lineSpacing) { lineSpacing.value = p.line_spacing; if (lineSpacingVal) lineSpacingVal.textContent = p.line_spacing; }
    if (jitterStrength) { jitterStrength.value = p.jitter_strength; if (jitterStrengthVal) jitterStrengthVal.textContent = p.jitter_strength; }
    if (jitter) jitter.checked = p.jitter;
    if (wordSizeVariation) wordSizeVariation.checked = p.word_size_variation;
    if (baselineShift) baselineShift.checked = p.baseline_shift;
    document.querySelectorAll('.btn-preset').forEach(el => el.classList.remove('btn-preset-active'));
    const active = document.getElementById('preset' + name.charAt(0).toUpperCase() + name.slice(1));
    if (active) active.classList.add('btn-preset-active');
    schedulePreview();
    saveSettings();
}

document.getElementById('presetNeat')?.addEventListener('click', () => applyPreset('neat'));
document.getElementById('presetNatural')?.addEventListener('click', () => applyPreset('natural'));
document.getElementById('presetFast')?.addEventListener('click', () => applyPreset('fast'));

if (resetSettingsBtn) {
    resetSettingsBtn.addEventListener('click', () => {
        if (!confirm('Reset all settings to default?')) return;
        fontSize.value = 18; if (fontSizeVal) fontSizeVal.textContent = 18;
        lineSpacing.value = 28; if (lineSpacingVal) lineSpacingVal.textContent = 28;
        marginLeft.value = 60; if (marginLeftVal) marginLeftVal.textContent = 60;
        inkColor.value = '#0A1F5C'; if (inkColorVal) inkColorVal.textContent = '#0A1F5C';
        pageStyle.value = 'notebook'; pageSize.value = 'A4';
        jitterStrength.value = 1; if (jitterStrengthVal) jitterStrengthVal.textContent = '1.0';
        [spacingVariation, jitter, inkVariation, wordSizeVariation, baselineShift, inkFlow].forEach(c => { if (c) c.checked = true; });
        if (gelPen) gelPen.checked = false;
        if (marginRule) marginRule.checked = true;
        if (doubleMargin) doubleMargin.checked = false;
        if (newQuestionOnNewPage) newQuestionOnNewPage.checked = false;
        if (boldQuestion) boldQuestion.checked = false;
        if (underlineHeadings) underlineHeadings.checked = false;
        if (scanEffect) scanEffect.checked = false;
        applyPreset('natural');
        statusBar.textContent = 'Settings reset.';
    });
}

if (newPdfBtn) newPdfBtn.addEventListener('click', showEditorState);

if (clearSignatureBtn) {
    clearSignatureBtn.addEventListener('click', () => {
        signatureBase64 = null;
        if (signatureFile) signatureFile.value = '';
        const canvas = document.getElementById('signaturePreview');
        if (canvas) { canvas.hidden = true; const ctx = canvas.getContext('2d'); ctx.clearRect(0, 0, canvas.width, canvas.height); }
        statusBar.textContent = 'Signature cleared.';
    });
}

function closeFullscreenModal() {
    if (fullscreenModal) {
        fullscreenModal.hidden = true;
        document.body.style.overflow = '';
    }
}

if (fullscreenPreviewBtn && fullscreenModal && fullscreenContent && closeFullscreen) {
    fullscreenPreviewBtn.addEventListener('click', () => {
        fullscreenContent.innerHTML = '';
        const clone = previewPage.cloneNode(true);
        clone.classList.add('fullscreen-preview-page');
        fullscreenContent.appendChild(clone);
        fullscreenModal.hidden = false;
        document.body.style.overflow = 'hidden';
    });
    closeFullscreen.addEventListener('click', closeFullscreenModal);
    fullscreenModal.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeFullscreenModal(); });
    fullscreenModal.addEventListener('click', (e) => {
        if (e.target === fullscreenModal) closeFullscreenModal();
    });
    fullscreenContent.addEventListener('click', (e) => e.stopPropagation());
}

if (autoStructureBtn) {
    autoStructureBtn.addEventListener('click', async () => {
        const text = textInput.value.trim();
        if (!text) { statusBar.textContent = 'Enter or paste text first'; return; }
        try {
            const r = await fetch('/api/auto-structure', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text }) });
            const data = await r.json();
            if (data.structured != null) {
                textInput.value = data.structured;
                updateStats();
                schedulePreview();
                statusBar.textContent = 'Text restructured with headings and formatting.';
            }
        } catch (e) {
            statusBar.textContent = 'Auto-structure failed.';
        }
    });
}

if (signatureFile) {
    signatureFile.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (!file) { signatureBase64 = null; return; }
        const reader = new FileReader();
        reader.onload = () => {
            signatureBase64 = reader.result;
            const canvas = document.getElementById('signaturePreview');
            if (canvas) {
                const img = new Image();
                img.onload = () => {
                    canvas.getContext('2d').drawImage(img, 0, 0, 120, 50);
                    canvas.style.display = 'block';
                };
                img.src = reader.result;
            }
        };
        reader.readAsDataURL(file);
    });
}

if (jitterStrength) {
    jitterStrength.addEventListener('input', () => {
        if (jitterStrengthVal) jitterStrengthVal.textContent = jitterStrength.value;
        saveSettings();
    });
}

if (darkMode) {
    darkMode.addEventListener('change', () => {
        document.body.classList.toggle('dark', darkMode.checked);
        try { localStorage.setItem('hw_dark', darkMode.checked ? '1' : '0'); } catch (e) {}
    });
}

function setupAdvancedAndDelegation() {
    var advanced = document.getElementById('advancedDetails');
    if (advanced) {
        var summary = advanced.querySelector('summary');
        if (summary) {
            summary.addEventListener('click', function(e) {
                e.preventDefault();
                advanced.toggleAttribute('open');
            });
        }
    }
    var controlsPanel = document.querySelector('.controls-panel');
    if (controlsPanel) {
        controlsPanel.addEventListener('change', function(e) {
            if (e.target.matches('input, select')) {
                schedulePreview();
                saveSettings();
                if (e.target.id === 'jitterStrength' && jitterStrengthVal) jitterStrengthVal.textContent = e.target.value;
            }
        });
        controlsPanel.addEventListener('input', function(e) {
            if (e.target.matches('input, select')) {
                schedulePreview();
                saveSettings();
                if (e.target.id === 'fontSize' && fontSizeVal) fontSizeVal.textContent = e.target.value;
                if (e.target.id === 'lineSpacing' && lineSpacingVal) lineSpacingVal.textContent = e.target.value;
                if (e.target.id === 'marginLeft' && marginLeftVal) marginLeftVal.textContent = e.target.value;
                if (e.target.id === 'inkColor' && inkColorVal) inkColorVal.textContent = e.target.value;
                if (e.target.id === 'jitterStrength' && jitterStrengthVal) jitterStrengthVal.textContent = e.target.value;
            }
        });
    }
}
setupAdvancedAndDelegation();

if (loadingOverlay) {
    loadingOverlay.hidden = true;
    document.getElementById('closeLoadingOverlay')?.addEventListener('click', () => {
        loadingOverlay.hidden = true;
        generateBtn.disabled = false;
        statusBar.textContent = 'Cancelled.';
    });
}

// File import functionality
if (importFileBtn && importFileInput) {
    importFileBtn.addEventListener('click', () => {
        importFileInput.click();
    });
    importFileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = (event) => {
            saveToUndoStack();
            textInput.value = event.target.result;
            updateStats();
            schedulePreview();
            statusBar.textContent = `Imported: ${file.name}`;
            importFileInput.value = '';
        };
        reader.onerror = () => {
            statusBar.textContent = 'Failed to read file.';
        };
        reader.readAsText(file);
    });
}


// Print functionality
if (printBtn) {
    printBtn.addEventListener('click', () => {
        if (currentFilename) {
            const printWindow = window.open(`/generated/${currentFilename}`, '_blank');
            if (printWindow) {
                printWindow.onload = () => {
                    printWindow.print();
                };
            } else {
                statusBar.textContent = 'Please allow popups to print.';
            }
        }
    });
}

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // Ctrl+Z / Cmd+Z - Undo
    if ((e.ctrlKey || e.metaKey) && e.key === 'z' && !e.shiftKey) {
        e.preventDefault();
        if (undoStack.length > 1) performUndo();
    }
    // Ctrl+Y / Cmd+Y or Ctrl+Shift+Z - Redo
    if ((e.ctrlKey || e.metaKey) && (e.key === 'y' || (e.key === 'z' && e.shiftKey))) {
        e.preventDefault();
        if (redoStack.length > 0) performRedo();
    }
    // Ctrl+S / Cmd+S - Generate PDF
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        if (generateBtn && !generateBtn.disabled) generatePdf();
    }
    // Escape - Close modals
    if (e.key === 'Escape') {
        if (fullscreenModal && !fullscreenModal.hidden) closeFullscreenModal();
    }
});


// Ensure history and find modals are removed if they exist
(function() {
    const hm = document.getElementById('historyModal');
    const fm = document.getElementById('findModal');
    if (hm) {
        hm.remove(); // Completely remove from DOM
    }
    if (fm) {
        fm.remove(); // Completely remove find modal from DOM
    }
    // Also remove any dynamically created history buttons
    const historyBtns = document.querySelectorAll('[id*="history"], [class*="history"]');
    historyBtns.forEach(btn => {
        if (btn.textContent && btn.textContent.includes('History')) {
            btn.remove();
        }
    });
})();

loadSettings();
updateStats();
updatePreview();
