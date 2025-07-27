from transformers import pipeline, AutoTokenizer

summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")
tokenizer = AutoTokenizer.from_pretrained("sshleifer/distilbart-cnn-12-6")
MAX_TOKENS = 1024

def chunk_text(text, chunk_size=800, overlap=100):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i+chunk_size])
        if chunk:
            chunks.append(chunk)
    return chunks

def num_tokens(text):
    return len(tokenizer.encode(text, truncation=False))

def summarize_text(text, persona=None, job=None, prompt_type="summarize", max_length=None, min_length=None):
    if not text or len(text.split()) < 30:
        return text

    prompt = prompt_type
    if persona:
        prompt += f" for a {persona}"
    if job:
        prompt += f" whose task is to {job}"

    def make_input(t):
        return f"{prompt}: {t}"

    def num_tokens(text):
        return len(tokenizer.encode(text, truncation=False))

    input_text = make_input(text)
    if num_tokens(input_text) > MAX_TOKENS:
        # Chunk and summarize
        chunks = chunk_text(text, chunk_size=600, overlap=100)
        summaries = []
        for chunk in chunks:
            summaries.append(
                summarize_text(chunk, persona=persona, job=job, prompt_type=prompt_type, max_length=200, min_length=50)
            )
        merged = " ".join(summaries)
        merged_input = make_input(merged)
        # Aggressively truncate merged summary if still too long
        while num_tokens(merged_input) > MAX_TOKENS:
            # Truncate merged summary to fit within MAX_TOKENS minus prompt tokens
            prompt_tokens = len(tokenizer.encode(f"{prompt}: ", truncation=False))
            allowed = MAX_TOKENS - prompt_tokens
            merged_tokens = tokenizer.encode(merged, truncation=False)[:allowed]
            merged = tokenizer.decode(merged_tokens)
            merged_input = make_input(merged)
        return summarize_text(merged, persona=persona, job=job, prompt_type=prompt_type, max_length=256, min_length=100)

    # Final check: truncate input_text to MAX_TOKENS if needed
    if num_tokens(input_text) > MAX_TOKENS:
        prompt_tokens = len(tokenizer.encode(f"{prompt}: ", truncation=False))
        allowed = MAX_TOKENS - prompt_tokens
        text_tokens = tokenizer.encode(text, truncation=False)[:allowed]
        text = tokenizer.decode(text_tokens)
        input_text = make_input(text)

    input_len = num_tokens(input_text)
    if not max_length:
        max_length = min(256, max(40, int(0.8 * input_len)))
    max_length = min(max_length, input_len)
    if min_length is None:
        min_length = min(max_length - 1, max(20, int(0.3 * max_length)))
    if min_length >= max_length:
        min_length = max(10, max_length - 1)

    try:
        summary = summarizer(input_text, max_length=max_length, min_length=min_length, do_sample=False)
        return summary[0]['summary_text']
    except Exception as e:
        print(f"Summarization failed: {e}")
        return text