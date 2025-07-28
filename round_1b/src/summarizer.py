import re
import numpy as np
from sentence_transformers import SentenceTransformer
from spellchecker import SpellChecker

spell = SpellChecker()

def cosine_sim(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def summarize_text(text, embedder, keywords, num_sentences=3):
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())

    if not sentences or len(sentences) <= num_sentences:
        return text

    keyword_str = " ".join(keywords)
    keyword_emb = embedder.encode([keyword_str])[0]

    sentence_embs = embedder.encode(sentences)

    similarities = [cosine_sim(keyword_emb, emb) for emb in sentence_embs]

    top_indices = np.argsort(similarities)[-num_sentences:][::-1]

    summary_sentences = [sentences[i] for i in sorted(top_indices)]

    corrected_summary = " ".join(
        (spell.correction(word) or word) for word in " ".join(summary_sentences).split()
    )

    return corrected_summary