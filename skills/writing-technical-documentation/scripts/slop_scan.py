#!/usr/bin/env python3
"""Scan prose for AI writing patterns, style problems, and structure statistics.

Usage:
    python3 slop_scan.py FILE [FILE ...] [--json] [--max-score N] [--min-weight N]
                         [--no-code-mask] [--quiet]
    cat doc.md | python3 slop_scan.py -

Exit code is 1 when any file's score (weighted hits per 1,000 words) exceeds
--max-score. Standard library only.

The scanner finds symptoms. Fix the cause: replace vague sentences with
specific facts from the code, or delete them.
"""
import argparse
import json
import re
import statistics
import sys

EM = "\u2014"
EN = "–"

# (category, weight, regex, fix hint)
# Weights: 1 = weak signal, 2 = moderate, 3 = strong.
WORDS_HIGH = [
    "delve", "delves", "delving", "tapestry", "testament", "beacon", "cornerstone",
    "multifaceted", "myriad", "plethora", "realm", "interplay", "unparalleled",
    "groundbreaking", "game-changer", "game changer", "game-changing", "paradigm",
    "synergy", "synergies", "seamless", "seamlessly", "meticulous", "meticulously",
    "intricate", "intricacies", "bustling", "unlock", "unleash", "unleashes",
    "supercharge", "revolutionize", "revolutionizes", "revolutionary",
    "cutting-edge", "state-of-the-art", "best-in-class", "world-class",
    "battle-tested", "future-proof", "blazing fast", "blazingly fast",
    "enterprise-grade", "mission-critical", "turnkey", "holistic", "transformative",
]
WORDS_MED = [
    "leverage", "leverages", "leveraged", "leveraging", "harness", "harnesses",
    "harnessing", "utilize", "utilizes", "utilized", "utilizing", "showcase",
    "showcases", "showcasing", "underscore", "underscores", "underscoring",
    "foster", "fosters", "fostering", "facilitate", "facilitates", "facilitating",
    "empower", "empowers", "empowering", "elevate", "elevates", "elevating",
    "embark", "embarks", "streamline", "streamlines", "streamlining", "bolster",
    "bolsters", "garner", "garners", "pivotal", "crucial", "vital", "paramount",
    "robust", "comprehensive", "nuanced", "vibrant", "dynamic", "innovative",
    "ecosystem", "journey", "landscape", "navigate", "navigating", "spearhead",
    "orchestrate", "resonate", "resonates", "cultivate", "cultivates",
    "indispensable", "invaluable", "noteworthy", "commendable", "profound",
    "compelling", "sophisticated", "powerful", "elegant", "versatile",
    "scalable", "production-ready", "developer-friendly", "intuitive",
    "lightweight", "end-to-end", "out of the box", "under the hood",
    "load-bearing", "genuinely", "stakeholders", "best practices",
    "deep dive", "key takeaways", "unpack", "unpacking", "reimagine",
    "reimagined", "ever-evolving", "fast-paced", "evolving",
]
WORDS_LOW = [
    "moreover", "furthermore", "additionally", "consequently", "nevertheless",
    "nonetheless", "indeed", "notably", "importantly", "crucially", "ultimately",
    "essentially", "fundamentally", "arguably", "undeniably", "remarkably",
    "incredibly", "truly", "really", "very", "extremely", "highly", "quite",
    "simply", "just", "easily", "easy", "obviously", "clearly", "of course",
    "straightforward", "trivial", "trivially", "basically", "literally",
    "significantly", "effectively", "particularly",
]

PHRASES = [
    (3, r"\bin today'?s (?:fast[- ]paced|digital|modern|ever[- ]changing|rapidly evolving)\b", "time-parasite opener; delete"),
    (3, r"\bin the (?:realm|world|age|era) of\b", "filler opener; name the subject"),
    (3, r"\bnow more than ever\b", "time parasite; delete"),
    (3, r"\b(?:it'?s|it is) (?:worth|important|crucial|essential) (?:noting|to note|mentioning|to mention|to remember)\b", "filler; state the fact"),
    (3, r"\bit (?:should|must) be noted\b", "filler; state the fact"),
    (2, r"\bneedless to say\b|\bit goes without saying\b", "filler; delete"),
    (3, r"\blet'?s (?:dive|delve|explore|unpack|break (?:it|this) down|get started)\b", "assistant filler; delete"),
    (2, r"\bwithout further ado\b", "filler; delete"),
    (2, r"\bhere'?s (?:the thing|the kicker|why|what you need to know|the catch)\b", "dramatic setup; state the point"),
    (3, r"\bimagine a world where\b", "dramatic setup; delete"),
    (2, r"\bat (?:its|the) core\b|\bat the heart of\b|\bat the end of the day\b", "filler; name the mechanism"),
    (1, r"\bwhen it comes to\b|\bin terms of\b|\bwith regard to\b|\bin order to\b", "wordy; shorten"),
    (3, r"\bplays? an? (?:crucial|pivotal|vital|key|important|significant|essential) role\b", "significance inflation; give the fact"),
    (3, r"\bserves? as an? (?:testament|reminder|beacon|cornerstone)\b|\bstands? as an? (?:testament|reminder|beacon)\b", "significance inflation"),
    (3, r"\bmarks? an? (?:significant|pivotal|important|major) (?:milestone|moment|shift|step)\b", "significance inflation"),
    (2, r"\bpaves? the way (?:for|to)\b|\bsets? the stage for\b|\bopens? the door to\b", "vague causation; name the effect"),
    (2, r"\btakes? (?:it|\w+) to the next level\b|\bunlock(?:s|ing)? the (?:full )?potential\b", "hype; delete"),
    (2, r"\ba (?:wide|broad|vast) (?:range|array|variety|spectrum) of\b|\ba (?:variety|number|host|multitude) of\b", "vague quantity; list or count them"),
    (3, r"\bwhether you(?:'re| are) an? \w+(?: or| and)? (?:an? )?\w+", "audience mush; name the reader"),
    (2, r"\bnavigate the (?:complexities|challenges|landscape)\b", "stock phrase; delete"),
    (2, r"\bfrom \w+(?: \w+)? to \w+(?: \w+)?,? (?:this|the|it)\b", "vague span; list real scope"),
    (3, r"\bi hope this helps\b|\bfeel free to (?:reach out|ask)\b|\bdon'?t hesitate to\b|\blet me know if\b", "leaked assistant text; delete"),
    (3, r"\bas an ai\b|\bas a language model\b|\bknowledge cutoff\b", "leaked assistant text; delete"),
    (2, r"\b(?:great|good|excellent) question\b|\byou'?re absolutely right\b", "sycophancy; delete"),
    (2, r"^\s*(?:certainly|absolutely|sure|of course)[!,.]", "assistant opener; delete"),
    (2, r"\b(?:in summary|in conclusion|to sum up|to recap|all in all|in short|overall),", "recap opener; usually delete"),
    (2, r"\bkey takeaways?\b|\bfinal thoughts\b", "recap section; delete"),
    (2, r"\b(?:this|the following) (?:comprehensive|complete|ultimate|detailed) guide\b", "self-labeling; delete"),
    (2, r"\bthis (?:document|guide|section|article|page) (?:will|aims to|provides?|covers?|explores?|outlines?)\b", "preamble; start with content"),
    (1, r"\bas (?:mentioned|discussed|noted) (?:above|earlier|previously|before)\b|\bas we'?ll see (?:below|later)\b", "narrated structure; link or delete"),
    (2, r"\bexperts? (?:say|agree|believe)\b|\bstudies (?:show|suggest|have shown)\b|\bresearch (?:shows|suggests)\b|\bindustry (?:best practices?|standards?|experts?|reports?)\b|\bit is (?:widely|generally|commonly) (?:believed|accepted|known)\b", "vague attribution; cite or own it"),
    (2, r"\bsome (?:argue|believe|say)\b|\bmany (?:developers|engineers|people|teams) (?:believe|think|say|find)\b|\bcritics (?:say|argue)\b", "vague attribution"),
    (2, r"\bin my experience\b|\bi'?ve (?:seen|found|noticed)\b|\bwe'?re (?:excited|thrilled|proud)\b|\bi'?m (?:excited|thrilled)\b", "invented experience or emotion"),
    (2, r"\bthink of (?:it|this|\w+) (?:as|like)\b", "metaphor stacking; state the mechanism"),
    (2, r"\bthe (?:key|real|actual|true) (?:insight|issue|problem|challenge|question) (?:is|here)\b", "dramatic framing"),
    (1, r"\bit (?:is|'s) (?:recommended|advisable|possible|important) (?:that|to)\b", "empty subject; use direct statement"),
    (2, r"\bplease note\b|\bkeep in mind that\b|\bremember,? (?:that|to)\b", "filler; state the fact"),
    (2, r"\bfeel free to\b", "filler; use an imperative"),
    (2, r"\bthe (?:best|good|great) part\?|\bthe (?:result|catch|answer|upshot|kicker|takeaway)\?", "self-answered question; state it"),
    (2, r"\b(?:can|may|might) (?:potentially|possibly) \w+", "hedge stack; state condition"),
    (2, r"\b(?:is|are) designed to\b|\baims? to\b|\bstrives? to\b|\bseeks? to\b", "vague purpose verb; use the real verb"),
    (1, r"\bcan help (?:you|to|ensure|improve)\b|\bhelps? to (?:ensure|improve|reduce)\b|\bhelps? ensure\b", "vague benefit; give the mechanism"),
    (2, r"\bthis (?:ensures|allows|enables|provides|helps)\b", "vague 'this' subject; name the thing"),
    (1, r"\bnot only\b.{1,80}\bbut also\b", "negative parallelism flourish"),
    (2, r"\bincluding but not limited to\b|\band more\.\s|\band much more\b|\betc\.", "open-ended list; enumerate or count"),
    (2, r"\b(?:easy|simple|straightforward) to (?:use|set up|install|configure|integrate)\b", "unproven adjective; show steps and time"),
    (2, r"\bout[- ]of[- ]the[- ]box\b", "vague; list defaults"),
    (3, r"oaicite|contentReference|turn\d+search\d+|utm_source=chatgpt|citeturn|grok_card", "leaked tool markup; delete"),
    (3, r"\[(?:insert|your|company|name|date|link)[^\]]*\]|\blorem ipsum\b", "unfilled placeholder"),
]

# Negative parallelism and similar regexes handled separately for sentence-level.
NEG_PARALLEL = [
    re.compile(r"\b(?:it|this|that|these|they)(?:'s| is| isn't| is not| are not|'re not| aren't)(?: just| only| merely| simply)? (?:a |an |the )?[^.;:\n]{1,60}[,;] (?:it|this|that|they)(?:'s| is| are|'re)\b", re.I),
    re.compile(r"\bnot (?:just|only|merely|simply) (?:a |an |the )?[^.;:\n]{1,60}[,;] (?:but|it|this|they)\b", re.I),
    re.compile(r"\b(?:isn't|is not|aren't|are not|wasn't|doesn't just|don't just)\s+(?:just|only|merely|simply)\b", re.I),
    re.compile(r"\bmore than just\b|\bless about \w+(?: \w+)?,? more about\b", re.I),
    re.compile(r"\bno \w+(?: \w+)?,? no \w+(?: \w+)?,? just\b", re.I),
    re.compile(r"\bisn'?t (?:about|just about) [^.;:\n]{1,60}[.;,] it'?s about\b", re.I),
]

TRAILING_PARTICIPLE = re.compile(
    r",\s+(?:ensuring|highlighting|underscoring|showcasing|reflecting|contributing to|fostering|"
    r"emphasizing|demonstrating|enabling|allowing|making it|making them|providing|offering|"
    r"empowering|helping|leading to|resulting in|paving)\b[^.\n]{0,100}[.\n]",
    re.I,
)

COPULA_AVOID = re.compile(r"\b(?:serves|stands|acts|functions) as\b|\bboasts?\b|\brepresents? a\b|\bfeatures? (?:a|an|the) \w+", re.I)

TITLE_CASE_WORDS_MIN = 3
SMALL = {"a", "an", "the", "and", "or", "but", "for", "nor", "on", "at", "to", "from", "by", "of", "in", "with", "as", "vs"}

BOLD_LEAD = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+\*\*[^*\n]{1,60}\*\*", re.M)
EMOJI = re.compile("[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F000-\U0001F2FF✅❌⭐]")
SMART_QUOTES = re.compile("[‘’“”]")
ARROWS = re.compile("[→⇒←↔⟶]")
ZERO_WIDTH = re.compile("[​‌‍⁠﻿]")
NBSP = re.compile(" ")

FILLER_HEADINGS = {
    "overview", "introduction", "conclusion", "summary", "final thoughts",
    "key takeaways", "key considerations", "best practices", "benefits",
    "use cases", "future work", "future directions", "challenges and opportunities",
    "getting started with confidence", "why it matters", "the bottom line",
    "wrapping up", "next steps",
}

TIME_WORDS = re.compile(
    r"\b(?:currently|presently|at the moment|as of (?:this writing|now|today)|"
    r"in the (?:near )?future|upcoming|soon|newly|recently|latest|nowadays|these days)\b",
    re.I,
)

CONDESCEND = re.compile(r"\b(?:simply|just|easily|obviously|of course|clearly|trivially|all you need to do)\b", re.I)


def mask_code(text):
    """Blank out fenced and inline code so identifiers and commands are not scanned."""
    def blank(m):
        return re.sub(r"[^\n]", " ", m.group(0))
    text = re.sub(r"```.*?```", blank, text, flags=re.S)
    text = re.sub(r"~~~.*?~~~", blank, text, flags=re.S)
    text = re.sub(r"`[^`\n]+`", blank, text)
    return text


def strip_front_matter(text):
    if text.startswith("---"):
        m = re.match(r"---\n.*?\n---\n", text, flags=re.S)
        if m:
            return re.sub(r"[^\n]", " ", m.group(0)) + text[m.end():]
    return text


def line_of(text, pos):
    return text.count("\n", 0, pos) + 1


def snippet(text, start, end, width=70):
    s = max(0, start - 20)
    e = min(len(text), end + width - 20)
    return re.sub(r"\s+", " ", text[s:e]).strip()


def split_sentences(text):
    plain = re.sub(r"^\s*(?:#+|[-*+]|\d+[.)]|>|\|)\s*", "", text, flags=re.M)
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z\"'(])", plain)
    return [p.strip() for p in parts if p.strip()]


def word_count(text):
    return len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'_-]*", text))


def scan(raw, mask=True):
    text = strip_front_matter(raw)
    scan_text = mask_code(text) if mask else text
    hits = []  # dict(category, weight, line, match, hint)

    def add(cat, weight, start, end, hint, source=None):
        src = scan_text if source is None else source
        hits.append({
            "category": cat,
            "weight": weight,
            "line": line_of(src, start),
            "match": src[start:end].strip()[:80],
            "context": snippet(src, start, end),
            "fix": hint,
        })

    # Vocabulary
    for words, weight, cat in ((WORDS_HIGH, 3, "vocabulary-high"), (WORDS_MED, 2, "vocabulary"), (WORDS_LOW, 1, "filler-word")):
        pattern = re.compile(r"\b(?:" + "|".join(re.escape(w) for w in sorted(words, key=len, reverse=True)) + r")\b", re.I)
        for m in pattern.finditer(scan_text):
            add(cat, weight, m.start(), m.end(), "replace with the concrete fact, or delete")

    # Phrases
    for weight, pat, hint in PHRASES:
        for m in re.finditer(pat, scan_text, flags=re.I | re.M):
            add("phrase", weight, m.start(), m.end(), hint)

    # Negative parallelism
    for rx in NEG_PARALLEL:
        for m in rx.finditer(scan_text):
            add("negative-parallelism", 3, m.start(), m.end(), "state the true claim only")

    for m in TRAILING_PARTICIPLE.finditer(scan_text):
        add("trailing-participle", 2, m.start(), m.end(), "delete, or make a separate sentence with a fact")

    for m in COPULA_AVOID.finditer(scan_text):
        add("copula-avoidance", 1, m.start(), m.end(), "use 'is' or 'has'")

    for m in TIME_WORDS.finditer(scan_text):
        add("timeless-text", 1, m.start(), m.end(), "use a version or date, or state what is true")

    # Formatting
    em_count = scan_text.count(EM)
    for m in re.finditer(EM, scan_text):
        add("em-dash", 1, m.start(), m.end(), "use a period, comma, colon, or parentheses")
    for m in re.finditer(EN, scan_text):
        if not re.search(r"\d\s*" + EN + r"\s*\d", scan_text[max(0, m.start() - 3):m.end() + 3]):
            add("en-dash", 1, m.start(), m.end(), "use a hyphen or restructure")
    for m in BOLD_LEAD.finditer(scan_text):
        add("bold-lead-bullet", 2, m.start(), m.end(), "use a table or plain sentences")
    for m in EMOJI.finditer(scan_text):
        add("emoji", 2, m.start(), m.end(), "delete")
    for m in SMART_QUOTES.finditer(scan_text):
        add("smart-quote", 1, m.start(), m.end(), "use straight quotes")
    for m in ARROWS.finditer(scan_text):
        add("unicode-arrow", 1, m.start(), m.end(), "use words")
    for m in ZERO_WIDTH.finditer(scan_text):
        add("hidden-char", 3, m.start(), m.end(), "remove zero-width character")
    for m in NBSP.finditer(scan_text):
        add("hidden-char", 1, m.start(), m.end(), "replace non-breaking space")

    # Headings
    heading_lines = []
    for m in re.finditer(r"^(#{1,6})\s+(.+?)\s*$", scan_text, flags=re.M):
        level, title = len(m.group(1)), m.group(2).strip()
        heading_lines.append((level, title, m.start()))
        plain = re.sub(r"[`*_]", "", title)
        words = re.findall(r"[A-Za-z][A-Za-z'-]*", plain)
        if plain.lower().rstrip(":?.") in FILLER_HEADINGS:
            add("filler-heading", 2, m.start(), m.end(), "delete section or name its content")
        if len(words) >= TITLE_CASE_WORDS_MIN + 1:
            rest = words[1:]
            capped = [w for w in rest if w[0].isupper() and w.lower() not in SMALL]
            if len(capped) >= 2 and len(capped) >= 0.6 * len([w for w in rest if w.lower() not in SMALL]):
                add("title-case-heading", 1, m.start(), m.end(), "use sentence case")
        if title.endswith(":") or title.endswith("?"):
            add("heading-punctuation", 1, m.start(), m.end(), "remove trailing punctuation")

    # Heading inflation: heading followed by very little text
    for i, (level, title, pos) in enumerate(heading_lines):
        end = heading_lines[i + 1][2] if i + 1 < len(heading_lines) else len(scan_text)
        body = scan_text[pos:end].split("\n", 1)[1] if "\n" in scan_text[pos:end] else ""
        if level >= 3 and 0 < word_count(body) < 12:
            add("heading-inflation", 1, pos, pos + len(title) + level, "merge into parent section")

    # Sentence-level stats and patterns
    prose = re.sub(r"^\s*\|.*$", " ", scan_text, flags=re.M)
    sentences = split_sentences(prose)
    lengths = [word_count(s) for s in sentences if word_count(s) > 0]
    stats = {}
    if lengths:
        stats["sentences"] = len(lengths)
        stats["mean_sentence_words"] = round(statistics.mean(lengths), 1)
        stats["stdev_sentence_words"] = round(statistics.pstdev(lengths), 1)

    # Repeated sentence openers
    openers = [" ".join(re.findall(r"[A-Za-z']+", s.lower())[:2]) for s in sentences]
    run = 1
    for i in range(1, len(openers)):
        if openers[i] and openers[i] == openers[i - 1]:
            run += 1
            if run == 3:
                hits.append({"category": "repeated-opener", "weight": 1, "line": 0,
                             "match": openers[i], "context": "three consecutive sentences start with '%s'" % openers[i],
                             "fix": "vary by merging or restructuring"})
        else:
            run = 1

    # Connector density
    conn = re.findall(r"(?:^|\n)\s*(?:moreover|furthermore|additionally|however|in addition|consequently|thus|therefore|overall|ultimately)\b", scan_text, flags=re.I)
    paragraphs = [p for p in re.split(r"\n\s*\n", prose) if word_count(p) > 8]
    if len(paragraphs) >= 4 and len(conn) / max(1, len(paragraphs)) > 0.4:
        hits.append({"category": "connector-density", "weight": 2, "line": 0, "match": "%d/%d paragraphs" % (len(conn), len(paragraphs)),
                     "context": "many paragraphs open with a transition word", "fix": "delete the transitions"})

    # Rule of three: "X, Y, and Z" density
    triples = re.findall(r"\b\w+(?:\s\w+)?,\s\w+(?:\s\w+)?,\s(?:and|or)\s\w+(?:\s\w+)?\b", prose)
    sent_total = max(1, len(sentences))
    if len(triples) >= 4 and len(triples) / sent_total > 0.12:
        hits.append({"category": "rule-of-three", "weight": 2, "line": 0, "match": "%d triplets in %d sentences" % (len(triples), sent_total),
                     "context": "frequent three-item lists", "fix": "list the items that exist"})

    # Em dash density
    words = word_count(prose)
    if words and em_count / max(1, words) * 1000 > 5:
        hits.append({"category": "em-dash-density", "weight": 2, "line": 0, "match": "%d em dashes" % em_count,
                     "context": "high em-dash density (%.1f per 1,000 words)" % (em_count / words * 1000), "fix": "replace with other punctuation"})

    # Uniform lengths
    if len(lengths) >= 12 and stats.get("stdev_sentence_words", 99) < 3.5:
        hits.append({"category": "uniform-rhythm", "weight": 1, "line": 0, "match": "stdev %.1f" % stats["stdev_sentence_words"],
                     "context": "sentence lengths are unusually uniform", "fix": "let content set length"})

    # Concrete specifics density: backticked identifiers, numbers, paths, urls
    concrete = len(re.findall(r"`[^`\n]+`", text)) + len(re.findall(r"\b\d[\d.,]*\b", prose)) + len(re.findall(r"[\w./-]+\.(?:py|js|ts|go|rs|java|yml|yaml|json|toml|md|sh)\b", prose))
    stats["concrete_items"] = concrete
    stats["concrete_per_100_words"] = round(concrete / max(1, words) * 100, 1)
    if words >= 150 and stats["concrete_per_100_words"] < 1.0:
        hits.append({"category": "low-specificity", "weight": 3, "line": 0, "match": "%.1f concrete items per 100 words" % stats["concrete_per_100_words"],
                     "context": "few names, numbers, paths, or commands", "fix": "add evidence-backed specifics or cut"})

    # Bullet ratio
    lines = [l for l in scan_text.split("\n") if l.strip()]
    bullets = sum(1 for l in lines if re.match(r"\s*(?:[-*+]|\d+[.)])\s", l))
    if len(lines) >= 20:
        stats["bullet_line_ratio"] = round(bullets / len(lines), 2)
        if bullets / len(lines) > 0.6:
            hits.append({"category": "over-listing", "weight": 1, "line": 0, "match": "%d%% list lines" % int(100 * bullets / len(lines)),
                         "context": "most lines are list items", "fix": "write reasoning as prose where items relate"})

    # Bold density in prose
    bold = len(re.findall(r"\*\*[^*\n]+\*\*", prose))
    if words and bold / max(1, words) * 1000 > 15:
        hits.append({"category": "bold-density", "weight": 1, "line": 0, "match": "%d bold spans" % bold,
                     "context": "bold used heavily", "fix": "reserve bold for UI labels"})

    # Repeated 4-grams (restatement)
    toks = re.findall(r"[a-z']+", prose.lower())
    grams = {}
    for i in range(len(toks) - 3):
        g = " ".join(toks[i:i + 4])
        grams[g] = grams.get(g, 0) + 1
    repeats = [(g, c) for g, c in grams.items() if c >= 3 and len(set(g.split())) >= 3]
    for g, c in sorted(repeats, key=lambda x: -x[1])[:5]:
        hits.append({"category": "repeated-phrase", "weight": 1, "line": 0, "match": g,
                     "context": "phrase appears %d times" % c, "fix": "vary or merge"})

    # Cluster detection: windows of 150 words with 3+ categories
    positions = []
    for h in hits:
        if h["line"]:
            positions.append((h["line"], h["category"]))
    clusters = []
    positions.sort()
    i = 0
    while i < len(positions):
        j = i
        cats = set()
        while j < len(positions) and positions[j][0] - positions[i][0] <= 8:
            cats.add(positions[j][1])
            j += 1
        if len(cats) >= 3:
            clusters.append({"start_line": positions[i][0], "end_line": positions[j - 1][0], "categories": sorted(cats)})
            i = j
        else:
            i += 1

    total_weight = sum(h["weight"] for h in hits)
    cluster_bonus = 3 * len(clusters)
    score = round((total_weight + cluster_bonus) / max(1, words) * 1000, 1) if words else 0.0
    by_cat = {}
    for h in hits:
        c = by_cat.setdefault(h["category"], {"count": 0, "weight": 0})
        c["count"] += 1
        c["weight"] += h["weight"]
    stats["words"] = words
    return {"score": score, "words": words, "hits": hits, "by_category": by_cat, "clusters": clusters, "stats": stats}


def render(name, res, min_weight, quiet):
    out = []
    out.append("== %s ==" % name)
    out.append("words: %d   score: %s per 1,000 words   hits: %d   clusters: %d" % (res["words"], res["score"], len(res["hits"]), len(res["clusters"])))
    band = "clean" if res["score"] < 5 else ("needs a pass" if res["score"] < 15 else "rewrite from evidence")
    out.append("band: %s" % band)
    s = res["stats"]
    out.append("sentence length mean/stdev: %s/%s   concrete items per 100 words: %s" % (s.get("mean_sentence_words", "-"), s.get("stdev_sentence_words", "-"), s.get("concrete_per_100_words", "-")))
    out.append("")
    out.append("By category:")
    for cat, v in sorted(res["by_category"].items(), key=lambda x: -x[1]["weight"]):
        out.append("  %-24s count %-3d weight %d" % (cat, v["count"], v["weight"]))
    if res["clusters"]:
        out.append("")
        out.append("Clusters (3+ categories close together; fix first):")
        for c in res["clusters"]:
            out.append("  lines %d-%d: %s" % (c["start_line"], c["end_line"], ", ".join(c["categories"])))
    if not quiet:
        out.append("")
        out.append("Findings:")
        shown = [h for h in res["hits"] if h["weight"] >= min_weight]
        shown.sort(key=lambda h: (h["line"], -h["weight"]))
        for h in shown:
            loc = "L%d" % h["line"] if h["line"] else "doc"
            out.append("  [%s] %-4s w%d %-22s '%s'" % (loc, "", h["weight"], h["category"], h["match"]))
            out.append("        fix: %s" % h["fix"])
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Scan text for AI writing patterns.")
    ap.add_argument("files", nargs="+", help="files to scan, or - for stdin")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--max-score", type=float, default=None, help="exit 1 if any score exceeds this")
    ap.add_argument("--min-weight", type=int, default=1, help="hide findings below this weight (1-3)")
    ap.add_argument("--no-code-mask", action="store_true", help="scan code blocks too")
    ap.add_argument("--quiet", action="store_true", help="summary only")
    args = ap.parse_args(argv)

    results = {}
    worst = 0.0
    for f in args.files:
        if f == "-":
            raw = sys.stdin.read()
            name = "<stdin>"
        else:
            with open(f, "r", encoding="utf-8", errors="replace") as fh:
                raw = fh.read()
            name = f
        res = scan(raw, mask=not args.no_code_mask)
        results[name] = res
        worst = max(worst, res["score"])

    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=True))
    else:
        for name, res in results.items():
            print(render(name, res, args.min_weight, args.quiet))
            print()
    if args.max_score is not None and worst > args.max_score:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
