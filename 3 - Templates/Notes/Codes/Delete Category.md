<%*
// Deletes a category and all of its scaffolding, to the system trash.
// Run manually: Templater -> Open insert template modal -> Delete Category.
// Content notes in 0 - Notes/ are NEVER deleted and never edited - only the
// category's own artifacts go. Notes that referenced it keep a dangling link,
// which the confirmation counts for you first.

const CATEGORIES = "2 - Categories";
const TOPICS = `${CATEGORIES}/Topics`;
const BASES = "3 - Templates/Bases";
const CATEGORY_TEMPLATES = "3 - Templates/Categories";

const file = tp.config.target_file;

// Category notes are the notes sitting directly in 2 - Categories.
const cats = app.vault.getMarkdownFiles()
    .filter((f) => f.parent?.path === CATEGORIES)
    .map((f) => f.basename)
    .sort();
if (!cats.length) { new Notice("Delete Category: no categories found."); return; }

const countIn = (dir) => app.vault.getFiles().filter((f) => f.path.startsWith(`${dir}/`)).length;
const rows = cats.map((c) => {
    const n = countIn(`${TOPICS}/${c}`);
    return `${c}  -  ${n} topic${n === 1 ? "" : "s"}`;
});
const cat = await tp.system.suggester(rows, cats, false, "Delete which category?");
if (!cat) { new Notice("Delete Category: cancelled."); return; }

const loose = [
    `${CATEGORIES}/${cat}.md`,
    `${BASES}/${cat}.base`,
    `${CATEGORY_TEMPLATES}/${cat} Template.md`,
].filter((p) => app.vault.getAbstractFileByPath(p));

const dirs = [
    `${TOPICS}/${cat}`,
    `${BASES}/Topics/${cat}`,
].filter((p) => app.vault.getAbstractFileByPath(p));

// Every file that will disappear, including everything inside those two folders.
const doomed = new Set(loose);
for (const d of dirs)
    for (const f of app.vault.getFiles())
        if (f.path.startsWith(`${d}/`)) doomed.add(f.path);

// Templater writes tR to the active file AFTER this block returns, which would
// recreate the note on disk moments after we trashed it.
if (doomed.has(file.path)) {
    new Notice(`Delete Category: this note is part of "${cat}". Open a note outside it, then run this again.`, 10000);
    return;
}

// Who points at anything being deleted? Warning only - these are never touched.
const doomedNames = new Set([...doomed].filter((p) => p.endsWith(".md"))
    .map((p) => p.slice(p.lastIndexOf("/") + 1, -3)));
const referrers = new Set();
for (const [src, targets] of Object.entries(app.metadataCache.resolvedLinks)) {
    if (doomed.has(src)) continue;
    if (Object.keys(targets).some((t) => doomed.has(t))) referrers.add(src);
}
// Belt and braces: frontmatter wikilinks, in case the link graph misses any.
for (const f of app.vault.getMarkdownFiles()) {
    if (doomed.has(f.path) || referrers.has(f.path)) continue;
    const fm = app.metadataCache.getFileCache(f)?.frontmatter;
    if (!fm) continue;
    for (const m of JSON.stringify(fm).matchAll(/\[\[([^\]|#]+)/g))
        if (doomedNames.has(m[1])) { referrers.add(f.path); break; }
}

const refLine = referrers.size === 1 ? "1 note references it" : `${referrers.size} notes reference it`;

const summary = [
    `Deleting "${cat}" moves these to the system trash:`,
    ...loose.map((p) => `  ${p}`),
    ...dirs.map((p) => `  ${p}/   (${countIn(p)} files)`),
    "",
    referrers.size
        ? `${refLine}.\nNOT deleted, NOT edited - their links will dangle.`
        : "Nothing references it.",
].join("\n");

console.log(`[Delete Category] ${cat}`, { loose, dirs, doomed: [...doomed], referrers: [...referrers] });
new Notice(summary, 15000);

// Cancel is first, so it is the highlighted default and Enter is always safe.
const go = await tp.system.suggester(
    ["Cancel",
     `DELETE "${cat}"  -  ${doomed.size} files, ${dirs.length} folders, ${referrers.size} referrer${referrers.size === 1 ? "" : "s"}  ->  system trash`],
    [false, true],
    false,
    `Confirm: delete category "${cat}"?`
);
if (!go) { new Notice("Delete Category: cancelled."); return; }

const trashed = [];
try {
    // Folders first: trashing a folder takes everything inside it in one move.
    for (const p of [...dirs, ...loose]) {
        const f = app.vault.getAbstractFileByPath(p);
        if (!f) continue;
        await app.vault.trash(f, true); // true = system trash, recoverable from Finder
        trashed.push(p);
    }
} catch (e) {
    console.error("[Delete Category]", e);
    new Notice(`Delete Category: ${e.message}`);
}

console.log(`[Delete Category] trashed`, trashed);
new Notice(
    `✓ Deleted "${cat}": ${trashed.length} item${trashed.length === 1 ? "" : "s"} to the system trash.` +
    (referrers.size ? `\n${referrers.size} note${referrers.size === 1 ? " has" : "s have"} a dangling link now.` : ""),
    10000);
-%>
