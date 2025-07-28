import re
from typing import Dict, Set

common_words = set(["the", "be", "to", "of", "and", "a", "in", "that", "have", "it", "for", "not", "on", "with", "he", "as", "you", "do", "at", "this", "but", "his", "by", "from", "they", "we", "say", "her", "she", "or", "an", "will", "my", "one", "all", "would", "there", "their", "what", "so", "up", "out", "if", "about", "who", "get", "which", "go", "me", "when", "make", "can", "like", "time", "no", "just", "him", "know", "take", "people", "into", "year", "your", "good", "some", "could", "them", "see", "other", "than", "then", "now", "look", "only", "come", "its", "over", "think", "also", "back", "after", "use", "two", "how", "our", "work", "first", "well", "way", "even", "new", "want", "because", "any", "these", "give", "day", "most", "us"])

def extract_keywords(text: str) -> Set[str]:
    if not text:
        return set()
    text = text.strip().lower()
    try:
        import spacy
        nlp = spacy.load('en_core_web_sm')
        doc = nlp(text)
        keywords = set(chunk.text.lower() for chunk in doc.noun_chunks if len(chunk.text) > 2)
        keywords |= set(ent.text.lower() for ent in doc.ents if len(ent.text) > 2)
        keywords |= set(token.lemma_.lower() for token in doc if token.pos_ in {"NOUN", "PROPN", "ADJ", "VERB"} and not token.is_stop and len(token.text) > 2)
    except ImportError:
        words = re.findall(r"\b\w+\b", text)
        keywords = set()
        for i in range(len(words) - 1):
            bigram = f"{words[i]} {words[i+1]}"
            if all(w not in common_words for w in bigram.split()) and len(bigram) > 5:
                keywords.add(bigram)
        keywords |= set(w for w in words if w not in common_words and len(w) > 2)
    return keywords

def extract_persona_and_task_keywords(persona: Dict, job_to_be_done: Dict) -> Set[str]:
    persona_text = " ".join(str(v).lower() for v in persona.values() if v)
    job_text = " ".join(str(v).lower() for v in job_to_be_done.values() if v)
    keywords = extract_keywords(persona_text)
    keywords |= extract_keywords(job_text)
    return keywords