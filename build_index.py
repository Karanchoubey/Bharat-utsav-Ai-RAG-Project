import json

import pandas as pd
from langchain_core.documents import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS


CSV_FILES = [
    "indian-festivals-list.csv",
    "indian-festivals-list2.csv",
    "indian-festivals-list3.csv",
    "indian-festivals-list4.csv",
    "indian-festivals-list5.csv",
    "indian-festivals-list6.csv",
    "indian-festivals-list7.csv",
]

HF_DATASETS = [
    {
        "path": "13ari/Sanskriti",
        "split": "train",
    },
]

INDEX_DIR = "festival_faiss"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def normalize_value(value):
    if value is None:
        return ""

    if isinstance(value, str):
        return value.strip()

    if isinstance(value, (list, tuple, set)):
        parts = [normalize_value(item) for item in value]
        return ", ".join(part for part in parts if part)

    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=True, sort_keys=True)

    try:
        if pd.isna(value):
            return ""
    except TypeError:
        pass

    return str(value).strip()


def row_to_text(row_dict):
    parts = []
    for key, value in row_dict.items():
        normalized = normalize_value(value)
        if normalized:
            parts.append(f"{key}: {normalized}")
    return " | ".join(parts)


def load_csv_documents():
    documents = []

    for csv_path in CSV_FILES:
        df = pd.read_csv(
            csv_path,
            engine="python",
            on_bad_lines="skip",
        )

        if df.empty:
            print(f"Skipping empty CSV: {csv_path}")
            continue

        print(f"Loaded {len(df)} rows from {csv_path}")
        print("Columns:", list(df.columns))

        for idx, row in df.iterrows():
            row_text = row_to_text(
                {
                    col: row[col]
                    for col in df.columns
                }
            )

            if not row_text:
                continue

            documents.append(
                Document(
                    page_content=row_text,
                    metadata={
                        "source": csv_path,
                        "row_id": int(idx),
                        "dataset_type": "csv",
                    },
                )
            )

    print(f"CSV documents created: {len(documents)}")
    return documents


def load_hf_documents():
    documents = []

    try:
        from datasets import load_dataset
    except ImportError:
        print(
            "Skipping Hugging Face datasets because the 'datasets' package is not installed."
        )
        return documents

    for dataset_config in HF_DATASETS:
        dataset_path = dataset_config["path"]
        split = dataset_config.get("split", "train")

        try:
            dataset = load_dataset(dataset_path, split=split)
        except Exception as exc:
            print(f"Failed to load dataset {dataset_path} [{split}]: {exc}")
            continue

        print(f"Loaded {len(dataset)} rows from {dataset_path} [{split}]")

        for idx, row in enumerate(dataset):
            row_text = row_to_text(dict(row))

            if not row_text:
                continue

            documents.append(
                Document(
                    page_content=row_text,
                    metadata={
                        "source": dataset_path,
                        "split": split,
                        "row_id": idx,
                        "dataset_type": "huggingface",
                    },
                )
            )

    print(f"Hugging Face documents created: {len(documents)}")
    return documents


def build_index(documents):
    if not documents:
        raise ValueError("No documents were created. Nothing to index.")

    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    db = FAISS.from_documents(documents, embeddings)
    db.save_local(INDEX_DIR)


def main():
    csv_documents = load_csv_documents()
    hf_documents = load_hf_documents()
    all_documents = csv_documents + hf_documents

    print(f"Total documents created: {len(all_documents)}")
    build_index(all_documents)
    print("FAISS index built successfully from CSV + Hugging Face sources")


if __name__ == "__main__":
    main()
