# 🪷 Bharat Utsav — Festival Atlas

> An AI-powered Retrieval-Augmented Generation (RAG) application that lets you explore India's rich festival heritage through natural-language questions, grounded answers, and related imagery.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-FAISS-EE4C2C)
![Ollama](https://img.shields.io/badge/Ollama-qwen2.5:7b-blueviolet)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ What It Does

**Bharat Utsav** (Festival Atlas) is a local-first AI assistant built around Indian festivals. Ask a question in plain English — the app retrieves the most relevant festival records from a **FAISS** vector index, feeds them to a local **Ollama** LLM, and streams back a grounded, hallucination-resistant answer along with related images.

### Key Features

| Feature | Description |
|---|---|
| 🔍 **Semantic Search** | FAISS-backed similarity search over curated festival datasets |
| 🤖 **Grounded Generation** | Answers are generated strictly from retrieved context — no hallucinations |
| 🖼️ **Image Discovery** | Relevant festival images fetched via DuckDuckGo image search |
| ⚡ **Real-time Streaming** | Token-by-token answer streaming via NDJSON for a responsive UX |
| 🏠 **Fully Local** | Runs entirely on your machine — no API keys, no cloud dependency |
| 🎨 **Premium UI** | Glassmorphism design, ambient gradients, smooth animations |

---

## 🏗️ Architecture

```
┌──────────────┐     ┌─────────────────┐     ┌──────────────────┐
│  Browser UI  │────▶│  FastAPI Server  │────▶│  FAISS Index     │
│  (Jinja2 +   │     │  (main.py)       │     │  (festival_faiss)│
│   Vanilla JS)│◀────│                  │◀────│                  │
└──────────────┘     │                  │     └──────────────────┘
                     │                  │
                     │    ┌─────────┐   │     ┌──────────────────┐
                     │    │ Ollama  │◀──│────▶│  DuckDuckGo      │
                     │    │qwen2.5  │   │     │  Image Search    │
                     │    └─────────┘   │     └──────────────────┘
                     └─────────────────┘
```

### How It Works

1. **Index Building** (`build_index.py`) — Reads multiple CSV files and a Hugging Face dataset ([`13ari/Sanskriti`](https://huggingface.co/datasets/13ari/Sanskriti)), converts each row into a text document, and builds a FAISS vector index using `sentence-transformers/all-MiniLM-L6-v2` embeddings.

2. **Query Flow** (`main.py`) — When a user asks a question:
   - The question is embedded and the top-*k* most similar documents are retrieved from FAISS.
   - Retrieved context is injected into a strict prompt that forbids external knowledge.
   - The prompt is sent to a locally running **Ollama** model (`qwen2.5:7b`) which streams the answer token-by-token.
   - Related images are fetched via DuckDuckGo and returned alongside the answer.

3. **Frontend** (`templates/index.html` + `static/`) — A responsive, single-page UI built with Jinja2 templates, vanilla CSS (glassmorphism + ambient gradients), and vanilla JavaScript that consumes the NDJSON stream.

---

## 📁 Project Structure

```
project/
├── main.py                     # FastAPI app — routes, RAG pipeline, streaming
├── build_index.py              # Builds the FAISS index from CSV + HuggingFace data
├── rag_query.py                # Standalone RAG query module (earlier version)
├── templates/
│   └── index.html              # Jinja2 HTML template
├── static/
│   ├── styles.css              # Premium UI styles (glassmorphism, animations)
│   └── app.js                  # Client-side streaming logic (NDJSON consumer)
├── festival_faiss/             # Pre-built FAISS vector index
│   ├── index.faiss
│   └── index.pkl
├── indian-festivals-list.csv   # Primary festival dataset (Bihar festivals)
├── indian-festivals-list2.csv  # Supplementary festival data
├── indian-festivals-list3.csv  # Supplementary festival data
├── indian-festivals-list4.csv  # Supplementary festival data
├── indian-festivals-list5.csv  # Supplementary festival data
├── indian-festivals-list6.csv  # Supplementary festival data
├── indian-festivals-list7.csv  # Supplementary festival data
├── indian-festivals-list8.csv  # Additional festival data
├── indian-festivals-list.pdf   # PDF reference document
├── indian-festivals.pdf        # PDF reference document
├── .gitignore
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

| Requirement | Details |
|---|---|
| **Python** | 3.10 or higher |
| **Ollama** | Installed and running locally ([ollama.com](https://ollama.com)) |
| **Ollama Model** | `qwen2.5:7b` pulled (`ollama pull qwen2.5:7b`) |

### 1. Clone the Repository

```bash
git clone https://github.com/Karanchoubey/Bharat-utsav-Ai-RAG-Project.git
cd Bharat-utsav-Ai-RAG-Project
```

### 2. Create a Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install fastapi uvicorn jinja2 langchain-community langchain-core faiss-cpu sentence-transformers pandas ddgs ollama
```

> **Optional** — To use the Hugging Face dataset during index building:
> ```bash
> pip install datasets
> ```

### 4. Pull the Ollama Model

```bash
ollama pull qwen2.5:7b
```

### 5. Build the FAISS Index (optional — pre-built index is included)

```bash
python build_index.py
```

This reads all CSV files and (optionally) the Hugging Face dataset, then saves the index to `festival_faiss/`.

### 6. Run the App

```bash
uvicorn main:app --reload
```

Open your browser at **http://127.0.0.1:8000** and start exploring!

---

## 💡 Usage

1. Type a question in the search bar, for example:
   - *"Tell me about Pongal"*
   - *"Festivals in Kerala"*
   - *"When is Diwali celebrated?"*
   - *"What is Chhath Puja?"*
2. The app streams the answer in real-time.
3. Related images appear below the answer for visual context.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | [FastAPI](https://fastapi.tiangolo.com/) |
| **Templating** | [Jinja2](https://jinja.palletsprojects.com/) |
| **Vector Store** | [FAISS](https://github.com/facebookresearch/faiss) via LangChain |
| **Embeddings** | [sentence-transformers/all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) |
| **LLM** | [Ollama](https://ollama.com) — `qwen2.5:7b` |
| **Image Search** | [DuckDuckGo Search](https://pypi.org/project/ddgs/) |
| **Frontend** | Vanilla HTML, CSS, JavaScript |
| **Data Sources** | Custom CSV datasets + [13ari/Sanskriti](https://huggingface.co/datasets/13ari/Sanskriti) HuggingFace dataset |

---

## 📊 Data Sources

The knowledge base is built from:

- **7 curated CSV files** containing detailed information about Indian festivals — celebration timings, regions, rituals, cultural significance, and more.
- **Hugging Face Dataset** — [`13ari/Sanskriti`](https://huggingface.co/datasets/13ari/Sanskriti) for broader Indian cultural context.
- **PDF reference documents** for supplementary festival information.

---

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Ideas for Contribution

- Add more festival datasets (South Indian, North-East, tribal festivals)
- Support additional LLM models via Ollama
- Add multi-language support (Hindi, Tamil, etc.)
- Improve the UI with dark mode toggle
- Add festival calendar view

---

## 📝 License

This project is open source and available under the [MIT License](LICENSE).

---

## 🙏 Acknowledgments

- [Ollama](https://ollama.com) for making local LLM inference accessible
- [LangChain](https://www.langchain.com/) for the RAG framework
- [FAISS](https://github.com/facebookresearch/faiss) by Meta AI for efficient similarity search
- [Hugging Face](https://huggingface.co/) for the Sanskriti dataset and embedding models
- The rich cultural heritage of India that inspired this project

---

<p align="center">
  Made with ❤️ for Bharat 🇮🇳
</p>
