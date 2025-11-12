import spacy
from typing import List, Dict, Any
import os
from glob import glob
import sys
import io
from tabulate import tabulate

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

try:
    import fitz
except ImportError:
    fitz = None

try:
    import docx
except ImportError:
    docx = None

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("CRITICAL: SpaCy model not found. Run: python3 -m spacy download en_core_web_sm")
    sys.exit(1)

DATASET_ROOT = "pure_dataset"
OUTPUT_LOG_FILE = "analysis_results_log.txt"
CONDITIONAL_MODALS = ["could", "might", "should", "would"]

def extract_text_from_document(filepath: str) -> str:
    ext = filepath.split('.')[-1].lower()
    try:
        if ext in ["html", "htm"] and BeautifulSoup:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                soup = BeautifulSoup(f.read(), "html.parser")
            for tag in soup(["script", "style"]):
                tag.decompose()
            return " ".join(soup.get_text().split())
        elif ext == "pdf" and fitz:
            text = ""
            with fitz.open(filepath) as doc:
                for page in doc:
                    text += page.get_text()
            return text
        elif ext == "docx" and docx:
            document = docx.Document(filepath)
            return "\n".join(p.text for p in document.paragraphs)
        elif ext == "txt":
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        elif ext == "doc":
            print(f"[Warning] Skipped legacy .doc file: {filepath}", file=sys.stderr)
            return ""
        else:
            print(f"[Error] Unsupported file type: {ext} ({filepath})", file=sys.stderr)
            return ""
    except Exception as e:
        print(f"[Error] Could not process {filepath}: {e}", file=sys.stderr)
        return ""

def detect_passive_voice(sentence: spacy.tokens.Span) -> bool:
    for token in sentence:
        if token.dep_ == "nsubjpass":
            return True
    for token in sentence:
        if token.tag_ == "VBN" and token.dep_ == "ROOT":
            if any(child.dep_ == "nsubjpass" for child in token.children):
                return True
    return False

def detect_conditional_modal(sentence: spacy.tokens.Span) -> List[str]:
    return list({token.text for token in sentence if token.lower_ in CONDITIONAL_MODALS and token.pos_ == "AUX"})

def analyze_document(doc_text: str, doc_id: str) -> Dict[str, Any]:
    doc = nlp(doc_text)
    results = {"doc_id": doc_id, "total_sentences": 0, "passive_sentences": [], "conditional_sentences": []}
    for sent in doc.sents:
        text = sent.text.strip()
        if len(text.split()) < 3:
            continue
        results["total_sentences"] += 1
        if detect_passive_voice(sent):
            results["passive_sentences"].append({"text": text, "position": results["total_sentences"], "doc_id": doc_id})
        modals = detect_conditional_modal(sent)
        if modals:
            results["conditional_sentences"].append({"text": text, "position": results["total_sentences"], "modals": modals, "doc_id": doc_id})
    return results

def suggest_rewrite(smell: str) -> str:
    if smell == "passive":
        return "Rewrite in Active Voice. Identify the agent (e.g., 'The System' or 'The User') and use a strong, active verb (shall/must)."
    if smell == "conditional":
        return "Replace weak modals (could, might, should, would) with firm verbs ('shall' or 'must')."
    return "N/A"

def generate_report(all_results: List[Dict[str, Any]], out):
    total_sentences = sum(r["total_sentences"] for r in all_results)
    all_passive = [s for r in all_results for s in r["passive_sentences"]]
    all_conditional = [s for r in all_results for s in r["conditional_sentences"]]

    print("="*80, file=out)
    print("AGGREGATE QUALITY REPORT (Assignment 1 - Passive Voice & Conditional Modals)", file=out)
    print(f"Total Documents Analyzed: {len(all_results)}", file=out)
    print(f"Total Sentences Scanned: {total_sentences}", file=out)
    print(f"Passive Voice Sentences: {len(all_passive)} | Conditional Modals: {len(all_conditional)}", file=out)
    print("="*80, file=out)

    table_data = []
    if all_passive:
        ex = all_passive[0]
        table_data.append([
            "Passive Voice",
            f"{len(all_passive)} occurrences",
            f"(Doc: {ex['doc_id']}) \"{ex['text']}\"",
            suggest_rewrite("passive")
        ])
    else:
        table_data.append(["Passive Voice", "0", "N/A", "N/A"])

    if all_conditional:
        ex = all_conditional[0]
        modals = ", ".join(ex["modals"])
        table_data.append([
            "Conditional Modal (Weak Commitment)",
            f"{len(all_conditional)} occurrences",
            f"(Doc: {ex['doc_id']}) \"{ex['text']}\" (Modals: {modals})",
            suggest_rewrite("conditional")
        ])
    else:
        table_data.append(["Conditional Modal", "0", "N/A", "N/A"])

    print("\nSUMMARY TABLE\n", file=out)
    print(tabulate(
        table_data,
        headers=["Type of Bad Smell", "Frequency in Dataset", "Example(s) from SRS", "Solution for Improvements"],
        tablefmt="fancy_grid",
        maxcolwidths=[25, 20, 60, 60]
    ), file=out)

    print("\n--- Detailed Findings (First 5 Examples) ---", file=out)
    print("\nPassive Voice Sentences:", file=out)
    for ex in all_passive[:5]:
        print(f"[{ex['doc_id']}-S{ex['position']}] {ex['text']}", file=out)

    print("\nConditional Modal Sentences:", file=out)
    for ex in all_conditional[:5]:
        modals = ", ".join(ex["modals"])
        print(f"[{ex['doc_id']}-S{ex['position']}] {ex['text']} (Modals: {modals})", file=out)

    print("="*80, file=out)

if __name__ == "__main__":
    sys.stdout = out_buffer = io.StringIO()
    sys.stderr = err_buffer = io.StringIO()

    try:
        print("Checking required libraries...", file=sys.stderr)
        print(f"  - PyMuPDF: {'OK' if fitz else 'Missing'}", file=sys.stderr)
        print(f"  - BeautifulSoup: {'OK' if BeautifulSoup else 'Missing'}", file=sys.stderr)
        print(f"  - python-docx: {'OK' if docx else 'Missing'}", file=sys.stderr)

        if not os.path.exists(DATASET_ROOT):
            os.makedirs(DATASET_ROOT)
            print(f"Created folder '{DATASET_ROOT}'. Please place dataset files inside.", file=sys.stderr)

        files = sum([glob(f"{DATASET_ROOT}/**/*.{ext}", recursive=True)
                     for ext in ["txt", "pdf", "html", "htm", "docx"]], [])

        if not files:
            print(f"No files found in '{DATASET_ROOT}'. Please add your SRS files.", file=sys.stderr)
            sys.exit(1)

        all_results = []
        print("\n--- Beginning Analysis ---", file=sys.stderr)
        for path in files:
            name = os.path.basename(path)
            print(f"Processing: {name}", file=sys.stderr)
            text = extract_text_from_document(path)
            if text.strip():
                all_results.append(analyze_document(text, name))
        print("--- Analysis Complete ---", file=sys.stderr)

        if all_results:
            generate_report(all_results, out_buffer)
        else:
            print("No documents analyzed successfully.", file=sys.stderr)

    finally:
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

        try:
            with open(OUTPUT_LOG_FILE, "w", encoding="utf-8") as f:
                f.write(err_buffer.getvalue())
                f.write("\n\n=== CLEAN ANALYSIS RESULTS ===\n\n")
                f.write(out_buffer.getvalue())
            print(f"\n✅ All analysis results saved to {OUTPUT_LOG_FILE}")
        except Exception as e:
            print(f"[Error] Could not write output file: {e}")
            print("\n--- Raw Output ---")
            print(out_buffer.getvalue())
