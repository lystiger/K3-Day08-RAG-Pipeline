"""
api.py — Backend cho giao diện chat trong web/index.html (Role 4).

Chạy:
    uvicorn api:app --reload --port 8000
    # rồi mở http://localhost:8000

Kiến trúc: đây chỉ là lớp vỏ HTTP. Toàn bộ logic RAG vẫn nằm ở Task 9 và
Task 10 — file này KHÔNG được import task5/6/7/8 (xem TEAM_ARCHITECTURE.md §1.3).

Endpoint /api/chat trả về Server-Sent Events, đúng hợp đồng mà
web/index.html::runLive() đang đọc:

    event: token    data: {"text": "..."}          # từng mẩu câu trả lời
    event: sources  data: {"sources": [...], "retrieval_source": "hybrid"}
    event: error    data: {"message": "..."}

Khi Task 9 / Task 10 chưa implement xong, endpoint trả event `error` kèm thông
báo rõ task nào còn thiếu — giao diện sẽ hiện thẻ lỗi + nút "Thử lại" thay vì
treo. Trong lúc đó cứ để USE_MOCK = true trong web/index.html để dựng UI.
"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

load_dotenv()

PROJECT_ROOT = Path(__file__).parent
INDEX_HTML = PROJECT_ROOT / "web" / "index.html"

app = FastAPI(title="University Services RAG API")


class ChatRequest(BaseModel):
    query: str
    top_k: int = 5
    history: list[dict] = []


# =============================================================================
# SSE helpers
# =============================================================================

def sse(event: str, payload: dict) -> str:
    """Một frame SSE. json.dumps không sinh newline nên data luôn nằm 1 dòng."""
    return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


# =============================================================================
# /api/chat
# =============================================================================

def _stream_answer(req: ChatRequest):
    """
    Generator đồng bộ — Starlette tự chạy trong threadpool nên gọi SDK sync
    ở đây không chặn event loop.
    """
    # Import muộn: server vẫn khởi động được khi chưa cài chromadb /
    # sentence-transformers, hoặc khi các task còn là stub.
    try:
        from src.task9_retrieval_pipeline import retrieve
        from src.task10_generation import (
            LLM_MODEL,
            SYSTEM_PROMPT,
            TEMPERATURE,
            TOP_P,
            format_context,
            reorder_for_llm,
        )
    except Exception as exc:  # ImportError, RuntimeError khi chưa index...
        yield sse("error", {"message": f"Không import được pipeline: {exc}"})
        return

    # --- Retrieval (Task 9) ---------------------------------------------------
    try:
        chunks = retrieve(req.query, top_k=req.top_k)
    except NotImplementedError:
        yield sse("error", {"message": "Task 9 retrieve() chưa được implement."})
        return
    except Exception as exc:
        yield sse("error", {"message": f"Lỗi retrieval: {exc}"})
        return

    chunks = chunks or []
    retrieval_source = chunks[0].get("source", "hybrid") if chunks else "hybrid"

    # Gửi nguồn ngay sau retrieval: nếu LLM lỗi giữa chừng, phần đã trả về vẫn
    # có nguồn để đối chiếu. UI chỉ hiển thị chúng khi stream kết thúc.
    yield sse("sources", {"sources": chunks, "retrieval_source": retrieval_source})

    if not chunks:
        return  # UI tự hiển thị trạng thái "không tìm thấy thông tin"

    # --- Prompt (Task 10) -----------------------------------------------------
    try:
        context = format_context(reorder_for_llm(chunks))
    except NotImplementedError:
        yield sse("error", {"message": "Task 10 reorder_for_llm()/format_context() chưa implement."})
        return

    api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        yield sse("error", {"message": "Thiếu OPENROUTER_API_KEY trong .env"})
        return

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for turn in req.history[-8:]:  # giữ 4 lượt gần nhất cho follow-up
        role = turn.get("role")
        content = turn.get("content")
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": f"Context:\n{context}\n\n---\n\nQuestion: {req.query}"})

    # --- Generation (streaming) ----------------------------------------------
    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")
        stream = client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            temperature=TEMPERATURE,
            top_p=TOP_P,
            stream=True,
        )
        for part in stream:
            if not part.choices:
                continue
            piece = part.choices[0].delta.content
            if piece:
                yield sse("token", {"text": piece})
    except Exception as exc:
        yield sse("error", {"message": f"Lỗi generation: {exc}"})


@app.post("/api/chat")
def chat(req: ChatRequest):
    return StreamingResponse(
        _stream_answer(req),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# =============================================================================
# Static frontend
# =============================================================================

@app.get("/")
def index():
    return FileResponse(INDEX_HTML)
