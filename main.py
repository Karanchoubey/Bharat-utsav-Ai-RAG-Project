from pathlib import Path
import json
import traceback

from fastapi import FastAPI, Form, Request
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


# -------------------------
# FastAPI app
# -------------------------
app = FastAPI()
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
db = None
embeddings = None


# -------------------------
# Load embeddings + FAISS
# -------------------------
def init_rag():
    global db, embeddings

    if db is not None:
        return

    try:
        from langchain_community.embeddings import HuggingFaceEmbeddings
        from langchain_community.vectorstores import FAISS

        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

        db = FAISS.load_local(
            "festival_faiss",
            embeddings,
            allow_dangerous_deserialization=True,
        )

        print("FAISS index loaded successfully")

    except Exception:
        print("FAISS load failed")
        traceback.print_exc()
        db = None


# -------------------------
# Image search
# -------------------------
def web_image_search(query, max_images=5):
    images = []
    try:
        from ddgs import DDGS

        with DDGS() as ddgs:
            for result in ddgs.images(query, max_results=max_images):
                images.append(
                    {
                        "title": result.get("title", ""),
                        "url": result.get("image", ""),
                    }
                )
    except Exception as exc:
        print("Image search error:", exc)

    return images


# -------------------------
# RAG helpers
# -------------------------
def prepare_rag_context(question, k=3):
    init_rag()

    if db is None:
        return None, "error"

    docs = db.similarity_search(question, k=k)

    if docs:
        context = "\n\n".join(doc.page_content for doc in docs)
        source = "local_faiss"
    else:
        context = ""
        source = "no_data"

    return context, source


def build_prompt(question, context):
    return f"""
You are a factual assistant.

Rules:
- Use ONLY the information in the context.
- Do NOT add any external knowledge.
- Do NOT invent facts.
- Rewrite the information into a natural, descriptive paragraph.
- Do NOT list fields or bullet points.
- If the context is empty, say exactly:
  "Not mentioned in the available sources."

Context (structured facts):
{context}

Question:
{question}

Answer (write in paragraph form):
"""


def stream_ollama_answer(prompt):
    import ollama

    stream = ollama.generate(
        model="qwen2.5:7b",
        prompt=prompt,
        options={"temperature": 0},
        stream=True,
    )

    for chunk in stream:
        yield chunk.get("response", "")


def hybrid_rag(question, k=3):
    context, source = prepare_rag_context(question, k=k)

    if context is None:
        return "RAG database not available.", source, []

    prompt = build_prompt(question, context)

    answer_parts = []
    try:
        for chunk in stream_ollama_answer(prompt):
            answer_parts.append(chunk)
    except Exception as exc:
        return f"Ollama error: {exc}", source, []

    images = web_image_search(question)

    return "".join(answer_parts).strip(), source, images


def stream_hybrid_rag(question, k=3):
    context, source = prepare_rag_context(question, k=k)

    if context is None:
        yield json.dumps(
            {"type": "error", "message": "RAG database not available.", "source": source}
        ) + "\n"
        return

    prompt = build_prompt(question, context)

    yield json.dumps({"type": "start", "source": source}) + "\n"

    try:
        for chunk in stream_ollama_answer(prompt):
            if chunk:
                yield json.dumps({"type": "chunk", "content": chunk}) + "\n"
    except Exception as exc:
        yield json.dumps(
            {"type": "error", "message": f"Ollama error: {exc}", "source": source}
        ) + "\n"
        return

    images = web_image_search(question)
    yield json.dumps({"type": "done", "source": source, "images": images}) + "\n"


# -------------------------
# Routes
# -------------------------
@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "question": "",
            "answer": "",
            "source": "",
            "images": [],
        },
    )


@app.post("/")
def ask(request: Request, question: str = Form(...)):
    answer, source, images = hybrid_rag(question)
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "question": question,
            "answer": answer,
            "source": source,
            "images": images,
        },
    )


@app.post("/stream")
def ask_stream(question: str = Form(...)):
    return StreamingResponse(
        stream_hybrid_rag(question),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-cache"},
    )


# -------------------------
# CLI compatibility check
# -------------------------
if __name__ == "__main__":
    print("Running CLI test mode. Type exit to quit.")
    while True:
        q = input("Ask: ").strip()
        if q.lower() == "exit":
            break
        a, s, _ = hybrid_rag(q)
        print("\nAnswer:", a)
        print("Source:", s)
