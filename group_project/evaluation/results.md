# RAG Pipeline Evaluation & A/B Testing Report (HUST Domain)

Báo cáo so sánh chất lượng câu trả lời giữa hai cấu hình RAG Pipeline trên bộ tài liệu thực tế của Đại học Bách khoa Hà Nội (HUST).

> ⚠️ **Phạm vi lần chạy này: 1/16 câu** trong `golden_dataset.json` (do hạn mức 429 của LLM
> free tier). Vì vậy bảng §3 "Worst Performers" mới có 1 dòng thay vì bottom 3, và các số
> trung bình ở §1 chưa đủ ý nghĩa thống kê. Chạy lại đầy đủ:
> `python -m group_project.evaluation.eval_pipeline` — file này sẽ được ghi đè bằng kết quả 16 câu.

## 1. Tóm tắt Điểm số Trung bình (Overall Mean Scores)

| Metric | Config A: Hybrid + Rerank | Config B: Dense Only | Chênh lệch (A - B) |
| :--- | :---: | :---: | :---: |
| **Faithfulness** | 0.6667 | 0.8333 | -0.1667 |
| **Answer Relevancy** | 0.9437 | 0.7639 | +0.1798 |
| **Context Recall** | 1.0000 | 1.0000 | +0.0000 |
| **Context Precision** | 0.2000 | 0.3667 | -0.1667 |

## 2. Chi tiết Kết quả Đánh giá theo từng Câu hỏi

### Config A: Hybrid + Reranking

| QID | Question | Faithfulness | Answer Relevancy | Context Recall | Context Precision |
| :---: | :--- | :---: | :---: | :---: | :---: |
| 1 | Quyết định 6888/QĐ-ĐHBK cập nhật Quy định Công tác Học sinh Sinh viên Đại học Bách khoa Hà Nội có nội dung chi tiết quy định về những lĩnh vực nào? | 0.6667 | 0.9437 | 1.0000 | 0.2000 |

### Config B: Dense Search Only

| QID | Question | Faithfulness | Answer Relevancy | Context Recall | Context Precision |
| :---: | :--- | :---: | :---: | :---: | :---: |
| 1 | Quyết định 6888/QĐ-ĐHBK cập nhật Quy định Công tác Học sinh Sinh viên Đại học Bách khoa Hà Nội có nội dung chi tiết quy định về những lĩnh vực nào? | 0.8333 | 0.7639 | 1.0000 | 0.3667 |

## 3. Worst Performers (Bottom 3 Q&A trong Config A)

| QID | Question | Điểm TB | Nguyên nhân & Hướng giải quyết đề xuất |
| :---: | :--- | :---: | :--- |
| 1 | Quyết định 6888/QĐ-ĐHBK cập nhật Quy định Công tác Học sinh Sinh viên Đại học Bách khoa Hà Nội có nội dung chi tiết quy định về những lĩnh vực nào? | 0.7026 | Điểm relevancy thấp. Câu trả lời của LLM lan man, cần thêm post-processing lọc nhiễu văn cảnh. |

## 4. Đề xuất Cải tiến Hệ thống (Recommendations)
1. **Tối ưu hóa Alpha trong Hybrid Search:** Điều chỉnh tỉ lệ trọng số BM25 và Dense Search để tăng độ phủ đối với các từ viết tắt chuyên ngành Bách Khoa (như HUST, TNTHPT, VSTEP).
2. **Cải tiến Chunking:** Áp dụng Semantic Chunking thay vì RecursiveCharacterTextSplitter cố định để các đoạn văn quy chế giữ nguyên tính toàn vẹn thông tin.
3. **Fine-tune Cross-Encoder:** Huấn luyện Cross-Encoder trên tập dữ liệu tiếng Việt chuyên ngành để nâng cao độ chính xác của bước Reranking.
