<%*
// Turns the selected word into a link to the heading of the same name in a glossary.
// The glossaries are read from the folder below, so a new glossary needs no edit here.
const FOLDER = "0 - Notes/Glossaries";

// Templater replaces the selection with this script's output, so every way out
// that does not create a link must hand the selection back, or the word is lost.
const selection = tp.file.selection();
const giveBack = () => { tR += selection; };

let term = selection;
if (!term) term = await tp.system.prompt("Term to link:");
if (!term || !term.trim()) { giveBack(); return; }

// Keep any spaces selected around the word outside the link.
const [, lead, core, trail] = term.match(/^(\s*)([\s\S]*?)(\s*)$/);

const glossaries = app.vault.getMarkdownFiles()
    .filter((f) => f.parent?.path === FOLDER)
    .sort((a, b) => a.basename.localeCompare(b.basename));
if (!glossaries.length) {
    new Notice(`Link to Glossary: no notes in ${FOLDER}.`, 8000);
    giveBack();
    return;
}

const pick = await tp.system.suggester(glossaries.map((f) => f.basename), glossaries, false, `Glossary for "${core}"`);
if (!pick) { giveBack(); return; }

// Warn when the glossary has no heading with that name: the link would then open
// the glossary at the top instead of at the term.
const norm = (s) => s.trim().replace(/\s+/g, " ").toLowerCase();
const headings = (app.metadataCache.getFileCache(pick)?.headings ?? []).map((h) => norm(h.heading));
if (!headings.includes(norm(core))) {
    new Notice(`Link to Glossary: "${core}" is not a heading in ${pick.basename} yet. Add it there as a level 4 heading.`, 10000);
}

tR += `${lead}[[${pick.basename}#${core}|${core}]]${trail}`;
-%>
