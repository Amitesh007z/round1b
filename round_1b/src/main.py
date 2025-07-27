import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import re

from pdf_utils import extract_outline_from_pdf, extract_sections_with_text
from persona_analysis import extract_persona_and_task_keywords
from section_ranker import rank_sections, extract_top_subsections
from summarizer import summarize_text

def load_input(input_path: str) -> Dict[str, Any]:
    with open(input_path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_output(output_path: str, data: Dict[str, Any]):
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def main(input_json: str, output_json: str):
    input_data = load_input(input_json)
    documents = input_data["documents"]
    persona = input_data["persona"]
    job = input_data["job_to_be_done"]
    keywords = extract_persona_and_task_keywords(persona, job)
    all_sections = []
    for doc in documents:
        pdf_path = doc["filename"]
        outline_data = extract_outline_from_pdf(pdf_path)
        outline = outline_data["outline"]
        sections = extract_sections_with_text(pdf_path, outline)
        all_sections.extend(sections)
    # Build doc_index for first heading in each document
    doc_index = {}
    for idx, section in enumerate(all_sections):
        doc = section["document"]
        if doc not in doc_index:
            doc_index[doc] = idx
    # Rank sections with doc_index
    top_sections = rank_sections(all_sections, keywords, top_n=5, doc_index=doc_index)
    # Sub-section analysis
    subsection_analysis = []
    persona_role = persona.get("role", "")
    job_task = job.get("task", "")
    for sec in top_sections:
        subs = extract_top_subsections(sec["text"], keywords, sec["page_number"], max_subs=50)
        all_subs = [sub["refined_text"] for sub in subs if sub["refined_text"].strip()]
        merged_text = "\n".join(all_subs)
        # If merged_text is too short, use the full section text
        if not merged_text or len(merged_text.split()) < 30:
            merged_text = sec["text"]
        # If the section is a list/recipe (many short lines or bullets), output extractive
        lines = merged_text.splitlines()
        num_bullets = sum(1 for l in lines if l.strip().startswith(("-", "•", "*", "1.", "2.", "3.")))
        avg_line_len = sum(len(l.split()) for l in lines) / max(1, len(lines))
        if num_bullets > 2 or avg_line_len < 15 or len(lines) > 5:
            # Output extractive: just the lines from the PDF section
            summary = "\n".join([l.strip() for l in lines if l.strip()])
        else:
            # For long, narrative text, use the summarizer
            summary = summarize_text(
                merged_text,
                persona=persona_role,
                job=job_task,
                prompt_type="summarize in detail",
                max_length=256,
                min_length=100
            )
        # If summary is still empty, fallback to section text
        if not summary or len(summary.split()) < 10:
            summary = sec["text"]
        subsection_analysis.append({
            "document": sec["document"],
            "refined_text": summary,
            "page_number": sec["page_number"]
        })
    # Output JSON
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
                "importance_rank": sec["importance_rank"],
                "page_number": sec["page_number"]
            } for sec in top_sections
        ],
        "subsection_analysis": subsection_analysis
    }
    save_output(output_json, output)
    print(f"✅ Output written to {output_json}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Path to challenge1b_input.json")
    parser.add_argument("--output", required=True, help="Path to challenge1b_output.json")
    args = parser.parse_args()
    main(args.input, args.output)
