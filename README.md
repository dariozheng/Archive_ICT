Archive_ICT Guide

# Categories
This is the folder where 

# Template
There is a template for each category. 
Every category have the following propertie:
- categories: The categories of the notes, can be one or mor
- topic@category: the topic under each categories, if there are more than one category add topic@category for each of them
- tags
- created: this is a code from Templater plugin, it's the date of creation
- modified: this is updated by the **Update modified date** plugin

# Graph view:
In Filters add:
- **-path:Notes/Glossaries**
- Enable only **Orphans**
In Groups add:
- tag:#categories
- tag:#topic

# Files and links
Default location for new notes: Notes
Advanced/Excluded files: 
- Templates/
- attachments/

# Plugins
## Highlightr
In Hotkeys bind **Highlightr: Open Highlightr**
## Wrap with shortcuts
Add a new wrapper with a shortcut: 
- Name = **bold** Start Tag = **\<strong>** End Tag = **\</strong>**
## Update modified date
Modified date property: **modified**
Date format: **YYYY-MM-DDTHH:mm:ssZ**
Date locale: **it**
Vault options/Exclude folders: **Templates**
## Templater:
Teplate folder location: **Templates/Notes**
**Templates/Notes/Codes/Link to Glossary**: This template add a link to the selected word to the corrispondent word in the chosen glossary, the glossaries can be found in the folder Notes/Glossaries


