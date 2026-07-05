# Documentary Research Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the existing Summarizer PDF pipeline with a resumable, citation-preserving research mode, then use it to extract and review rules from the approved Take Two book corpus.

**Architecture:** The existing `/Users/insular/transcripts` repository remains responsible for PDF extraction, OCR, Gemini routing, usage logging, and ignored working outputs. A new `PdfResearcher` processes page-bounded Markdown chunks independently and stores a resumable manifest instead of producing a lossy whole-book summary. The Take Two repository stores only manifests without absolute paths, specialized prompts, validated rules, conflict records, and quality reports.

**Tech Stack:** Python 3.11, Typer, PyPDF, OCRmyPDF, MinerU, Gemini client already present in Summarizer, pytest, Markdown, JSON.

---

## File structure

### Summarizer repository

- Create `src/research/__init__.py`: research package boundary.
- Create `src/research/pdf_researcher.py`: page-bounded chunk extraction, Gemini calls, validation, and resume manifest.
- Modify `src/pipeline.py`: route `mode=research` through extraction and `PdfResearcher`.
- Modify `src/cli.py`: expose `--prompt-file`, `--research-chunk-tokens`, and working `--resume`.
- Modify `runpdf`: document research-mode invocation in CLI help.
- Modify `COMMANDS.md`: document the durable research command.
- Create `tests/test_pdf_researcher.py`: unit tests for page bounds, output validation, manifest, and resume.
- Create `tests/test_pipeline_pdf_research.py`: pipeline integration test with all external work mocked.

### Take Two repository

- Create `option-research-engine/research/corpus_manifest.json`: nine unique sources, aliases, hashes, editions, and processing status without absolute paths.
- Create `option-research-engine/prompts/books/b_mcmillan_2012.md`: complete McMillan extraction prompt.
- Create `option-research-engine/prompts/books/b_natenberg_1994.md`: complete Natenberg extraction prompt.
- Create `option-research-engine/prompts/books/b_passarelli_2012.md`: complete Passarelli extraction prompt.
- Create `option-research-engine/research/pilot/QUALITY_REPORT.md`: citation review and go/no-go decision.
- Modify the three corresponding files under `option-research-engine/books/fiches/`: append processing journal entries.
- Create accepted rule files under `option-research-engine/rules/<category>/` only after manual citation review.

### Local ignored outputs

- `/Users/insular/transcripts/cache/pdf_md/`: extracted or OCR Markdown.
- `/Users/insular/transcripts/output/books/<book>_research/`: Gemini chunk outputs and local resume manifest.
- No PDF, OCR text, full book Markdown, or Gemini secret enters Git.

---

### Task 1: Add page-bounded research chunking

**Files:**
- Create: `/Users/insular/transcripts/src/research/__init__.py`
- Create: `/Users/insular/transcripts/src/research/pdf_researcher.py`
- Test: `/Users/insular/transcripts/tests/test_pdf_researcher.py`

- [ ] **Step 1: Write failing page-bound tests**

```python
from src.research.pdf_researcher import page_bounds


def test_page_bounds_reads_pdf_page_headings() -> None:
    text = "# Page 17\n\nAlpha\n\n# Page 18\n\nBeta"
    assert page_bounds(text) == (17, 18)


def test_page_bounds_rejects_chunk_without_page_heading() -> None:
    with pytest.raises(ValueError, match="page marker"):
        page_bounds("Alpha only")
```

- [ ] **Step 2: Run the tests and verify failure**

Run:

```bash
cd /Users/insular/transcripts
.venv/bin/python -m pytest tests/test_pdf_researcher.py -q
```

Expected: collection fails because `src.research.pdf_researcher` does not exist.

- [ ] **Step 3: Implement focused research types and page bounds**

```python
PAGE_HEADING = re.compile(r"^# Page (\d+)\s*$", re.MULTILINE)


@dataclass(frozen=True)
class ResearchChunk:
    index: int
    page_start: int
    page_end: int
    token_count: int
    text: str


def page_bounds(text: str) -> tuple[int, int]:
    pages = [int(value) for value in PAGE_HEADING.findall(text)]
    if not pages:
        raise ValueError("Research chunk requires at least one PDF page marker.")
    return min(pages), max(pages)


def _page_sections(markdown: str) -> list[str]:
    matches = list(PAGE_HEADING.finditer(markdown))
    if not matches:
        raise ValueError("Research Markdown requires PDF page markers.")
    return [
        markdown[match.start() : matches[index + 1].start()].strip()
        if index + 1 < len(matches)
        else markdown[match.start() :].strip()
        for index, match in enumerate(matches)
    ]


def build_research_chunks(markdown: str, max_tokens: int) -> list[ResearchChunk]:
    chunks: list[ResearchChunk] = []
    current: list[str] = []
    for page in _page_sections(markdown):
        candidate = "\n\n".join([*current, page]).strip()
        if current and count_tokens(candidate) > max_tokens:
            body = "\n\n".join(current).strip()
            first, last = page_bounds(body)
            chunks.append(ResearchChunk(len(chunks), first, last, count_tokens(body), body))
            current = [page]
        else:
            current.append(page)
    if current:
        body = "\n\n".join(current).strip()
        first, last = page_bounds(body)
        chunks.append(ResearchChunk(len(chunks), first, last, count_tokens(body), body))
    return chunks
```

- [ ] **Step 4: Add and test `build_research_chunks`**

The function must call `split_markdown_by_tokens`, derive page bounds for every chunk, and reject
any split that loses the first `# Page N` heading. Long single pages remain one chunk even when
they exceed the requested target; page provenance takes priority over a hard token cut.

Run:

```bash
.venv/bin/python -m pytest tests/test_pdf_researcher.py -q
```

Expected: page-bound and chunk tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/research tests/test_pdf_researcher.py
git commit -m "feat: add page-bounded PDF research chunks"
```

### Task 2: Add resumable Gemini research extraction

**Files:**
- Modify: `/Users/insular/transcripts/src/research/pdf_researcher.py`
- Modify: `/Users/insular/transcripts/tests/test_pdf_researcher.py`

- [ ] **Step 1: Write failing manifest and resume tests**

Use a fake Gemini client that records requests. Assert that:

- chunk outputs are `chunk-0001-p0017-p0018.md`;
- `manifest.json` records `done`, page bounds, token count, model, and output filename;
- a second run with `resume=True` makes zero Gemini calls for completed chunks;
- a failed chunk is recorded as `failed` without deleting completed outputs.

- [ ] **Step 2: Run the focused test and verify failure**

```bash
.venv/bin/python -m pytest tests/test_pdf_researcher.py -q
```

Expected: failure because `PdfResearcher` is not implemented.

- [ ] **Step 3: Implement `PdfResearcher.research`**

Required interface:

```python
class PdfResearcher:
    def __init__(
        self,
        client: GeminiClient | None = None,
        router: ModelRouter | None = None,
    ) -> None:
        self.client = client
        self.router = router or ModelRouter()

    def research(
        self,
        title: str,
        source_file: str,
        markdown: str,
        output_dir: Path,
        prompt_path: Path,
        *,
        chunk_tokens: int = 30_000,
        resume: bool = False,
    ) -> Path:
        client = self.client or GeminiClient()
        prompt = prompt_path.read_text(encoding="utf-8")
        output_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = output_dir / "manifest.json"
        manifest = load_manifest(manifest_path, title, source_file)
        completed = {
            item["index"]: item
            for item in manifest["chunks"]
            if item["status"] in {"done", "no_rules", "needs_review"}
        }

        for chunk in build_research_chunks(markdown, chunk_tokens):
            output_name = (
                f"chunk-{chunk.index + 1:04d}-"
                f"p{chunk.page_start:04d}-p{chunk.page_end:04d}.md"
            )
            output_path = output_dir / output_name
            if resume and chunk.index in completed and output_path.exists():
                continue

            model = self.router.for_pdf(chunk.token_count)
            content = (
                f"LIVRE: {title}\n"
                f"FICHIER SOURCE: {source_file}\n"
                f"PLAGE PDF: {chunk.page_start}-{chunk.page_end}\n"
                "REGLE: utilise uniquement les marqueurs # Page N visibles dans ce bloc.\n\n"
                f"{chunk.text}"
            )
            try:
                response = client.generate(prompt, content, model)
                status = validate_research_output(response)
                output_path.write_text(response.strip() + "\n", encoding="utf-8")
                item = {
                    "index": chunk.index,
                    "page_start": chunk.page_start,
                    "page_end": chunk.page_end,
                    "token_count": chunk.token_count,
                    "model": model.model,
                    "status": status,
                    "output": output_name,
                }
            except Exception as exc:
                item = {
                    "index": chunk.index,
                    "page_start": chunk.page_start,
                    "page_end": chunk.page_end,
                    "token_count": chunk.token_count,
                    "model": model.model,
                    "status": "failed",
                    "error": str(exc),
                }
            upsert_manifest_chunk(manifest, item)
            write_manifest_atomic(manifest_path, manifest)

        return manifest_path
```

Each Gemini request must include:

```text
LIVRE: {title}
FICHIER SOURCE: {source_file}
PLAGE PDF: {page_start}-{page_end}
REGLE: utilise uniquement les marqueurs # Page N visibles dans ce bloc.
```

Write the manifest atomically through a temporary file followed by `Path.replace`.

- [ ] **Step 4: Implement structural output checks**

For every rule block, require these headings:

```python
REQUIRED_RULE_HEADINGS = {
    "## Condition",
    "## Variables nécessaires",
    "## Action",
    "## Justification",
    "## Auteur",
    "## Livre",
    "## Chapitre",
    "## Page",
    "## Niveau de confiance",
    "## Historique",
}
```

Outputs with no rule block may contain exactly `AUCUNE_REGLE_EXPLOITABLE`. Any other malformed
output receives `needs_review` and remains visible in the manifest.

Implement the manifest and validation helpers as:

```python
def validate_research_output(response: str) -> str:
    stripped = response.strip()
    if stripped == "AUCUNE_REGLE_EXPLOITABLE":
        return "no_rules"
    blocks = [block for block in re.split(r"(?=^# R-)", stripped, flags=re.MULTILINE) if block]
    if not blocks:
        return "needs_review"
    if all(REQUIRED_RULE_HEADINGS.issubset(set(re.findall(r"^## .+$", block, re.MULTILINE))) for block in blocks):
        return "done"
    return "needs_review"


def load_manifest(path: Path, title: str, source_file: str) -> dict[str, object]:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"title": title, "source_file": source_file, "chunks": []}


def upsert_manifest_chunk(manifest: dict[str, object], item: dict[str, object]) -> None:
    chunks = list(manifest["chunks"])
    chunks = [chunk for chunk in chunks if chunk["index"] != item["index"]]
    chunks.append(item)
    manifest["chunks"] = sorted(chunks, key=lambda chunk: chunk["index"])


def write_manifest_atomic(path: Path, manifest: dict[str, object]) -> None:
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)
```

- [ ] **Step 5: Run focused tests**

```bash
.venv/bin/python -m pytest tests/test_pdf_researcher.py -q
```

Expected: all tests pass and no real Gemini request occurs.

- [ ] **Step 6: Commit**

```bash
git add src/research/pdf_researcher.py tests/test_pdf_researcher.py
git commit -m "feat: add resumable Gemini PDF research"
```

### Task 3: Expose research mode through `runpdf`

**Files:**
- Modify: `/Users/insular/transcripts/src/pipeline.py`
- Modify: `/Users/insular/transcripts/src/cli.py`
- Modify: `/Users/insular/transcripts/runpdf`
- Modify: `/Users/insular/transcripts/COMMANDS.md`
- Test: `/Users/insular/transcripts/tests/test_pipeline_pdf_research.py`

- [ ] **Step 1: Write a failing pipeline test**

Mock `_extract_pdf`, `clean_markdown`, and `PdfResearcher`. Call:

```python
run_pdf(
    pdf_path,
    engine="text",
    mode="research",
    prompt_file=prompt_path,
    research_chunk_tokens=12_000,
    resume=True,
)
```

Assert that the standard `PdfSummarizer` is not called and the researcher receives the extracted
Markdown, prompt path, chunk target, and resume flag.

- [ ] **Step 2: Run the test and verify failure**

```bash
.venv/bin/python -m pytest tests/test_pipeline_pdf_research.py -q
```

Expected: `run_pdf()` rejects the new arguments.

- [ ] **Step 3: Add pipeline routing**

Extend `run_pdf` with:

```python
prompt_file: Path | None = None,
research_chunk_tokens: int = 30_000,
resume: bool = False,
```

When `mode == "research"`:

- require `prompt_file`;
- write into `output/books/<slug>_research/`;
- call `PdfResearcher.research`;
- never export full research chunks to Graphipy automatically.

Reject unknown modes with `ValueError(f"Unsupported PDF mode: {mode}")`.

- [ ] **Step 4: Add CLI options**

Both `pdf` and `run-pdf` must forward:

```python
prompt_file: Path | None = None
research_chunk_tokens: int = 30_000
resume: bool = False
```

The durable command becomes:

```bash
./runpdf "/path/book.pdf" \
  --mode research \
  --prompt-file "/path/book_prompt.md" \
  --engine smart \
  --research-chunk-tokens 30000 \
  --resume
```

- [ ] **Step 5: Update help and commands**

Document that research mode writes ignored local chunks, preserves page markers, resumes completed
chunks, and does not create a trading recommendation.

- [ ] **Step 6: Run focused and full tests**

```bash
.venv/bin/python -m pytest tests/test_pdf_researcher.py tests/test_pipeline_pdf_research.py -q
.venv/bin/python -m pytest -q
```

Expected: all tests pass.

- [ ] **Step 7: Commit**

```bash
git add src/cli.py src/pipeline.py runpdf COMMANDS.md tests/test_pipeline_pdf_research.py
git commit -m "feat: expose PDF research mode"
```

### Task 4: Create the Take Two corpus manifest and pilot prompts

**Files:**
- Create: `option-research-engine/research/corpus_manifest.json`
- Create: `option-research-engine/prompts/books/b_mcmillan_2012.md`
- Create: `option-research-engine/prompts/books/b_natenberg_1994.md`
- Create: `option-research-engine/prompts/books/b_passarelli_2012.md`

- [ ] **Step 1: Create the corpus manifest**

Each entry must contain:

```json
{
  "book_id": "B-MCMILLAN-2012",
  "source_filename": "options-as-a-strategic-investment-fifth-edition-5nbsped-0735204659-9780735204652_compress.pdf",
  "aliases": ["pdfcoffee.com_options-as-a-strategic-investment-by-lawrence-g-mcmillan-pdf-pdf-free.pdf"],
  "sha256": "8ad4a357fd7f0c90a8fb0b82f119978628467608a52bddbbe82aa8b431211a67",
  "pages": 1069,
  "source_type": "book",
  "extraction": "ready_text",
  "status": "pilot_pending"
}
```

Record the nine unique documents. Use filenames only, never absolute paths.

- [ ] **Step 2: Create the three pilot prompts**

Each prompt must embed:

- the official rule format from `rules/FORMAT_REGLE.md`;
- the relevant category prompt;
- the book-specific instructions from its fiche;
- `AUCUNE_REGLE_EXPLOITABLE` as the only allowed no-result response;
- an explicit ban on invented page numbers, thresholds, formulas, and chapter titles;
- the distinction between `documentary_validated` and quantitative validation.

- [ ] **Step 3: Validate prompt hygiene**

```bash
rg -n 'T[B]D|T[O]DO|GEMINI_API_KEY|/Users/' option-research-engine/prompts/books option-research-engine/research/corpus_manifest.json
python3 -m json.tool option-research-engine/research/corpus_manifest.json >/dev/null
git diff --check
```

Expected: no placeholders, secret names used as values, or absolute paths; valid JSON.

- [ ] **Step 4: Commit**

```bash
git add option-research-engine/prompts/books option-research-engine/research/corpus_manifest.json
git commit -m "research: define pilot corpus and extraction prompts"
```

### Task 5: Run the three-book pilot

**Files:**
- Local ignored outputs under `/Users/insular/transcripts/`
- Create: `option-research-engine/research/pilot/QUALITY_REPORT.md`

- [ ] **Step 1: Run a text-extraction pilot on McMillan**

```bash
cd /Users/insular/transcripts
./runpdf "/Users/insular/Desktop/book 📙/options-as-a-strategic-investment-fifth-edition-5nbsped-0735204659-9780735204652_compress.pdf" \
  --mode research \
  --prompt-file "/Users/insular/take two/take-two/option-research-engine/prompts/books/b_mcmillan_2012.md" \
  --engine text \
  --max-pages 40 \
  --research-chunk-tokens 12000 \
  --resume
```

Expected: page-bounded chunk outputs and a manifest; no standard whole-book summary.

- [ ] **Step 2: Run OCR pilots on Natenberg and Passarelli**

```bash
./runpdf "/Users/insular/Desktop/book 📙/pdfcoffee.com_option-volatility-and-pricing-sheldon-natenberg-pdf-free.pdf" \
  --mode research \
  --prompt-file "/Users/insular/take two/take-two/option-research-engine/prompts/books/b_natenberg_1994.md" \
  --engine ocrmypdf \
  --ocr-language eng \
  --max-pages 20 \
  --research-chunk-tokens 12000 \
  --resume

./runpdf "/Users/insular/Desktop/book 📙/pdfcoffee.com_dan-passarelli-trading-option-greekspdf-pdf-free.pdf" \
  --mode research \
  --prompt-file "/Users/insular/take two/take-two/option-research-engine/prompts/books/b_passarelli_2012.md" \
  --engine ocrmypdf \
  --ocr-language eng \
  --max-pages 20 \
  --research-chunk-tokens 12000 \
  --resume
```

- [ ] **Step 3: Review every pilot citation**

For each extracted rule:

- locate the cited `# Page N` in cached Markdown;
- compare the rule to the source passage;
- mark `supported`, `partially_supported`, or `unsupported`;
- verify every number and formula character by character;
- reject rules inferred from front matter or table-of-contents text.

- [ ] **Step 4: Write the pilot quality report**

Record:

- extraction engine and page range;
- Gemini request count;
- extracted/accepted/rejected rule counts;
- citation support rate;
- OCR errors;
- prompt changes;
- go/no-go decision per book.

- [ ] **Step 5: Iterate prompts until acceptance criteria pass**

Re-run only failed or weak chunks with `--resume` disabled after moving the prior local chunk output
to a timestamped ignored archive. Do not process a whole book until the report reaches the design
criteria.

- [ ] **Step 6: Commit only the quality report**

```bash
git add option-research-engine/research/pilot/QUALITY_REPORT.md
git commit -m "research: document PDF extraction pilot"
```

### Task 6: Process accepted books and consolidate documentary research

**Files:**
- Local ignored full-book outputs under `/Users/insular/transcripts/`
- Create: `option-research-engine/books/fiches/b_grinold_kahn_1999.md`
- Create: `option-research-engine/books/fiches/b_klarman_1991.md`
- Create: `option-research-engine/books/fiches/b_mauboussin_2001.md`
- Create: `option-research-engine/books/fiches/b_lynch_2000.md`
- Create: `option-research-engine/books/fiches/b_duke_notes.md`
- Create: six remaining prompts under `option-research-engine/prompts/books/`
- Create: accepted files under `option-research-engine/rules/<category>/`
- Modify: `option-research-engine/knowledge_base/registre_conflits.md`
- Modify: corresponding book fiches under `option-research-engine/books/fiches/`

- [ ] **Step 1: Prepare the six remaining source prompts**

Create standalone prompts for Douglas, Grinold/Kahn, Klarman, Mauboussin 2001, Lynch, and the
Annie Duke secondary notes. Create `draft_to_validate` fiches for sources that lack one. Do not
reuse `B-MAUBOUSSIN-2021` for the 2001 PDF; the two editions remain distinct sources.

The Annie Duke prompt must forbid market rules and set maximum source confidence to 2 because the
input is third-party notes rather than the complete book.

- [ ] **Step 2: Run full-book research only for pilot-approved sources**

Remove `--max-pages`, retain `--resume`, and process one book at a time. Stop if Gemini usage,
extraction quality, or citation support drifts materially from the pilot.

- [ ] **Step 3: Promote only manually supported rules**

Assign final IDs by category, copy one rule per file, and set history to:

```text
2026-07-05 — DOCUMENTARY_VALIDATED — source passage checked; quantitative validation pending
```

- [ ] **Step 4: Record conflicts and duplicates**

Add every open contradiction to `knowledge_base/registre_conflits.md`. Merge duplicate meaning only
when conditions, variables, and actions are logically equivalent; retain all source references.

- [ ] **Step 5: Update book journals**

Record processing date, PDF hash, edition, engine, prompt version, accepted/rejected counts, and
known OCR limitations. Never state that documentary validation proves profitability.

- [ ] **Step 6: Verify repository hygiene**

```bash
git diff --check
git status --short
git ls-files | rg '\\.(pdf|env)$' && exit 1 || true
rg -n 'GEMINI_API_KEY=|AIza' option-research-engine docs && exit 1 || true
```

- [ ] **Step 7: Commit each completed book separately**

```bash
git add option-research-engine/rules option-research-engine/knowledge_base/registre_conflits.md option-research-engine/books/fiches
git commit -m "research: integrate documentary rules from B-MCMILLAN-2012"
```

### Task 7: Final verification and handoff

**Files:**
- Modify: `option-research-engine/research/pilot/QUALITY_REPORT.md`

- [ ] **Step 1: Run Summarizer verification**

```bash
cd /Users/insular/transcripts
.venv/bin/python -m black --check src tests
.venv/bin/python -m ruff check src tests
.venv/bin/python -m pytest -q
detect-secrets scan $(git ls-files -co --exclude-standard)
```

- [ ] **Step 2: Verify Take Two research integrity**

```bash
cd "/Users/insular/take two/take-two"
git diff --check
python3 -m json.tool option-research-engine/research/corpus_manifest.json >/dev/null
rg -L '^## Page$' option-research-engine/rules/**/*.md
```

Expected: no formatting errors, valid manifest, and every promoted rule contains a page field.

- [ ] **Step 3: Report the boundary for the next phase**

The handoff must list:

- books processed;
- rules documentary-validated;
- rules rejected or still `to_review`;
- open conflicts;
- missing books;
- OCR limitations;
- exact files modified;
- Gemini usage delta;
- explicit statement that no IBKR or trading script has been created.

- [ ] **Step 4: Do not start IBKR work**

IBKR begins only after a separate user validation of the documentary research and a separate
design/specification cycle.
