# Round 1B: Persona-Driven Document Intelligence

## 🎯 Challenge Theme
**"Connect What Matters — For the User Who Matters"**

## 📋 Challenge Brief

You will build a system that acts as an intelligent document analyst, extracting and prioritizing the most relevant sections from a collection of documents based on a specific persona and their job-to-be-done.

### Input Specification
1. **Document Collection**: 3-10 related PDFs
2. **Persona Definition**: Role description with specific expertise and focus areas
3. **Job-to-be-Done**: Concrete task the persona needs to accomplish

### Key Requirements
Document collection, persona and job-to-be-done can be very diverse. So, the solution that teams need to build needs to be **generic to generalize to this variety**.

- **Documents can be from any domain**: Research papers, school/college books, financial reports, news articles, etc.
- **Persona can be very diverse**: Researcher, Student, Salesperson, Journalist, Entrepreneur, etc.
- **Job-to-be-Done**: Related to the persona (e.g., Provide a literature review for a given topic, What should I study for Organic Chemistry, Summarize the financials of corporation XYZ, etc.)

### Technical Constraints
- **Must run on CPU only**
- **Model size ≤ 1GB**
- **Processing time ≤ 60 seconds** for document collection (3-5 documents)
- **No internet access allowed during execution**

---

# PDF Document Analysis and Content Extraction System

## 📋 Overview

This project is an intelligent PDF document analysis system that extracts, ranks, and summarizes relevant content from multiple PDF documents based on a specific persona and job-to-be-done scenario. The system uses advanced NLP techniques including sentence embeddings, semantic similarity, and content ranking to provide targeted information extraction.

## 🚨 Important Setup Instructions

### 1. Input File Structure
You **MUST** have a `challenge1b_input.json` file in the root directory with this structure:

```json
{
  "challenge_info": {
    "challenge_id": "round_1b_001",
    "test_case_name": "menu_planning",
    "description": "Dinner menu planning"
  },
  "documents": [
    {
      "filename": "inputs/Breakfast Ideas.pdf",
      "title": "Breakfast Ideas"
    }
  ],
  "persona": {
    "role": "Food Contractor"
  },
  "job_to_be_done": {
    "task": "Prepare a vegetarian buffet-style dinner menu for a corporate gathering, including gluten-free items."
  }
}
```

### 2. PDF Documents
Place your PDF documents in the `inputs/` directory. The filenames must match exactly with what's specified in your `challenge1b_input.json` file.

### 3. Quick Start (IMPORTANT)
```bash
# 1. Build the Docker image
docker build -t pdf-analyzer .

# 2. Run the system
docker run -v $(pwd):/app pdf-analyzer python main.py --input challenge1b_input.json --output challenge1b_output.json
```

## 🔧 Offline Model Setup (Optional)

For offline execution without internet access, you can download models locally:

### 1. Download Models
```bash
# Run the model setup script
python setup_models.py
```

This will:
- Download spaCy model (`en_core_web_sm`) to `models/spacy/`
- Download sentence transformer model (`intfloat/e5-small`) to `models/sentence_transformers/`
- Create model configuration file

### 2. Git LFS Setup (For Large Models)
If you want to include models in your repository:

```bash
# Install Git LFS
git lfs install

# Track model files
git lfs track "models/**"
git lfs track "*.bin"
git lfs track "*.model"
git lfs track "*.pkl"

# Add and commit
git add .gitattributes
git add models/
git commit -m "Add offline models"
```

**Note**: Models are large files (~500MB). Consider if you really need them in the repository.

## 🎯 Use Case Examples

The system is designed for diverse scenarios:

### Academic Research
- **Documents**: 4 research papers on "Graph Neural Networks for Drug Discovery"
- **Persona**: PhD Researcher in Computational Biology
- **Job**: "Prepare a comprehensive literature review focusing on methodologies, datasets, and performance benchmarks"

### Business Analysis
- **Documents**: 3 annual reports from competing tech companies (2022-2024)
- **Persona**: Investment Analyst
- **Job**: "Analyze revenue trends, R&D investments, and market positioning strategies"

### Educational Content
- **Documents**: 5 chapters from organic chemistry textbooks
- **Persona**: Undergraduate Chemistry Student
- **Job**: "Identify key concepts and mechanisms for exam preparation on reaction kinetics"

### Food Service (Current Example)
- **Documents**: 9 recipe and menu PDFs
- **Persona**: Food Contractor
- **Job**: "Prepare a vegetarian buffet-style dinner menu for a corporate gathering, including gluten-free items"

## 🏗️ Architecture

The system consists of several key components:

### Core Modules

1. **PDF Utils** (`src/pdf_utils.py`)
   - Extracts document outlines and structure
   - Identifies headings, sections, and content hierarchy
   - Handles multi-language content detection
   - Processes font sizes and formatting for structure analysis

2. **Persona Analysis** (`src/persona_analysis.py`)
   - Extracts relevant keywords from persona and job descriptions
   - Uses spaCy NLP for entity recognition and keyword extraction
   - Identifies domain-specific terminology

3. **Section Ranker** (`src/section_ranker.py`)
   - Ranks document sections by relevance to the persona/job
   - Uses sentence embeddings for semantic similarity
   - Extracts top subsections from relevant content
   - Implements cosine similarity scoring

4. **Summarizer** (`src/summarizer.py`)
   - Creates concise summaries of extracted content
   - Uses keyword-based sentence ranking
   - Includes spell-checking for quality assurance

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Docker (recommended for consistent execution)

### Docker Setup (Recommended)

1. **Build the Docker image:**
   ```bash
   docker build -t pdf-analyzer .
   ```

2. **Run the container:**
   ```bash
   docker run -v $(pwd):/app pdf-analyzer python main.py --input challenge1b_input.json --output challenge1b_output.json
   ```

### Local Setup

1. **Clone and navigate to the project:**
   ```bash
   cd round_1b
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   ```

3. **Run the system:**
   ```bash
   python main.py --input challenge1b_input.json --output challenge1b_output.json
   ```

## 📁 Project Structure

```
round_1b/
├── main.py                          # Main execution script
├── requirements.txt                 # Python dependencies
├── Dockerfile                      # Docker configuration
├── setup_models.py                 # Model download script
├── challenge1b_input.json          # Input configuration (REQUIRED)
├── challenge1b_output.json         # Output results
├── approach_explanation.md         # Methodology explanation
├── SUBMISSION_CHECKLIST.md         # Submission verification
├── GITHUB_SUBMISSION_GUIDE.md      # Submission guide
├── .gitignore                      # Git exclusions
├── .gitattributes                  # Git LFS configuration
├── src/                           # Source code modules
│   ├── pdf_utils.py              # PDF processing utilities
│   ├── persona_analysis.py       # Persona and keyword analysis
│   ├── section_ranker.py         # Content ranking and extraction
│   ├── summarizer.py             # Text summarization
│   └── config.py                 # Configuration settings
├── models/                        # Model storage (optional)
│   ├── spacy/                    # spaCy models
│   ├── sentence_transformers/    # Sentence transformer models
│   └── model_config.json         # Model configuration
└── inputs/                       # PDF documents directory (REQUIRED)
    ├── Breakfast Ideas.pdf
    ├── Dinner Ideas - Mains_1.pdf
    ├── Dinner Ideas - Mains_2.pdf
    ├── Dinner Ideas - Mains_3.pdf
    ├── Dinner Ideas - Sides_1.pdf
    ├── Dinner Ideas - Sides_2.pdf
    ├── Dinner Ideas - Sides_3.pdf
    ├── Dinner Ideas - Sides_4.pdf
    └── Lunch Ideas.pdf
```

## 📊 Input Format

The system expects a JSON input file with the following structure:

```json
{
  "challenge_info": {
    "challenge_id": "round_1b_001",
    "test_case_name": "menu_planning",
    "description": "Dinner menu planning"
  },
  "documents": [
    {
      "filename": "inputs/Breakfast Ideas.pdf",
      "title": "Breakfast Ideas"
    }
  ],
  "persona": {
    "role": "Food Contractor"
  },
  "job_to_be_done": {
    "task": "Prepare a vegetarian buffet-style dinner menu for a corporate gathering, including gluten-free items."
  }
}
```

## 📈 Output Format

The system generates a structured JSON output:

```json
{
  "metadata": {
    "input_documents": ["inputs/Breakfast Ideas.pdf"],
    "persona": "Food Contractor",
    "job_to_be_done": "Prepare a vegetarian buffet-style dinner menu...",
    "processing_timestamp": "2024-01-01T12:00:00Z"
  },
  "extracted_sections": [
    {
      "document": "inputs/Dinner Ideas - Mains_1.pdf",
      "section_title": "Vegetarian Main Dishes",
      "importance_rank": 1,
      "page_number": 5
    }
  ],
  "subsection_analysis": [
    {
      "document": "inputs/Dinner Ideas - Mains_1.pdf",
      "refined_text": "Summarized content relevant to the task...",
      "page_number": 5
    }
  ]
}
```

## 🔧 Configuration

### Key Parameters

- **Top Sections**: Number of most relevant sections to extract (default: 5)
- **Max Subsections**: Maximum subsections per section (default: 50)
- **Summary Sentences**: Number of sentences in summaries (default: 3)
- **Minimum Text Length**: Minimum words required for content (default: 30)

### Model Settings

- **Embedding Model**: `intfloat/e5-small` (sentence transformers)
- **NLP Model**: `en_core_web_sm` (spaCy)
- **Similarity Metric**: Cosine similarity

## 🧠 How It Works

### 1. Document Processing
- Extracts document structure and outlines
- Identifies headings, sections, and content hierarchy
- Processes font sizes and formatting for structure analysis

### 2. Keyword Extraction
- Analyzes persona role and job requirements
- Extracts domain-specific keywords using NLP
- Identifies relevant entities and terminology

### 3. Content Ranking
- Computes semantic similarity between keywords and content
- Ranks sections by relevance score
- Considers position and content length

### 4. Content Extraction
- Extracts top subsections from relevant sections
- Applies bullet point and list detection
- Removes duplicates and low-quality content

### 5. Summarization
- Creates concise summaries using keyword-based ranking
- Applies spell-checking for quality
- Maintains context and relevance

## 🛠️ Dependencies

### Core Libraries
- **PyMuPDF**: PDF processing and text extraction
- **sentence-transformers**: Semantic embeddings
- **spaCy**: Natural language processing
- **scikit-learn**: Machine learning utilities
- **numpy**: Numerical computations
- **networkx**: Graph algorithms for structure analysis

### Additional Tools
- **langdetect**: Language detection
- **pyspellchecker**: Spell checking

## 🐛 Troubleshooting

### Common Issues

1. **spaCy Model Not Found**
   ```bash
   python -m spacy download en_core_web_sm
   ```

2. **Memory Issues with Large PDFs**
   - Reduce the number of concurrent processes
   - Process documents in smaller batches

3. **Docker Build Failures**
   - Ensure Docker has sufficient memory (4GB+ recommended)
   - Check internet connection for model downloads

4. **Input File Not Found**
   - Ensure `challenge1b_input.json` exists in the root directory
   - Verify PDF files exist in the `inputs/` directory
   - Check file paths match exactly

### Performance Tips

- Use SSD storage for faster PDF processing
- Increase Docker memory allocation for large documents
- Process documents in parallel for better performance

## 📝 Customization

### Adding New Document Types
1. Extend `pdf_utils.py` with new parsing logic
2. Update heading detection patterns
3. Add language-specific processing

### Modifying Ranking Algorithm
1. Edit `section_ranker.py` scoring functions
2. Adjust similarity weights
3. Add custom ranking criteria

### Enhancing Summarization
1. Modify `summarizer.py` sentence selection
2. Add custom summarization models
3. Implement domain-specific rules

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is part of a technical challenge and follows the specified licensing terms.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the code comments
3. Examine the example input/output files
4. Contact the development team

---

**Note**: This system is optimized for structured PDF documents with clear headings and sections. For best results, ensure your input PDFs have well-defined document structure. 