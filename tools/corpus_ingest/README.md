# Olympiad corpus ingestion prototype

A deliberately small vertical slice for turning a large source registry into reviewable task candidates without manually opening every PDF.

## Flow

`CSV registry -> download -> immutable raw PDF -> PyMuPDF task segmentation -> lossless task crop -> confidence routing -> SQLite -> LLM queue / Human Desk`

The crop is the source of truth. The parser is not allowed to invent unreadable text or formulas. Graphic/vector-heavy, broken-glyph and uncertain-boundary tasks are routed away from silent acceptance.

## Run

```bash
cd tools/corpus_ingest
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp sources.example.csv sources.csv
python corpus.py sources.csv --root .corpus
streamlit run review_app.py
```

Workspace:

```text
.corpus/
  raw/                 # SHA-256 named originals
  crops/               # exact visual task fragments; never reconstructed
  queues/needs_llm.jsonl
  corpus.sqlite3
```

## Prototype routing

- `accepted`: clean, numbered, text-dominant candidate with confidence >= 0.90.
- `needs_llm`: ambiguous candidate; exported as JSONL with crop path and strict no-invention instruction.
- `needs_human`: badly broken / very low confidence candidate.
- `verified`: accepted in Human Desk after edit.

The LLM call itself is intentionally an adapter boundary in this prototype. `needs_llm.jsonl` is the contract: a provider/model can consume one cropped task at a time and must either return structured extraction or escalate `needs_human=true`. This keeps the crawler/parser runnable with zero model tokens and avoids hard-wiring model credentials into the corpus layer.

## Next after prototype validation

Once task boundaries and routing prove useful on real olympiad PDFs, split this into crawler/parser/reviewer services, add OCR fallback for scanned pages, structured formula/image blocks, and write verified tasks into the app's canonical generator/content schema.
