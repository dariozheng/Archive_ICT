Archive_ICT Guide

# Template
There is a template for each category. 
Every category have the following propertie:
- categories: In this field are the categories of the note, can be more than one. The field must be filled with links to the corrispondent notes in the folder <strong>Categories</strong>, and not plain text.
- topic@category: the topic under each categories, if there are more than one category add topic@category for each of them
- tags

# Categories
This is the folder where is present the notes that are linked to the category field. 
Each main category field note has the tag <strong>categories</strong> and it's linked to its corrispondent <strong>.base</strong> file. To link a base, use: ![[filename.base]]
In this folder its also present the Topic folder where each catogory has its topic folder with their <strong>.base</strong> files.

# Base
The base file can be found in <strong>Templates/Bases</strong>. 
Filter the base file in the following way:

```where categories.contains(link("Networking")) and !file.name.contains("Template")```
  
# Graph view:
In Filters add:
- <strong>-path:Notes/Glossaries</strong>
- Enable only <strong>Orphans</strong>
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
In Hotkeys bind <strong>Highlightr: Open Highlightr</strong>

## Wrap with shortcuts
Add a new wrapper with a shortcut: 
- Name = <strong>bold</strong> Start Tag = <strong>\<strong></strong> End Tag = <strong>\</strong></strong>
  
## Templater:
Teplate folder location: <strong>Templates/Notes</strong>
<strong>Templates/Notes/Codes/Link to Glossary</strong>: This template add a link to the selected word to the corrispondent word in the chosen glossary, the glossaries can be found in the folder Notes/Glossaries


