<%*
// Get active file by leaf instead
const leaf = app.workspace.getMostRecentLeaf();
const file = leaf?.view?.file;
if (!file) { new Notice("No active file"); return; }

if (!file.path.endsWith(".md")) { new Notice("Active file is not a markdown/Excalidraw file"); return; }

const content = await app.vault.read(file);

// Excalidraw stores JSON in a text block, try multiple patterns
let rawJson = null;

// Pattern 1: ```json block after Excalidraw Data header
const jsonMatch1 = content.match(/##\s*Excalidraw Data[\s\S]*?```json\n([\s\S]*?)\n```/);
// Pattern 2: just a raw ```json block
const jsonMatch2 = content.match(/```json\n([\s\S]*?)\n```/);
// Pattern 3: the JSON object starts directly with {"type":"excalidraw"
const jsonMatch3 = content.match(/({"type":"excalidraw"[\s\S]*})/);

if (jsonMatch1) rawJson = jsonMatch1[1];
else if (jsonMatch2) rawJson = jsonMatch2[1];
else if (jsonMatch3) rawJson = jsonMatch3[1];

if (!rawJson) {
  new Notice("Could not find Excalidraw JSON in this file. Make sure the Excalidraw note is open.");
  return;
}

let excalidrawData;
try {
  excalidrawData = JSON.parse(rawJson);
} catch (e) {
  new Notice("Failed to parse JSON: " + e.message);
  return;
}

const SCALE_BY_TYPE = {
  large:  28,  // H1 (was ≥30)
  medium: 22,  // H2 (was 20–29)
  small:  16,  // H3 (was <20)
};

let changed = 0;

for (const el of excalidrawData.elements) {
  if (el.type === "text" && el.fontSize) {
    const oldSize = el.fontSize;
    let newSize;
    if (oldSize >= 30) newSize = SCALE_BY_TYPE.large;
    else if (oldSize >= 20) newSize = SCALE_BY_TYPE.medium;
    else newSize = SCALE_BY_TYPE.small;

    if (newSize !== oldSize) {
      const ratio = newSize / oldSize;
      el.fontSize = newSize;
      el.width  = el.width  * ratio;
      el.height = el.height * ratio;
      changed++;
    }
  }
}

if (changed === 0) {
  new Notice("No text elements needed updating.");
  return;
}

const newJson = JSON.stringify(excalidrawData, null, 2);
const newContent = content.replace(rawJson, newJson);
await app.vault.modify(file, newContent);

new Notice(`✓ Updated ${changed} text element(s). Close and reopen the note to see changes.`);
%>