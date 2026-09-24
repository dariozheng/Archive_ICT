<%*
// Pick a category (then optionally a topic) and stamp this note's frontmatter.
// Run manually: Templater -> Open insert template modal -> New Note.
// The per-category templates live in 3 - Templates/Categories/, deliberately
// OUTSIDE Templater's templates folder, so this picker is the only way in and
// the insert modal stays down to the scripts.

const CATEGORY_TEMPLATES = "3 - Templates/Categories";
const TOPICS = "2 - Categories/Topics";
const SUFFIX = " Template";

const templates = app.vault.getMarkdownFiles()
    .filter((f) => f.parent?.path === CATEGORY_TEMPLATES && f.basename.endsWith(SUFFIX))
    .sort((a, b) => a.basename.localeCompare(b.basename));
if (!templates.length) {
    new Notice(`New Note: no "<Category>${SUFFIX}.md" files in ${CATEGORY_TEMPLATES}.`, 8000);
    return;
}

const cats = templates.map((f) => f.basename.slice(0, -SUFFIX.length));
const pick = await tp.system.suggester(cats, templates, false, "Which category?");
if (!pick) { new Notice("New Note: cancelled."); return; }
const category = pick.basename.slice(0, -SUFFIX.length);

let body = await app.vault.read(pick);

// The topic property is whatever key the template declares that is not a fixed one
// - the same discovery New Topic uses, so any per-category quirk (e.g. Linux's extra
// Distro key) needs no special casing here either.
const FIXED = ["categories", "tags", "icon", "iconColor", "last_update", "status", "aliases", "cssclasses"];
const fm = body.match(/^---\n([\s\S]*?)\n---/);
let keys = fm
    ? [...fm[1].matchAll(/^([A-Za-z][A-Za-z0-9_@-]*):/gm)].map((m) => m[1]).filter((k) => !FIXED.includes(k))
    : [];
// Linux declares both Distro and topic@linux; the topic@ one wins.
if (keys.length > 1 && keys.some((k) => k.startsWith("topic@"))) keys = keys.filter((k) => k.startsWith("topic@"));
const topicProp = keys.length === 1 ? keys[0] : null;

if (topicProp) {
    const topics = app.vault.getMarkdownFiles()
        .filter((f) => f.parent?.path === `${TOPICS}/${category}`)
        .sort((a, b) => a.basename.localeCompare(b.basename));
    if (topics.length) {
        // Skip is first, so it is the highlighted default and Enter leaves it blank.
        const rows = [`(skip - fill ${topicProp} in later)`, ...topics.map((f) => f.basename)];
        const vals = [null, ...topics.map((f) => f.basename)];
        const topic = await tp.system.suggester(rows, vals, false, `Which topic in ${category}?`);
        if (topic) {
            // Fill the empty "<prop>:" line in place so the template's key order survives.
            // List form: 45 of the 49 notes that set a topic use it, and it allows several.
            const key = topicProp.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
            body = body.replace(new RegExp(`^${key}:[ \\t]*$`, "m"), `${topicProp}:\n  - "[[${topic}]]"`);
            // Deepen the category tag: category/<cat>  ->  category/<cat>/<topic>.
            const catSlug = category.toLowerCase().replace(/\s+/g, "_");
            const topicSlug = topic.toLowerCase().replace(/\s+/g, "_");
            const catTag = `category/${catSlug}`.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
            body = body.replace(new RegExp(`^  - ${catTag}$`, "m"), `  - category/${catSlug}/${topicSlug}`);
        }
    }
}

console.log(`[New Note] ${category}`, { template: pick.path, topicProp });

// Templater parses this frontmatter, merges it into the note and re-serialises it
// with Obsidian's YAML writer.
tR += body;
-%>
