'use strict';

// Category Tag Sync
// The nested category/<cat>/<topic> tags are DERIVED from a note's `categories` and
// `topic@<cat>` properties. On every metadata change this recomputes the desired
// category-tag set and rewrites frontmatter ONLY when it differs - so it is loop-safe
// (the write triggers another change event, which finds nothing to do) and causes no
// churn on notes that are already correct.

const obsidian = require('obsidian');

const TEMPLATES = '3 - Templates/'; // seeds, not content - never touch

const slug = (s) => String(s).toLowerCase().replace(/\s+/g, '_');
const asArray = (v) => (v == null ? [] : Array.isArray(v) ? v : [v]);
// "[[2 - Cat/Topics/Networking/Cisco ISE|Cisco ISE]]" -> "Cisco ISE"
const linkName = (v) =>
  String(v).replace(/^["']|["']$/g, '').replace(/^\[\[|\]\]$/g, '').split('|')[0].split('/').pop().trim();

// Pure: frontmatter object -> Set of desired category tags. Exposed statically for tests.
function desiredCategoryTags(fm) {
  const tags = new Set();
  const withTopic = new Set();

  // 3-level tag for every topic@<slug> property that has a value.
  for (const key of Object.keys(fm)) {
    if (!key.startsWith('topic@')) continue;
    const catSlug = key.slice('topic@'.length);
    for (const val of asArray(fm[key])) {
      if (val == null || String(val).trim() === '') continue;
      tags.add(`category/${catSlug}/${slug(linkName(val))}`);
      withTopic.add(catSlug);
    }
  }
  // 2-level tag for a category that has no topic value of its own.
  for (const cat of asArray(fm.categories)) {
    if (cat == null || String(cat).trim() === '') continue;
    const catSlug = slug(linkName(cat));
    if (!withTopic.has(catSlug)) tags.add(`category/${catSlug}`);
  }
  return tags;
}

const sameSet = (a, b) => a.size === b.size && [...a].every((x) => b.has(x));

class CategoryTagSync extends obsidian.Plugin {
  async onload() {
    this.busy = new Set();
    // metadataCache "changed" fires after Obsidian re-parses a file (on save / after a
    // typing pause), so fm here is the committed, parsed frontmatter.
    this.registerEvent(this.app.metadataCache.on('changed', (file) => { this.sync(file); }));
    // One-shot pass over already-open files on load; the rest sync as they change.
    this.app.workspace.onLayoutReady(() => {
      const f = this.app.workspace.getActiveFile();
      if (f) this.sync(f);
    });
    this.addCommand({
      id: 'sync-active',
      name: 'Sync category tags in the active note',
      callback: () => { const f = this.app.workspace.getActiveFile(); if (f) this.sync(f, true); },
    });
  }

  async sync(file, force = false) {
    if (!(file instanceof obsidian.TFile) || file.extension !== 'md') return;
    if (file.path.startsWith(TEMPLATES)) return;
    if (this.busy.has(file.path)) return;

    const cache = this.app.metadataCache.getFileCache(file);
    const fm = cache && cache.frontmatter;
    if (!fm) return;

    const hasCats = fm.categories != null;
    const hasTopic = Object.keys(fm).some((k) => k.startsWith('topic@'));
    if (!hasCats && !hasTopic && !force) return;

    const desired = desiredCategoryTags(fm);
    const current = new Set(asArray(fm.tags).filter((t) => String(t).startsWith('category/')));
    if (sameSet(desired, current)) return; // loop guard + no-churn

    // Keep every non-category tag in place; append the category tags, sorted (stable).
    const keep = asArray(fm.tags).filter((t) => !String(t).startsWith('category/'));
    const next = [...keep, ...[...desired].sort()];

    this.busy.add(file.path);
    try {
      await this.app.fileManager.processFrontMatter(file, (f) => {
        if (next.length) f.tags = next;
        else delete f.tags;
      });
    } catch (e) {
      console.error('[Category Tag Sync]', file.path, e);
    } finally {
      // Release after the resulting change event has been delivered.
      setTimeout(() => this.busy.delete(file.path), 150);
    }
  }
}

CategoryTagSync.desiredCategoryTags = desiredCategoryTags; // test hook
module.exports = CategoryTagSync;
