"""
Task 8 — PageIndex Vectorless RAG.

Đăng ký tài khoản tại: https://pageindex.ai/
SDK & sample code: https://github.com/VectifyAI/PageIndex

PageIndex cho phép RAG mà không cần vector store — sử dụng
structural understanding của document thay vì embedding.

Cài đặt:
    pip install pageindex fpdf2

Luồng:
    1. md_to_pdf(): PageIndex nhận PDF, không nhận .md → convert trước bằng fpdf2
    2. upload_documents(): submit từng PDF, lưu doc_id vào data/pageindex_docs.json
    3. pageindex_search(): submit_query → poll get_retrieval → parse retrieved_nodes

Lưu ý: API `/retrieval` của PageIndex hiện đã deprecated (vẫn hoạt động, nhưng response
có field "deprecation" cảnh báo) và trả kết quả trong "retrieved_nodes" — mỗi node có
"relevant_contents": list[list[{section_title, relevant_content}]]. In response thật ra
(json.dumps(...)) trước khi viết logic parse, đừng đoán schema từ ví dụ code cũ.

NGUYÊN TẮC: mọi lỗi / thiếu key / thiếu SDK → return [], KHÔNG raise. Module này là
đường FALLBACK của Task 9, nó chết thì cả pipeline chết theo.
"""

import json
import os
import time
from pathlib import Path

from pathlib import Path
from dotenv import load_dotenv

# Load env variables từ đúng thư mục dự án
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=PROJECT_ROOT / ".env", override=True)

PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY", "")
STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
# Tên khớp với .gitignore sẵn có của repo (pageindex_pdfs/, pageindex_doc_ids.json)
PDF_CACHE_DIR = Path(__file__).parent.parent / "data" / "pageindex_pdfs"
DOC_REGISTRY = Path(__file__).parent.parent / "data" / "pageindex_doc_ids.json"

POLL_INTERVAL_SEC = 3
POLL_MAX_ATTEMPTS = 20

# Corpus của nhóm là TIẾNG VIỆT → font core của fpdf2 (Helvetica, latin-1) sẽ nuốt
# hết dấu: "học phí" → "hoc phi". PageIndex đọc PDF đó sẽ index sai hoàn toàn.
# Bắt buộc nhúng 1 font TTF Unicode. Tìm theo thứ tự dưới, dừng ở file đầu tiên có thật.
UNICODE_FONT_CANDIDATES = [
    Path("/Library/Fonts/Arial Unicode.ttf"),                        # macOS
    Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),    # macOS
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),         # Linux
    Path("C:/Windows/Fonts/arial.ttf"),                              # Windows
    Path(__file__).parent.parent / "fonts" / "DejaVuSans.ttf",       # tự bỏ vào repo
]


MAX_TOKEN_LEN = 60  # token dài hơn mức này sẽ bị chèn khoảng trắng để xuống dòng được


def _soft_wrap(line: str, max_token_len: int = MAX_TOKEN_LEN) -> str:
    """
    Chèn khoảng trắng vào các token quá dài để fpdf2 xuống dòng được.

    Markdown của nhóm có bảng kẻ ngang ('|--------...---|') và URL dài — đó là các
    "từ" không có khoảng trắng, rộng hơn bề ngang trang giấy, khiến multi_cell()
    ném 'Not enough horizontal space to render a single character' và hỏng cả file.
    """
    parts = []
    for token in line.split(" "):
        if len(token) > max_token_len:
            token = " ".join(
                token[i : i + max_token_len] for i in range(0, len(token), max_token_len)
            )
        parts.append(token)
    return " ".join(parts)


def _find_unicode_font() -> Path | None:
    """Trả về TTF Unicode đầu tiên tìm được, hoặc None."""
    for candidate in UNICODE_FONT_CANDIDATES:
        if candidate.exists():
            return candidate
    return None


def md_to_pdf(md_file: Path, out_dir: Path = PDF_CACHE_DIR) -> Path | None:
    """
    Convert 1 file .md sang PDF bằng fpdf2 (PageIndex chỉ nhận PDF, không nhận .md).

    Nhúng font TTF Unicode để giữ dấu tiếng Việt. Nếu máy không có font nào trong
    UNICODE_FONT_CANDIDATES thì degrade về Helvetica + latin-1 và IN CẢNH BÁO RÕ —
    lúc đó PDF sẽ mất dấu và kết quả PageIndex không dùng được cho corpus tiếng Việt.

    Returns:
        Path tới PDF, hoặc None nếu convert thất bại.
    """
    try:
        from fpdf import FPDF
    except ImportError:
        print("⚠ Thiếu fpdf2 — chạy: pip install fpdf2")
        return None

    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = out_dir / f"{md_file.stem}.pdf"

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        font_path = _find_unicode_font()
        if font_path is not None:
            pdf.add_font("uni", "", str(font_path))
            pdf.set_font("uni", size=11)
            transcode = False
        else:
            print(
                "⚠ Không tìm thấy font Unicode — PDF sẽ MẤT DẤU tiếng Việt.\n"
                "  Tải DejaVuSans.ttf vào fonts/ hoặc sửa UNICODE_FONT_CANDIDATES."
            )
            pdf.set_font("Helvetica", size=11)
            transcode = True

        for line in md_file.read_text(encoding="utf-8").splitlines():
            text = _soft_wrap(line)
            if transcode:
                text = text.encode("latin-1", "replace").decode("latin-1")
            # new_x/new_y bắt buộc: mặc định của fpdf2 2.8 giữ con trỏ ở MÉP PHẢI
            # sau mỗi multi_cell → dòng kế tiếp không còn bề ngang → ném
            # "Not enough horizontal space to render a single character".
            pdf.multi_cell(0, 6, text or " ", new_x="LMARGIN", new_y="NEXT")

        pdf.output(str(pdf_path))
        return pdf_path
    except Exception as e:  # noqa: BLE001
        print(f"⚠ Convert PDF thất bại cho {md_file.name}: {e}")
        return None


def _get_client():
    """Khởi tạo PageIndexClient, trả None nếu thiếu key hoặc thiếu SDK."""
    if not PAGEINDEX_API_KEY:
        return None
    try:
        from pageindex.client import PageIndexClient
    except ImportError:
        print("⚠ Thiếu SDK pageindex — chạy: pip install pageindex")
        return None
    try:
        return PageIndexClient(api_key=PAGEINDEX_API_KEY)
    except Exception as e:  # noqa: BLE001
        print(f"⚠ Không khởi tạo được PageIndexClient: {e}")
        return None


def _load_registry() -> dict:
    """Đọc map {md_filename: doc_id} đã upload trước đó."""
    if DOC_REGISTRY.exists():
        try:
            return json.loads(DOC_REGISTRY.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            return {}
    return {}


def upload_documents() -> dict:
    """
    Convert markdown → PDF rồi upload toàn bộ lên PageIndex.

    Returns:
        dict {md_filename: doc_id}. Trả {} nếu thiếu key/SDK hoặc chưa có dữ liệu.
        Kết quả được ghi ra data/pageindex_docs.json để pageindex_search() tái dùng.
    """
    client = _get_client()
    if client is None:
        print("⚠ Thiếu PAGEINDEX_API_KEY hoặc SDK — bỏ qua upload")
        return {}

    registry = _load_registry()
    md_files = sorted(STANDARDIZED_DIR.rglob("*.md"))
    if not md_files:
        print("⚠ data/standardized/ chưa có .md — chờ Role 2 (Task 3)")
        return registry

    for md_file in md_files:
        if md_file.name in registry:
            continue  # đã upload rồi, không tốn call

        pdf_path = md_to_pdf(md_file)
        if pdf_path is None:
            continue

        try:
            resp = client.submit_document(str(pdf_path))
            doc_id = resp.get("doc_id") or resp.get("id")
            if doc_id:
                registry[md_file.name] = doc_id
                print(f"  ✓ Uploaded: {md_file.name} -> {doc_id}")
            else:
                print(f"  ✗ Không lấy được doc_id cho {md_file.name}: {resp}")
        except Exception as e:  # noqa: BLE001
            print(f"  ✗ Upload lỗi {md_file.name}: {e}")

    DOC_REGISTRY.parent.mkdir(parents=True, exist_ok=True)
    DOC_REGISTRY.write_text(
        json.dumps(registry, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return registry


def _poll_retrieval(client, retrieval_id: str) -> dict:
    """Poll cho tới khi status == 'completed' (hoặc hết lượt). Trả {} nếu fail."""
    for _ in range(POLL_MAX_ATTEMPTS):
        try:
            retrieval = client.get_retrieval(retrieval_id)
        except Exception as e:  # noqa: BLE001
            print(f"⚠ get_retrieval lỗi: {e}")
            return {}
        status = retrieval.get("status")
        if status == "completed":
            return retrieval
        if status in ("failed", "error"):
            print(f"⚠ Retrieval {retrieval_id} status={status}")
            return {}
        time.sleep(POLL_INTERVAL_SEC)
    print(f"⚠ Retrieval {retrieval_id} timeout sau {POLL_MAX_ATTEMPTS} lần poll")
    return {}


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """
    Vectorless retrieval sử dụng PageIndex.
    Dùng làm fallback khi hybrid search không có kết quả tốt.

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả tối đa

    Returns:
        List of {
            'content': str,
            'score': float,       # PageIndex không trả score → tự gán giảm dần theo rank
            'metadata': dict,
            'source': 'pageindex' # key TOP-LEVEL, khác metadata['source']
        }
        Trả [] khi thiếu API key / SDK / chưa upload / có lỗi. KHÔNG raise.
    """
    if not PAGEINDEX_API_KEY:
        print("⚠ Thiếu PAGEINDEX_API_KEY — bỏ qua PageIndex fallback")
        return []

    client = _get_client()
    if client is None:
        return []

    registry = _load_registry()
    if not registry:
        registry = upload_documents()
    if not registry:
        return []

    results: list[dict] = []
    for md_name, doc_id in registry.items():
        if len(results) >= top_k:
            break
        try:
            # submit_document trả doc_id NGAY, nhưng PageIndex còn phải dựng cây
            # mục lục + OCR ở background. Query sớm sẽ lỗi → bỏ qua doc chưa sẵn sàng.
            if not client.is_retrieval_ready(doc_id):
                print(f"⏳ {md_name} chưa index xong trên PageIndex — bỏ qua")
                continue

            resp = client.submit_query(doc_id=doc_id, query=query)
            retrieval_id = resp.get("retrieval_id") or resp.get("id")
            if not retrieval_id:
                continue

            retrieval = _poll_retrieval(client, retrieval_id)
            if not retrieval:
                continue

            for node in retrieval.get("retrieved_nodes", [])[:2]:
                for group in node.get("relevant_contents", []) or []:
                    for item in group or []:
                        content = item.get("relevant_content", "")
                        if not content:
                            continue
                        rank = len(results) + 1
                        results.append(
                            {
                                "content": content,
                                # score giả lập giảm dần theo rank để Task 9 sort được
                                "score": 1.0 / rank,
                                "metadata": {
                                    "source": md_name,
                                    "type": "legal" if "legal" in md_name else "news",
                                    "section": item.get("section_title"),
                                },
                                "source": "pageindex",
                            }
                        )
        except Exception as e:  # noqa: BLE001
            print(f"⚠ Query PageIndex lỗi trên {md_name}: {e}")
            continue

    return results[:top_k]


if __name__ == "__main__":
    if not PAGEINDEX_API_KEY:
        print("⚠ Hãy set PAGEINDEX_API_KEY trong file .env")
        print("  Đăng ký tại: https://pageindex.ai/")
        print("  (pageindex_search() vẫn trả [] an toàn, không làm sập Task 9)")
    else:
        print("Uploading documents...")
        upload_documents()

        print("\nTest query:")
        results = pageindex_search("tuition fee payment methods", top_k=3)
        for r in results:
            print(f"[{r['score']:.3f}] {r['content'][:100]}...")
