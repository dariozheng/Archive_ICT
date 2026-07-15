<%*
// Deletes one topic - its note and its .base - to the system trash.
// Run manually: Templater -> Open insert template modal -> Delete Topic.
// The category itself and every content note stay untouched.

const TOPICS = "2 - Categories/Topics";
const BASES_TOPICS = "3 - Templates/Bases/Topics";

const file = tp.config.target_file;

// Topic notes are exactly one level under Topics/: Topics/<Category>/<Topic>.md
const topics = app.vault.getMarkdownFiles()
    .filter((f) => f.parent?.parent?.path === TOPICS)
    .sort((a, b) => a.path.localeCompare(b.path));
if (!topics.length) { new Notice("Delete Topic: no topics found."); return; }

const rows = topics.map((f) => `${f.parent.name}  /  ${f.basename}`);
const pick = await tp.system.suggester(rows, topics, false, "Delete which topic?");
if (!pick) { new Notice("Delete Topic: cancelled."); return; }

const category = pick.parent.name;
const name = pick.basename;

const doomed = [pick.path];
const basePath = `${BASES_TOPICS}/${category}/${name}.base`;
if (app.vault.getAbstractFileByPath(basePath)) doomed.push(basePath);

// Templater writes tR to the active file AFTER this block returns, which would
// recreate the note on disk moments after we trashed it.
if (doomed.includes(file.path)) {
    new Notice("Delete Topic: that is the note you are viewing. Open a different note, then run this again.", 10000);
    return;
}

// Who points at it? Warning only - these are never touched.
const referrers = new Set();
for (const [src, targets] of Object.entries(app.metadataCache.resolvedLinks)) {
    if (doomed.includes(src)) continue;
    if (Object.keys(targets).some((t) => doomed.includes(t))) referrers.add(src);
}
// Belt and braces: frontmatter wikilinks, in case the link graph misses any.
for (const f of app.vault.getMarkdownFiles()) {
    if (doomed.includes(f.path) || referrers.has(f.path)) continue;
    const fm = app.metadataCache.getFileCache(f)?.frontmatter;
    if (!fm) continue;
    for (const m of JSON.stringify(fm).matchAll(/\[\[([^\]|#]+)/g))
        if (m[1] === name) { referrers.add(f.path); break; }
}

const isGeneral = name === `${category} General`;
const refLine = referrers.size === 1 ? "1 note references it" : `${referrers.size} notes reference it`;

console.log(`[Delete Topic] ${category}/${name}`, { doomed, referrers: [...referrers] });
new Notice([
    `Deleting "${name}" from ${category} moves these to the system trash:`,
    ...doomed.map((p) => `  ${p}`),
    "",
    referrers.size
        ? `${refLine}.\nNOT deleted, NOT edited - their links will dangle.`
        : "Nothing references it.",
    isGeneral ? `\nHeads up: this is ${category}'s General topic, part of its scaffold.` : "",
].join("\n"), 15000);

// Cancel is first, so it is the highlighted default and Enter is always safe.
const go = await tp.system.suggester(
    ["Cancel",
     `DELETE "${name}" from ${category}  -  ${doomed.length} files, ${referrers.size} referrer${referrers.size === 1 ? "" : "s"}  ->  system trash`],
    [false, true],
    false,
    `Confirm: delete topic "${name}"?`
);
if (!go) { new Notice("Delete Topic: cancelled."); return; }

const trashed = [];
try {
    for (const p of doomed) {
        const f = app.vault.getAbstractFileByPath(p);
        if (!f) continue;
        await app.vault.trash(f, true); // true = system trash, recoverable from Finder
        trashed.push(p);
    }
} catch (e) {
    console.error("[Delete Topic]", e);
    new Notice(`Delete Topic: ${e.message}`);
}

console.log(`[Delete Topic] trashed`, trashed);
new Notice(
    `✓ Deleted "${name}" from ${category}: ${trashed.length} file${trashed.length === 1 ? "" : "s"} to the system trash.` +
    (referrers.size ? `\n${referrers.size} note${referrers.size === 1 ? " has" : "s have"} a dangling link now.` : ""),
    10000);
-%>
