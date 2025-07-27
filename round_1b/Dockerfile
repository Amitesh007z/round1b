FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for PyMuPDF and spaCy
RUN apt-get update && apt-get install -y build-essential libglib2.0-0 libsm6 libxrender1 libxext6 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model at build time
RUN python -m spacy download en_core_web_sm

# Download summarization and embedding models at build time
RUN python -c "from transformers import pipeline; pipeline('summarization', model='sshleifer/distilbart-cnn-12-6')"
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('intfloat/e5-small')"
# Fallback for embedding model if e5-small fails
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

COPY src/ ./src/
COPY . /app/

ENTRYPOINT ["python", "src/main.py"]
