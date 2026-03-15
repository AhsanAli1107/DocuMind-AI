# 📄 DocuMind AI

A smart document Q&A system that answers questions **only from your uploaded documents**.

## 🚀 Features
- Upload PDF, DOCX, TXT, CSV files
- Ask questions in natural language
- Gets answers **strictly from document** only
- Rejects out-of-scope questions
- Chat history maintained

## 🛠️ Tech Stack
- **Frontend**: Streamlit
- **Backend**: FastAPI
- **LLM**: Llama 3.1 8B (Groq - Free)
- **Vector DB**: ChromaDB
- **Framework**: LlamaIndex

## ⚡ Quick Start
```bash
# 1. Clone repo
git clone https://github.com/yourusername/documind-ai.git
cd documind-ai

# 2. Install dependencies
pip install -r requirements.txt

# 3. Add your Groq API key in .env
echo "GROQ_API_KEY=your-key-here" > .env

# 4. Run backend
python app.py

# 5. Run frontend (new terminal)
streamlit run streamlit_app.py
