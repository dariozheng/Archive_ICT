const files = app.vault.getMarkdownFiles();
const fileNames = files.map(f => f.path);
const chosen = await utils.suggester(fileNames, fileNames, "Pick a note");
if (!chosen) return;

const file = files.find(f => f.path === chosen);
if (!file) { new Notice("File not found"); return; }

const cache = app.metadataCache.getFileCache(file);
if (!cache?.headings || cache.headings.length === 0) {
  new Notice("No headers found.");
  return;
}

const content = await app.vault.read(file);
const lines = content.split("\n");

const baseName = file.basename;
let y = 0;
const BOX_WIDTH = 400;
const BOX_PADDING_X = 18;
const BOX_PADDING_Y = 14;
const PREVIEW_FONT_SIZE = 13;
const LINE_HEIGHT = PREVIEW_FONT_SIZE * 1.2;  // tighter line height
const TEXT_BASELINE_OFFSET = 2;               // compensate for Excalidraw top padding
const CHAR_WIDTH = PREVIEW_FONT_SIZE * 0.52;
const MAX_TEXT_WIDTH = BOX_WIDTH - BOX_PADDING_X * 2;
const CHARS_PER_LINE = Math.floor(MAX_TEXT_WIDTH / CHAR_WIDTH);

function cleanText(raw) {
  return raw
    .replace(/!\[.*?\]\(.*?\)/g, '')
    .replace(/\[\[([^\]|]+\|)?([^\]]+)\]\]/g, '$2')
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
    .replace(/<[^>]+>/g, '')
    .replace(/[*_~`#>]+/g, '')
    .replace(/%%.*?%%/gs, '')
    .replace(/```[\s\S]*?```/g, '')
    .replace(/\s+/g, ' ')
    .trim();
}

function firstTwoSentences(text) {
  const sentences = text.match(/[^.!?]+[.!?]+/g);
  if (!sentences) return text;
  return sentences.slice(0, 2).join(' ').trim();
}

function wrapText(text, maxChars) {
  const words = text.split(' ');
  const wrappedLines = [];
  let current = '';
  for (const word of words) {
    if ((current + ' ' + word).trim().length <= maxChars) {
      current = (current + ' ' + word).trim();
    } else {
      if (current) wrappedLines.push(current);
      current = word;
    }
  }
  if (current) wrappedLines.push(current);
  return wrappedLines;
}

for (let i = 0; i < cache.headings.length; i++) {
  const heading = cache.headings[i];
  const level = heading.level;
  const displayText = heading.heading;

  const fontSize = Math.max(36 - (level - 1) * 6, 16);
  const indent = (level - 1) * 30;

  // --- Heading text ---
  ea.style.fontSize = fontSize;
  ea.style.fontFamily = 1;
  ea.style.strokeColor =
    level === 1 ? "#1e1e1e" :
    level === 2 ? "#364fc7" :
    "#5c7cfa";
  ea.style.backgroundColor = "transparent";
  ea.style.fillStyle = "solid";
  ea.style.roundness = null;

  const headingId = ea.addText(indent, y, displayText);
  const cleanHeading = displayText.replace(/#\S+/g, '').trim();
  ea.getElement(headingId).link = `[[${baseName}#${cleanHeading}]]`;

  y += fontSize + 10;

  // --- Extract and clean section preview text ---
  const startLine = heading.position.end.line + 1;
  const nextHeading = cache.headings[i + 1];
  const endLine = nextHeading
    ? nextHeading.position.start.line
    : lines.length;

  const rawSection = lines
    .slice(startLine, endLine)
    .filter(l => {
      const t = l.trim();
      return t !== "" && !t.startsWith("#") && !t.startsWith("![[");
    })
    .join(" ");

  const sectionText = cleanText(rawSection);

  if (sectionText.length > 0) {
    const preview = firstTwoSentences(sectionText);

    const wrappedLines = wrapText(preview, CHARS_PER_LINE);
    const textBlockHeight = wrappedLines.length * LINE_HEIGHT;
    const boxHeight = textBlockHeight + BOX_PADDING_Y * 2;
    const wrappedText = wrappedLines.join('\n');

    // --- Background rectangle ---
    ea.style.strokeColor = level === 1 ? "#1e1e1e" : level === 2 ? "#364fc7" : "#5c7cfa";
    ea.style.backgroundColor = level === 1 ? "#f8f9fa" : level === 2 ? "#e8f4ff" : "#eef2ff";
    ea.style.fillStyle = "solid";
    ea.style.strokeWidth = 1;
    ea.style.roughness = 0;
    ea.style.roundness = { type: 3 };

    const rectId = ea.addRect(indent, y, BOX_WIDTH, boxHeight);
    ea.style.roundness = null;

    // --- Preview text inside the box ---
    ea.style.fontSize = PREVIEW_FONT_SIZE;
    ea.style.strokeColor = "#444444";
    ea.style.backgroundColor = "transparent";

    const previewId = ea.addText(
      indent + BOX_PADDING_X,
      y + BOX_PADDING_Y - TEXT_BASELINE_OFFSET,
      wrappedText
    );

    ea.addToGroup([headingId, rectId, previewId]);

    y += boxHeight + 24;
  } else {
    y += 16;
  }
}

await ea.addElementsToView(true, true);
new Notice("Done!");