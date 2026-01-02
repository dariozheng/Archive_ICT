<%*
let text = tp.file.selection();
if (!text) {
    text = await tp.system.prompt("Alias text:");
}

const glossary = await tp.system.prompt("Glossary term:");

tR += `[[${glossary} glossary#### ${text} | ${text}]]`;
%>