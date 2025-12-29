from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
import asyncio
from pathlib import Path
from langchain_chroma import Chroma
from bot.tools.rag_tool import build_embeddings, load_pdf_documents, chunk_documents

import argparse

async def main(api_key: str):
    docs_path = Path("docs")
    if not docs_path.exists():
        print("The `docs` folder does not exist. Please create it and add your PDFs.")
        return

    pdf_files = list(docs_path.glob("*.pdf"))
    if not pdf_files:
        print("No PDF files found in the `docs` folder.")
        return

    print(f"Found {len(pdf_files)} PDF files to ingest.")

    all_chunks = []
    for pdf_path in pdf_files:
        print(f"Processing {pdf_path.name}...")
        docs = await asyncio.to_thread(load_pdf_documents, pdf_path)
        chunks = chunk_documents(docs)
        all_chunks.extend(chunks)
        print(f"  - {len(chunks)} chunks created.")

    if not all_chunks:
        print("No chunks were created from the PDFs.")
        return
    print(f"\nTotal chunks to ingest: {len(all_chunks)}")

    embeddings = build_embeddings(api_key)
    persist_dir = Path("db/chroma")
    collection_name = "pdfs"
    
    vectorstore = Chroma(
        collection_name=collection_name,
        persist_directory=str(persist_dir),
        embedding_function=embeddings,
    )

    print("Ingesting chunks into ChromaDB...")
    await asyncio.to_thread(vectorstore.add_documents, all_chunks)
    print("Ingestion complete!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-key", required=True, help="OpenAI API key")
    args = parser.parse_args()
    asyncio.run(main(args.api_key))

