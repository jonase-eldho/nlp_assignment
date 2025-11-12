import spacy
from typing import List, Dict, Any
import os
from glob import glob
from functools import reduce
import sys # New import for redirecting output
import io # New import for in-memory text buffer

# --- External Library Imports ---
# These imports are wrapped in try/except blocks to provide clear feedback 
# if the required libraries are not installed (essential for your assignment).

try:
    from bs4 import BeautifulSoup  # For .html and .htm files
except ImportError:
    BeautifulSoup = None
    # print("WARNING: BeautifulSoup (beautifulsoup4) not found. HTML/HTM files will be skipped.")
    
try:
    import fitz  # PyMuPDF for .pdf files
except ImportError:
    fitz = None
    # print("WARNING: PyMuPDF (fitz) not found. PDF files will be skipped.")
    
try:
    import docx  # python-docx for .docx files
except ImportError:
    docx = None
    # print("WARNING: python-docx not found. DOCX files will be skipped.")

# --- Setup: SpaCy NLP Model ---

# Install Command Reminder: python3 -m spacy download en_core_web_sm
try:
    # Use the small model for efficiency on batch processing
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("---")
    print("CRITICAL ERROR: SpaCy model 'en_core_web_sm' not found.")
    print("Please run this command in your Mac Terminal (outside of this script):")
    print("python3 -m spacy download en_core_web_sm")
    print("Then try running the script again.")
    exit()

# --- Configuration ---

# The specific conditional modals that weaken a requirement's commitment
CONDITIONAL_MODALS = ["could", "might", "should", "would"]

# The directory where you must place your PURE dataset files
DATASET_ROOT = "pure_dataset"
# The file where all analysis results will be saved
OUTPUT_LOG_FILE = "analysis_results_log.txt"

# --- Text Extraction Logic (Robust Pre-processing) ---

def extract_text_from_document(filepath: str) -> str:
    """
    Handles text extraction based on file type using external libraries.
    """
    file_extension = filepath.split('.')[-1].lower()
    
    # 1. HTML/HTM Handling (BeautifulSoup)
    if file_extension in ['html', 'htm']:
        if BeautifulSoup is None: return ""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f: # Added errors='ignore' for better encoding resilience
                content = f.read()
            soup = BeautifulSoup(content, 'html.parser')
            for script_or_style in soup(['script', 'style']):
                script_or_style.decompose()
            text = soup.get_text()
            return ' '.join(text.split())
        except Exception as e:
            # We will now print a detailed error to stderr/log buffer
            print(f"Error processing HTML/HTM file {filepath}: {e}", file=sys.stderr)
            return ""

    # 2. PDF Handling (PyMuPDF / fitz)
    elif file_extension in ['pdf']:
        if fitz is None: return ""
        try:
            with fitz.open(filepath) as doc:
                text = ""
                for page in doc:
                    text += page.get_text()
                return text
        except Exception as e:
            # We will now print a detailed error to stderr/log buffer
            print(f"MuPDF error processing PDF file {filepath}: {e}", file=sys.stderr)
            return ""

    # 3. DOCX Handling (python-docx)
    elif file_extension in ['docx']:
        if docx is None: return ""
        try:
            document = docx.Document(filepath)
            return '\n'.join([paragraph.text for paragraph in document.paragraphs])
        except Exception as e:
            print(f"Error processing DOCX file {filepath}: {e}", file=sys.stderr)
            return ""
            
    # 4. TXT Handling
    elif file_extension in ['txt']:
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            print(f"Error processing TXT file {filepath}: {e}", file=sys.stderr)
            return ""
    
    # 5. Legacy DOC Warning
    elif file_extension in ['doc']:
        print(f"Skipped: File type .{file_extension} (legacy format) is unreliable. Recommend manual conversion to DOCX/PDF/TXT.", file=sys.stderr)
        return ""
    
    else:
        print(f"Error: Unsupported file extension: .{file_extension}", file=sys.stderr)
        return ""

# --- Detection Logic Functions (No Change) ---

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
    found_modals = []
    for token in sentence:
        if token.lower_ in CONDITIONAL_MODALS and token.pos_ == "AUX": 
            found_modals.append(token.text)
    return list(set(found_modals))

# --- Analysis & Reporting Functions (Modified to output to buffer) ---

def analyze_document(doc_text: str, doc_id: str) -> Dict[str, Any]:
    """
    Parses the document, applies detectors, and compiles the analysis report.
    """
    doc = nlp(doc_text)
    
    results = {
        "doc_id": doc_id,
        "total_sentences": 0,
        "passive_sentences": [],
        "conditional_sentences": []
    }

    for sentence in doc.sents:
        sentence_text = sentence.text.strip()
        if not sentence_text or len(sentence_text.split()) < 3:
            continue

        results["total_sentences"] += 1

        if detect_passive_voice(sentence):
            results["passive_sentences"].append({
                "text": sentence_text,
                "position": results["total_sentences"],
                "doc_id": doc_id
            })

        modals = detect_conditional_modal(sentence)
        if modals:
            results["conditional_sentences"].append({
                "text": sentence_text,
                "position": results["total_sentences"],
                "modals": modals,
                "doc_id": doc_id
            })

    return results

def suggest_rewrite(smell_type: str, sentence_text: str) -> str:
    if smell_type == "passive":
        return f"IMPROVEMENT SUGGESTION: Rewrite in Active Voice. Identify the agent (e.g., 'The System' or 'The User') and use a strong, active verb in the mandatory form (shall/must)."
    elif smell_type == "conditional":
        return f"IMPROVEMENT SUGGESTION: Replace weak modals ({', '.join(CONDITIONAL_MODALS)}) with firm commitment verbs ('shall' or 'must')."
    return "N/A"


def generate_report_output(all_analysis_results: List[Dict[str, Any]], output_stream):
    """
    Writes the analysis results to the specified output_stream (either sys.stdout or a file buffer).
    """
    # Combine results from all documents
    total_sentences = sum(res['total_sentences'] for res in all_analysis_results)
    all_passive = reduce(lambda a, b: a + b['passive_sentences'], all_analysis_results, [])
    all_conditional = reduce(lambda a, b: a + b['conditional_sentences'], all_analysis_results, [])
    
    passive_count = len(all_passive)
    conditional_count = len(all_conditional)
    total_smells = passive_count + conditional_count

    print("="*80, file=output_stream)
    print("AGGREGATE REQUIREMENTS QUALITY CHECKER ANALYSIS (ASSIGNMENT 1)", file=output_stream)
    print(f"Total Documents Successfully Analyzed: {len(all_analysis_results)}", file=output_stream)
    print(f"Total Sentences Analyzed: {total_sentences}", file=output_stream)
    print(f"Total Bad Smells Found: {total_smells}", file=output_stream)
    print("="*80, file=output_stream)

    # --- Summary Table Content: Passive Voice ---
    print("\n[ SUMMARY TABLE ENTRY 1: PASSIVE VOICE ]", file=output_stream)
    print("Type of bad smell: Passive Voice", file=output_stream)
    print(f"Frequency in the dataset: {passive_count} occurrences", file=output_stream)
    if passive_count > 0:
        example_item = all_passive[0]
        print(f"Example(s) from the SRS: (Doc: {example_item['doc_id']}) \"{example_item['text']}\"", file=output_stream)
        solution = suggest_rewrite("passive", example_item['text'])
        print(f"Solution for improvements: {solution}", file=output_stream)
    else:
        print("Example(s) from the SRS: N/A", file=output_stream)
        print("Solution for improvements: N/A", file=output_stream)


    # --- Summary Table Content: Conditional Modals ---
    print("\n[ SUMMARY TABLE ENTRY 2: CONDITIONAL MODALS ]", file=output_stream)
    print("Type of bad smell: Conditional Modal (Weak Commitment)", file=output_stream)
    print(f"Frequency in the dataset: {conditional_count} occurrences", file=output_stream)
    if conditional_count > 0:
        example_item = all_conditional[0]
        modals_str = ', '.join(example_item['modals'])
        print(f"Example(s) from the SRS: (Doc: {example_item['doc_id']}) \"{example_item['text']}\" (Modals: {modals_str})", file=output_stream)
        solution = suggest_rewrite("conditional", example_item['text'])
        print(f"Solution for improvements: {solution}", file=output_stream)
    else:
        print("Example(s) from the SRS: N/A", file=output_stream)
        print("Solution for improvements: N/A", file=output_stream)
        
    print("\n" + "="*80, file=output_stream)
    print("--- Detailed Findings for Report (First 5 examples of each) ---", file=output_stream)
    
    print("\nPassive Voice Instances (First 5):", file=output_stream)
    for i, item in enumerate(all_passive[:5]):
        print(f"  [{item['doc_id']}-S{item['position']}] Passive: {item['text']}", file=output_stream)
        print(f"  |-> Improvement: {suggest_rewrite('passive', item['text'])}", file=output_stream)

    print("\nConditional Modal Instances (First 5):", file=output_stream)
    for i, item in enumerate(all_conditional[:5]):
        modals_str = ', '.join(item['modals'])
        print(f"  [{item['doc_id']}-S{item['position']}] Conditional ({modals_str}): {item['text']}", file=output_stream)
        print(f"  |-> Improvement: {suggest_rewrite('conditional', item['text'])}", file=output_stream)
    
    print("\n" + "="*80, file=output_stream)


# --- Main Execution (UPDATED TO SAVE OUTPUT) ---

if __name__ == "__main__":
    
    # Use an in-memory buffer to capture all output (stdout and stderr)
    original_stdout = sys.stdout
    sys.stdout = output_buffer = io.StringIO()
    
    # Use a separate buffer to capture warnings/errors
    original_stderr = sys.stderr
    sys.stderr = error_buffer = io.StringIO()
    
    try:
        # Initial checks and file discovery print to the error buffer
        print("REQUIRED LIBRARIES CHECK (Run 'pip install PyMuPDF beautifulsoup4 python-docx'):", file=sys.stderr)
        print(f"  - PyMuPDF (PDF): {'OK' if fitz else 'MISSING'}", file=sys.stderr)
        print(f"  - BeautifulSoup (HTML): {'OK' if BeautifulSoup else 'MISSING'}", file=sys.stderr)
        print(f"  - python-docx (DOCX): {'OK' if docx else 'MISSING'}", file=sys.stderr)
        
        # --- File Discovery ---
        if not os.path.exists(DATASET_ROOT):
            os.makedirs(DATASET_ROOT)
            print(f"\nCreated directory: '{DATASET_ROOT}'. Please place your PURE dataset files here.", file=sys.stderr)

        file_paths = glob(f'{DATASET_ROOT}/**/*.txt', recursive=True) + \
                     glob(f'{DATASET_ROOT}/**/*.html', recursive=True) + \
                     glob(f'{DATASET_ROOT}/**/*.htm', recursive=True) + \
                     glob(f'{DATASET_ROOT}/**/*.pdf', recursive=True) + \
                     glob(f'{DATASET_ROOT}/**/*.docx', recursive=True)

        DOCUMENTS_TO_PROCESS = [(os.path.basename(p), p) for p in file_paths]
        
        if not DOCUMENTS_TO_PROCESS:
            print(f"\nNO FILES FOUND in '{DATASET_ROOT}'. Please place your SRS documents there and run again.", file=sys.stderr)
        
        all_analysis_results = []
        
        print("\n--- STARTING BATCH PROCESSING ---", file=sys.stderr)
        
        for doc_id, doc_path in DOCUMENTS_TO_PROCESS:
            print(f"Processing document: {doc_id} ({doc_path})...", end="", file=sys.stderr)
            
            # 1. Load and extract text
            raw_text = extract_text_from_document(doc_path)
            
            if not raw_text:
                print("SKIPPED.", file=sys.stderr)
                continue
                
            # 2. Analyze the content
            analysis = analyze_document(raw_text, doc_id)
            all_analysis_results.append(analysis)
            print("DONE.", file=sys.stderr)
            
        print("\n--- BATCH PROCESSING COMPLETE ---", file=sys.stderr)

        # 3. Generate the final aggregate report into the output buffer
        if all_analysis_results:
            generate_report_output(all_analysis_results, output_buffer)
        else:
            print("\nNo documents were successfully analyzed. Check warnings above.", file=sys.stderr)

    finally:
        # Restore stdout/stderr
        sys.stdout = original_stdout
        sys.stderr = original_stderr
        
        # --- File Writing ---
        
        # Combine error messages (warnings, skips, etc.) and clean analysis results
        final_output = error_buffer.getvalue() + "\n\n" + ("="*80 + "\nCLEAN ANALYSIS RESULTS (FOR REPORT)\n" + "="*80 + "\n") + output_buffer.getvalue()

        # Write the combined log to the file
        try:
            with open(OUTPUT_LOG_FILE, 'w', encoding='utf-8') as f:
                f.write(final_output)
            print(f"\n[ SUCCESS ] All analysis results, warnings, and detailed findings saved to: {OUTPUT_LOG_FILE}")
            print("\nNOTE: The terminal output has been redirected to this file for reliability and collaboration.")
        except Exception as e:
            print(f"\n[ FATAL ERROR ] Could not write output file: {e}")
            print("\n--- Displaying Raw Output Instead ---")
            print(final_output)
