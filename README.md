Requirement Quality Checker using NLP

GROUP MEMBERS: Name Roll Number Anugraha Pulinjeri B220177CS Abhinandh P B220095CS Jonase Eldho B220342CS Arjun Sarath B220190CS

Introduction
Software Requirement Specifications (SRS) are crucial in defining what a system should do. However, ambiguous language — especially passive voice and conditional modal verbs (like could, might, should, would) — makes requirements unclear and hard to test.

This project presents an NLP-based Quality Checker that automatically detects and rewrites such ambiguous sentences to ensure clarity and enforceability in software requirements.

Our system uses spaCy for linguistic analysis and integrates an AI API (Gemini model) to automatically rewrite passive sentences into clear active voice statements.

Objectives
Detect passive voice constructions in SRS documents. Detect conditional modal verbs indicating uncertainty. Provide a quantitative analysis of language quality in SRS files. Suggest rewritten, clearer sentences using AI-based grammar correction.

Theoretical Background 
Passive Voice Detection
Passive voice typically follows this syntactic pattern:

Object + auxiliary verb (be/get) + past participle (+ by agent) e.g., “The task is completed by the system.”

In spaCy’s dependency parser, such constructions are identified by:

nsubjpass → Passive subject auxpass → Passive auxiliary verb

Our algorithm flags any sentence containing these dependency labels as passive.

Conditional Modal Detection

Conditional modals indicate possibility or uncertainty. Examples: could, might, should, would.

Our script checks for these modal auxiliaries in each sentence. Such usage weakens requirement enforceability (e.g., “The system should allow login.” → “The system shall allow login.”).

Methodology 🔹 Step 1: Data Collection
We use multiple .txt files of SRS documents stored in the /data directory.

🔹 Step 2: Preprocessing

Each file is read, tokenized, and split into sentences using spaCy’s NLP pipeline.

🔹 Step 3: Detection

Two main detection functions are applied:

detect_passive_voice(sentence)

detect_conditional_modal(sentence)

These functions check for passive constructions and modal verbs respectively.

🔹 Step 4: AI Rewriting (Optional Extension)

We integrated the OpenAI GPT API to automatically rewrite passive sentences into active voice.

Example prompt: "Rewrite the following sentence into active voice: 'The data shall be processed by the system.'"

Report Generation
Results are stored in a pandas DataFrame and displayed as a summary table. The summary includes:

Total sentences per file Passive voice count Conditional modal count Rewritten suggestions

Working Flow Input Folder (data/) ↓ Read All .txt Files ↓ Sentence Segmentation using spaCy ↓ POS Tagging & Dependency Parsing ↓ → Passive Voice Detection (nsubjpass / auxpass) → Conditional Modal Detection (should / would / might / could) ↓ AI API Rewriting (Active Voice Conversion) ↓
Result Summary Table (pandas DataFrame) ↓ Console Output / File Output

Code Overview detect_passive_voice(sentence) Uses spaCy dependency tags (nsubjpass, auxpass) to detect passive constructions. detect_conditional_modal(sentence) Searches for modal words like could, might, should, would. analyze_document(text) Tokenizes the text, applies both detectors, and summarizes counts. rewrite_passive_to_active(sentence) Calls OpenAI API to rewrite passive to active voice. process_files(folder) Loops through .txt SRS files and returns a report.

How to Run

Place your SRS .txt files in the data/ folder.

Run the program: python nlp_quality_checker.py

Results & Findings
Passive Voice: Found mostly in requirement descriptions. Reducing passive forms improves clarity and responsibility definition.

Conditional Modals: “Should” and “Would” appear frequently; replacing them with “Shall” makes requirements testable.

AI Rewriting: The OpenAI model accurately converts most passive sentences into grammatically correct active forms.

Limitations & Future Work
Some sentences lack explicit agents (e.g., “The system shall be used.”) Use contextual AI rewriting to infer agent Limited to English text Extend to multilingual NLP Works on static files Extend for live document editors

Conclusion
This project successfully applies Natural Language Processing techniques to detect and improve the linguistic quality of SRS documents. By combining dependency parsing with AI-based rewriting, we bridge the gap between linguistic correctness and requirement clarity — ensuring that specifications are unambiguous, testable, and implementation-ready.

References
spaCy Documentation — https://spacy.io OpenAI GPT Models — https://platform.openai.com/docs IEEE Std 830-1998 – Recommended Practice for Software Requirements Specifications
