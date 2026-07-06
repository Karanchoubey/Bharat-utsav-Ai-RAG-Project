# =========================
# main.py (FIXED & SAFE)
# =========================

from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse

# -------------------------------------------------
# App must be created BEFORE heavy imports
# -------------------------------------------------
app = FastAPI()

# -------------------------------------------------
# Lazy-loaded globals
# -------------------------------------------------
db = None
embeddings = None

# -------------------------------------------------
# Initialize heavy resources safely
# -------------------------------------------------
def init_rag():
    global db, embeddings

    if db is not None:
        return

    try:
        from langchain_community.vectorstores import FAISS
        from langchain_community.embeddings import HuggingFaceEmbeddings

        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

        db = FAISS.load_local(
            "festival_faiss",
            embeddings,
            allow_dangerous_deserialization=True
        )

    except Exception as e:
        print("❌ RAG init failed:", e)
        db = None


# -------------------------------------------------
# Helper functions
# -------------------------------------------------
def web_image_search(query, max_images=5):
    images = []
    try:
        from ddgs import DDGS
        with DDGS() as ddgs:
            for r in ddgs.images(query, max_results=max_images):
                images.append({
                    "title": r.get("title", ""),
                    "url": r.get("image", "")
                })
    except Exception as e:
        print("Image search failed:", e)

    return images


def hybrid_rag(question, k=3):
    init_rag()

    if db is None:
        return "RAG database not available.", "error", []

    docs = db.similarity_search(question, k=k)

    if docs:
        context = "\n\n".join(d.page_content for d in docs)
        source = "local_faiss"
    else:
        context = ""
        source = "no_data"

    prompt = f"""
You are a factual assistant.

Rules:
- Use ONLY the information in the context.
- Do NOT add any external knowledge.
- Do NOT invent facts.
- Rewrite the information into a natural paragraph.
- If context is empty, say exactly:
  "Not mentioned in the available sources."

Context:
{context}

Question:
{question}

Answer:
"""

    try:
        import ollama
        response = ollama.generate(
            model="qwen2.5:7b",
            prompt=prompt,
            options={"temperature": 0}
        )
        answer = response["response"].strip()
    except Exception as e:
        answer = f"Ollama error: {e}"

    images = web_image_search(question)
    return answer, source, images


# -------------------------------------------------
# HTML renderer
# -------------------------------------------------
def render_page(question="", answer="", source="", images=None):
    images = images or []
    images_html = "".join(
        f"""
        <div class="img-card">
            <img src="{img['url']}">
            <p>{img['title']}</p>
        </div>
        """ for img in images
    )

    return f"""
<!DOCTYPE html>
<html>
<head>
    <title>Hybrid RAG Assistant</title>
    <style>
        body {{ font-family: Arial; margin: 30px; }}
        input {{ width: 70%; padding: 10px; }}
        button {{ padding: 10px 15px; }}
        .card {{ background: #f5f5f5; padding: 15px; margin-top: 20px; }}
        .images {{ display: flex; gap: 15px; flex-wrap: wrap; }}
        .img-card {{ width: 200px; }}
        img {{ width: 100%; border-radius: 5px; }}
    </style>
</head>
<body>

<h1>🔎 Hybrid RAG Assistant</h1>

<form method="post">
    <input name="question" placeholder="Ask a question" value="{question}" required>
    <button type="submit">Search</button>
</form>

{f"""
<div class="card">
    <h2>Answer</h2>
    <p>{answer}</p>
    <small>Source: {source}</small>
</div>
""" if answer else ""}

{f"""
<h2>Related Images</h2>
<div class="images">{images_html}</div>
""" if images else ""}

</body>
</html>
"""


# -------------------------------------------------
# Routes
# -------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def home():
    return render_page()


@app.post("/", response_class=HTMLResponse)
def ask(question: str = Form(...)):
    answer, source, images = hybrid_rag(question)
    return render_page(question, answer, source, images)


# -------------------------------------------------
# Debug import check
# -------------------------------------------------
if __name__ == "__main__":
    print("✅ main.py loaded successfully")
