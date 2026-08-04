# RAG Pipeline Evaluation & A/B Testing Report (HUST Domain)

Báo cáo so sánh chất lượng câu trả lời giữa hai cấu hình RAG Pipeline trên bộ tài liệu thực tế của Đại học Bách khoa Hà Nội (HUST).

## 1. Tóm tắt Điểm số Trung bình (Overall Mean Scores)

| Metric | Config A: Hybrid + Rerank | Config B: Dense Only | Chênh lệch (A - B) |
| :--- | :---: | :---: | :---: |
| **Faithfulness** | 0.7521 | 0.6429 | +0.1092 |
| **Answer Relevancy** | 0.7391 | 0.6633 | +0.0758 |
| **Context Recall** | 0.9688 | 0.9643 | +0.0045 |
| **Context Precision** | 0.6030 | 0.8194 | -0.2165 |

## 2. Chi tiết Kết quả Đánh giá theo từng Câu hỏi

### Config A: Hybrid + Reranking

| QID | Question | Faithfulness | Answer Relevancy | Context Recall | Context Precision |
| :---: | :--- | :---: | :---: | :---: | :---: |
| 1 | Quyết định 6888/QĐ-ĐHBK cập nhật Quy định Công tác Học sinh Sinh viên Đại học Bách khoa Hà Nội có nội dung chi tiết quy định về những lĩnh vực nào? | 1.0000 | 0.9070 | 1.0000 | 0.2000 |
| 2 | Theo Thông báo ngưỡng đảm bảo chất lượng đầu vào lĩnh vực Vi mạch Bán dẫn năm 2026, ngưỡng yêu cầu được xác định dựa trên điểm thi nào và bao gồm bao nhiêu tiêu chí? | 1.0000 | 0.8795 | 1.0000 | 0.3333 |
| 3 | Theo Thông báo ngưỡng đảm bảo chất lượng đầu vào lĩnh vực Vi mạch Bán dẫn năm 2026, tiêu chí thứ nhất về tổng điểm thi được quy định như thế nào? | 1.0000 | 0.8911 | 1.0000 | 0.2000 |
| 4 | Theo Quyết định phê duyệt Thông tin tuyển sinh đại học năm 2026 của Đại học Bách khoa Hà Nội, Quy chế tuyển sinh đại học được ban hành kèm theo Quyết định số bao nhiêu và ngày nào của Giám đốc Đại học Bách khoa Hà Nội? | 0.5000 | 0.9351 | 1.0000 | 0.3333 |
| 5 | Theo tài liệu teacher_dinh_muc_giang_day.md, văn bản được Giám đốc Đại học Bách khoa Hà Nội phê duyệt là gì và căn cứ vào Luật Giáo dục đại học ngày nào? | 0.0000 | 0.0000 | 1.0000 | 1.0000 |
| 6 | Theo tài liệu teacher_dinh_muc_giang_day.md, Quy chế tuyển sinh đại học được ban hành kèm theo Quyết định số bao nhiêu và ngày ký là ngày nào? | 0.0000 | 0.0000 | 1.0000 | 1.0000 |
| 7 | Tài liệu teacher_qd_6888_can_bo.md có doc_id là gì và đối tượng áp dụng (audience) là ai? | 0.8000 | 0.9569 | 0.5000 | 0.0000 |
| 8 | Theo tài liệu teacher_qd_6888_can_bo.md, nội dung chi tiết của Quyết định 6888/QĐ-ĐHBK quy định về những vấn đề gì? | 1.0000 | 0.8768 | 1.0000 | 0.2500 |
| 9 | Kỳ tuyển sinh năm 2026, Đại học Bách khoa Hà Nội công bố tổng chỉ tiêu tuyển sinh là bao nhiêu sinh viên, cho bao nhiêu chương trình đào tạo, và chính sách học bổng theo Nghị định số 179/2026/NĐ-CP được áp dụng cho bao nhiêu chương trình? | 0.8333 | nan | 1.0000 | 1.0000 |
| 10 | Thông tin tuyển sinh đại học năm 2026 của Đại học Bách khoa Hà Nội được ban hành căn cứ vào Thông tư số mấy, ngày bao nhiêu của Bộ Giáo dục và Đào tạo? | 0.5000 | 0.9095 | 1.0000 | 0.3250 |
| 11 | Theo Hướng dẫn đăng ký xác thực chứng chỉ Ngoại ngữ 2026, thí sinh cần đạt điểm thi tốt nghiệp THPT năm 2026 môn ngoại ngữ từ bao nhiêu trở lên, và chứng chỉ tiếng Anh VSTEP được quy đổi thành điểm môn tiếng Anh khi xét tuyển theo các tổ hợp nào? | 0.4000 | 0.8694 | 1.0000 | 0.8667 |
| 12 | Hội nghị Quốc tế lần thứ 11 về Truyền thông và Điện tử (IEEE ICCE 2026) diễn ra tại đâu, trong khoảng thời gian nào, và gắn với dấu mốc kỷ niệm bao nhiêu năm thành lập Đại học Bách khoa Hà Nội? | 1.0000 | nan | 1.0000 | 1.0000 |
| 13 | TS. Nguyễn Quang Minh được giới thiệu trong bài viết sở hữu hai tấm bằng tiến sĩ tại những quốc gia nào và giữ vai trò gì tại start-up công nghệ plasma ở Anh? | 1.0000 | 0.8509 | 1.0000 | 1.0000 |
| 14 | TS. Nguyễn Quang Minh tham gia Đề án thu hút và tuyển dụng giảng viên trẻ tài năng, chuyên gia, nhà khoa học đầu ngành của Đại học Bách khoa Hà Nội giai đoạn nào, tên viết tắt là gì? | 1.0000 | nan | 1.0000 | 0.5000 |
| 15 | Theo bài viết 'Bộ GD&ĐT công bố loạt quyết định bổ nhiệm lãnh đạo cơ sở GD đại học, GD nghề nghiệp trực thuộc', Bộ trưởng Bộ GD&ĐT nào đã trao các quyết định bổ nhiệm cho ban lãnh đạo Đại học Bách khoa Hà Nội trong Hội nghị chiều 5/6? | 1.0000 | 0.7628 | 1.0000 | 0.6389 |
| 16 | GS.TS. NGƯT. Lê Anh Tuấn được bổ nhiệm giữ chức Giám đốc Đại học Bách khoa Hà Nội theo quyết định số mấy và ban hành ngày nào? | 1.0000 | 0.7692 | 1.0000 | 1.0000 |

### Config B: Dense Search Only

| QID | Question | Faithfulness | Answer Relevancy | Context Recall | Context Precision |
| :---: | :--- | :---: | :---: | :---: | :---: |
| 1 | Quyết định 6888/QĐ-ĐHBK cập nhật Quy định Công tác Học sinh Sinh viên Đại học Bách khoa Hà Nội có nội dung chi tiết quy định về những lĩnh vực nào? | 1.0000 | 0.9515 | 1.0000 | nan |
| 2 | Theo Thông báo ngưỡng đảm bảo chất lượng đầu vào lĩnh vực Vi mạch Bán dẫn năm 2026, ngưỡng yêu cầu được xác định dựa trên điểm thi nào và bao gồm bao nhiêu tiêu chí? | 1.0000 | 0.9193 | 1.0000 | nan |
| 3 | Theo Thông báo ngưỡng đảm bảo chất lượng đầu vào lĩnh vực Vi mạch Bán dẫn năm 2026, tiêu chí thứ nhất về tổng điểm thi được quy định như thế nào? | 1.0000 | 0.9631 | 1.0000 | nan |
| 4 | Theo Quyết định phê duyệt Thông tin tuyển sinh đại học năm 2026 của Đại học Bách khoa Hà Nội, Quy chế tuyển sinh đại học được ban hành kèm theo Quyết định số bao nhiêu và ngày nào của Giám đốc Đại học Bách khoa Hà Nội? | 0.5000 | 0.9009 | 1.0000 | nan |
| 5 | Theo tài liệu teacher_dinh_muc_giang_day.md, văn bản được Giám đốc Đại học Bách khoa Hà Nội phê duyệt là gì và căn cứ vào Luật Giáo dục đại học ngày nào? | 0.0000 | 0.0000 | 1.0000 | nan |
| 6 | Theo tài liệu teacher_dinh_muc_giang_day.md, Quy chế tuyển sinh đại học được ban hành kèm theo Quyết định số bao nhiêu và ngày ký là ngày nào? | 0.0000 | 0.0000 | 1.0000 | nan |
| 7 | Tài liệu teacher_qd_6888_can_bo.md có doc_id là gì và đối tượng áp dụng (audience) là ai? | nan | 0.0000 | 0.5000 | nan |
| 8 | Theo tài liệu teacher_qd_6888_can_bo.md, nội dung chi tiết của Quyết định 6888/QĐ-ĐHBK quy định về những vấn đề gì? | nan | 0.8745 | 1.0000 | nan |
| 9 | Kỳ tuyển sinh năm 2026, Đại học Bách khoa Hà Nội công bố tổng chỉ tiêu tuyển sinh là bao nhiêu sinh viên, cho bao nhiêu chương trình đào tạo, và chính sách học bổng theo Nghị định số 179/2026/NĐ-CP được áp dụng cho bao nhiêu chương trình? | nan | nan | nan | nan |
| 10 | Thông tin tuyển sinh đại học năm 2026 của Đại học Bách khoa Hà Nội được ban hành căn cứ vào Thông tư số mấy, ngày bao nhiêu của Bộ Giáo dục và Đào tạo? | nan | nan | 1.0000 | nan |
| 11 | Theo Hướng dẫn đăng ký xác thực chứng chỉ Ngoại ngữ 2026, thí sinh cần đạt điểm thi tốt nghiệp THPT năm 2026 môn ngoại ngữ từ bao nhiêu trở lên, và chứng chỉ tiếng Anh VSTEP được quy đổi thành điểm môn tiếng Anh khi xét tuyển theo các tổ hợp nào? | nan | 0.8715 | 1.0000 | nan |
| 12 | Hội nghị Quốc tế lần thứ 11 về Truyền thông và Điện tử (IEEE ICCE 2026) diễn ra tại đâu, trong khoảng thời gian nào, và gắn với dấu mốc kỷ niệm bao nhiêu năm thành lập Đại học Bách khoa Hà Nội? | nan | 0.8591 | 1.0000 | nan |
| 13 | TS. Nguyễn Quang Minh được giới thiệu trong bài viết sở hữu hai tấm bằng tiến sĩ tại những quốc gia nào và giữ vai trò gì tại start-up công nghệ plasma ở Anh? | nan | 0.8499 | 1.0000 | nan |
| 14 | TS. Nguyễn Quang Minh tham gia Đề án thu hút và tuyển dụng giảng viên trẻ tài năng, chuyên gia, nhà khoa học đầu ngành của Đại học Bách khoa Hà Nội giai đoạn nào, tên viết tắt là gì? | nan | nan | nan | nan |
| 15 | Theo bài viết 'Bộ GD&ĐT công bố loạt quyết định bổ nhiệm lãnh đạo cơ sở GD đại học, GD nghề nghiệp trực thuộc', Bộ trưởng Bộ GD&ĐT nào đã trao các quyết định bổ nhiệm cho ban lãnh đạo Đại học Bách khoa Hà Nội trong Hội nghị chiều 5/6? | nan | nan | 1.0000 | 0.6389 |
| 16 | GS.TS. NGƯT. Lê Anh Tuấn được bổ nhiệm giữ chức Giám đốc Đại học Bách khoa Hà Nội theo quyết định số mấy và ban hành ngày nào? | 1.0000 | 0.7692 | 1.0000 | 1.0000 |

## 3. Worst Performers (Bottom 3 Q&A trong Config A)

| QID | Question | Điểm TB | Nguyên nhân & Hướng giải quyết đề xuất |
| :---: | :--- | :---: | :--- |
| 6 | Theo tài liệu teacher_dinh_muc_giang_day.md, Quy chế tuyển sinh đại học được ban hành kèm theo Quyết định số bao nhiêu và ngày ký là ngày nào? | 0.5000 | LLM bị ảo giác (hallucination) hoặc sinh câu trả lời không bám sát nguồn. Cần siết chặt System Prompt. |
| 5 | Theo tài liệu teacher_dinh_muc_giang_day.md, văn bản được Giám đốc Đại học Bách khoa Hà Nội phê duyệt là gì và căn cứ vào Luật Giáo dục đại học ngày nào? | 0.5000 | LLM bị ảo giác (hallucination) hoặc sinh câu trả lời không bám sát nguồn. Cần siết chặt System Prompt. |
| 7 | Tài liệu teacher_qd_6888_can_bo.md có doc_id là gì và đối tượng áp dụng (audience) là ai? | 0.5642 | Thiếu thông tin trong ngữ cảnh được retrieve. Cần tăng chunk_size hoặc cải tiến bộ phân đoạn chunking. |

## 4. Đề xuất Cải tiến Hệ thống (Recommendations)
1. **Tối ưu hóa Alpha trong Hybrid Search:** Điều chỉnh tỉ lệ trọng số BM25 và Dense Search để tăng độ phủ đối với các từ viết tắt chuyên ngành Bách Khoa (như HUST, TNTHPT, VSTEP).
2. **Cải tiến Chunking:** Áp dụng Semantic Chunking thay vì RecursiveCharacterTextSplitter cố định để các đoạn văn quy chế giữ nguyên tính toàn vẹn thông tin.
3. **Fine-tune Cross-Encoder:** Huấn luyện Cross-Encoder trên tập dữ liệu tiếng Việt chuyên ngành để nâng cao độ chính xác của bước Reranking.
