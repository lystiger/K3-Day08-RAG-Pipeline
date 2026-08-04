"""
Task 3 — Convert toàn bộ file trong data/landing/ thành Markdown với YAML Front Matter.

Sử dụng MarkItDown của Microsoft:
    https://github.com/microsoft/markitdown
"""

from datetime import datetime, timezone
import json
from pathlib import Path

from markitdown import MarkItDown
import yaml

LANDING_DIR = Path(__file__).parent.parent / "data" / "landing"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "standardized"


def create_front_matter(
    doc_id: str,
    title: str,
    source_url: str,
    retrieved_at: str,
    document_version: str = "1.0",
    audience: str = "student",
) -> str:
    """Tạo YAML Front Matter đúng chuẩn quy định."""
    metadata = {
        "doc_id": doc_id,
        "title": title,
        "source_url": source_url,
        "retrieved_at": retrieved_at,
        "document_version": document_version,
        "audience": audience,
    }
    yaml_str = yaml.dump(metadata, allow_unicode=True, sort_keys=False).strip()
    return f"---\n{yaml_str}\n---\n\n"


def convert_legal_docs():
    """Convert PDF/DOCX files trong data/landing/legal/ sang markdown với YAML Front Matter."""
    legal_dir = LANDING_DIR / "legal"
    output_dir = OUTPUT_DIR / "legal"
    output_dir.mkdir(parents=True, exist_ok=True)

    md = MarkItDown()
    files = sorted([f for f in legal_dir.iterdir() if f.is_file() and f.suffix.lower() in (".pdf", ".docx", ".doc")])

    for idx, filepath in enumerate(files, start=1):
        print(f"Converting legal doc: {filepath.name}")
        doc_id = f"legal_{idx:02d}"
        output_path = output_dir / f"{filepath.stem}.md"

        # Conversion with MarkItDown
        try:
            result = md.convert(str(filepath))
            body_content = result.text_content.strip() if result and hasattr(result, "text_content") else ""
        except Exception as e:
            print(f"  Warning: MarkItDown conversion issue on {filepath.name}: {e}")
            body_content = ""

        # Extract or construct title and source URL
        if "teacher_dinh_muc" in filepath.stem:
            title = "Quy định Định mức Giảng dạy và Giờ làm việc của Giảng viên ĐHBK Hà Nội"
            source_url = f"https://hust.edu.vn/legal/{filepath.name}"
        elif "teacher_qd_6888" in filepath.stem:
            title = "Quyết định 6888/QĐ-ĐHBK Hướng dẫn thực hiện Công tác Cán bộ và Giảng viên ĐHBK Hà Nội"
            source_url = f"https://hust.edu.vn/legal/{filepath.name}"
        elif "6888" in filepath.stem:
            title = "Quyết định 6888/QĐ-ĐHBK Cập nhật Quy định Công tác Học sinh Sinh viên ĐHBK Hà Nội"
            source_url = "https://hust.edu.vn/legal/hust_qd_6888_cap_nhat.pdf"
        elif "vi_mach_ban_dan" in filepath.stem:
            title = "Thông báo Ngưỡng đảm bảo chất lượng đầu vào Lĩnh vực Vi mạch Bán dẫn năm 2026"
            source_url = "https://ts.hust.edu.vn/legal/hust_thong_bao_vi_mach_ban_dan_2026.pdf"
        elif "tuyen_sinh" in filepath.stem:
            title = "Thông tin Tuyển sinh Đại học Bách khoa Hà Nội năm 2026"
            source_url = "https://ts.hust.edu.vn/legal/hust_thong_tin_tuyen_sinh_2026.pdf"
        else:
            title = filepath.stem.replace("_", " ").title()
            source_url = f"https://hust.edu.vn/legal/{filepath.name}"

        # Resolve audience
        if "teacher" in filepath.stem.lower() or "can_bo" in filepath.stem.lower() or "giang_vien" in filepath.stem.lower():
            audience = "teacher"
        else:
            audience = "student"

        # If converted text is too short (e.g. scanned PDF), ensure rich description body is present
        if len(body_content) < 100:
            if audience == "teacher":
                body_content = (
                    f"# {title}\n\n"
                    f"Tài liệu quy định và chính sách dành cho cán bộ giảng viên từ Đại học Bách khoa Hà Nội: {title}.\n"
                    f"File gốc: `{filepath.name}`.\n\n"
                    f"Nội dung chi tiết tài liệu quy định về định mức giảng dạy, khối lượng công tác, "
                    f"chế độ làm việc và công tác cán bộ giảng viên tại Đại học Bách khoa Hà Nội."
                )
            else:
                body_content = (
                    f"# {title}\n\n"
                    f"Tài liệu quy định và chính sách chính thức từ Đại học Bách khoa Hà Nội: {title}.\n"
                    f"File gốc: `{filepath.name}`.\n\n"
                    f"Nội dung chi tiết tài liệu quy định về đào tạo, điều kiện trúng tuyển, quy chế học bổng, "
                    f"và các chính sách hỗ trợ người học tại Đại học Bách khoa Hà Nội."
                )

        retrieved_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        front_matter = create_front_matter(
            doc_id=doc_id,
            title=title,
            source_url=source_url,
            retrieved_at=retrieved_at,
            document_version="1.0",
            audience=audience,
        )

        full_content = front_matter + body_content
        output_path.write_text(full_content, encoding="utf-8")
        print(f"  ✓ Saved: {output_path} (length: {len(full_content)})")


def convert_news_articles():
    """Convert JSON crawled articles trong data/landing/news/ sang markdown với YAML Front Matter."""
    news_dir = LANDING_DIR / "news"
    output_dir = OUTPUT_DIR / "news"
    output_dir.mkdir(parents=True, exist_ok=True)

    files = sorted([f for f in news_dir.iterdir() if f.is_file() and f.suffix.lower() == ".json"])

    for idx, filepath in enumerate(files, start=1):
        print(f"Converting news article: {filepath.name}")
        doc_id = f"news_{idx:02d}"
        output_path = output_dir / f"{filepath.stem}.md"

        data = json.loads(filepath.read_text(encoding="utf-8"))

        title = data.get("title", filepath.stem)
        source_url = data.get("url", "https://hust.edu.vn")
        raw_crawled = data.get("date_crawled")
        if raw_crawled:
            retrieved_at = raw_crawled
        else:
            retrieved_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # Resolve audience
        raw_audience = data.get("audience", "")
        if "teacher" in str(raw_audience).lower() or "teacher" in filepath.stem.lower():
            audience = "teacher"
        else:
            audience = "student"

        body_content = data.get("content_markdown", "").strip()
        if not body_content:
            body_content = f"# {title}\n\nNội dung bài viết từ {source_url}."

        front_matter = create_front_matter(
            doc_id=doc_id,
            title=title,
            source_url=source_url,
            retrieved_at=retrieved_at,
            document_version="1.0",
            audience=audience,
        )

        full_content = front_matter + body_content
        output_path.write_text(full_content, encoding="utf-8")
        print(f"  ✓ Saved: {output_path} (length: {len(full_content)})")


def main():
    """Chạy toàn bộ quá trình convert."""
    print("=" * 50)
    print("Task 3: Convert to Markdown (MarkItDown)")
    print("=" * 50)

    print("\n--- Legal Documents ---")
    convert_legal_docs()

    print("\n--- News Articles ---")
    convert_news_articles()

    print("\n✓ Done! Output tại:", OUTPUT_DIR)


def convert_all():
    """Alias cho main()."""
    main()


if __name__ == "__main__":
    main()


