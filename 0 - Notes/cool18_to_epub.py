#!/usr/bin/env python3
"""
cool18_to_epub.py — scrape, translate, and bundle Chinese forum novels into EPUBs.

Translation backend: Google Translate unofficial endpoint
(translate.googleapis.com, client=gtx). Free but unofficial — paced
conservatively with adaptive jitter and VPN-switch detection.

Two ways to invoke:

  # Discovery mode: hand it ONE index URL and it finds all linked chapter threads
  python cool18_to_epub.py https://www.cool18.com/.../threadview&tid=13963653 -o book.epub

  # File mode: a text file with one URL per line (# comments allowed)
  python cool18_to_epub.py urls.txt -o book.epub

Pipeline:
  1. Resolve input to a list of thread URLs. If a single URL is given, the
     index page is scraped for sibling chapter threads (cool18 lists
     newest-first, so we reverse to chronological).
  2. Fetch each thread (decoded as GB18030 — these pages are not UTF-8).
  3. Extract the main post body and strip forum chrome / TOC link rows.
  4. Split the Chinese source on chapter markers (第X章 / 第X回 / 第X节 /
     numeric).
  5. Translate each chapter via Google Translate (unofficial endpoint),
     chunked, paced with jitter and adaptive backoff. If rate-limited,
     polls public IP every 30s — switch VPN to resume automatically.
  6. Emit a single EPUB.

Caches under ./.cache/  (delete to force refetch / retranslate).

Tip when rate-limited:
  - The script logs cooldown time remaining every ~30s.
  - Switch your VPN exit node — the script polls public IP and will resume
    automatically when it detects the change.
  - Or press Enter in the terminal to force-retry immediately.

Dependencies:
  pip install requests beautifulsoup4 lxml EbookLib
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import logging
import os
import random
import re
import select
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse

import requests
from bs4 import BeautifulSoup
from ebooklib import epub

# ---------------------------------------------------------------------------
# Config

CACHE_DIR = Path(".cache")
HTML_CACHE = CACHE_DIR / "html"
TR_CACHE = CACHE_DIR / "tr"
HTTP_TIMEOUT = 30
HTTP_RETRIES = 3
HTTP_BACKOFF = 2.0
FETCH_DELAY_SEC = 1.5            # politeness pause between fresh fetches

# Default UA for fetching cool18 (translation block has its own rotating UA).
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    level=logging.INFO,
)
log = logging.getLogger("cool18")

# ---------------------------------------------------------------------------
# Chinese number parsing

CN_DIGITS = {
    "零": 0, "〇": 0, "○": 0,
    "一": 1, "二": 2, "两": 2, "三": 3, "四": 4,
    "五": 5, "六": 6, "七": 7, "八": 8, "九": 9,
    "0": 0, "1": 1, "2": 2, "3": 3, "4": 4,
    "5": 5, "6": 6, "7": 7, "8": 8, "9": 9,
}
CN_UNITS = {"十": 10, "百": 100, "千": 1000, "万": 10000}


def cn_to_int(s: str) -> int | None:
    """Convert a Chinese-numeral or Arabic-numeral string to int. None on failure."""
    s = s.strip()
    if not s:
        return None
    if all(c.isdigit() or c in "0123456789" for c in s):
        try:
            normalized = "".join(str(CN_DIGITS[c]) if c in CN_DIGITS else c for c in s)
            return int(normalized)
        except ValueError:
            return None
    total = 0
    section = 0
    current = 0
    for ch in s:
        if ch in CN_DIGITS:
            current = CN_DIGITS[ch]
        elif ch in CN_UNITS:
            unit = CN_UNITS[ch]
            if unit == 10000:
                section = (section + current) * unit
                total += section
                section = 0
            else:
                if current == 0:
                    current = 1
                section += current * unit
            current = 0
        else:
            return None
    return total + section + current


# ---------------------------------------------------------------------------
# URL utilities

def normalize_url(url: str) -> str:
    """Canonicalize for dedup: force https, sort query params, drop fragments."""
    parsed = urlparse(url)
    scheme = "https"
    netloc = parsed.netloc
    qs = parse_qs(parsed.query, keep_blank_values=True)
    flat = sorted((k, v[0] if v else "") for k, v in qs.items())
    new_q = urlencode(flat)
    return urlunparse((scheme, netloc, parsed.path, "", new_q, ""))


def _sha1(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# HTTP fetch with disk cache

_last_fresh_fetch_at = 0.0


def fetch(url: str) -> str:
    """Fetch URL, return decoded HTML. Caches to disk."""
    global _last_fresh_fetch_at
    HTML_CACHE.mkdir(parents=True, exist_ok=True)
    cache_path = HTML_CACHE / f"{_sha1(normalize_url(url))}.html"
    if cache_path.exists():
        log.info("cached HTML  %s", url)
        return cache_path.read_text(encoding="utf-8", errors="replace")

    elapsed = time.monotonic() - _last_fresh_fetch_at
    if elapsed < FETCH_DELAY_SEC:
        time.sleep(FETCH_DELAY_SEC - elapsed)

    headers = {"User-Agent": USER_AGENT, "Accept-Language": "zh-CN,zh;q=0.9"}
    last_err: Exception | None = None
    for attempt in range(1, HTTP_RETRIES + 1):
        try:
            log.info("GET (attempt %d) %s", attempt, url)
            r = requests.get(url, headers=headers, timeout=HTTP_TIMEOUT)
            r.raise_for_status()
            raw = r.content
            # Resolve the encoding intelligently. GB18030 is a near-universal
            # superset — it almost never raises UnicodeDecodeError, even on
            # UTF-8 bytes, which means a naive "try gb18030 first" silently
            # produces mojibake on UTF-8 pages. So:
            #   1. Honor a Content-Type charset header if present.
            #   2. Honor a <meta charset> in the response body if present.
            #   3. Otherwise default to gb18030 (cool18's actual encoding),
            #      then gbk, then utf-8 as final fallbacks.
            declared = None
            ct = r.headers.get("Content-Type", "")
            mct = re.search(r"charset=([\w-]+)", ct, re.I)
            if mct:
                declared = mct.group(1)
            else:
                head_chunk = raw[:2048].decode("ascii", errors="replace")
                mmeta = re.search(
                    r'<meta\s+[^>]*charset=["\']?([\w-]+)',
                    head_chunk, re.I,
                )
                if mmeta:
                    declared = mmeta.group(1)
            encs: list[str] = []
            if declared:
                encs.append(declared)
            for fallback in ("gb18030", "gbk", "utf-8"):
                if fallback not in (e.lower() for e in encs):
                    encs.append(fallback)
            text = None
            for enc in encs:
                try:
                    text = raw.decode(enc)
                    break
                except (UnicodeDecodeError, LookupError, TypeError):
                    continue
            if text is None:
                text = raw.decode("utf-8", errors="replace")
            cache_path.write_text(text, encoding="utf-8")
            _last_fresh_fetch_at = time.monotonic()
            return text
        except Exception as e:  # noqa: BLE001
            last_err = e
            log.warning("fetch failed: %s", e)
            time.sleep(HTTP_BACKOFF * attempt)
    raise RuntimeError(f"failed to fetch {url}: {last_err}")


# ---------------------------------------------------------------------------
# Index-page discovery

BRACKET_TITLE_RE = re.compile(r"【\s*([^】\s][^】]{0,40}?)\s*】")
THREADVIEW_RE = re.compile(r"act=threadview", re.I)
TID_RE = re.compile(r"[?&]tid=(\d+)")


def discover_chapter_links(
    html: str, base_url: str
) -> tuple[str, list[tuple[str, str]]]:
    """Return (novel_title, [(url, anchor_text), ...]) for sibling chapter threads."""
    soup = BeautifulSoup(html, "lxml")

    title_text = (soup.title.string if soup.title else "") or ""
    h1 = soup.find(["h1", "h2"])
    if h1:
        title_text = h1.get_text(" ", strip=True) + " " + title_text
    m = BRACKET_TITLE_RE.search(title_text)
    novel_title = m.group(1).strip() if m else ""
    if not novel_title:
        return "", []

    novel_pattern = re.compile(rf"【\s*{re.escape(novel_title)}\s*】", re.UNICODE)

    found: list[tuple[str, str]] = []
    seen: set[str] = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if not THREADVIEW_RE.search(href):
            continue
        text = a.get_text(" ", strip=True)
        if not novel_pattern.search(text):
            continue
        full = urljoin(base_url, href)
        canon = normalize_url(full)
        if canon in seen:
            continue
        # Note: we intentionally include the user's own base_url here. The
        # discovery soup lists sibling threads in newest-first DOM order;
        # reversing that downstream gives chronological order. If we drop
        # base_url from the list, the caller has to re-insert it and ends
        # up corrupting source_index ordering.
        seen.add(canon)
        found.append((canon, text))

    return novel_title, found


# ---------------------------------------------------------------------------
# Body extraction

_JUNK_REGEXES = [
    re.compile(r"^\s*(?:回复|引用|转载|转贴|楼主|沙发|板凳|地板|来自|本帖|举报|签名)\b"),
    re.compile(r"^\s*\[\s*(?:本帖|楼主)"),
    re.compile(r"^\s*(?:---+|\*\*\*+|=+)\s*$"),
    re.compile(r"cool18\.com", re.I),
    re.compile(r"^\s*https?://\S+\s*$"),
    re.compile(r"送交者"),
    re.compile(r"已读\s*\d+\s*次"),
    re.compile(r"^\s*于\s+\d{4}[-/]"),
    re.compile(r"^\s*(?:大字阅读|小字阅读|繁体|简体|大字|小字|下载)\s*$"),
    re.compile(r"\[[☆★◆◇■□]"),
    re.compile(r"^\s*作者[:]"),
    re.compile(r"^\s*\d{4}[-/]\d{1,2}[-/]\d{1,2}\s*发表"),
    re.compile(r"^\s*\d{4}[-/]\d{1,2}[-/]\d{1,2}\s+\d+:\d+"),
    re.compile(r"^\s*\d+\s*赞\s*$"),
    re.compile(r"^\s*[\d\uFF10-\uFF19]{1,3}\s*[\-\u2014\uFF0D]\s*[\d\uFF10-\uFF19]{1,3}\s*$"),
    re.compile(r"^\s*(?:返回禁忌书屋首页|版主管理|所有跟帖|回复本帖|前期主贴)\s*$"),
    # Cool18 page chrome that often appears below the post body when the
    # CSS selectors don't fully isolate the post container. Stripping these
    # before chapter detection prevents them from being translated into
    # English and showing up as footer junk in the EPUB.
    re.compile(r"如果你喜欢"),                        # "If you like ..."
    re.compile(r"请点击这里(?:去)?投票"),             # "Please click here to vote"
    re.compile(r"您认为此帖.*?(?:AI|人工智能|生成)"),  # AI-detection prompt
    re.compile(r"本帖内容由网友"),                     # disclaimer
    re.compile(r"^\s*(?:广告服务|联系我们|关于我们|网站地图|版权声明)\s*$"),
    re.compile(r"上一个?用户(?:帖|主题)"),
    re.compile(r"下一个?用户(?:帖|主题)"),
    re.compile(r"^\s*扫(?:一扫|码|描)?分享\s*$"),
    re.compile(r"^\s*回(?:主帖|主题|帖)\s*$"),
    re.compile(r"楼主自删"),
    re.compile(r"本月楼主热帖"),
    re.compile(r"楼主保留删除"),
    re.compile(r"违反(?:规定|本站规则|相关法律)"),
    re.compile(r"^\s*▲返回顶部\s*$"),
    re.compile(r"未成年人|奸兽|奸亲|乱伦内容"),       # report-link text
    re.compile(r">>>\s*查看更多"),                     # "view more from this poster"
    # Translated leftovers from prior runs (already in English) — strip
    # these too so re-runs after the fix don't leave stale junk in the cache.
    re.compile(r"^\s*\[?(?:Previous|Next) User Post\]?\s*$", re.I),
    re.compile(r"^\s*\[?Scan to Share\]?\s*$", re.I),
    re.compile(r"^\s*\[?Return to Main Post\]?\s*$", re.I),
    re.compile(r"^\s*\[?(?:Advertising Services?|Contact us?|About us?)\]?\s*$", re.I),
    re.compile(r"If you like this post"),
    re.compile(r"please click here to vote", re.I),
    re.compile(r"Please mark whether"),
]


def _is_junk_line(line: str) -> bool:
    return any(p.search(line) for p in _JUNK_REGEXES)


# A line that looks like a TOC entry from an index page: 【novel-title】 short tail.
# The negative lookahead is important — without it, this also matches legitimate
# chapter headings inside individual thread bodies that happen to be wrapped in
# 【 ... 】 brackets (cool18's older format does this: "【第三十六章】 倾城宫主"),
# and stripping them would leave the body with no detectable chapter markers.
TOC_LINK_RE = re.compile(
    r"^\s*【"
    r"(?!\s*第\s*[一二三四五六七八九十百千万零〇○\d０-９]+\s*[章回节卷篇])"
    r"[^】]+】[^。!?\n]{0,80}\s*$"
)


def extract_body(html: str, *, strip_toc_links: bool = True) -> tuple[str, str]:
    """Return (thread_title, cleaned_body_text)."""
    soup = BeautifulSoup(html, "lxml")

    page_title = (soup.title.string or "").strip() if soup.title else ""
    page_title = re.sub(r"\s*-\s*cool18.*$", "", page_title, flags=re.I).strip()
    page_title = re.sub(r"\s*-\s*禁忌书屋.*$", "", page_title).strip()

    for tag in soup(["script", "style", "noscript", "iframe", "form", "input",
                     "button", "select", "textarea", "nav", "header", "footer"]):
        tag.decompose()

    candidates: list = []
    for sel in [
        "div.show_content", "td.show_content",
        "div#read_tpc", "td#read_tpc",
        ".tpc_content", ".message",
    ]:
        candidates.extend(soup.select(sel))

    if not candidates:
        best, best_score = None, 0
        for el in soup.find_all(["td", "div"]):
            txt = el.get_text("\n", strip=True)
            cjk = sum(1 for c in txt if "\u4e00" <= c <= "\u9fff")
            if cjk > best_score and not el.find(["table"]):
                best, best_score = el, cjk
        if best is not None:
            candidates = [best]

    if not candidates:
        return page_title, ""

    best_el = max(candidates, key=lambda e: len(e.get_text(strip=True)))
    text = best_el.get_text("\n", strip=True)

    cleaned: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if _is_junk_line(line):
            continue
        if strip_toc_links and TOC_LINK_RE.match(line):
            continue
        cleaned.append(line)
    return page_title, "\n".join(cleaned)


# ---------------------------------------------------------------------------
# Chapter detection / splitting

STRICT_CHAPTER_RE = re.compile(
    r"""
    (?P<full>
        第\s*
        (?P<num>[一二三四五六七八九十百千万零〇○\d0123456789]+)
        \s*
        (?P<unit>[章回节卷篇])
        # Real chapter markers are followed by ONE of:
        #   1. End-of-line / end-of-string
        #   2. Whitespace or punctuation (typical "第X章 标题")
        #   3. A short (≤4 chars) Chinese title then newline, BUT only
        #      when the unit char is 章 (formal "chapter"). The colloquial
        #      回 (literally "time/round") is used heavily INLINE in
        #      narrative — "第一回来金玉阁" = "the first time [he] came to
        #      the Jade Pavilion" — so we do NOT allow squashed format
        #      with 回; it must have an explicit boundary character.
        (?=
            $
            | [\s\u3000、。．!?！？:：·,，\-－—()（）【】「」『』]
            | (?<=章)[\u4e00-\u9fff]{1,4}(?:\r?\n|$)
        )
        (?P<rest>[^\n]{0,80})
    )
    """,
    re.VERBOSE | re.MULTILINE,
)

# Standalone volume markers used in older extras: 上篇 / 中篇 / 下篇 / 前篇 / 后篇
# These never appear with the 第 prefix; they're chapter markers in their own
# right when they show up alone on a line. We use them as a fallback after
# STRICT and LOOSE detection both produce nothing.
VOLUME_TRIPLET_RE = re.compile(
    r"^\s*(上篇|中篇|下篇|前篇|后篇)\s*$",
    re.MULTILINE,
)

LOOSE_CHAPTER_RE = re.compile(
    r"^\s*[((]?\s*(?P<num>[一二三四五六七八九十百千零〇○\d0123456789]{1,6})\s*[))]?\s*$",
    re.MULTILINE,
)

UNIT_PRIORITY = {"节": 0, "章": 1, "回": 2, "卷": 3, "篇": 4, "": 99}
SECTION_PRIORITY = {"main": 0, "side": 1}


# Patterns for lines that frequently appear at the START of a chapter body
# in cool18 posts but aren't actually part of the chapter content. The body
# of a chapter often begins with: a repeat of the thread title, an author
# byline, a "PS:" note from the poster, a "first published at..." line, and
# sometimes a duplicate of the chapter heading written without the 第 prefix.
# We strip these greedily until we hit something that looks like real prose.
_PREAMBLE_PATTERNS = [
    re.compile(r"^\s*$"),                                       # blank line
    re.compile(r"^\s*P\.?\s*S\.?\s*[：:]", re.I),               # PS：群已更新...
    re.compile(r"^\s*作者\s*[：:]"),                            # 作者：xxx
    re.compile(r"^\s*首发(?:时间|地址)?[：:、 ]*"),             # 首发时间...
    re.compile(r"^\s*【[^】]+】(?:[\s\u3000]*[^\n]{0,40})?\s*$"),  # 【...】 lines
    # 标题党 / 转载 / 摘录 etc. annotation lines
    re.compile(r"^\s*(?:转载|摘录|引用|本章字数|来源)\s*[：:]"),
]


def _strip_chapter_preamble(text: str, chapter_num: int | None) -> str:
    """Strip leading junk lines from a chapter body. Removes thread-title
    repeats, author bylines, PS notes, and duplicate chapter headings (e.g.
    '三十一章 篝火狂欢' that follows the actual matched 第三十一章 heading)."""
    if not text:
        return text
    lines = text.splitlines()
    # Don't strip more than the first ~12 lines — beyond that we'd risk
    # eating real prose
    LIMIT = 12
    while lines and LIMIT > 0:
        line = lines[0]
        stripped = line.strip()
        if not stripped:
            lines.pop(0)
            LIMIT -= 1
            continue

        if any(p.match(line) for p in _PREAMBLE_PATTERNS):
            lines.pop(0)
            LIMIT -= 1
            continue

        # Duplicate heading without 第 prefix, e.g. "三十一章 篝火狂欢" right
        # after we already matched 第三十一章 on the title line.
        m_dup = re.match(
            r"^\s*[【\(（]?\s*"
            r"([一二三四五六七八九十百千万零〇○\d０-９]+)"
            r"\s*[章回节卷篇]"
            r"[】\)）]?[\s\u3000]*[^\n]{0,40}\s*$",
            line,
        )
        if m_dup and chapter_num is not None:
            n_dup = cn_to_int(m_dup.group(1))
            if n_dup == chapter_num:
                lines.pop(0)
                LIMIT -= 1
                continue

        break    # first real-looking line — stop stripping
    return "\n".join(lines).strip()


@dataclass
class Chapter:
    number: float
    unit: str
    title_zh: str
    body_zh: str
    source_url: str = ""
    source_index: int = 0
    title_en: str = ""
    body_en: str = ""
    # Classification (set from page title; defaults match a generic main chapter)
    section: str = "main"        # "main" or "side"
    arc_zh: str = ""             # raw Chinese arc name, e.g. "玄女篇" or "" for main
    arc_en: str = ""             # filled in during translation pass
    sub_label_zh: str = ""       # raw sub-position from title, e.g. "1-2" or "上篇"
    # Where this chapter starts in the original body text. Used by process()
    # to decide whether a chapter falls before or after an in-body 番外
    # separator, which lets us classify each chapter individually when a
    # single thread mixes main-story prose and side-story extras.
    body_offset: int = 0

    def sort_key(self) -> tuple[int, int, float, int, int]:
        # Section first (main < side); within section, numbered chapters
        # (tier 0) sort before unnumbered (tier 1). Numbered chapters sort
        # by chapter number — chronological regardless of which URL the
        # user provided as their entry point. Unnumbered chapters fall back
        # to source_index. The trailing source_index breaks ties between
        # chapters that claim the same number (rare; dedup handles
        # real collisions), and UNIT_PRIORITY breaks remaining ties when a
        # thread mixes 节 and 章 within the same chapter range.
        numbered = self.number > 0
        return (
            SECTION_PRIORITY[self.section],
            0 if numbered else 1,
            self.number if numbered else float(self.source_index),
            self.source_index,
            UNIT_PRIORITY.get(self.unit, 99),
        )


# ---------------------------------------------------------------------------
# Page-title classification: figures out whether a thread is a side story
# (番外), what arc it belongs to (玄女篇 / 西大陆篇 / 上中下篇 / etc), and what
# its position is. Used both to tag chapters and to recover a chapter number
# when the body has no in-text 第X章 markers.

SIDE_MARKER_RE = re.compile(r"番外")

# An in-body separator line that signals a transition from main story to
# side stories. Cool18 posters who pack a final chapter + extras into the
# same thread typically write one of these on its own line BEFORE the
# extras content. We detect this so we can split the thread into a "main"
# half and a "side" half — otherwise the page-title classification would
# wrongly mark the entire thread (including the real chapter) as side.
SIDE_BODY_SEPARATOR_RE = re.compile(
    r"^[\s\u3000]*[（(【「『]?\s*"
    r"(?:番外|外传|特别篇|后记|尾声|附录)"
    r"\s*[）)】」』]?[\s\u3000]*$",
    re.MULTILINE
)


def _find_side_marker_in_body(body: str) -> int:
    """Return the position of the first 番外/外传/etc separator line in
    body, or -1 if none. We require the marker to be on its own line so
    inline narrative use of these terms doesn't trigger the split."""
    m = SIDE_BODY_SEPARATOR_RE.search(body)
    return m.start() if m else -1

# Volume-style triplet (上/中/下篇) — treat as one logical "Volumes" arc, not
# three different arcs called 上篇 / 中篇 / 下篇.
VOLUME_PARTS = {"上篇": 1, "中篇": 2, "下篇": 3, "前篇": 1, "后篇": 2}
ARC_RE = re.compile(r"([^\s（()【】　]{1,12}篇)")
PAREN_RANGE_RE = re.compile(
    r"[（(]\s*([一二三四五六七八九十百千零〇○\d０-９]+)"
    r"\s*[\-－—~〜～]?"
    r"\s*[一二三四五六七八九十百千零〇○\d０-９]*\s*[）)]"
)
INLINE_CHAPTER_RE = re.compile(
    r"第\s*([一二三四五六七八九十百千万零〇○\d０-９]+)\s*"
    r"[\-－—~〜～]?\s*[一二三四五六七八九十百千万零〇○\d０-９]*\s*"
    r"[章回节卷]"
)


def classify_thread_title(page_title: str, novel_title: str) -> dict:
    """Inspect the cool18 page <title> / H1 for clues about this thread's
    place in the work. Returns:
      {
        'section':       'main' | 'side',
        'arc_zh':        '' or e.g. '玄女篇',  '_VOLUMES_' for the 上中下 set,
                                              '_NUMBERED_EXTRAS_' for 番外 第X章,
        'sub_label_zh':  short label from the title for display
        'sub_index':     numeric ordering hint (float) — chapter or part number
      }
    """
    rest = page_title or ""
    if novel_title:
        rest = re.sub(rf"^.*?【\s*{re.escape(novel_title)}\s*】\s*",
                      "", rest, count=1)
    rest = rest.strip()

    section = "side" if SIDE_MARKER_RE.search(rest) else "main"
    if section == "side":
        rest = re.sub(r"^番外\s*", "", rest).strip()

    arc_zh = ""
    sub_label_zh = rest
    sub_index = 0.0

    # 1. Volume-style first (上/中/下篇 trump arc detection)
    for vol, idx in VOLUME_PARTS.items():
        if vol in rest:
            arc_zh = "_VOLUMES_"
            sub_label_zh = vol
            sub_index = float(idx)
            break

    # 2. Otherwise an arc name like 玄女篇 or 西大陆篇
    if not arc_zh:
        m = ARC_RE.search(rest)
        if m:
            arc_zh = m.group(1)
            tail = rest[m.end():].strip()
            sub_label_zh = tail or arc_zh

    # 3. Numeric position from a (1-2) / (3) range, or from 第X章
    m_range = PAREN_RANGE_RE.search(rest)
    if m_range:
        n = cn_to_int(m_range.group(1))
        if n is not None:
            sub_index = float(n)
    if sub_index == 0.0:
        m_chap = INLINE_CHAPTER_RE.search(rest)
        if m_chap:
            n = cn_to_int(m_chap.group(1))
            if n is not None:
                sub_index = float(n)
                if section == "side" and not arc_zh:
                    arc_zh = "_NUMBERED_EXTRAS_"

    # 4. Side stories with no detectable structure → bucket as miscellaneous
    if section == "side" and not arc_zh:
        arc_zh = "_MISC_EXTRAS_"

    return {
        "section": section,
        "arc_zh": arc_zh,
        "sub_label_zh": sub_label_zh,
        "sub_index": sub_index,
    }


# Map internal arc keys to displayed (English) labels. Real Chinese arc names
# get translated by the translation pipeline; the synthetic "_X_" keys map
# to fixed labels because they don't correspond to real Chinese phrases.
SYNTHETIC_ARC_LABELS = {
    "_VOLUMES_": "Side Volumes",
    "_NUMBERED_EXTRAS_": "Numbered Extras",
    "_MISC_EXTRAS_": "Extras",
}


def _drop_match_outliers(matches):
    """Drop chapter matches whose numbers don't cluster with the others in
    the same body. Cool18 threads typically contain a small range of
    consecutive chapters (e.g. 36-40); a lone match for chapter 2 alongside
    chapters 36-40 is almost certainly a 第N回 / 第N章 reference inline in
    the narrative, not a real chapter marker. We split numbers into clusters
    by gap-size and keep only the largest cluster.

    Conservative: only fires when there are ≥3 matches AND the gap between
    clusters exceeds GAP_THRESHOLD."""
    if len(matches) < 3:
        return matches
    pairs = []
    for m in matches:
        n = cn_to_int(m.group("num"))
        if n is not None:
            pairs.append((m, n))
    if len(pairs) < 3:
        return matches

    sorted_pairs = sorted(pairs, key=lambda p: p[1])
    GAP_THRESHOLD = 10
    clusters: list[list] = [[sorted_pairs[0]]]
    for prev, cur in zip(sorted_pairs, sorted_pairs[1:]):
        if cur[1] - prev[1] > GAP_THRESHOLD:
            clusters.append([cur])
        else:
            clusters[-1].append(cur)

    if len(clusters) == 1:
        return matches

    # On ties of cluster size, prefer the higher-numbered cluster — for
    # cool18 threads, the higher cluster is more likely to be the real
    # chapters and the lower cluster is more likely an inline 第N回 / 第N章
    # narrative reference (e.g. "the first time he visited").
    largest = max(clusters, key=lambda c: (len(c), c[-1][1]))
    if len(largest) == len(pairs):
        return matches
    keep_ids = {id(m) for m, _ in largest}
    dropped = [(m, n) for m, n in pairs if id(m) not in keep_ids]
    if dropped:
        log.warning(
            "split_chapters: dropped %d outlier match(es) — %s; "
            "kept cluster around chapters %d-%d",
            len(dropped),
            ", ".join(f"第{m.group('num')}{m.group('unit')}(n={n})"
                      for m, n in dropped),
            largest[0][1], largest[-1][1],
        )
    return [m for m in matches if id(m) in keep_ids
            or cn_to_int(m.group("num")) is None]


def split_chapters(body: str, source_url: str, source_index: int) -> list[Chapter]:
    # First try strict 第X章 markers (now boundary-anchored, so inline 第N回XX
    # narrative use no longer false-matches).
    matches = list(STRICT_CHAPTER_RE.finditer(body))
    matches = _drop_match_outliers(matches)
    if matches:
        return _split_by_matches(body, matches, source_url, source_index,
                                 strict=True)

    # Fallback to standalone numeric lines like "(1)" / "1." — but reject
    # cool18-style repost markers where the number is followed by an author
    # signature on the same line, e.g. "(31)【作者：喵喵大人】". Those are
    # NOT chapter splits, they're "this is part 31 of the same chapter".
    loose_raw = [m for m in LOOSE_CHAPTER_RE.finditer(body)
                 if cn_to_int(m.group("num")) is not None]
    loose: list = []
    for m in loose_raw:
        line_start = body.rfind("\n", 0, m.start()) + 1
        line_end = body.find("\n", m.end())
        if line_end == -1:
            line_end = len(body)
        # Look at the next line too: cool18 often puts "(31)" then "[Author:..]"
        # on the next line.
        ctx_end = body.find("\n", line_end + 1)
        if ctx_end == -1:
            ctx_end = len(body)
        ctx = body[line_start:ctx_end]
        if "【作者" in ctx or "作者：" in ctx or "作者:" in ctx:
            continue   # repost/section marker, not a real chapter
        loose.append(m)
    if len(loose) >= 2:
        return _split_by_matches(body, loose, source_url, source_index,
                                 strict=False)

    # Final fallback: 上篇/中篇/下篇 standalone markers (used in older extras).
    triplet = list(VOLUME_TRIPLET_RE.finditer(body))
    if len(triplet) >= 2:
        return _split_by_matches(body, triplet, source_url, source_index,
                                 strict=False, is_triplet=True)

    # No detectable structure → one bare chapter; process() may repair it
    # using the page title via classify_thread_title.
    return [Chapter(
        number=0.0, unit="", title_zh="",
        body_zh=_strip_chapter_preamble(body.strip(), None),
        source_url=source_url, source_index=source_index,
    )]


# Volume-triplet ordering: 前/上 → 1, 中 → 2, 下/后 → 3.
_TRIPLET_ORDER = {"前篇": 1, "上篇": 1, "中篇": 2, "下篇": 3, "后篇": 3}

# Hard cap on chapter title length. Real Chinese chapter titles are short;
# anything past this on the heading line is body text that the regex's
# `(?P<rest>[^\n]{0,80})` accidentally pulled in.
_MAX_TITLE_LEN = 30


def _split_by_matches(body, matches, source_url, source_index, *,
                     strict, is_triplet=False):
    chapters: list[Chapter] = []
    first_start = matches[0].start()
    preamble = body[:first_start].strip()
    cjk = sum(1 for c in preamble if "\u4e00" <= c <= "\u9fff")
    # Substantial Chinese text BEFORE the first chapter heading in a thread
    # gets merged into the first chapter's body rather than becoming a
    # separate "Front Matter N" item. This text is typically a recap, a
    # scene-setting paragraph, or narrative that the original poster put
    # before adding the 第X章 label — content that belongs with the chapter
    # the user is about to read, not a standalone TOC entry.
    preamble_to_prepend = ""
    if preamble and len(preamble) > 200 and cjk > 100:
        # Run the preamble through the same junk-stripper used on chapter
        # body starts so PS notes, author bylines, "first published at..."
        # lines and other forum chrome in the pre-chapter text don't get
        # carried into the chapter body when we prepend. Whatever survives
        # the stripper is real content — merge it.
        cleaned = _strip_chapter_preamble(preamble, None)
        if cleaned.strip():
            preamble_to_prepend = cleaned + "\n\n"
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        chunk = body[start:end].strip()
        head, _, rest = chunk.partition("\n")
        head = head.strip()

        # If the heading line is suspiciously long, the regex's optional
        # trailing-text capture sucked in narrative text. Trim back to the
        # chapter prefix, and push the rest into the body.
        if not is_triplet:
            unit_marker = m.group("unit") if strict else ""
            if unit_marker:
                # "第X章 真正的标题  body text continues..." — keep through
                # the title; body continues.
                anchor = head.find(unit_marker)
                if anchor != -1:
                    head_after_unit = head[anchor + 1:]
                    # Allow up to ~_MAX_TITLE_LEN chars of title after the unit
                    if len(head_after_unit) > _MAX_TITLE_LEN:
                        # Truncate at a sensible boundary if any
                        cutoff = _MAX_TITLE_LEN
                        for boundary in ("。", "！", "？", "，"):
                            idx = head_after_unit.find(boundary, 0, _MAX_TITLE_LEN)
                            if 0 < idx < cutoff:
                                cutoff = idx
                        rescued = head_after_unit[cutoff:].strip()
                        head = head[:anchor + 1 + cutoff].strip()
                        if rescued:
                            rest = rescued + ("\n" + rest if rest else "")

        if is_triplet:
            label = m.group(1)   # 上篇 / 中篇 / 下篇
            n_val: float = float(_TRIPLET_ORDER.get(label, i + 1))
            unit = ""
            head = label
            # The whole chunk EXCEPT the label line is body
            body_text = chunk[len(label):].lstrip("\n").strip()
            chapter_num_for_strip: int | None = None
        else:
            n = cn_to_int(m.group("num"))
            n_val = float(n if n is not None else i + 1)
            unit = m.group("unit") if strict else ""
            body_text = rest.strip() or head
            chapter_num_for_strip = n

        # Cool18 wraps headings as 【第N章】 title — the regex match begins
        # at 第 (inside the bracket pair), so a stray 】 sticks to the front
        # of head_after_unit. Strip leading bracket-close chars from head.
        head = re.sub(r"^(.*?[章回节卷篇])[】\)）」』]+\s*", r"\1 ", head).strip()

        # Body sometimes ends with a stray 【 — the start of the next chapter's
        # 【第N章】 heading is just outside our chunk slice. Trim trailing
        # bracket-open chars and whitespace.
        body_text = re.sub(r"[【「『\s]+$", "", body_text)

        # Strip PS:/byline/duplicate-heading junk from the start of the body.
        body_text = _strip_chapter_preamble(body_text, chapter_num_for_strip)

        # On the first chapter, prepend any held preamble text so it reads
        # as part of this chapter instead of becoming a separate item.
        if i == 0 and preamble_to_prepend:
            body_text = preamble_to_prepend + body_text

        chapters.append(Chapter(
            number=n_val,
            unit=unit,
            title_zh=head,
            body_zh=body_text,
            source_url=source_url,
            source_index=source_index,
            body_offset=int(m.start()),
        ))
    return chapters
# ---------------------------------------------------------------------------
# Translation: Google Translate unofficial endpoint (translate.googleapis.com)
#
# This endpoint isn't meant for programmatic use, so we behave conservatively:
#   - Slow baseline pace with random jitter (looks less bot-like)
#   - Adaptive pacing: speed up after sustained clean responses, slow down on
#     near-misses
#   - Long backoff schedule on 405/429/503/sorry-redirects
#   - During cooldown, poll public IP every 30s — if it changed (you flipped
#     VPN), reset strikes and resume immediately
#   - Press Enter during a cooldown to force-retry early (e.g. right after you
#     manually switched VPN exit)
#   - User-Agent rotates whenever the public IP changes

# Pacing — conservative defaults for the unofficial endpoint.
# Chunk size: 1800 characters. The unofficial endpoint silently truncates
# long requests, especially for CJK input where each character URL-encodes
# to ~9 bytes. Empirically 1800 chars of Chinese is the largest chunk that
# reliably round-trips fully translated; larger chunks come back with the
# tail half left as raw Chinese, producing the "every-other-paragraph in
# Chinese" symptom in the EPUB. _translate_with_verification below also
# detects this case and re-splits.
TR_CHUNK_CHARS = 1800
TR_PAUSE_MIN_SEC = 3.0
TR_PAUSE_MAX_SEC = 6.0

# Adaptive pacing
ADAPTIVE_SPEEDUP_AFTER = 20      # consecutive clean calls before nudging faster
ADAPTIVE_FLOOR_SEC = 2.0
ADAPTIVE_CEILING_SEC = 12.0

# Backoff schedule on hard rate limits (405/429/503/sorry).
# Realistic for the unofficial endpoint: blocks can genuinely last 24h.
# First few strikes try fast in case it's a transient hiccup, then back off
# into block-duration territory. Caps at the last value (24h).
GOOGLE_BACKOFF_SCHEDULE = [
    60,      # 1m   — transient hiccup
    300,     # 5m
    900,     # 15m
    1800,    # 30m
    3600,    # 1h
    7200,    # 2h
    21600,   # 6h
    86400,   # 24h  — assume IP is benched for the day
]

# Stop the run after this many consecutive strikes (~ a full day of escalating
# waits). User can re-run; cache preserves progress chunk-by-chunk.
MAX_GOOGLE_STRIKES = 8

# IP probe — how often to check public IP during cooldown.
IP_PROBE_INTERVAL_SEC = 30
IP_PROBE_URLS = [
    "https://api.ipify.org",
    "https://ifconfig.me/ip",
    "https://icanhazip.com",
]

# Realistic recent desktop UAs. We pick a fresh one each time the public IP
# changes so a VPN flip doesn't carry forward a UA that may already be flagged.
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]


class _RateLimited(Exception):
    """Raised on 405 / 429 / 503 / sorry-redirect.
    Caller pauses through cooldown then retries (possibly on a new IP)."""


class _NetworkError(Exception):
    """Raised on DNS failure, connection refused, or timeout — i.e. we
    never reached Google. Distinct from _RateLimited because it's not a
    block and should not advance the strike counter or long-backoff schedule.
    Often a transient VPN issue: DNS not ready yet, route flapping, etc."""


class _PermanentlyBlocked(Exception):
    """Raised after MAX_GOOGLE_STRIKES consecutive cooldowns with no
    recovery — give up cleanly so the caller can write a partial EPUB."""


# ---- Mutable state -------------------------------------------------------

_current_pause_sec: float = (TR_PAUSE_MIN_SEC + TR_PAUSE_MAX_SEC) / 2
_clean_streak: int = 0

_google_cooldown_until: float = 0.0
_google_strikes: int = 0

_current_ip: str | None = None
_current_user_agent: str = random.choice(USER_AGENTS)


def _probe_public_ip() -> str | None:
    """Return current public IP, or None on failure."""
    for url in IP_PROBE_URLS:
        try:
            r = requests.get(url, timeout=8)
            if r.ok:
                ip = r.text.strip()
                # Cheap sanity check
                if ip and len(ip) <= 45 and all(
                    c.isdigit() or c in ".:abcdefABCDEF" for c in ip
                ):
                    return ip
        except requests.RequestException:
            continue
    return None


def _refresh_identity_if_ip_changed() -> bool:
    """Probe IP. If changed since last probe, rotate UA. Returns True if changed."""
    global _current_ip, _current_user_agent
    ip = _probe_public_ip()
    if ip is None:
        return False
    if ip != _current_ip:
        old = _current_ip
        _current_ip = ip
        _current_user_agent = random.choice(USER_AGENTS)
        if old is None:
            log.info("public IP detected: %s", ip)
        else:
            log.info("public IP changed: %s -> %s (rotated User-Agent)", old, ip)
        return True
    return False


def _stdin_has_input(timeout: float) -> bool:
    """True if stdin has a line ready within timeout. POSIX-only; on Windows
    or when stdin isn't a TTY we just sleep the timeout."""
    if not sys.stdin or not sys.stdin.isatty() or sys.platform == "win32":
        time.sleep(timeout)
        return False
    try:
        ready, _, _ = select.select([sys.stdin], [], [], timeout)
        if ready:
            sys.stdin.readline()    # consume the line so it doesn't echo later
            return True
        return False
    except (OSError, ValueError):
        time.sleep(timeout)
        return False


def _wait_through_cooldown(deadline: float, what: str) -> str:
    """Wait until monotonic >= deadline. Every IP_PROBE_INTERVAL_SEC, check
    if public IP changed (VPN switch). Return early if so, or if user presses
    Enter.

    Returns one of: 'expired' | 'ip_changed' | 'user_skipped'
    """
    log.info("%s — press Enter to force-retry "
             "(useful right after switching VPN)", what)
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return "expired"
        eta = time.strftime("%H:%M:%S", time.localtime(time.time() + remaining))
        log.info("  cooldown: %s remaining (resume ~%s, current IP: %s)",
                 _format_duration(remaining), eta, _current_ip or "?")
        slept = min(remaining, IP_PROBE_INTERVAL_SEC)
        if _stdin_has_input(slept):
            log.info("  user pressed Enter — retrying now")
            _refresh_identity_if_ip_changed()    # log new IP if any
            return "user_skipped"
        if _refresh_identity_if_ip_changed():
            log.info("  VPN switch detected — retrying now")
            return "ip_changed"


def _format_duration(seconds: float) -> str:
    s = int(seconds)
    if s < 60:
        return f"{s}s"
    if s < 3600:
        return f"{s // 60}m{s % 60:02d}s"
    if s < 86400:
        return f"{s // 3600}h{(s % 3600) // 60:02d}m"
    return f"{s // 86400}d{(s % 86400) // 3600:02d}h"


def _trigger_google_cooldown(reason: str) -> int:
    global _google_cooldown_until, _google_strikes
    if _google_strikes >= MAX_GOOGLE_STRIKES:
        total = sum(GOOGLE_BACKOFF_SCHEDULE)
        raise _PermanentlyBlocked(
            f"Google has rate-limited this IP for {_google_strikes} consecutive "
            f"strikes (~{_format_duration(total)} total of waiting). Giving up "
            f"so we can write a partial EPUB. Switch VPN and re-run, or wait "
            f"out the day — the translation cache preserves all progress."
        )
    wait = GOOGLE_BACKOFF_SCHEDULE[
        min(_google_strikes, len(GOOGLE_BACKOFF_SCHEDULE) - 1)
    ]
    _google_strikes += 1
    _google_cooldown_until = time.monotonic() + wait
    log.warning("Google rate-limited (%s) — strike %d/%d, cooldown %s",
                reason, _google_strikes, MAX_GOOGLE_STRIKES,
                _format_duration(wait))
    return wait


def _reset_google_backoff(reason: str = "") -> None:
    global _google_strikes, _google_cooldown_until
    if _google_strikes:
        log.info("Google responding cleanly%s — strike counter reset",
                 f" ({reason})" if reason else "")
    _google_strikes = 0
    _google_cooldown_until = 0.0


def _adaptive_record_success() -> None:
    """Successful translation: nudge pace down after a clean streak."""
    global _clean_streak, _current_pause_sec
    _clean_streak += 1
    if _clean_streak >= ADAPTIVE_SPEEDUP_AFTER and _current_pause_sec > ADAPTIVE_FLOOR_SEC:
        new = max(ADAPTIVE_FLOOR_SEC, _current_pause_sec - 0.5)
        if new != _current_pause_sec:
            log.info("adaptive pace: speeding up %.1fs -> %.1fs after %d clean calls",
                     _current_pause_sec, new, _clean_streak)
            _current_pause_sec = new
        _clean_streak = 0


def _adaptive_record_warning() -> None:
    """Empty result or transient hiccup (not a hard block): slow down."""
    global _clean_streak, _current_pause_sec
    _clean_streak = 0
    new = min(ADAPTIVE_CEILING_SEC, _current_pause_sec + 1.5)
    if new != _current_pause_sec:
        log.info("adaptive pace: slowing down %.1fs -> %.1fs",
                 _current_pause_sec, new)
        _current_pause_sec = new


# ---------------------------------------------------------------------------
# Google Cloud Translation API v3 backend (paid, official)
#
# Auth via service account JSON. The path comes from --credentials, the
# GOOGLE_APPLICATION_CREDENTIALS env var, or a default fallback. The project
# ID is read from the JSON itself (the `project_id` field), no need to
# specify it separately.
#
# Pricing (as of 2026): $20 per 1M characters of source text after the first
# 500K free per month per project.
#
# We also implement a hard cooldown: every CHARS_PER_COOLDOWN consecutive
# characters translated triggers a sleep of COOLDOWN_AFTER_CHARS_SECS seconds.
# Useful for pacing long runs and giving a regular checkpoint where the user
# can monitor progress / stop the job.

GCV3_BACKEND_NAME = "gcv3"
GCV3_DEFAULT_CHUNK_CHARS = 8000     # well under v3's 30K codepoint limit
GCV3_DEFAULT_REQUEST_TIMEOUT = 60
GCV3_DEFAULT_COOLDOWN_EVERY_CHARS = 500_000
GCV3_DEFAULT_COOLDOWN_SECS = 60
GCV3_SCOPE = "https://www.googleapis.com/auth/cloud-translation"

# A reasonable default search path for the credentials file. Falls through if
# nothing exists; user must then pass --credentials or set the env var.
GCV3_DEFAULT_CREDENTIAL_PATHS = [
    "/credentials/gcp.json",
    "/credentials/google-translate.json",
    str(Path.home() / ".config/gcloud/application_default_credentials.json"),
]

# --- Mutable state -------------------------------------------------------
_gcv3_credentials = None
_gcv3_project_id: str | None = None
_gcv3_chars_since_cooldown: int = 0
_gcv3_chars_total: int = 0
# Configurable at runtime
gcv3_cooldown_every_chars: int = GCV3_DEFAULT_COOLDOWN_EVERY_CHARS
gcv3_cooldown_secs: int = GCV3_DEFAULT_COOLDOWN_SECS


# ---------------------------------------------------------------------------
# DeepSeek backend (deepseek-chat = V3). OpenAI-compatible HTTP API. Strong
# Chinese-to-English novel translation at roughly 1/20th GPT/Claude pricing
# and no aggressive rate limits — best cost/quality tradeoff for this script.
#
# A 200K-character novel translates for roughly US$0.15-0.25 in tokens.
# Set DEEPSEEK_API_KEY in env (preferred) or pass --deepseek-key.

DEEPSEEK_BACKEND_NAME = "deepseek"
DEEPSEEK_DEFAULT_ENDPOINT = "https://api.deepseek.com/chat/completions"
DEEPSEEK_DEFAULT_MODEL = "deepseek-chat"        # V3; "deepseek-reasoner" = R1
DEEPSEEK_DEFAULT_CHUNK_CHARS = 6000             # comfortable inside 64K context
DEEPSEEK_DEFAULT_TIMEOUT = 120
DEEPSEEK_DEFAULT_TEMPERATURE = 0.2              # low for translation consistency
DEEPSEEK_MAX_RETRIES = 6

# Display names so the system prompt reads naturally — DeepSeek understands
# ISO codes but a real language name gives more reliable output.
_LANG_NAMES = {
    "zh": "Chinese", "en": "English", "fr": "French", "de": "German",
    "es": "Spanish", "it": "Italian", "pt": "Portuguese", "ru": "Russian",
    "ja": "Japanese", "ko": "Korean", "vi": "Vietnamese",
    "th": "Thai", "id": "Indonesian", "ar": "Arabic", "nl": "Dutch",
    "pl": "Polish", "tr": "Turkish",
}

# --- Mutable state -------------------------------------------------------
_deepseek_api_key: str | None = None
deepseek_model: str = DEEPSEEK_DEFAULT_MODEL


def _deepseek_load_key(explicit: str | None = None) -> str:
    """Resolve the DeepSeek API key from --deepseek-key, then DEEPSEEK_API_KEY
    env var. Aborts if neither is set when the backend is selected."""
    global _deepseek_api_key
    if _deepseek_api_key:
        return _deepseek_api_key
    key = explicit or os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if not key:
        raise SystemExit(
            "backend deepseek requires an API key. Either:\n"
            "  export DEEPSEEK_API_KEY=sk-...   (preferred — env var)\n"
            "  --deepseek-key sk-...            (command-line, visible in `ps`)"
        )
    _deepseek_api_key = key
    return key


def _gcv3_load_credentials(explicit_path: str | None = None):
    """Load Google service-account credentials. Caches across calls.
    Returns (credentials_object, project_id)."""
    global _gcv3_credentials, _gcv3_project_id
    if _gcv3_credentials is not None and _gcv3_project_id is not None:
        return _gcv3_credentials, _gcv3_project_id

    try:
        from google.oauth2 import service_account
        from google.auth.transport.requests import Request as _AuthRequest  # noqa: F401
    except ImportError as e:
        raise SystemExit(
            f"backend gcv3 requires the 'google-auth' package: pip install google-auth\n"
            f"(import error: {e})"
        )

    # Resolution order: explicit CLI > env var > default search paths.
    candidates: list[str] = []
    if explicit_path:
        candidates.append(explicit_path)
    env_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")
    if env_path:
        candidates.append(env_path)
    candidates.extend(GCV3_DEFAULT_CREDENTIAL_PATHS)

    chosen: str | None = None
    for p in candidates:
        if p and Path(p).is_file():
            chosen = p
            break
    if chosen is None:
        raise SystemExit(
            "gcv3 backend: no credentials file found.\n"
            "  Pass --credentials PATH, set GOOGLE_APPLICATION_CREDENTIALS, "
            "or place the JSON at one of:\n    " +
            "\n    ".join(GCV3_DEFAULT_CREDENTIAL_PATHS)
        )

    log.info("gcv3: loading credentials from %s", chosen)
    creds = service_account.Credentials.from_service_account_file(
        chosen, scopes=[GCV3_SCOPE]
    )

    # Extract project_id directly from the JSON (the SDK exposes it as an
    # attribute, but reading the raw JSON makes the source explicit and
    # works even if the SDK API changes).
    try:
        with open(chosen, encoding="utf-8") as f:
            blob = json.load(f)
        project_id = blob.get("project_id") or getattr(creds, "project_id", None)
    except (OSError, json.JSONDecodeError) as e:
        raise SystemExit(f"gcv3: cannot read credentials JSON: {e}")
    if not project_id:
        raise SystemExit(
            "gcv3: credentials JSON has no 'project_id' field. "
            "Is this really a service-account key?"
        )

    _gcv3_credentials = creds
    _gcv3_project_id = project_id
    log.info("gcv3: project_id=%s, scopes=%s", project_id, GCV3_SCOPE)
    return creds, project_id


def _gcv3_token() -> str:
    """Return a valid bearer token, refreshing if expired."""
    creds, _ = _gcv3_load_credentials()
    if not creds.valid:
        from google.auth.transport.requests import Request as _AuthRequest
        creds.refresh(_AuthRequest())
    return creds.token


def _gcv3_maybe_cooldown(chars_consumed: int) -> None:
    """Sleep gcv3_cooldown_secs whenever we've translated
    gcv3_cooldown_every_chars characters since the last cooldown."""
    global _gcv3_chars_since_cooldown, _gcv3_chars_total
    _gcv3_chars_since_cooldown += chars_consumed
    _gcv3_chars_total += chars_consumed
    if _gcv3_chars_since_cooldown >= gcv3_cooldown_every_chars:
        log.info("gcv3: %d chars translated since last cooldown "
                 "(%d total this run) — sleeping %d sec",
                 _gcv3_chars_since_cooldown, _gcv3_chars_total,
                 gcv3_cooldown_secs)
        time.sleep(gcv3_cooldown_secs)
        _gcv3_chars_since_cooldown = 0


def _translate_gcv3(text: str, target: str, source: str = "zh-CN") -> str:
    """Call Cloud Translation v3 via REST. Retries transient errors with
    exponential backoff. Hard-fails on auth / billing / quota errors."""
    creds, project_id = _gcv3_load_credentials()

    url = (f"https://translation.googleapis.com/v3/projects/{project_id}"
           f"/locations/global:translateText")
    payload: dict = {
        "contents": [text],
        "targetLanguageCode": target,
        "mimeType": "text/plain",
    }
    if source and source != "auto":
        payload["sourceLanguageCode"] = source

    backoff = 5
    for attempt in range(1, 7):
        token = _gcv3_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
            "x-goog-user-project": project_id,
        }
        try:
            r = requests.post(url, headers=headers, json=payload,
                              timeout=GCV3_DEFAULT_REQUEST_TIMEOUT)
        except (requests.ConnectionError, requests.Timeout) as e:
            log.warning("gcv3: network error (%s) — retry %d in %ds",
                        type(e).__name__, attempt, backoff)
            time.sleep(backoff); backoff = min(backoff * 2, 120)
            continue

        # Auth / billing / quota — hard-fail with the GCP error body
        if r.status_code in (400, 401, 403):
            try:
                err = r.json().get("error", {})
                msg = err.get("message", "")
                status = err.get("status", "")
            except ValueError:
                msg, status = r.text[:300], ""
            # 403 with rateLimitExceeded reason → backoff
            if r.status_code == 403 and ("rateLimit" in msg or "Quota" in msg):
                log.warning("gcv3: rate limited (%s) — retry %d in %ds",
                            msg[:100], attempt, backoff)
                time.sleep(backoff); backoff = min(backoff * 2, 300)
                continue
            raise SystemExit(
                f"gcv3 fatal error ({r.status_code} {status}): {msg}\n"
                f"This usually means the service account lacks the "
                f"'Cloud Translation API User' role, the API isn't enabled "
                f"on the project, or billing isn't set up."
            )

        # Transient: retry
        if r.status_code in (429, 500, 502, 503, 504):
            log.warning("gcv3: HTTP %d — retry %d in %ds",
                        r.status_code, attempt, backoff)
            time.sleep(backoff); backoff = min(backoff * 2, 300)
            continue

        r.raise_for_status()
        data = r.json()
        translations = data.get("translations") or []
        if not translations:
            return ""
        return translations[0].get("translatedText", "")

    raise RuntimeError("gcv3: too many retries, giving up on this chunk")


_CJK_RANGE_RE = re.compile(r"[\u3400-\u9fff]")


def _cjk_ratio(text: str) -> float:
    """Fraction of characters in `text` that are CJK ideographs. Used to
    detect translation 'leaks' — chunks where gcv3 returned the source
    text largely untranslated (rare, but happens on certain stylized
    passages, names, or when the API silently truncates)."""
    if not text:
        return 0.0
    cjk = len(_CJK_RANGE_RE.findall(text))
    return cjk / max(1, len(text))


def _translate_gcv3_with_cooldown(text: str, target: str, source: str,
                                  _depth: int = 0) -> str:
    """Translate `text` via Cloud Translation v3. Triggers the periodic
    cooldown after each successful call. If the output retains more than
    a small fraction of CJK characters (a sign the API didn't translate
    something), split the chunk in half and retry recursively, up to
    `_MAX_DEPTH` levels deep."""
    _MAX_DEPTH = 4
    _CJK_LEAK_THRESHOLD = 0.05    # >5% Chinese chars in supposedly-English output
    _MIN_SPLIT_LEN = 200

    out = _translate_gcv3(text, target, source)
    _gcv3_maybe_cooldown(len(text))

    # If the result still looks like Chinese (the API silently returned
    # untranslated source for some part of the chunk), bisect and retry.
    # Only applies when translating INTO a non-CJK target (en, fr, etc.).
    if (target and not target.startswith(("zh", "ja", "ko"))
            and _cjk_ratio(out) > _CJK_LEAK_THRESHOLD
            and len(text) > _MIN_SPLIT_LEN
            and _depth < _MAX_DEPTH):
        log.warning("gcv3: CJK-leak detected (%.1f%% chinese in output) — "
                    "splitting chunk (depth %d, len %d) and retrying",
                    _cjk_ratio(out) * 100, _depth, len(text))
        # Split at a sentence/paragraph boundary near the midpoint
        mid = len(text) // 2
        split_chars = "\n。！？；"
        for offset in range(0, mid // 2):
            for delta in (offset, -offset):
                pos = mid + delta
                if 0 < pos < len(text) and text[pos] in split_chars:
                    mid = pos + 1
                    break
            else:
                continue
            break
        a = _translate_gcv3_with_cooldown(text[:mid], target, source,
                                          _depth + 1)
        b = _translate_gcv3_with_cooldown(text[mid:], target, source,
                                          _depth + 1)
        return (a + "\n" + b).strip()

    return out


def _translate_deepseek(text: str, target: str, source: str = "zh-CN") -> str:
    """Single-chunk translation via DeepSeek's chat-completions API.
    Retries 429/5xx with exponential backoff; 4xx auth/format errors fail
    fast. On retry exhaustion, raises _PermanentlyBlocked so the caller
    falls back to writing a partial EPUB."""
    if _deepseek_api_key is None:
        _deepseek_load_key()
    src_name = _LANG_NAMES.get(source.split("-")[0].lower(), source)
    tgt_name = _LANG_NAMES.get(target.split("-")[0].lower(), target)
    system_prompt = (
        f"You are translating {src_name} web fiction to {tgt_name}. "
        "Output only the translation — no commentary, no notes, no headers. "
        "Preserve paragraph breaks and the narrative tone of the source. "
        "Render dialogue in natural conversational style. "
        "Translate character and place names consistently throughout."
    )
    payload = {
        "model": deepseek_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ],
        "temperature": DEEPSEEK_DEFAULT_TEMPERATURE,
        "stream": False,
    }
    headers = {
        "Authorization": f"Bearer {_deepseek_api_key}",
        "Content-Type": "application/json",
    }
    last_err: str = ""
    for attempt in range(1, DEEPSEEK_MAX_RETRIES + 1):
        try:
            r = requests.post(
                DEEPSEEK_DEFAULT_ENDPOINT, json=payload, headers=headers,
                timeout=DEEPSEEK_DEFAULT_TIMEOUT,
            )
        except requests.RequestException as e:
            wait = min(60, 2 ** attempt)
            log.warning("deepseek network error %s — retry %d/%d in %ds",
                        e, attempt, DEEPSEEK_MAX_RETRIES, wait)
            time.sleep(wait)
            last_err = str(e)
            continue

        if r.status_code == 200:
            try:
                content = r.json()["choices"][0]["message"]["content"]
            except (KeyError, IndexError, ValueError) as e:
                raise RuntimeError(
                    f"deepseek returned malformed response: {e}: {r.text[:300]}"
                )
            content = content.strip()
            if not content:
                # Rare but seen — model returned empty completion. Retry once
                # before giving up.
                wait = 2 ** attempt
                log.warning("deepseek returned empty content — retry %d/%d in %ds",
                            attempt, DEEPSEEK_MAX_RETRIES, wait)
                time.sleep(wait)
                last_err = "empty content"
                continue
            return content

        if r.status_code in (401, 403):
            # Authentication/authorization failure — no point retrying.
            raise SystemExit(
                f"deepseek auth failed ({r.status_code}). Check DEEPSEEK_API_KEY "
                f"is valid and your account has credit. Body: {r.text[:200]}"
            )
        if r.status_code == 429 or r.status_code >= 500:
            wait = min(60, 2 ** attempt + random.uniform(0, 1))
            log.warning("deepseek HTTP %d — retry %d/%d in %.1fs",
                        r.status_code, attempt, DEEPSEEK_MAX_RETRIES, wait)
            time.sleep(wait)
            last_err = f"HTTP {r.status_code}"
            continue
        # Other 4xx — bad request shape, no benefit to retry
        raise RuntimeError(f"deepseek HTTP {r.status_code}: {r.text[:300]}")

    raise _PermanentlyBlocked(
        f"deepseek failed after {DEEPSEEK_MAX_RETRIES} retries "
        f"(last error: {last_err}). Re-run later — translation cache "
        f"preserves any chapters that did complete."
    )


# Backend selection — set by main() based on --backend, default is unofficial
TRANSLATION_BACKEND: str = "unofficial"


def _translate_google_direct(text: str, target: str, source: str = "auto") -> str:
    """Call Google Translate's public unofficial endpoint via POST.

    Treats 405/429/503, /sorry redirects, and network resets as rate-limit
    signals (raised as _RateLimited)."""
    url = "https://translate.googleapis.com/translate_a/single"
    params = {"client": "gtx", "sl": source, "tl": target, "dt": "t"}
    headers = {
        "User-Agent": _current_user_agent,
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Content-Type": "application/x-www-form-urlencoded;charset=utf-8",
    }
    body = urlencode({"q": text}).encode("utf-8")
    try:
        r = requests.post(url, params=params, data=body, headers=headers,
                          timeout=45, allow_redirects=False)
    except (requests.ConnectionError, requests.Timeout) as e:
        # Distinguish "Google said no" from "we couldn't reach Google at all".
        # DNS failures, connection refused, and timeouts are network problems,
        # not rate-limiting. Common causes: VPN DNS not ready, captive portal,
        # IPv6 weirdness. Don't burn strikes on these.
        msg = str(e).lower()
        is_dns = any(k in msg for k in [
            "nameresolutionerror", "name or service not known",
            "nodename nor servname", "failed to resolve",
            "temporary failure in name resolution",
            "name resolution",
        ])
        is_unreachable = any(k in msg for k in [
            "network is unreachable", "no route to host",
            "connection refused",
        ])
        if is_dns or is_unreachable or isinstance(e, requests.Timeout):
            raise _NetworkError(f"{type(e).__name__}: {str(e)[:200]}") from e
        # Other connection errors (resets, broken pipe mid-response) are more
        # plausibly rate-limit signals (Google shutting us off).
        raise _RateLimited(f"network: {type(e).__name__}: {str(e)[:200]}") from e

    if r.status_code in (405, 429, 503):
        raise _RateLimited(f"HTTP {r.status_code}")
    if 300 <= r.status_code < 400:
        location = r.headers.get("Location", "")
        if "sorry" in location or "captcha" in location.lower():
            raise _RateLimited(f"abuse-check redirect: {location[:120]}")

    r.raise_for_status()
    data = r.json()
    if not data or not isinstance(data, list) or not data[0]:
        return ""
    return "".join(seg[0] for seg in data[0]
                   if isinstance(seg, list) and seg and seg[0])


def _translate_chunk_patient(chunk: str, target: str, source: str) -> str:
    """Translate a single chunk via the unofficial endpoint. Retries through
    rate limits indefinitely, with VPN-switch awareness. Network errors
    (DNS, unreachable, timeout) get short local retries and don't burn strikes."""
    network_retry_count = 0
    while True:
        if _google_cooldown_until > time.monotonic():
            outcome = _wait_through_cooldown(
                _google_cooldown_until, "Google on cooldown"
            )
            if outcome in ("ip_changed", "user_skipped"):
                # Fresh IP (or user says they have one) — reset strikes so
                # the next hit starts the schedule from the top.
                _reset_google_backoff(reason=outcome)

        try:
            result = _translate_google_direct(chunk, target, source)
            if result.strip():
                _reset_google_backoff()
                _adaptive_record_success()
                return result
            log.warning("google returned empty result; brief retry in 10s")
            _adaptive_record_warning()
            time.sleep(10)
        except _NetworkError as e:
            network_retry_count += 1
            # Short backoff that doesn't touch the strike counter. After a few
            # quick retries, slow down to give a flapping VPN time to settle.
            wait = 15 if network_retry_count < 5 else 60
            log.warning("network error (not a rate-limit) — %s. "
                        "Retry %d in %ds. Check VPN/DNS if this persists.",
                        e, network_retry_count, wait)
            # Re-probe IP so we'll notice if the user reconnects to a different
            # exit during this wait.
            time.sleep(wait)
            _refresh_identity_if_ip_changed()
        except _RateLimited as e:
            network_retry_count = 0
            _trigger_google_cooldown(str(e))
        except Exception as e:  # noqa: BLE001
            log.warning("google call failed: %s: %s — retrying in 30s",
                        type(e).__name__, e)
            time.sleep(30)


def _has_translation_leak(translated: str, target: str) -> bool:
    """Detect when Google silently echoed back source text instead of
    translating it. Symptom: the output of a non-CJK target language still
    contains substantial CJK. > 3% CJK characters in a translation to
    en/it/etc. is a near-certain partial-translation."""
    if target.startswith(("zh", "ja", "ko")):
        return False
    return _cjk_ratio(translated) > 0.03


def _split_at_boundary(chunk: str, mid: int) -> int:
    """Return an index near `mid` that falls on a paragraph or sentence
    boundary. Used to re-split a chunk that came back partially translated."""
    n = len(chunk)
    if n <= 1:
        return n
    boundaries = "\n。！？!?\u3002"
    for delta in range(min(mid, n - mid)):
        for cand in (mid + delta, mid - delta):
            if 0 < cand < n and chunk[cand - 1] in boundaries:
                return cand
    return mid    # no boundary found; split anywhere


def _translate_with_verification(
    chunk: str, target: str, source: str, depth: int = 0
) -> str:
    """Translate a chunk; if the output looks partial (still has CJK when
    target is non-CJK), recursively split and retry. Bottoms out at depth 4
    (chunks ≤ ~110 chars), at which point the result is returned as-is —
    sometimes Google really cannot translate a fragment and we'd loop
    forever otherwise."""
    result = _translate_chunk_patient(chunk, target, source)
    if depth >= 4 or len(chunk) < 120:
        return result
    if not _has_translation_leak(result, target):
        return result

    log.warning("translation leak detected (%.0f%% CJK in output, depth=%d) "
                "— re-splitting %d-char chunk",
                _cjk_ratio(result) * 100, depth, len(chunk))
    mid = _split_at_boundary(chunk, len(chunk) // 2)
    if mid <= 0 or mid >= len(chunk):
        return result    # can't usefully re-split
    a = _translate_with_verification(chunk[:mid], target, source, depth + 1)
    b = _translate_with_verification(chunk[mid:], target, source, depth + 1)
    glue = "\n" if (chunk[mid - 1:mid] == "\n" or chunk[mid:mid + 1] == "\n") else " "
    return (a.rstrip() + glue + b.lstrip()).strip()


def translate(text: str, target: str = "en", source: str = "zh-CN") -> str:
    if not text.strip():
        return ""

    TR_CACHE.mkdir(parents=True, exist_ok=True)
    # Cache key includes backend so unofficial-cached translations don't
    # masquerade as v3 results (or vice versa).
    key = _sha1(f"{TRANSLATION_BACKEND}|{source}|{target}|{text}")
    cache_path = TR_CACHE / f"{key}.txt"
    if cache_path.exists():
        return cache_path.read_text(encoding="utf-8")

    if TRANSLATION_BACKEND == GCV3_BACKEND_NAME:
        # GCv3: large chunks (well under the 30K codepoint limit), no jitter,
        # no VPN logic. Just call the API and let the cooldown wrapper pace
        # things at every gcv3_cooldown_every_chars characters.
        out_parts: list[str] = []
        for chunk in _chunks(text, GCV3_DEFAULT_CHUNK_CHARS):
            out_parts.append(
                _translate_gcv3_with_cooldown(chunk, target, source)
            )
        out = "\n\n".join(p.strip() for p in out_parts if p)
        cache_path.write_text(out, encoding="utf-8")
        return out

    if TRANSLATION_BACKEND == DEEPSEEK_BACKEND_NAME:
        # DeepSeek: large chunks, no rate-limit gymnastics, no CJK-leak
        # detection (the model translates the whole input or returns 4xx;
        # it doesn't silently echo source like Google does).
        out_parts = []
        for chunk in _chunks(text, DEEPSEEK_DEFAULT_CHUNK_CHARS):
            out_parts.append(_translate_deepseek(chunk, target, source))
        out = "\n\n".join(p.strip() for p in out_parts if p)
        cache_path.write_text(out, encoding="utf-8")
        return out

    # Unofficial backend: small chunks, jittered pacing, VPN-switch awareness,
    # CJK-leak detection.
    if _current_ip is None:
        _refresh_identity_if_ip_changed()

    out_parts = []
    for chunk in _chunks(text, TR_CHUNK_CHARS):
        out_parts.append(_translate_with_verification(chunk, target, source))
        jitter_low = max(ADAPTIVE_FLOOR_SEC, _current_pause_sec - 1.0)
        jitter_high = _current_pause_sec + 1.5
        time.sleep(random.uniform(jitter_low, jitter_high))
    out = "\n\n".join(p.strip() for p in out_parts if p)
    cache_path.write_text(out, encoding="utf-8")
    return out


def _chunks(text: str, max_chars: int) -> Iterable[str]:
    paragraphs = text.split("\n")
    buf = ""
    for p in paragraphs:
        if len(buf) + len(p) + 1 <= max_chars:
            buf = f"{buf}\n{p}" if buf else p
            continue
        if buf:
            yield buf
            buf = ""
        if len(p) > max_chars:
            for sentence in re.findall(r".{1,%d}(?:[。!?\.]|$)" % max_chars, p, re.S):
                if not sentence.strip():
                    continue
                if len(buf) + len(sentence) <= max_chars:
                    buf += sentence
                else:
                    if buf:
                        yield buf
                    buf = sentence
        else:
            buf = p
    if buf:
        yield buf


# ---------------------------------------------------------------------------
# EPUB build

def build_epub(
    chapters: list[Chapter],
    out_path: Path,
    book_title: str,
    author: str = "Unknown",
    language: str = "en",
) -> None:
    book = epub.EpubBook()
    book.set_identifier(_sha1(book_title + str(time.time()))[:16])
    book.set_title(book_title)
    book.set_language(language)
    book.add_author(author)

    css = epub.EpubItem(
        uid="style_default",
        file_name="style/default.css",
        media_type="text/css",
        content=(
            "body { font-family: Georgia, serif; line-height: 1.6; padding: 0 1em; }\n"
            "h1 { text-align: center; margin-top: 2em; }\n"
            "h2 { color: #333; border-bottom: 1px solid #ccc; }\n"
            "p  { text-indent: 1.2em; margin: 0.5em 0; }\n"
            ".source { color: #888; font-size: 0.8em; text-align: right; }\n"
            ".divider { text-align: center; padding: 4em 1em 3em; }\n"
            ".divider h1 { font-size: 1.8em; letter-spacing: 0.05em; "
            "border-top: 2px solid #999; border-bottom: 2px solid #999; "
            "padding: 0.6em 0; margin: 0; }\n"
            ".divider .sub { color: #666; font-style: italic; "
            "margin-top: 1em; font-size: 0.95em; }\n"
        ),
    )
    book.add_item(css)

    def _make_html_item(uid_idx: int, file_name: str, title: str, html_body: str):
        item = epub.EpubHtml(
            title=title, file_name=file_name, lang=language,
            content=(
                "<html><head>"
                "<link rel='stylesheet' href='style/default.css'/>"
                f"</head><body>{html_body}</body></html>"
            ),
        )
        item.add_item(css)
        book.add_item(item)
        return item

    def _make_divider(seq: int, big: str, small: str = ""):
        body_html = (
            f'<div class="divider"><h1>{html.escape(big)}</h1>'
            + (f'<p class="sub">{html.escape(small)}</p>' if small else "")
            + "</div>"
        )
        return _make_html_item(seq, f"sec_{seq:04d}.xhtml", big, body_html)

    epub_chapters: list = []
    side_counter = 0
    file_seq = 0
    last_section: str | None = None
    last_arc: str | None = None
    # Within _MISC_EXTRAS_ (uncategorized side stories from threads with no
    # shared arc identifier), we sub-group by source_url so a "West Continent
    # gaiden" thread following a "Xuanwu side note" thread doesn't continue
    # the same numbering sequence. Each misc thread gets its own sub-divider.
    last_misc_source: str | None = None

    for ch in chapters:
        # Section divider — emitted once when entering the side-story block.
        if ch.section != last_section:
            if ch.section == "side":
                file_seq += 1
                epub_chapters.append(
                    _make_divider(file_seq, "✦  Side Stories  ✦",
                                  "Extras and bonus chapters")
                )
            last_arc = None    # force arc-divider on first side-story arc
            last_misc_source = None

        # Arc divider — emitted when arc_zh changes (named arcs like 玄女篇,
        # plus synthetic _VOLUMES_ / _NUMBERED_EXTRAS_ / _MISC_EXTRAS_).
        # Side-story counter resets to 1 inside the new arc so each arc has
        # its own "Side Story 1, 2, 3..." sequence rather than continuing
        # the previous arc's numbering.
        emitted_arc_divider = False
        if ch.section == "side" and ch.arc_zh and ch.arc_zh != last_arc:
            arc_label = (ch.arc_en.strip()
                         or SYNTHETIC_ARC_LABELS.get(ch.arc_zh, "")
                         or ch.arc_zh)
            file_seq += 1
            epub_chapters.append(
                _make_divider(file_seq, f"— {arc_label} —", "")
            )
            last_arc = ch.arc_zh
            side_counter = 0
            emitted_arc_divider = True
            # If we just entered _MISC_EXTRAS_, mark this thread's source as
            # the currently-active one so the misc sub-divider below doesn't
            # immediately re-emit for the same chapter.
            if ch.arc_zh == "_MISC_EXTRAS_":
                last_misc_source = ch.source_url

        # Misc sub-divider — within _MISC_EXTRAS_, each new source thread
        # gets its own sub-section header. These threads have no shared arc
        # identifier; a source_url transition is our only signal that the
        # chapters belong to a distinct (and likely differently-named)
        # extra. The sub-divider label is the chapter's translated title
        # so the reader can see what they're entering.
        if (not emitted_arc_divider
                and ch.section == "side"
                and ch.arc_zh == "_MISC_EXTRAS_"
                and ch.source_url != last_misc_source):
            sub_label = (ch.title_en.strip() or ch.title_zh.strip()
                         or "Misc Extra")
            if len(sub_label) > 60:
                sub_label = sub_label[:57].rstrip() + "..."
            file_seq += 1
            epub_chapters.append(
                _make_divider(file_seq, f"· {sub_label} ·", "")
            )
            last_misc_source = ch.source_url
            side_counter = 0

        last_section = ch.section

        # Build the chapter title.
        # Google often translates "第三十二章 剑姬震怒" as
        # "Chapter 32: Sword Maiden's Rage" — already prefixed. Strip any
        # leading "Chapter N", "Section N", "Volume N" so we don't end up
        # with "Chapter 32: Chapter 32: ..." duplicates.
        clean_en = re.sub(
            r"^\s*(?:chapter|section|volume|episode|part)\s*\d+\s*[:.\-—–]?\s*",
            "", ch.title_en.strip(), flags=re.I
        ).strip()

        if ch.section == "side":
            side_counter += 1
            base = clean_en or ch.title_zh.strip() or "(untitled)"
            arc = ch.arc_en.strip()
            if arc and arc.lower() not in base.lower():
                title = f"Side Story {side_counter}: {arc} — {base}"
            else:
                title = f"Side Story {side_counter}: {base}"
        else:
            # process() guarantees every main chapter has a positive integer
            # number (explicit from extraction, or assigned by promote-all).
            title = f"Chapter {int(ch.number)}"
            if clean_en:
                title = f"{title}: {clean_en}"

        paragraphs = [p.strip() for p in ch.body_en.split("\n") if p.strip()]
        body_html = "\n".join(f"<p>{html.escape(p)}</p>" for p in paragraphs)
        content = (
            f"<h1>{html.escape(title)}</h1>\n{body_html}\n"
            f'<p class="source">Source: {html.escape(ch.source_url)}</p>\n'
        )
        file_seq += 1
        epub_chapters.append(
            _make_html_item(file_seq, f"chap_{file_seq:04d}.xhtml", title, content)
        )

    book.toc = tuple(epub_chapters)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ["nav", *epub_chapters]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    epub.write_epub(str(out_path), book)
    log.info("wrote %s (%d chapters)", out_path, len(epub_chapters))


# ---------------------------------------------------------------------------
# Input resolution and main flow

def resolve_input(
    arg: str, *, no_discover: bool, max_chapters: int | None
) -> tuple[list[str], str]:
    """Return (urls, suggested_book_title)."""
    if re.match(r"^https?://", arg, re.I):
        url = normalize_url(arg)
        if no_discover:
            return [url], ""
        log.info("discovery: scanning index page for sibling chapter links ...")
        html = fetch(url)
        novel_title, links = discover_chapter_links(html, url)
        if not links:
            log.warning("no sibling links discovered; using URL alone")
            return [url], novel_title
        log.info("discovered %d sibling thread link(s) for 【%s】",
                 len(links), novel_title)
        ordered = [u for u, _ in reversed(links)]   # newest-first → chronological
        # Use the discovered chronological order as-is. The user's URL is
        # almost always one of the discovered links; if not (the forum
        # didn't render a clickable self-reference), append it at the end
        # so it's still processed. Per-chapter number-based sorting will
        # then slot every chapter into the right place, even if the user's
        # URL is appended in the "wrong" position here.
        urls = list(ordered)
        if url not in urls:
            urls.append(url)
        if max_chapters:
            urls = urls[:max_chapters]
        return urls, novel_title

    path = Path(arg)
    if not path.exists():
        raise SystemExit(f"input is neither a URL nor an existing file: {arg}")
    urls = [
        normalize_url(line.strip())
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    return urls, ""


# Per-chapter classification constants shared by the in-thread classifier.
_STRICT_UNITS = ("章", "回", "节", "卷", "篇")
_TRUE_ARC_LABELS = {"_VOLUMES_", "_NUMBERED_EXTRAS_"}


def _apply_thread_classification(
    chapters: list[Chapter], side_chapter_ids: set[int], cls: dict
) -> None:
    """Apply per-chapter section/arc rules using the thread-level
    classification `cls` and the set of chapter ids that came from the
    side_body half of an in-body 番外 split. Three rules in order:

      1. Chapters from the side_body half are always side stories.
      2. If the thread is tagged side AND has NO clear arc identifier,
         AND a chapter has a real numbered 第X章 heading — treat it as
         main. This catches the "56-老番外" case (chapter 56 + appended
         extras) without mis-promoting extras-collection threads whose
         internal numbering is its own sequence ("玄女篇 chapter 1").
      3. Otherwise inherit the thread classification.
    """
    thread_has_real_arc = (
        cls["arc_zh"] in _TRUE_ARC_LABELS
        or (cls["arc_zh"] and cls["arc_zh"] != "_MISC_EXTRAS_")
    )
    for ch in chapters:
        has_strict_heading = ch.unit in _STRICT_UNITS and ch.number > 0
        if id(ch) in side_chapter_ids:
            # Thread title may have been MAIN with an in-body 番外 marker,
            # so cls's arc_zh can be empty here. Fall back to
            # _MISC_EXTRAS_ so the side chapter still gets a divider.
            ch.section = "side"
            ch.arc_zh = cls["arc_zh"] or "_MISC_EXTRAS_"
            ch.sub_label_zh = ch.sub_label_zh or cls["sub_label_zh"]
        elif (cls["section"] == "side"
                and has_strict_heading and not thread_has_real_arc):
            ch.section = "main"
            ch.arc_zh = ""
        else:
            ch.section = cls["section"]
            ch.arc_zh = cls["arc_zh"]
            ch.sub_label_zh = ch.sub_label_zh or cls["sub_label_zh"]


def _chapters_from_thread(
    url: str, idx: int, novel_title: str
) -> list[Chapter]:
    """Fetch one thread URL, extract its body, split into chapters, and
    apply per-chapter section/arc classification. Returns [] on fetch or
    extract failure; the caller continues with the next URL."""
    try:
        html = fetch(url)
    except Exception as e:  # noqa: BLE001
        log.error("fetch failed for %s: %s", url, e)
        return []
    page_title, body = extract_body(html)
    if not body:
        log.warning("empty body for %s", url)
        return []
    log.info("    %d chars from %s", len(body), page_title[:60] or url)

    cls = classify_thread_title(page_title, novel_title)

    # Find an in-body 番外/外传/尾声/... separator. When present, we
    # process the pre-marker and post-marker halves independently —
    # otherwise the post-marker extras get swallowed into the body of
    # the last main chapter (since extras typically have no 第X章
    # markers of their own).
    side_marker_pos = _find_side_marker_in_body(body)
    do_split = (side_marker_pos > 0
                and bool(STRICT_CHAPTER_RE.search(body[:side_marker_pos])))

    if do_split:
        main_body = body[:side_marker_pos].rstrip()
        side_body = body[side_marker_pos:].lstrip()
        log.info("    in-body 番外 separator at offset %d — splitting "
                 "thread into main (%d chars) + side (%d chars)",
                 side_marker_pos, len(main_body), len(side_body))
        main_chapters = split_chapters(main_body, source_url=url,
                                       source_index=idx)
        side_chapters = split_chapters(side_body, source_url=url,
                                       source_index=idx)
        # If the extras half had no in-text chapter heading, give it one
        # from the first non-empty line of side_body.
        if (len(side_chapters) == 1 and side_chapters[0].number == 0.0
                and not side_chapters[0].title_zh):
            first_line = next((ln for ln in side_body.splitlines()
                               if ln.strip()), "番外")
            side_chapters[0].title_zh = first_line.strip()[:30] or "番外"
            side_chapters[0].number = 1.0
        chapters = main_chapters + side_chapters
        side_chapter_ids = {id(c) for c in side_chapters}
    else:
        chapters = split_chapters(body, source_url=url, source_index=idx)
        side_chapter_ids = set()

    # Recover from a bare body using the page title (only meaningful when
    # there was no in-body split — otherwise main/side were synthesized).
    if not side_chapter_ids:
        is_bare = (len(chapters) == 1
                   and chapters[0].number == 0.0
                   and not chapters[0].title_zh)
        if is_bare and cls["sub_index"] > 0:
            chapters[0].number = cls["sub_index"]
            chapters[0].title_zh = cls["sub_label_zh"] or page_title
            chapters[0].unit = "章"

    _apply_thread_classification(chapters, side_chapter_ids, cls)

    side_marker_log = " [SIDE]" if cls["section"] == "side" else ""
    arc_marker_log = f" arc={cls['arc_zh']}" if cls["arc_zh"] else ""
    log.info("    -> %d chapter(s) detected%s%s",
             len(chapters), side_marker_log, arc_marker_log)
    return chapters


def _promote_unnumbered_main(all_chapters: list[Chapter]) -> None:
    """Mutates `all_chapters` so every main-section chapter has a positive
    integer number. Assignment respects source position: unnumbered
    chapters from earlier sources get lower numbers, later sources
    continue past the highest explicit number, and gaps in the explicit
    sequence are filled when an unnumbered chapter sits between two
    explicits."""
    main = [c for c in all_chapters if c.section == "main"]
    unnumbered = sorted(
        [c for c in main if c.number == 0.0],
        key=lambda c: (c.source_index, c.body_offset),
    )
    if not unnumbered:
        return
    explicit_pos = sorted(
        (c.source_index, c.body_offset, int(c.number))
        for c in main
        if c.number > 0 and c.number == int(c.number)
    )
    used = {n for _, _, n in explicit_pos}
    if not explicit_pos:
        for i, c in enumerate(unnumbered, start=1):
            c.number = float(i)
            c.unit = "章"
        log.info("no chapter markers detected; numbered %d chapter(s) "
                 "sequentially as Chapter 1-%d",
                 len(unnumbered), len(unnumbered))
        return
    for c in unnumbered:
        # Highest explicit chapter number whose source position precedes
        # this unnumbered chapter — walk the sorted list and stop once
        # we pass our position.
        max_prev = 0
        for sidx, boff, n in explicit_pos:
            if (sidx, boff) < (c.source_index, c.body_offset):
                if n > max_prev:
                    max_prev = n
            else:
                break
        candidate = max_prev + 1
        while candidate in used:
            candidate += 1
        c.number = float(candidate)
        c.unit = "章"
        used.add(candidate)
    log.info("promoted %d unnumbered chapter(s) to numbered chapters "
             "based on source position", len(unnumbered))


def _dedup_main_chapters(all_chapters: list[Chapter]) -> list[Chapter]:
    """Dedupe main chapters by chapter number, keeping the longer-bodied
    (or better-titled) version. Side chapters are NOT deduped — sharing
    a chapter number across different arcs is expected. Returns a
    re-sorted list."""
    main_by_number: dict[float, Chapter] = {}
    others: list[Chapter] = []
    for ch in all_chapters:
        if ch.section != "main":
            others.append(ch)
            continue
        prev = main_by_number.get(ch.number)
        if prev is None or (
            len(ch.body_zh) > len(prev.body_zh)
            or (not prev.title_zh.strip() and ch.title_zh.strip())
        ):
            main_by_number[ch.number] = ch
    new_total = len(main_by_number) + len(others)
    if new_total != len(all_chapters):
        log.info("deduped %d → %d chapters",
                 len(all_chapters), new_total)
    return sorted(
        list(main_by_number.values()) + others,
        key=Chapter.sort_key,
    )


def _translate_chapters(
    chapters: list[Chapter], target_lang: str
) -> list[Chapter]:
    """Translate every chapter's title, body, and arc name. On a
    permanent block from the translator, fill remaining chapters with
    their Chinese text so the partial EPUB still contains every
    chapter — re-running with the cache later fills in the rest."""
    log.info("translating %d chapters to %s ...", len(chapters), target_lang)
    completed: list[Chapter] = []
    arc_cache: dict[str, str] = {}
    try:
        for i, ch in enumerate(chapters, start=1):
            log.info("  [%d/%d] %s", i, len(chapters),
                     ch.title_zh[:50] or "(unnumbered)")
            ch.title_en = translate(ch.title_zh, target=target_lang) if ch.title_zh else ""
            ch.body_en = translate(ch.body_zh, target=target_lang)
            if ch.arc_zh:
                if ch.arc_zh in SYNTHETIC_ARC_LABELS:
                    ch.arc_en = SYNTHETIC_ARC_LABELS[ch.arc_zh]
                else:
                    if ch.arc_zh not in arc_cache:
                        arc_cache[ch.arc_zh] = translate(
                            ch.arc_zh, target=target_lang
                        ).strip()
                    ch.arc_en = arc_cache[ch.arc_zh]
            completed.append(ch)
    except _PermanentlyBlocked as e:
        log.error("translation aborted: %s", e)
        completed_count = len(completed)
        for c in chapters[completed_count:]:
            if not c.title_en:
                c.title_en = c.title_zh
            if not c.body_en:
                c.body_en = c.body_zh
            if not c.arc_en and c.arc_zh:
                c.arc_en = SYNTHETIC_ARC_LABELS.get(c.arc_zh, c.arc_zh)
            completed.append(c)
        untranslated = len(completed) - completed_count
        log.warning("writing partial EPUB: %d translated, %d untranslated "
                    "(Chinese text). Re-run later — translation cache "
                    "preserves progress, only untranslated chapters will "
                    "be re-fetched from Google.",
                    completed_count, untranslated)
    return completed


def process(urls: list[str], target_lang: str, no_translate: bool,
            novel_title: str = "") -> list[Chapter]:
    all_chapters: list[Chapter] = []
    for idx, url in enumerate(urls):
        log.info("[%d/%d] %s", idx + 1, len(urls), url)
        all_chapters.extend(_chapters_from_thread(url, idx, novel_title))

    _promote_unnumbered_main(all_chapters)
    all_chapters.sort(key=Chapter.sort_key)
    all_chapters = _dedup_main_chapters(all_chapters)

    if no_translate:
        for ch in all_chapters:
            ch.title_en = ch.title_zh
            ch.body_en = ch.body_zh
        return all_chapters

    return _translate_chapters(all_chapters, target_lang)


def _bust_translation_cache_for_urls(urls: list[str]) -> int:
    """Delete all .cache/tr/ entries whose source text was extracted from
    the given URLs. We can't reverse-map SHA1 keys back to URLs, so instead
    we refetch/re-extract each URL (HTML is still cached), recompute the
    exact chunk texts, derive the cache keys, and delete those files.
    Returns number of cache files deleted."""
    if not TR_CACHE.exists():
        return 0
    deleted = 0
    for url in urls:
        try:
            html = fetch(url)
        except Exception as e:  # noqa: BLE001
            log.warning("retranslate: could not fetch %s: %s", url, e)
            continue
        _, body = extract_body(html)
        if not body:
            continue
        # Collect every chunk of every text that translate() would produce
        # for this body (title is usually short and cached separately but
        # we cover it too by iterating all possible source texts).
        texts_to_bust: list[str] = [body]
        chapters = split_chapters(body, source_url=url, source_index=0)
        for ch in chapters:
            if ch.title_zh:
                texts_to_bust.append(ch.title_zh)
            if ch.body_zh:
                texts_to_bust.append(ch.body_zh)
        for text in texts_to_bust:
            for chunk in _chunks(text, TR_CHUNK_CHARS):
                for lang_pair in (("zh-CN", "en"), ("zh-CN", "it"),
                                  ("zh-CN", "es"), ("zh-CN", "fr"),
                                  ("zh-CN", "de"), ("zh-CN", "pt"),
                                  ("auto", "en")):
                    src, tgt = lang_pair
                    key = _sha1(f"{src}|{tgt}|{chunk}")
                    cf = TR_CACHE / f"{key}.txt"
                    if cf.exists():
                        cf.unlink()
                        deleted += 1
    return deleted


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("input", help="a thread URL (auto-discovers) or a file with URLs")
    ap.add_argument("-o", "--output", type=Path, default=Path("novel.epub"))
    ap.add_argument("-t", "--title", default="", help="EPUB title (auto from page if empty)")
    ap.add_argument("-a", "--author", default="Unknown")
    ap.add_argument("-l", "--lang", default="en", help="target language (en, it, es, ...)")
    ap.add_argument("--no-discover", action="store_true",
                    help="treat single URL as one-off (skip auto-discovery)")
    ap.add_argument("--list-only", action="store_true",
                    help="just print resolved URLs and exit (no translate / EPUB)")
    ap.add_argument("--max-chapters", type=int, default=None,
                    help="cap discovered URL count (useful for a quick test run)")
    ap.add_argument("--no-translate", action="store_true",
                    help="skip translation; build EPUB from raw Chinese (debug)")
    ap.add_argument("--clear-cache", action="store_true",
                    help="wipe ALL of .cache/ (HTML + translations) before running")
    ap.add_argument("--clear-translations", action="store_true",
                    help="wipe only .cache/tr/ (translation cache) before running. "
                         "HTML stays cached so pages are not refetched. "
                         "Use this when old translations have CJK leaks or "
                         "wrong language and you want a clean re-translate.")
    ap.add_argument("--retranslate-url", metavar="URL", action="append",
                    default=[],
                    help="delete translation cache only for this specific thread URL "
                         "and re-translate it. Can be given multiple times. "
                         "Useful when one chapter came out wrong without redoing "
                         "the whole book.")
    # ---- translation backend ---------------------------------------------
    ap.add_argument("--backend", choices=["unofficial", "gcv3", "deepseek"],
                    default=os.environ.get("TRANSLATION_BACKEND", "unofficial"),
                    help="Translation backend. 'unofficial' (default) uses "
                         "translate.googleapis.com (free, unauthenticated, "
                         "rate-limited). 'gcv3' uses Google Cloud Translation "
                         "API v3 (paid after 500K free chars/month, requires "
                         "a service-account JSON key). 'deepseek' uses the "
                         "DeepSeek chat API (~$0.20 per novel, much higher "
                         "narrative quality, requires DEEPSEEK_API_KEY).")
    ap.add_argument("--credentials", metavar="PATH", default=None,
                    help="(gcv3 only) Path to service-account JSON key. Falls "
                         "back to GOOGLE_APPLICATION_CREDENTIALS env var.")
    ap.add_argument("--cooldown-every-chars", type=int,
                    default=GCV3_DEFAULT_COOLDOWN_EVERY_CHARS,
                    help="(gcv3 only) Sleep --cooldown-secs after every N "
                         "characters translated. Default 500000.")
    ap.add_argument("--cooldown-secs", type=int,
                    default=GCV3_DEFAULT_COOLDOWN_SECS,
                    help="(gcv3 only) Cooldown duration in seconds. Default 60.")
    ap.add_argument("--deepseek-key", metavar="SK", default=None,
                    help="(deepseek only) API key. Prefer setting the "
                         "DEEPSEEK_API_KEY env var instead so it doesn't "
                         "show up in process listings.")
    ap.add_argument("--deepseek-model", metavar="MODEL",
                    default=DEEPSEEK_DEFAULT_MODEL,
                    help="(deepseek only) Model name. Default 'deepseek-chat' "
                         "(V3). Use 'deepseek-reasoner' for R1 (slower, "
                         "higher quality, ~3x cost).")
    args = ap.parse_args(argv)

    # Apply backend + cooldown settings before any translate() calls happen
    global TRANSLATION_BACKEND, gcv3_cooldown_every_chars, gcv3_cooldown_secs
    global deepseek_model
    TRANSLATION_BACKEND = args.backend
    gcv3_cooldown_every_chars = args.cooldown_every_chars
    gcv3_cooldown_secs = args.cooldown_secs
    deepseek_model = args.deepseek_model
    if args.backend == "gcv3":
        # Force load credentials now so we fail fast on a bad key
        _gcv3_load_credentials(args.credentials)
        log.info("gcv3 cooldown: %ds every %d chars",
                 gcv3_cooldown_secs, gcv3_cooldown_every_chars)
    elif args.backend == "deepseek":
        _deepseek_load_key(args.deepseek_key)
        log.info("deepseek backend ready (model=%s)", deepseek_model)

    # ---- cache busting -----------------------------------------------
    import shutil
    if args.clear_cache and CACHE_DIR.exists():
        shutil.rmtree(CACHE_DIR)
        log.info("full cache cleared (HTML + translations)")

    elif args.clear_translations and TR_CACHE.exists():
        shutil.rmtree(TR_CACHE)
        log.info("translation cache cleared; HTML cache preserved")

    if args.retranslate_url:
        n = _bust_translation_cache_for_urls(
            [normalize_url(u) for u in args.retranslate_url]
        )
        log.info("retranslate: deleted %d cached translation chunk(s) "
                 "for %d URL(s)", n, len(args.retranslate_url))
    # ------------------------------------------------------------------

    urls, discovered_title = resolve_input(
        args.input, no_discover=args.no_discover, max_chapters=args.max_chapters,
    )
    if not urls:
        log.error("no URLs to process"); return 2
    log.info("resolved %d URL(s)", len(urls))

    if args.list_only:
        for u in urls:
            print(u)
        return 0

    chapters = process(urls, target_lang=args.lang,
                       no_translate=args.no_translate,
                       novel_title=discovered_title)
    if not chapters:
        log.error("no chapters produced; aborting EPUB build"); return 1

    title = args.title or discovered_title or "Translated Novel"
    build_epub(
        chapters, out_path=args.output, book_title=title,
        author=args.author, language=args.lang,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
