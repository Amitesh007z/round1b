import os
import json
import argparse
from datetime import datetime
from multiprocessing import Pool
from sentence_transformers import SentenceTransformer
from src.pdf_utils import extract_outline_from_pdf, extract_sections_with_text
from src.persona_analysis import extract_persona_and_task_keywords
from src.section_ranker import rank_sections, extract_top_subsections
from src.summarizer import summarize_text

def load_input(input_path: str) -> dict:
    with open(input_path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_output(output_path: str, data: dict):
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def process_pdf(pdf_path):
    outline_data = extract_outline_from_pdf(pdf_path)
    outline = outline_data["outline"]
    sections = extract_sections_with_text(pdf_path, outline)
    return sections

def main(input_json: str, output_json: str):
    input_data = load_input(input_json)
    documents = input_data["documents"]
    persona = input_data["persona"]
    job = input_data["job_to_be_done"]
    keywords = extract_persona_and_task_keywords(persona, job)
    embedder = SentenceTransformer('intfloat/e5-small')
    with Pool() as pool:
        all_sections = sum(pool.map(process_pdf, [d["filename"] for d in documents]), [])
    top_sections = rank_sections(all_sections, keywords, embedder, top_n=5)
    subsection_analysis = []
    for sec in top_sections:
        subs = extract_top_subsections(sec["text"], keywords, embedder, sec["page_number"], max_subs=50)
        all_subs = [sub["refined_text"] for sub in subs if sub["refined_text"].strip() and len(sub["refined_text"].split()) >= 10]
        merged_text = "\n".join(all_subs)
        if not merged_text or len(merged_text.split()) < 30:
            merged_text = sec["text"]
        summary = summarize_text(merged_text, embedder, keywords, num_sentences=3)
        if not summary or len(summary.split()) < 10:
            summary = sec["text"]
        subsection_analysis.append({
            "document": sec["document"],
            "refined_text": summary,
            "page_number": sec["page_number"]
        })
    output = {
        "metadata": {
            "input_documents": [d["filename"] for d in documents],
            "persona": persona["role"],
            "job_to_be_done": job["task"],
            "processing_timestamp": datetime.utcnow().isoformat() + "Z"
        },
        "extracted_sections": [
            {
                "document": sec["document"],
                "section_title": sec["section_title"],
                "importance_rank": idx + 1,
                "page_number": sec["page_number"]
            } for idx, sec in enumerate(top_sections)
        ],
        "subsection_analysis": subsection_analysis
    }
    save_output(output_json, output)
    print(f" Output written to {output_json}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    main(args.input, args.output)