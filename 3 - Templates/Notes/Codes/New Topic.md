<%*
// Scaffolds a topic inside an existing category: the note body + its .base.
// Wired as a Templater folder template on "2 - Categories/Topics".
// The category is the parent folder, and its topic property is read back from
// "3 - Templates/Categories/<Category> Template.md" - so the only prompt is the name.
// Safe to re-run manually on an existing topic note to repair a missing base.

const TOPICS = "2 - Categories/Topics";
const BASES_TOPICS = "3 - Templates/Bases/Topics";
const CATEGORY_TEMPLATES = "3 - Templates/Categories";

// Folder templates cascade, so this also sees Topics/ itself and any deeper path.
// Only fire exactly one level deep: 2 - Categories/Topics/<Category>/<Topic>.md.
const folder = tp.file.folder(true);
if (!folder.startsWith(`${TOPICS}/`)) return;
const category = folder.slice(TOPICS.length + 1);
if (!category || category.includes("/")) return;

// Live TFile ref. Do NOT use tp.file.title: it is a string snapshot taken before
// this block runs, so it stays "Untitled" even after a rename.
const file = tp.config.target_file;

// trigger_on_file_creation hooks vault "create" and waits only 300ms, so the note
// is still "Untitled" here - the user has not typed the real name yet.
let name = file.basename;
if (/^Untitled( \d+)?$/.test(name)) {
    const input = await tp.system.prompt(`Topic name (in ${category})`);
    if (!input || !input.trim()) { new Notice("New Topic: cancelled."); return; }
    name = input.trim();
}

// tp.file.rename() throws on these.
if (/[\\/:]/.test(name)) {
    new Notice("New Topic: name cannot contain \\ / or :");
    return;
}

// Read the category's topic property back from its note template instead of deriving
// it: robust even where a category carries a second key (Linux has Distro alongside
// topic@linux). Whatever key is left after removing the fixed ones is the topic property.
const FIXED = ["categories", "tags", "icon", "iconColor", "last_update", "status", "aliases", "cssclasses"];
let topicProp = null;
const tmpl = app.vault.getAbstractFileByPath(`${CATEGORY_TEMPLATES}/${category} Template.md`);
if (tmpl) {
    const fm = (await app.vault.read(tmpl)).match(/^---\n([\s\S]*?)\n---/);
    if (fm) {
        let keys = [...fm[1].matchAll(/^([A-Za-z][A-Za-z0-9_@-]*):/gm)]
            .map((m) => m[1])
            .filter((k) => !FIXED.includes(k));
        // Linux declares both Distro and topic@linux; the topic@ one wins.
        if (keys.length > 1 && keys.some((k) => k.startsWith("topic@"))) {
            keys = keys.filter((k) => k.startsWith("topic@"));
        }
        if (keys.length === 1) topicProp = keys[0];
    }
}
// Only reached for a hand-made category with no template, or an ambiguous one.
if (!topicProp) {
    const slug = category.toLowerCase().replace(/\s+/g, "_");
    const input = await tp.system.prompt(`Topic property for ${category}`, `topic@${slug}`);
    if (!input || !input.trim()) { new Notice("New Topic: cancelled."); return; }
    topicProp = input.trim();
}

const basesFolder = `${BASES_TOPICS}/${category}`;
const basePath = `${basesFolder}/${name}.base`;
const notePath = `${folder}/${name}.md`;

// Bases are embedded by filename only (![[X.base]]), which Obsidian resolves
// vault-wide - so a duplicate name would make the embed resolve to the wrong base.
const clash = app.vault.getFiles().find((f) => f.name === `${name}.base` && f.path !== basePath);
if (clash) {
    new Notice(`New Topic: a base named "${name}.base" already exists at ${clash.path}.`);
    return;
}

// Rename first: it is the only step that can collide, so failing here means we abort
// before creating anything. basename is re-read live because opening the prompt modal
// blurs the explorer's inline rename box, committing whatever was typed there.
if (file.basename !== name) {
    if (app.vault.getAbstractFileByPath(notePath)) {
        new Notice(`New Topic: "${name}" already exists in ${folder}.`);
        return;
    }
    try {
        await tp.file.rename(name);
    } catch (e) {
        new Notice(`New Topic: rename failed - ${e.message}`);
        return;
    }
}

// Bases requires bracket syntax for properties containing "@".
const topicRef = topicProp.includes("@") ? `note["${topicProp}"]` : topicProp;
const categorySlug = category.toLowerCase().replace(/\s+/g, "_");
const topicSlug = name.toLowerCase().replace(/\s+/g, "_");

// The kind tag (topic/product) is a per-category convention the property does NOT
// determine - Microsoft and Linux use "product" despite topic@ properties. Copy it
// from the category's General hub note; default to "topic" if there isn't one yet.
let kindTag = "topic";
const generalNote = app.vault.getAbstractFileByPath(`${folder}/${category} General.md`);
if (generalNote) {
    const gm = (await app.vault.read(generalNote)).match(/^tags:\n((?:  - .*\n)*)/m);
    if (gm) {
        const first = [...gm[1].matchAll(/  - (.*)/g)].map((x) => x[1].trim())
            .find((t) => !t.startsWith("category/"));
        if (first) kindTag = first;
    }
}

const topicBase = [
    "views:",
    "  - type: table",
    "    name: Table",
    "    filters:",
    "      and:",
    `        - ${topicRef}.contains(link("${name}"))`,
    "",
].join("\n");

const created = [];
const skipped = [];

try {
    // app.vault.create does not create parent folders. The category's bases folder
    // exists for scaffolded categories but not necessarily for hand-made ones.
    if (!app.vault.getAbstractFileByPath(basesFolder)) {
        await app.vault.createFolder(basesFolder);
        created.push(basesFolder);
    }
    if (app.vault.getAbstractFileByPath(basePath)) skipped.push(basePath);
    else { await app.vault.create(basePath, topicBase); created.push(basePath); }
} catch (e) {
    // Report and fall through: the note body is still written below, so a manual
    // re-run can repair whatever is missing.
    console.error("[New Topic]", e);
    new Notice(`New Topic: ${e.message}`);
}

console.log(`[New Topic] ${name} in ${category}`, { topicProp, created, skipped });
new Notice(`✓ Topic "${name}" in ${category} (${topicProp}): ${created.length} created, ${skipped.length} skipped.`, 8000);

// Only write the body when the note is empty, so a manual re-run does not append a
// second embed. Templater parses this frontmatter, merges it into the note and
// re-serialises it with Obsidian's YAML writer - which yields exactly this shape.
if (tp.file.content.trim()) return;

tR += ["---", "tags:", `  - ${kindTag}`, `  - category/${categorySlug}/${topicSlug}`, "icon:", "iconColor:", "---", `![[${name}.base]]`].join("\n");
-%>
