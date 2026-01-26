<%*
const glossary = [
    { name: "cloud computing" },
    { name: "networking" },
    { name: "security" },
    { name: "hardware" }
];

// Get selected text or prompt for alias
let text = tp.file.selection();
if (!text) {
    text = await tp.system.prompt("Alias text:");
}

// Ensure the suggester is awaited
const choice = await tp.system.suggester(
    glossary.map(c => c.name),
    glossary.map(c => c.name) // Returns the same string selected
);

// Exit if no choice is made (e.g., ESC pressed)
if (!choice) return;

// Correct link syntax: [[File#Header|Alias]]
tR += `[[${choice} glossary#${text}|${text}]]`;
-%>

