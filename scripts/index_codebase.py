#!/usr/bin/env python3
"""
Index a codebase into ChromaDB for semantic retrieval by Hermes.
Usage: python3 index_codebase.py <project_dir> [--collection <name>]
"""
import argparse, os, sys, hashlib, ast, re
from pathlib import Path

HERMES_VENV = "/home/Evan/.hermes/hermes-agent/venv"
sys.path.insert(0, f"{HERMES_VENV}/lib/python3.11/site-packages")

import chromadb

CHROMA_PATH = os.path.expanduser("~/.hermes/chroma_codebase")
CHUNK_SIZE = 60   # lines per chunk
OVERLAP = 10      # lines of overlap between chunks

EXTENSIONS = {".py", ".cs", ".js", ".ts", ".sh", ".yaml", ".yml", ".md"}
SKIP_DIRS = {".git", "__pycache__", ".venv", "venv", "node_modules", "build", "dist", "chroma_codebase"}

def chunk_file(path: Path, text: str) -> list[dict]:
    lines = text.splitlines(keepends=True)
    chunks = []
    i = 0
    while i < len(lines):
        chunk_lines = lines[i:i + CHUNK_SIZE]
        chunk_text = "".join(chunk_lines)
        if chunk_text.strip():
            chunks.append({
                "text": chunk_text,
                "start_line": i + 1,
                "end_line": i + len(chunk_lines),
                "path": str(path),
            })
        i += CHUNK_SIZE - OVERLAP
    return chunks

def extract_symbols(path: Path, text: str) -> str:
    """Extract function/class names as extra context."""
    symbols = []
    if path.suffix == ".py":
        try:
            tree = ast.parse(text)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    symbols.append(node.name)
        except SyntaxError:
            pass
    elif path.suffix == ".cs":
        for m in re.finditer(r'\b(?:class|void|public|private|protected)\s+(\w+)', text):
            symbols.append(m.group(1))
    return " ".join(symbols[:20])

def index_project(project_dir: str, collection_name: str):
    root = Path(project_dir).resolve()
    print(f"Indexing {root} → collection '{collection_name}' in {CHROMA_PATH}")

    client = chromadb.PersistentClient(path=CHROMA_PATH)
    try:
        client.delete_collection(collection_name)
        print(f"  Deleted existing collection '{collection_name}'")
    except Exception:
        pass
    col = client.get_or_create_collection(collection_name, metadata={"hnsw:space": "cosine"})

    docs, ids, metas = [], [], []
    file_count = chunk_count = 0

    for fpath in sorted(root.rglob("*")):
        if any(skip in fpath.parts for skip in SKIP_DIRS):
            continue
        if fpath.suffix not in EXTENSIONS or not fpath.is_file():
            continue
        try:
            text = fpath.read_text(errors="replace")
        except Exception as e:
            print(f"  skip {fpath}: {e}")
            continue

        rel = fpath.relative_to(root)
        symbols = extract_symbols(fpath, text)
        file_count += 1

        for chunk in chunk_file(fpath, text):
            uid = hashlib.md5(f"{rel}:{chunk['start_line']}".encode()).hexdigest()
            doc = f"# {rel} (lines {chunk['start_line']}-{chunk['end_line']})\n"
            if symbols:
                doc += f"# symbols: {symbols}\n"
            doc += chunk["text"]
            docs.append(doc)
            ids.append(uid)
            metas.append({
                "path": str(rel),
                "start_line": chunk["start_line"],
                "end_line": chunk["end_line"],
                "project": collection_name,
            })
            chunk_count += 1

        if len(docs) >= 100:
            col.add(documents=docs, ids=ids, metadatas=metas)
            docs, ids, metas = [], [], []

    if docs:
        col.add(documents=docs, ids=ids, metadatas=metas)

    print(f"  Indexed {file_count} files, {chunk_count} chunks into '{collection_name}'")
    print(f"  Total docs: {col.count()}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("project_dir")
    parser.add_argument("--collection", default=None)
    args = parser.parse_args()
    name = args.collection or Path(args.project_dir).name.replace("-", "_").replace("/", "_")
    index_project(args.project_dir, name)
