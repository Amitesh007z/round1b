import re
from typing import Dict, List, Set

try:
    import spacy
    nlp = spacy.load('en_core_web_sm')
except Exception:
    nlp = None

def extract_keywords(text: str) -> Set[str]:
    """
    Extracts keywords from a text using spaCy if available, else fallback to simple regex/stopword removal.
    """
    if not text:
        return set()
    text = text.strip()
    if nlp:
        doc = nlp(text)
        
        keywords = set(chunk.text.lower() for chunk in doc.noun_chunks)
        keywords |= set(ent.text.lower() for ent in doc.ents)
       
        keywords |= set(token.lemma_.lower() for token in doc if token.pos_ in {"NOUN", "PROPN", "ADJ"} and not token.is_stop)
        return set(kw for kw in keywords if len(kw) > 2)
    # Fallback: simple split, remove stopwords
    stopwords = set([
        "the", "and", "of", "in", "to", "for", "with", "on", "by", "is", "as", "at", "from", "an", "be", "are", "or", "that", "this", "it", "a", "i", "you", "we", "he", "she", "they", "them", "his", "her", "their", "our", "your", "was", "were", "has", "have", "had", "do", "does", "did", "but", "if", "so", "not", "can", "will", "would", "should", "could"
    ])
    words = re.findall(r"\b\w+\b", text.lower())
    return set(w for w in words if w not in stopwords and len(w) > 2)

def extract_persona_and_task_keywords(persona: Dict, job_to_be_done: Dict) -> Set[str]:
    """
    Given persona and job-to-be-done dicts, extract a set of focus keywords.
    """
    persona_text = " ".join(str(v) for v in persona.values())
    job_text = " ".join(str(v) for v in job_to_be_done.values())
    keywords = extract_keywords(persona_text)
    keywords |= extract_keywords(job_text)
    return keywords
