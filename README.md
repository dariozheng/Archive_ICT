Archive_ICT Guide

# Template
There is a template for each category. 
Every category have the following propertie:
- categories: In this field are the categories of the note, can be more than one. The field must be filled with links to the corrispondent notes in the folder **Categories**, and not plain text.
- topic@category: the topic under each categories, if there are more than one category add topic@category for each of them
- tags
- created: this is a code from Templater plugin, it's the date of creation
- modified: this is updated by the **Update modified date** plugin

# Categories
This is the folder where is present the notes that are linked to the category field. 
Each main category field note has the tag **categories** and it's linked to its corrispondent **.base** file.


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


