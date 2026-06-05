# 📚 Gemma 4: 500+ Page Book Chatbot

A high-precision RAG (Retrieval-Augmented Generation) tool built with **Streamlit**, **LlamaIndex**, and **Gemma 4 31B**. Specifically designed to query large PDF books (500+ pages) with "perfect" accuracy.

## 🚀 Features
- **Perfect Retrieval:** Only sends relevant book segments to the AI to ensure precision.
- **Large Document Support:** Optimized for 500+ page PDFs.
- **Gemma 4 31B Power:** Uses the latest reasoning model from Google.
- **Clean UI:** Simple, one-page chat interface.

## 🛠️ Setup

1. **Clone the project** (or copy the files).
2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure Environment:**
   Create a `.env` file in the root directory:
   ```text
   GEMINI_API_KEY=your_google_ai_studio_api_key
   ```
4. **Run the App:**
   ```bash
   streamlit run app.py
   ```

## 📂 Project Structure
- `app.py`: Main Streamlit application and RAG logic.
- `.env`: Environment variables (API Keys).
- `requirements.txt`: Python dependencies.
- `.gitignore`: Files to exclude from version control.
