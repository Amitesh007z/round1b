import os
import json
import re
from pathlib import Path
import fitz
from collections import Counter, defaultdict
from langdetect import detect, DetectorFactory
from statistics import median, mode
import numpy as np
from sklearn.cluster import DBSCAN
import networkx as nx

DetectorFactory.seed = 0

def is_mostly_ascii(text):
    return sum(1 for c in text if ord(c) < 128) / max(1, len(text)) > 0.85

def looks_english(text):
    common_words = ["the", "and", "of", "in", "to", "for", "with", "on", "by", "is", "as", "at", "from", "an", "be", "are", "or", "that", "this", "it"]
    text_lower = text.lower()
    return is_mostly_ascii(text) and any(word in text_lower for word in common_words)

def clean_heading(text):
    if not text or len(text.strip()) < 3:
        return None
    if not re.search(r"[a-zA-Z]", text):
        return None
    return text.strip()

def detect_language_efficient(text):
    if len(text) < 10:
        return "unknown"
    try:
        lang = detect(text)
        if lang != "en" and looks_english(text):
            return "en"
        return lang
    except:
        return "unknown"

def is_probable_form_field(text):
    words = text.split()
    if len(words) > 2 and sum(len(w) <= 3 for w in words) / len(words) > 0.5:
        return True
    if text.count(":") > 1:
        return True
    if re.match(r"^[A-Za-z0-9_ ]+:$", text.strip()):
        return True
    return False

def is_heading_candidate(text, is_bold, size, heading_sizes, repeated_lines):
    if not text:
        return False
    if size not in heading_sizes:
        return False
    if not is_bold and size < min(heading_sizes):
        return False
    if len(text) < 4 or len(text.split()) < 1:
        return False
    if text.strip()[-1:] in ".,:;!?":
        return False
    if text.islower():
        return False
    if re.match(r"^[•\-\u2022]", text.strip()):
        return False
    if sum(c.isdigit() for c in text) > len(text) // 2:
        return False
    if sum(not c.isalnum() and not c.isspace() for c in text) > len(text) // 2:
        return False
    stopwords = set(["the", "and", "of", "in", "to", "for", "with", "on", "by", "is", "as", "at", "from", "an", "be", "are", "or", "that", "this", "it"])
    words = [w.lower() for w in text.split()]
    if len(words) > 2 and sum(w in stopwords for w in words) / len(words) > 0.7:
        return False
    if text in repeated_lines:
        return False
    if is_probable_form_field(text):
        return False
    return True


def extract_title_and_title_lines(doc):
    first_page = doc[0]
    blocks = first_page.get_text("dict")["blocks"]
    candidates = []
    title_lines = set()
    max_size = 0
    for b in blocks:
        for line in b.get("lines", []):
            spans = [span for span in line.get("spans", []) if span["text"].strip()]
            line_text = " ".join(span["text"].strip() for span in spans)
            size = max([span.get("size", 0) for span in spans], default=0)
            y0 = min([span.get("bbox", [0, 0, 0, 0])[1] for span in spans], default=999)
            if size >= max_size * 0.85 and y0 < 200:
                title_lines.add(line_text.strip().lower())


    for b in blocks:
        for line in b.get("lines", []):
            line_text = " ".join([span["text"].strip() for span in line.get("spans", []) if span["text"].strip()])
            if not line_text or len(line_text) < 4:
                continue
            size = max([span.get("size", 0) for span in line.get("spans", [])])
            if abs(size - max_size) < 0.1:
                title_lines.add(line_text.strip().lower())

    title = "  ".join([line for line in title_lines])
    if not title:
        title = doc.metadata.get("title")
        if title and title.lower() != "untitled":
            title = title.strip()
        else:
            title = os.path.basename(doc.name).strip()
    return title, title_lines

def get_body_size(font_sizes):

    mean = np.mean(font_sizes)
    std = np.std(font_sizes)
    return round(mean + 0.25 * std, 1)


def assign_heading_levels(font_sizes, body_size):

    heading_sizes = sorted(set([fs for fs in font_sizes if fs > body_size]), reverse=True)
    size_to_level = {}
    for idx, fs in enumerate(heading_sizes):
        if idx == 0:
            size_to_level[fs] = 'H1'
        elif idx == 1:
            size_to_level[fs] = 'H2'
        elif idx == 2:
            size_to_level[fs] = 'H3'
        else:
            size_to_level[fs] = f'H{idx+1}'
    return size_to_level, heading_sizes

def find_repeated_lines(line_info, num_pages):
    text_page_map = defaultdict(set)
    for line in line_info:
        text_page_map[line["text"]].add(line["page"])
    repeated = set()
    for text, pages in text_page_map.items():
        if len(pages) > max(2, num_pages // 2):
            repeated.add(text)
    return repeated

def is_numbered_heading(text):
    return bool(re.match(r'^\d+(\.\d+)+', text.strip()))

def get_numbering_level(text):
    m = re.match(r'^(\d+)(\.\d+)+', text.strip())
    if m:
        dots = text.strip().split()[0].count('.')
        return dots + 1
    return None

def merge_multiline_headings(candidates):
    merged = []
    i = 0
    while i < len(candidates):
        curr = candidates[i]
        j = i + 1
        lines = [curr["text"]]
        while j < len(candidates) and candidates[j]["size"] == curr["size"] and abs(candidates[j]["y0"] - curr["y0"]) < 3 * curr["size"] and candidates[j]["page"] == curr["page"]:
            lines.append(candidates[j]["text"])
            j += 1
        merged_text = " ".join(lines)
        merged.append({**curr, "text": merged_text})
        i = j
    return merged

def gnn_refine_headings(candidates):
    
    G = nx.Graph()
    for idx, cand in enumerate(candidates):
        G.add_node(idx, **cand)
    for i in range(len(candidates)):
        for j in range(i+1, len(candidates)):
            c1, c2 = candidates[i], candidates[j]
            if c1["page"] == c2["page"] and abs(c1["size"] - c2["size"]) < 1.1 and abs(c1["y0"] - c2["y0"]) < 2 * c1["size"]:
                G.add_edge(i, j)

    refined = []
    for idx in G.nodes:
        node = G.nodes[idx]
        degree = G.degree[idx]
        if degree >= 2 or node["is_bold"]:
            refined.append(node)
    return refined

def get_dbscan_heading_sizes(font_sizes):
    arr = np.array(font_sizes).reshape(-1, 1)
    db = DBSCAN(eps=1.5, min_samples=5).fit(arr)
    labels = db.labels_
    unique, counts = np.unique(labels, return_counts=True)
    body_label = unique[np.argmax(counts)]
    dbscan_headings = set([fs for fs, l in zip(font_sizes, labels) if l != body_label and l != -1])
    return dbscan_headings

def get_histogram_heading_sizes(font_sizes, body_size):
    return set([fs for fs in font_sizes if fs > body_size + 0.5])

def extract_outline_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    title, title_lines = extract_title_and_title_lines(doc)
    headings = []
    font_sizes = []
    line_info = []
    seen_headings = set()
    for page_num, page in enumerate(doc, start=1):
        blocks = page.get_text("dict")["blocks"]
        for b in blocks:
            for line in b.get("lines", []):
                line_text = " ".join([span["text"].strip() for span in line.get("spans", []) if span["text"].strip()])
                if not line_text:
                    continue
                max_size = max([span.get("size", 0) for span in line.get("spans", [])])
                is_bold = any(["bold" in span.get("font", "").lower() for span in line.get("spans", [])])
                y0 = min([span.get("bbox", [0, 0, 0, 0])[1] for span in line.get("spans", [])])
                font_sizes.append(max_size)
                line_info.append({
                    "text": line_text,
                    "size": max_size,
                    "is_bold": is_bold,
                    "y0": y0,
                    "page": page_num
                })
    body_size = get_body_size(font_sizes)
    heading_sizes = sorted(set([fs for fs in font_sizes if fs > body_size]), reverse=True)
    size_to_level = {}
    for idx, fs in enumerate(heading_sizes):
        if idx == 0:
            size_to_level[fs] = 'H1'
        elif idx == 1:
            size_to_level[fs] = 'H2'
        elif idx == 2:
            size_to_level[fs] = 'H3'
        else:
            size_to_level[fs] = f'H{idx+1}'
    dbscan_headings = get_dbscan_heading_sizes(font_sizes)
    hist_headings = get_histogram_heading_sizes(font_sizes, body_size)
    repeated_lines = find_repeated_lines(line_info, len(doc))
    raw_headings = []
    for line in line_info:
        text = clean_heading(line["text"])
        if not text:
            continue
        if is_numbered_heading(text):
            numbering_level = get_numbering_level(text)
            font_level = size_to_level.get(line["size"], 'H1')
            if not hasattr(extract_outline_from_pdf, "last_level_size"):
                extract_outline_from_pdf.last_level_size = {}
            last_level_size = extract_outline_from_pdf.last_level_size
            if numbering_level:
                promote = False
                for lvl, sz in last_level_size.items():
                    if line["size"] > sz and lvl < numbering_level:
                        promote = True
                        break
                if promote or numbering_level == 1:
                    level = font_level
                else:
                    if numbering_level == 1:
                        level = 'H1'
                    elif numbering_level == 2:
                        level = 'H2'
                    elif numbering_level == 3:
                        level = 'H3'
                    else:
                        level = f'H{numbering_level}'
                last_level_size[numbering_level] = line["size"]
                if line["page"] == 1 and text.strip().lower() in title_lines:
                    continue
                heading_key = (level, text.strip().lower(), line["page"])
                if heading_key in seen_headings:
                    continue
                seen_headings.add(heading_key)
                lang = detect_language_efficient(text)
                raw_headings.append({
                    "level": level,
                    "text": text,
                    "page": line["page"],
                    "lang": lang,
                    "size": line["size"],
                    "numbering_level": numbering_level
                })
                continue
        if line["size"] <= body_size:
            continue
        if not (line["size"] in heading_sizes or line["size"] in dbscan_headings or line["size"] in hist_headings):
            continue
        if not is_heading_candidate(text, line["is_bold"], line["size"], heading_sizes, repeated_lines):
            continue
        score = 0
        if line["is_bold"]:
            score += 1
        if line["y0"] < 150:
            score += 1
        if len(text.split()) <= 5:
            score += 1
        if score < 2:
            continue
        if line["page"] == 1 and text.strip().lower() in title_lines:
            continue
        heading_key = (size_to_level.get(line["size"], 'H1'), text.strip().lower(), line["page"])
        if heading_key in seen_headings:
            continue
        seen_headings.add(heading_key)
        level = size_to_level.get(line["size"], 'H1')
        lang = detect_language_efficient(text)
        raw_headings.append({
            "level": level,
            "text": text,
            "page": line["page"],
            "lang": lang,
            "size": line["size"],
            "numbering_level": None
        })

    def get_parent_numbering(num):
        if not num or '.' not in num:
            return None
        return '.'.join(num.split('.')[:-1])

    numbering_to_idx = {}
    for idx, h in enumerate(raw_headings):
        m = re.match(r'^(\d+(?:\.\d+)+)', h["text"].strip())
        if m:
            numbering_to_idx[m.group(1)] = idx

    changed = True
    while changed:
        changed = False
        for idx in reversed(range(len(raw_headings))):
            h = raw_headings[idx]
            m = re.match(r'^(\d+(?:\.\d+)+)', h["text"].strip())
            if m:
                parent_num = get_parent_numbering(m.group(1))
                if parent_num and parent_num in numbering_to_idx:
                    parent_idx = numbering_to_idx[parent_num]
                    parent = raw_headings[parent_idx]
                    parent_level_num = int(parent["level"][1:]) if parent["level"].startswith('H') else 1
                    child_level_num = int(h["level"][1:]) if h["level"].startswith('H') else 1
                    if parent_level_num >= child_level_num:
                        parent["level"] = f'H{max(1, child_level_num-1)}'
                        changed = True
    headings = [{k: v for k, v in h.items() if k in ["level", "text", "page", "lang"]} for h in raw_headings]
    if hasattr(extract_outline_from_pdf, "last_level_size"):
        del extract_outline_from_pdf.last_level_size
    return {
        "title": title,
        "outline": headings
    }

def is_true_heading(text, size, is_bold, min_size, max_size):
    if size < min_size or size > max_size:
        return False

    if not is_bold and not text.istitle() and not text.isupper():
        return False

    if text.strip().startswith(("-", "•", "*")):
        return False
    if re.match(r"^[0-9]+\. ", text.strip()):
        return False

    if len(text.split()) < 3:
        return False
    return True

def extract_sections_with_text(pdf_path, outline):
    """
    Given a PDF path and its outline (list of headings with page numbers),
    extract the full text for each section (from heading to next heading or end of doc).
    Only use real detected headings as section titles.
    Returns a list of dicts: {document, section_title, page_number, text}
    """
    import fitz
    doc = fitz.open(pdf_path)
    sections = []
    if not outline:
        return sections

    font_sizes = [h.get("size") for h in outline if h.get("size")]
    if font_sizes:
        min_size, max_size = min(font_sizes), max(font_sizes)
        most_common_size, _ = Counter(font_sizes).most_common(1)[0]
        filtered_outline = [h for h in outline if is_true_heading(h["text"], h.get("size", 0), h.get("is_bold", False), min_size, max_size) and h.get("size") == most_common_size]
    else:
        levels = [h.get("level") for h in outline if h.get("level")]
        if levels:
            most_common_level, _ = Counter(levels).most_common(1)[0]
            filtered_outline = [h for h in outline if h.get("level") == most_common_level]
        else:
            filtered_outline = outline

    heading_locs = []
    for idx, h in enumerate(filtered_outline):
        page_num = h["page"] - 1
        heading_text = h["text"].strip()
        y0 = None
        page = doc[page_num]
        blocks = page.get_text("dict")["blocks"]
        for b in blocks:
            for line in b.get("lines", []):
                line_text = " ".join([span["text"].strip() for span in line.get("spans", []) if span["text"].strip()])
                if line_text.strip() == heading_text:
                    y0 = min([span.get("bbox", [0, 0, 0, 0])[1] for span in line.get("spans", [])])
                    break
            if y0 is not None:
                break
        heading_locs.append({"idx": idx, "page": page_num, "y0": y0 if y0 is not None else 0, "heading_text": heading_text})

    for i, h in enumerate(filtered_outline):
        if not h["text"] or len(h["text"].strip()) < 3:
            continue
        start = heading_locs[i]
        end = heading_locs[i+1] if i+1 < len(heading_locs) else None
        texts = []
        for p in range(start["page"], doc.page_count if end is None else end["page"]+1):
            page = doc[p]
            blocks = page.get_text("dict")["blocks"]
            for b in blocks:
                for line in b.get("lines", []):
                    y0 = min([span.get("bbox", [0, 0, 0, 0])[1] for span in line.get("spans", [])])
                    line_text = " ".join([span["text"].strip() for span in line.get("spans", []) if span["text"].strip()])
                    if p == start["page"] and y0 < start["y0"]:
                        continue
                    if end and p == end["page"] and y0 >= end["y0"]:
                        continue
                    if p == start["page"] and y0 == start["y0"] and line_text.strip() == h["text"].strip():
                        continue
                    texts.append(line_text)
        section_text = "\n".join([t for t in texts if t.strip()])
        if h["text"].strip() and section_text.strip():
            sections.append({
                "document": os.path.basename(pdf_path),
                "section_title": h["text"],
                "page_number": h["page"],
                "text": section_text
            })
    return sections

def process_pdfs():
    input_dir = Path("./inputs")
    output_dir = Path("./output")
    output_dir.mkdir(parents=True, exist_ok=True)
    pdf_files = list(input_dir.glob("*.pdf"))
    print(f"Found {len(pdf_files)} PDF(s): {[f.name for f in pdf_files]}")
    for pdf_file in pdf_files:
        print(f"🔍 Processing {pdf_file.name}")
        try:
            data = extract_outline_from_pdf(pdf_file)
            output_file = output_dir / f"{pdf_file.stem}.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f" Output written to {output_file.name}")
        except Exception as e:
            print(f" Error processing {pdf_file.name}: {e}")

if __name__ == "__main__":
    print(" Starting improved PDF outline extraction...")
    process_pdfs()
    print(" All PDFs processed.")