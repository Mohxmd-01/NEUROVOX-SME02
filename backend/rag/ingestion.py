"""
Document ingestion pipeline — supports PDF, Excel, and JSON emails.
Chunks documents with metadata for the vector store.
"""
import os
import json
from typing import List, Dict
from datetime import datetime


def ingest_pdf(filepath: str) -> List[Dict]:
    """Extract text chunks from PDF with metadata"""
    try:
        import pdfplumber
        chunks = []
        with pdfplumber.open(filepath) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text:
                    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip() and len(p.strip()) > 20]
                    for j, para in enumerate(paragraphs):
                        chunks.append({
                            "id": f"pdf_{os.path.basename(filepath)}_{i}_{j}",
                            "text": para,
                            "source": os.path.basename(filepath),
                            "section": f"Page {i+1}, Section {j+1}",
                            "type": "pdf",
                            "date": datetime.now().strftime("%Y-%m-%d")
                        })
        return chunks
    except ImportError:
        print("⚠️ pdfplumber not installed, skipping PDF ingestion")
        return []
    except Exception as e:
        print(f"⚠️ Error ingesting PDF {filepath}: {e}")
        return []


def ingest_excel(filepath: str) -> List[Dict]:
    """Extract rows from Excel as searchable chunks"""
    try:
        import pandas as pd
        chunks = []
        df = pd.read_excel(filepath)
        
        for idx, row in df.iterrows():
            row_text = " | ".join([f"{col}: {val}" for col, val in row.items() if pd.notna(val)])
            if row_text.strip():
                chunks.append({
                    "id": f"excel_{os.path.basename(filepath)}_{idx}",
                    "text": row_text,
                    "source": os.path.basename(filepath),
                    "section": f"Row {idx + 1}",
                    "type": "excel",
                    "date": datetime.now().strftime("%Y-%m-%d")
                })
        
        # Column summary
        summary = f"Excel columns: {', '.join(df.columns.tolist())}. Total rows: {len(df)}"
        chunks.append({
            "id": f"excel_{os.path.basename(filepath)}_summary",
            "text": summary,
            "source": os.path.basename(filepath),
            "section": "Summary",
            "type": "excel",
            "date": datetime.now().strftime("%Y-%m-%d")
        })
        
        return chunks
    except ImportError:
        print("⚠️ pandas/openpyxl not installed, skipping Excel ingestion")
        return []
    except Exception as e:
        print(f"⚠️ Error ingesting Excel {filepath}: {e}")
        return []


def ingest_emails(filepath: str) -> List[Dict]:
    """Parse email JSON into searchable chunks"""
    try:
        chunks = []
        with open(filepath, 'r', encoding='utf-8') as f:
            emails = json.load(f)
        
        for i, email in enumerate(emails):
            text = (
                f"From: {email.get('from', 'Unknown')} | "
                f"To: {email.get('to', 'Unknown')} | "
                f"Subject: {email.get('subject', 'No Subject')} | "
                f"Date: {email.get('date', 'Unknown')}\n\n"
                f"{email.get('body', '')}"
            )
            chunks.append({
                "id": f"email_{i}",
                "text": text,
                "source": os.path.basename(filepath),
                "section": f"Email: {email.get('subject', f'Email #{i+1}')}",
                "type": "email",
                "date": email.get("date", datetime.now().strftime("%Y-%m-%d"))
            })
        
        return chunks
    except Exception as e:
        print(f"⚠️ Error ingesting emails {filepath}: {e}")
        return []


def ingest_text(filepath: str) -> List[Dict]:
    """Ingest plain text files"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip() and len(p.strip()) > 20]
        chunks = []
        for j, para in enumerate(paragraphs):
            chunks.append({
                "id": f"txt_{os.path.basename(filepath)}_{j}",
                "text": para,
                "source": os.path.basename(filepath),
                "section": f"Section {j+1}",
                "type": "text",
                "date": datetime.now().strftime("%Y-%m-%d")
            })
        return chunks
    except Exception as e:
        print(f"⚠️ Error ingesting text {filepath}: {e}")
        return []


def ingest_all_documents(doc_dir: str = None) -> List[Dict]:
    """Master ingestion — processes all files in the documents directory"""
    if doc_dir is None:
        doc_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "documents")
    
    all_chunks = []
    
    if not os.path.exists(doc_dir):
        print(f"⚠️ Document directory not found: {doc_dir}")
        return all_chunks
    
    for filename in os.listdir(doc_dir):
        filepath = os.path.join(doc_dir, filename)
        
        if not os.path.isfile(filepath):
            continue
        
        if filename.endswith('.pdf'):
            chunks = ingest_pdf(filepath)
            all_chunks.extend(chunks)
            print(f"  ✅ PDF: {filename} → {len(chunks)} chunks")
        
        elif filename.endswith(('.xlsx', '.xls')):
            chunks = ingest_excel(filepath)
            all_chunks.extend(chunks)
            print(f"  ✅ Excel: {filename} → {len(chunks)} chunks")
        
        elif filename.endswith('.json'):
            chunks = ingest_emails(filepath)
            all_chunks.extend(chunks)
            print(f"  ✅ Emails: {filename} → {len(chunks)} chunks")
        
        elif filename.endswith('.txt'):
            chunks = ingest_text(filepath)
            all_chunks.extend(chunks)
            print(f"  ✅ Text: {filename} → {len(chunks)} chunks")
    
    print(f"\n📚 Total chunks ingested: {len(all_chunks)}")
    return all_chunks
