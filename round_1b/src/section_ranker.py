import re
from typing import List, Dict, Any, Set
import numpy as np
from collections import defaultdict

def cosine_sim(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def rank_sections(sections, keywords, embedder, top_n=5):
    if not sections or not keywords:
        return []
    persona_job = " ".join(keywords)
    query_emb = embedder.encode([persona_job])[0]
    doc_scores = []
    doc_sections = defaultdict(list)
    for s in sections:
        doc_sections[s['document']].append(s)
    for doc, secs in doc_sections.items():
        for idx, s in enumerate(secs):
            s['index'] = idx
            s['num_sections'] = len(secs)
            title = s['section_title']
            text = s['text']
            title_emb = embedder.encode([title])[0]
            text_emb = embedder.encode([text])[0] if text.strip() else title_emb
            sim_score = 0.6 * cosine_sim(query_emb, title_emb) + 0.4 * cosine_sim(query_emb, text_emb)
            position_score = 1 - (s['index'] / s['num_sections'])
            final_score = sim_score + 0.1 * position_score
            doc_scores.append((s, final_score))
    ranked = sorted(doc_scores, key=lambda x: -x[1])
    selected = []
    used_docs = set()
    for section, score in ranked:
        doc = section['document']
        if doc not in used_docs and len(section.get('text', '').split()) >= 30:
            section['importance_score'] = float(score)
            section['importance_rank'] = len(selected) + 1
            selected.append(section)
            used_docs.add(doc)
        if len(selected) == top_n:
            break
    if len(selected) < top_n:
        for section, score in ranked:
            if section not in selected and len(section.get('text', '').split()) >= 30:
                section['importance_score'] = float(score)
                section['importance_rank'] = len(selected) + 1
                selected.append(section)
            if len(selected) == top_n:
                break
    return selected

def extract_top_subsections(section_text: str, keywords: Set[str], embedder, page: int, max_subs: int = 5) -> List[Dict[str, Any]]:
    if not section_text:
        return []
    bullet_pattern = re.compile(r"^\s*([•\-\*\d+\.]|\(\w+\)|[\[\(]\d+[\]\)])+\s+")
    lines = section_text.splitlines()
    subs = []
    curr = []
    for line in lines:
        if bullet_pattern.match(line) or (curr and not line.strip()):
            if curr:
                subs.append(" ".join(curr).strip())
                curr = []
        if line.strip():
            curr.append(line.strip())
    if curr:
        subs.append(" ".join(curr).strip())
    if not subs or all(len(s.split()) < 5 for s in subs):
        subs = [s.strip() for s in re.split(r"\n\s*\n|\n\s*[-•*]\s*", section_text) if len(s.strip()) > 15]
    list_like = [s for s in subs if re.search(r"[-•*]\s+", s) or re.search(r"\d+\.\s+", s)]
    if list_like:
        subs = list_like + [s for s in subs if s not in list_like]
    seen = set()
    unique_subs = [s for s in subs if s not in seen and not seen.add(s) and len(s.split()) >= 5]
    if not unique_subs:
        return [{"refined_text": section_text.strip(), "page_number": page, "score": 1.0}]
    keyword_str = " ".join(keywords)
    kw_emb = embedder.encode([keyword_str])[0]
    scored = []
    for s in unique_subs:
        s_emb = embedder.encode([s])[0]
        score = cosine_sim(s_emb, kw_emb)
        if not any(cosine_sim(s_emb, embedder.encode([other])[0]) > 0.95 for other, _ in scored):
            scored.append((s, score))
    ranked = sorted(scored, key=lambda x: -x[1])
    result = []
    for sub, score in ranked[:max_subs]:
        result.append({
            "refined_text": sub,
            "page_number": page,
            "score": float(score)
        })
    return result