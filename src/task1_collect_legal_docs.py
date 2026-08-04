"""
Task 1 — Thu thập văn bản chính sách/quy định dịch vụ đại học HUST.

Thực hiện crawler tải các file PDF quy định, thông tin tuyển sinh, quyết định đào tạo từ HUST.
"""

from pathlib import Path
import time
import requests
import urllib3

# Suppress insecure HTTPS warnings if verify=False is used
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "legal"

HUST_PDF_URLS = [
    {
        "url": "https://hust.edu.vn/uploads/sys/tuyen-sinh/2023_06/thong-tin-tuyen-sinh-dai-hoc-2026f.pdf",
        "filename": "hust_thong_tin_tuyen_sinh_2026.pdf"
    },
    {
        "url": "https://hust.edu.vn/uploads/sys/tuyen-sinh/2023_06/6888_qd-dhbk-cap-nhat.pdf",
        "filename": "hust_qd_6888_cap_nhat.pdf"
    },
    {
        "url": "https://hust.edu.vn/uploads/sys/news/2026_07/th_ng_b_o_v__ng__ng_ng_nh_vi_m_ch_b_n_d_n_n_m_2026_14.07.2026_final.pdf",
        "filename": "hust_thong_bao_vi_mach_ban_dan_2026.pdf"
    }
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def setup_directory():
    """Tạo thư mục data/landing/legal/ nếu chưa có."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"✓ Thư mục đã sẵn sàng: {DATA_DIR}")


def download_legal_docs():
    """Tải các văn bản pháp luật / chính sách PDF từ HUST."""
    setup_directory()
    downloaded_files = []

    for i, item in enumerate(HUST_PDF_URLS):
        url = item["url"]
        filename = item["filename"]
        filepath = DATA_DIR / filename

        print(f"[{i+1}/{len(HUST_PDF_URLS)}] Đang tải {filename} từ {url}...")
        try:
            # R4 compliance: proper User-Agent header, handle SSL verify=False if needed
            response = requests.get(url, headers=HEADERS, timeout=30, verify=False)
            response.raise_for_status()

            if len(response.content) <= 1024:
                print(f"⚠️ Cảnh báo: File {filename} quá nhỏ ({len(response.content)} bytes)")
            else:
                filepath.write_bytes(response.content)
                print(f"✓ Đã tải thành công: {filepath} ({len(response.content)} bytes)")
                downloaded_files.append(filepath)

        except Exception as e:
            print(f"❌ Lỗi khi tải {url}: {e}")

        # R4 compliance: delay >= 1s between requests
        if i < len(HUST_PDF_URLS) - 1:
            time.sleep(1.0)

    return downloaded_files


def main():
    download_legal_docs()


if __name__ == "__main__":
    main()
