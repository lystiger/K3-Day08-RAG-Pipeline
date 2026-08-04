"""
Task 2 — Crawl bài viết/thông báo về dịch vụ đại học HUST.

Mô tả:
    1. Crawl tối thiểu 5 bài viết từ trang công khai của Đại học Bách khoa Hà Nội (HUST).
    2. Crawl tối thiểu 3 bài viết dành cho giảng viên/giáo viên (audience: teacher).
    3. Lưu output vào data/landing/news/
    4. Mỗi bài lưu 1 file JSON với metadata (url, title, date_crawled, content_markdown, audience).
"""

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
import urllib3
import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as md

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "news"

ARTICLE_URLS = [
    # Student articles (5)
    {
        "url": "https://ts.hust.edu.vn/tin-tuc/chi-tiet-55-chuong-trinh-dao-tao-tai-bach-khoa-ha-noi-nhan-hoc-bong-chinh-phu-theo-nghi-dinh-179",
        "audience": "student",
        "filename": "article_01.json"
    },
    {
        "url": "https://ts.hust.edu.vn/tin-tuc/thong-tin-tuyen-sinh-nam-2026",
        "audience": "student",
        "filename": "article_02.json"
    },
    {
        "url": "https://ts.hust.edu.vn/tin-tuc/huong-dan-dang-ky-xac-thuc-chung-chi-ngoai-ngu-2026",
        "audience": "student",
        "filename": "article_03.json"
    },
    {
        "url": "https://hust.edu.vn/vi/news/hoat-dong-chung/sinh-vien-bach-khoa-tu-tin-toa-sang-truoc-11-quoc-gia-thanh-vien-asean-trung-quoc-656008.html",
        "audience": "student",
        "filename": "article_04.json"
    },
    {
        "url": "https://hust.edu.vn/vi/news/tin-tuc-su-kien/icce-2026-tai-nha-trang-diem-hen-cho-nhung-giai-phap-cong-nghe-phuc-vu-con-nguoi-656002.html",
        "audience": "student",
        "filename": "article_05.json"
    },
    # Teacher articles (3)
    {
        "url": "https://hust.edu.vn/vi/news/to-chuc-nhan-su-tuyen-dung/tien-si-kep-nganh-hoa-tro-thanh-giang-vien-xuat-sac-bach-khoa-ha-noi-655814.html",
        "audience": "teacher",
        "filename": "teacher_article_01.json"
    },
    {
        "url": "https://hust.edu.vn/vi/news/to-chuc-nhan-su-tuyen-dung/bo-gd-dt-cong-bo-loat-quyet-dinh-bo-nhiem-lanh-dao-co-so-gd-dai-hoc-gd-nghe-nghiep-truc-thuoc-655931.html",
        "audience": "teacher",
        "filename": "teacher_article_02.json"
    },
    {
        "url": "https://hust.edu.vn/vi/news/to-chuc-nhan-su-tuyen-dung/gs-ts-ngut-le-anh-tuan-duoc-bo-nhiem-giu-chuc-giam-doc-dai-hoc-bach-khoa-ha-noi-655916.html",
        "audience": "teacher",
        "filename": "teacher_article_03.json"
    },
]


def setup_directory():
    """Tạo thư mục data/landing/news/ nếu chưa có."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


async def crawl_article(url: str, audience: str = "student") -> dict:
    """
    Crawl một bài viết và trả về dict chứa metadata + content.

    Returns:
        {
            "url": str,
            "title": str,
            "date_crawled": str (ISO format),
            "content_markdown": str,
            "audience": str
        }
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None,
        lambda: requests.get(url, headers=headers, verify=False, timeout=15)
    )
    response.encoding = response.apparent_encoding or "utf-8"

    soup = BeautifulSoup(response.text, "html.parser")

    # Remove non-content tags
    for tag in soup(["script", "style", "nav", "header", "footer", "iframe", "form", "button"]):
        tag.decompose()

    h1 = soup.find("h1")
    title = (
        h1.get_text(strip=True)
        if h1
        else (soup.find("title").get_text(strip=True) if soup.find("title") else "Untitled")
    )

    container = None
    if h1:
        c = h1.parent
        while c and c.name != "body":
            classes = c.get("class", [])
            class_str = " ".join(classes) if isinstance(classes, list) else str(classes)
            if any(k in class_str for k in ["news_column", "col-md-9", "detail", "content", "panel-body", "page-content"]):
                container = c
                break
            c = c.parent
        if not container:
            container = h1.parent

    if not container:
        container = soup.find("main") or soup.find("article") or soup.body

    content_markdown = md(str(container), heading_style="ATX").strip()
    if not content_markdown:
        content_markdown = container.get_text(separator="\n\n", strip=True)

    # Fallback audience check based on URL/title keywords if default 'student' was passed
    if audience == "student" and any(k in url for k in ["giang-vien", "tuyen-dung", "nhan-su"]):
        audience = "teacher"

    return {
        "url": url,
        "title": title,
        "date_crawled": datetime.now().isoformat(),
        "content_markdown": content_markdown,
        "audience": audience,
    }


async def crawl_all():
    """Crawl toàn bộ bài viết trong ARTICLE_URLS."""
    setup_directory()

    total = len(ARTICLE_URLS)
    for i, item in enumerate(ARTICLE_URLS, 1):
        if isinstance(item, dict):
            url = item["url"]
            audience = item.get("audience", "student")
            filename = item.get("filename", f"article_{i:02d}.json")
        else:
            url = str(item)
            audience = "teacher" if any(k in url for k in ["giang-vien", "tuyen-dung", "nhan-su"]) else "student"
            filename = f"article_{i:02d}.json"

        print(f"[{i}/{total}] Crawling ({audience}): {url}")
        article = await crawl_article(url, audience=audience)

        # Lưu file JSON
        filepath = DATA_DIR / filename
        filepath.write_text(json.dumps(article, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  ✓ Saved: {filepath}")

        # Enforce rate limit / delay >= 1 sec (R4)
        if i < total:
            await asyncio.sleep(1.0)


if __name__ == "__main__":
    if not ARTICLE_URLS:
        print("⚠ Hãy điền ARTICLE_URLS trước khi chạy!")
        print("Gợi ý: tìm trang thông báo/sự kiện trên trang chính thức của trường đại học")
    else:
        asyncio.run(crawl_all())

