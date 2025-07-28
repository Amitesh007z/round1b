FROM python:3.10-slim

WORKDIR /app

# Install only necessary system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model
RUN python -m spacy download en_core_web_sm

# Pre-download the sentence transformer model
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('intfloat/e5-small')"

# Copy application files
COPY src/ ./src/
COPY challenge1b_input.json ./
COPY challenge1b_output.json ./

ENTRYPOINT ["python", "main.py"]
