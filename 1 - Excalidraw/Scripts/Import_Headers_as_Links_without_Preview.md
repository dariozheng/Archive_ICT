const files = app.vault.getMarkdownFiles();
const fileNames = files.map(f => f.path);
const chosen = await utils.suggester(fileNames, fileNames, "Pick a note");
if (!chosen) return;

const file = files.find(f => f.path === chosen);
if (!file) { new Notice("File not found"); return; }

const cache = app.metadataCache.getFileCache(file);
if (!cache?.headings || cache.headings.length === 0) { new Notice("No headers found."); return; }

const baseName = file.basename;
let y = 0;

const BOX_WIDTH  = 560;
const BOX_HEIGHT = 90;
const PAD_X      = 22;
const PAD_Y      = 18;
const GAP        = 12;
const CHAR_WIDTH_RATIO = 0.52;

const LEVEL_STYLES = [
  { stroke: "#0d1b2a", bg: "#e9ecef", text: "#0d1b2a", sw: 2.5 }, // H1
  { stroke: "#1864ab", bg: "#d0ebff", text: "#1864ab", sw: 2.0 }, // H2
  { stroke: "#2b4acb", bg: "#dbe4ff", text: "#2b4acb", sw: 1.5 }, // H3
  { stroke: "#5c7cfa", bg: "#edf2ff", text: "#5c7cfa", sw: 1.5 }, // H4
  { stroke: "#748ffc", bg: "#f0f3ff", text: "#748ffc", sw: 1.0 }, // H5
  { stroke: "#91a7ff", bg: "#f5f7ff", text: "#8c9ef0", sw: 1.0 }, // H6
];

const FONT_SIZES = [44, 36, 30, 26, 22, 19];

function wrapText(text, maxChars) {
  const words = text.split(' ');
  const wrappedLines = [];
  let current = '';
  for (const word of words) {
    const candidate = current ? current + ' ' + word : word;
    if (candidate.length <= maxChars) {
      current = candidate;
    } else {
      if (current) wrappedLines.push(current);
      current = word;
    }
  }
  if (current) wrappedLines.push(current);
  return wrappedLines;
}

for (const heading of cache.headings) {
  const level = Math.min(heading.level, 6);
  const idx   = level - 1;
  const { stroke, bg, text: textColor, sw } = LEVEL_STYLES[idx];
  const fontSize   = FONT_SIZES[idx];
  const lineHeight = fontSize * 1.2;

  const textMaxW     = BOX_WIDTH - PAD_X * 2;         // ← always full width
  const charWidth    = fontSize * CHAR_WIDTH_RATIO;
  const charsPerLine = Math.max(1, Math.floor(textMaxW / charWidth));
  const wrappedLines = wrapText(heading.heading, charsPerLine);
  const wrappedText  = wrappedLines.join('\n');

  const textBlockH = wrappedLines.length * lineHeight;
  const textY      = y + Math.max(PAD_Y, (BOX_HEIGHT - textBlockH) / 2);

  ea.style.strokeColor     = stroke;
  ea.style.backgroundColor = bg;
  ea.style.fillStyle       = "solid";
  ea.style.strokeWidth     = sw;
  ea.style.roughness       = 0;
  ea.style.roundness       = { type: 3 };
  const rectId = ea.addRect(0, y, BOX_WIDTH, BOX_HEIGHT); // ← x=0, full width

  ea.style.fontSize        = fontSize;
  ea.style.fontFamily      = 1;
  ea.style.strokeColor     = textColor;
  ea.style.backgroundColor = "transparent";
  ea.style.fillStyle       = "solid";
  ea.style.strokeWidth     = 0;
  ea.style.roundness       = null;
  const textId = ea.addText(PAD_X, textY, wrappedText, { width: textMaxW });

  const cleanHeading = heading.heading.replace(/#\S+/g, '').trim();
  ea.getElement(rectId).link = `[[${baseName}#${cleanHeading}]]`;
  ea.addToGroup([rectId, textId]);

  y += BOX_HEIGHT + GAP;
}

await ea.addElementsToView(true, true);
new Notice("Done!");