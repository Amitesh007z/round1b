import re
from typing import List, Dict, Any, Set
from sentence_transformers import SentenceTransformer
import numpy as np

# Use e5-small if available, else fallback to all-MiniLM-L6-v2
try:
    embedder = SentenceTransformer('intfloat/e5-small')
except Exception:
    embedder = SentenceTransformer('all-MiniLM-L6-v2')

def cosine_sim(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def rank_sections(sections, keywords, top_n=5, doc_index=None):
    if not sections or not keywords:
        return []
    persona_job = " ".join(keywords)
    query_emb = embedder.encode([persona_job])[0]
    doc_scores = []
    for s in sections:
        title = s['section_title']
        text = s['text']
        title_emb = embedder.encode([title])[0]
        text_emb = embedder.encode([text])[0] if text.strip() else title_emb
        # Weighted average: title and text
        sim_score = 0.6 * cosine_sim(query_emb, title_emb) + 0.4 * cosine_sim(query_emb, text_emb)
        doc_scores.append((s, sim_score))
    # Sort and enforce document diversity
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
    # If not enough, fill with next best regardless of doc
    if len(selected) < top_n:
        for section, score in ranked:
            if section not in selected and len(section.get('text', '').split()) >= 30:
                section['importance_score'] = float(score)
                section['importance_rank'] = len(selected) + 1
                selected.append(section)
            if len(selected) == top_n:
                break
    return selected

def extract_top_subsections(section_text: str, keywords: Set[str], page: int, max_subs: int = 3) -> List[Dict[str, Any]]:
    """
    Split section text into sub-sections (paragraphs, bullets, or numbered lists),
    prioritize those that are lists or actionable, and rank by semantic relevance to keywords.
    Return top N.
    """
    if not section_text:
        return []
    # Split by paragraphs, bullets, or numbered lists
    # Bullets: lines starting with -, •, *, or numbers
    bullet_pattern = re.compile(r"^(\s*[-•*\d+\.]+\s+)")
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
    # Fallback: if no bullets, split by double newlines
    if not subs or all(len(s.split()) < 8 for s in subs):
        subs = re.split(r"\n\s*\n|\n\s*[-•*]\s*", section_text)
        subs = [s.strip() for s in subs if len(s.strip()) > 20]
    # Prioritize sub-sections that are lists or have multiple bullets
    list_like = [s for s in subs if re.search(r"[-•*]\s+", s) or re.search(r"\d+\.\s+", s)]
    if list_like:
        subs = list_like + [s for s in subs if s not in list_like]
    # Remove duplicates
    seen = set()
    unique_subs = []
    for s in subs:
        if s not in seen:
            unique_subs.append(s)
            seen.add(s)
    subs = unique_subs
    # Rank by embedding similarity
    keyword_str = " ".join(keywords)
    scored = [(s, cosine_sim(embedder.encode([keyword_str])[0], embedder.encode([s])[0])) for s in subs]
    ranked = sorted(scored, key=lambda x: -x[1])
    result = []
    for sub, score in ranked[:max_subs]:
        result.append({
            "refined_text": sub,
            "page_number": page,
            "score": float(score)
        })
    return result

