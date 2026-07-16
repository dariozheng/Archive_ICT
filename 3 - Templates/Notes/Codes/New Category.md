<%*
// Scaffolds a full category: note body + Topics folders + bases + note template.
// Wired as a Templater folder template on "2 - Categories".
// Safe to re-run manually on an existing category note to repair a partial scaffold.

const CATEGORIES = "2 - Categories";
const BASES = "3 - Templates/Bases";
const CATEGORY_TEMPLATES = "3 - Templates/Categories";

// Folder templates cascade into subfolders ("the deepest match is used"), so this
// also fires for 2 - Categories/Topics/<X>/. Only scaffold at the top level.
if (tp.file.folder(true) !== CATEGORIES) return;

// Live TFile ref. Do NOT use tp.file.title: it is a string snapshot taken before
// this block runs, so it stays "Untitled" even after a rename.
const file = tp.config.target_file;

// trigger_on_file_creation hooks vault "create" and waits only 300ms, so the note
// is still "Untitled" here - the user has not typed the real name yet.
let name = file.basename;
if (/^Untitled( \d+)?$/.test(name)) {
    const input = await tp.system.prompt("Category name (e.g. Placeholder)");
    if (!input || !input.trim()) { new Notice("New Category: cancelled."); return; }
    name = input.trim();
}

// tp.file.rename() throws on these.
if (/[\\/:]/.test(name)) {
    new Notice("New Category: name cannot contain \\ / or :");
    return;
}

// Topic property. Default is topic@<slug>, but this vault has exceptions
// (Cloud Computing -> topic@cloud, Microsoft -> product), so allow an override.
// Slug for the nested tag tree: lowercase, spaces -> underscores (cloud_computing).
const tagSlug = name.toLowerCase().replace(/\s+/g, "_");
const propInput = await tp.system.prompt("Topic property", `topic@${tagSlug}`);
if (!propInput || !propInput.trim()) { new Notice("New Category: cancelled."); return; }
const topicProp = propInput.trim();

// Bases requires bracket syntax for properties containing "@".
const topicRef = topicProp.includes("@") ? `note["${topicProp}"]` : topicProp;

const general = `${name} General`;
const topicsFolder = `${CATEGORIES}/Topics/${name}`;
const basesFolder = `${BASES}/Topics/${name}`;
const categoryNotePath = `${CATEGORIES}/${name}.md`;

// Rename first: it is the only step that can collide, so failing here means we abort
// before creating anything. basename is re-read live because opening the prompt modal
// blurs the explorer's inline rename box, committing whatever was typed there.
if (file.basename !== name) {
    if (app.vault.getAbstractFileByPath(categoryNotePath)) {
        new Notice(`New Category: "${name}" already exists in ${CATEGORIES}.`);
        return;
    }
    try {
        await tp.file.rename(name);
    } catch (e) {
        new Notice(`New Category: rename failed - ${e.message}`);
        return;
    }
}

const created = [];
const skipped = [];

const ensureFolder = async (path) => {
    if (app.vault.getAbstractFileByPath(path)) { skipped.push(path); return; }
    await app.vault.createFolder(path);
    created.push(path);
};

// tp.file.create_new() forces .md for string templates, so .base files must go
// through app.vault.create - which does NOT create parent folders and throws if the
// file exists. Hence the folders-first ordering and the existence checks.
const ensureFile = async (path, content) => {
    if (app.vault.getAbstractFileByPath(path)) { skipped.push(path); return; }
    await app.vault.create(path, content);
    created.push(path);
};

const categoryBase = [
    "views:",
    "  - type: table",
    "    name: Table",
    "    filters:",
    "      and:",
    `        - categories.contains(link("${name}"))`,
    `        - '!file.name.contains("Template")'`,
    "",
].join("\n");

const generalBase = [
    "views:",
    "  - type: table",
    "    name: Table",
    "    filters:",
    "      and:",
    `        - ${topicRef}.contains(link("${general}"))`,
    "",
].join("\n");

const noteTemplate = [
    "---",
    "categories:",
    `  - "[[${name}]]"`,
    `${topicProp}:`,
    "tags:",
    `  - category/${tagSlug}`,
    "icon:",
    "iconColor:",
    "last_update:",
    "---",
    "",
].join("\n");

// New categories default to the "topic" kind; change it by hand for a product line.
const generalNote = [
    "---",
    "tags:",
    "  - topic",
    `  - category/${tagSlug}/${tagSlug}_general`,
    "icon:",
    "iconColor:",
    "---",
    `![[${general}.base]]`,
    "",
].join("\n");

try {
    await ensureFolder(topicsFolder);
    await ensureFolder(basesFolder);
    await ensureFile(`${BASES}/${name}.base`, categoryBase);
    await ensureFile(`${basesFolder}/${general}.base`, generalBase);
    await ensureFile(`${CATEGORY_TEMPLATES}/${name} Template.md`, noteTemplate);
    await ensureFile(`${topicsFolder}/${general}.md`, generalNote);
} catch (e) {
    // Report and fall through: the category note body is still written below, so a
    // manual re-run can repair whatever is missing.
    console.error("[New Category]", e);
    new Notice(`New Category: ${e.message}`);
}

console.log(`[New Category] ${name}`, { created, skipped });
new Notice(`✓ Category "${name}": ${created.length} created, ${skipped.length} skipped.`, 8000);

// Only write the body when the note is empty, so a manual re-run does not append a
// second embed. Templater parses this frontmatter, merges it into the note and
// re-serialises it with Obsidian's YAML writer - which yields exactly this shape.
if (tp.file.content.trim()) return;

tR += ["---", "tags:", "  - categories", "---", `![[${name}.base]]`].join("\n");
-%>
