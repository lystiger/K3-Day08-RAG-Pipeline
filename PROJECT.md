# Project: K3-Day08-RAG-Pipeline

## Architecture
- `data/landing/legal/`: Target directory for raw legal/policy PDF files scraped from HUST (Task 1).
- `data/landing/news/`: Target directory for raw news article JSON files scraped from HUST (Task 2).
- `data/standardized/legal/`: Target directory for standardized Markdown files converted from legal PDFs with YAML Front Matter (Task 3).
- `data/standardized/news/`: Target directory for standardized Markdown files converted from news JSONs with YAML Front Matter (Task 3).
- `src/task1_collect_legal_docs.py`: Entry point for Task 1 legal PDF downloading.
- `src/task2_crawl_news.py`: Entry point for Task 2 news JSON crawling.
- `src/task3_convert_markdown.py`: Entry point for Task 3 MarkItDown Markdown standardization.
- `tests/test_individual.py`: Pytest test suite validating Task 1 (`TestTask1`), Task 2 (`TestTask2`), and Task 3 (`TestTask3`).

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Legal PDF Collector | Download >= 3 real legal/policy PDFs (> 1KB) from hust.edu.vn/ts.hust.edu.vn into `data/landing/legal/` | M1 | survey |
| 2 | News JSON Scraper | Crawl >= 5 real news articles (> 500B) into `data/landing/news/*.json` with metadata (`url`, `title`, `date_crawled`, `content_markdown`) | M2 | survey |
| 3 | MarkItDown Standardizer | Convert all PDFs & JSONs to MD in `data/standardized/` with full YAML Front Matter (`doc_id`, `title`, `source_url`, `retrieved_at`, `document_version`, `audience`) | M3 | survey |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | M1_Legal_PDF_Scraper | Implement Task 1 in `src/task1_collect_legal_docs.py` and pass `TestTask1` | none | IN_PROGRESS |
| 2 | M2_News_JSON_Scraper | Implement Task 2 in `src/task2_crawl_news.py` and pass `TestTask2` | none | IN_PROGRESS |
| 3 | M3_MarkItDown_Standardizer | Implement Task 3 in `src/task3_convert_markdown.py` and pass `TestTask3` | M1, M2 | PLANNED |

## Interface Contracts
### Task 1 ↔ Task 3 (Legal PDFs)
- Input path: `data/landing/legal/*.pdf`
- File condition: Valid PDF format, file size > 1024 bytes.
- Output path: `data/standardized/legal/*.md`
- Header: YAML Front Matter containing `doc_id`, `title`, `source_url`, `retrieved_at`, `document_version`, `audience`.

### Task 2 ↔ Task 3 (News JSON)
- Input path: `data/landing/news/*.json`
- File condition: Valid JSON schema `{"url": str, "title": str, "date_crawled": str, "content_markdown": str}`, file size > 500 bytes.
- Output path: `data/standardized/news/*.md`
- Header: YAML Front Matter containing `doc_id`, `title`, `source_url`, `retrieved_at`, `document_version`, `audience`.

## Code Layout
- `src/task1_collect_legal_docs.py`: Task 1 implementation file.
- `src/task2_crawl_news.py`: Task 2 implementation file.
- `src/task3_convert_markdown.py`: Task 3 implementation file.
- `tests/test_individual.py`: Test suite for verification.
