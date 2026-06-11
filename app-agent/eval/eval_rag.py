"""Eval RAG accuracy theo key-points trên LangSmith.

Chấm 2 tiêu chí (không so nguyên văn, chỉ xét nội dung):
  - key_points_coverage: tỉ lệ ý bắt buộc được câu trả lời nêu đúng (0..1)
  - no_hallucination   : 1 nếu KHÔNG khẳng định ý sai trong must_not_include, 0 nếu có

Chạy:  python eval/eval_rag.py
Yêu cầu: Neon vector DB reachable (RAG không cần JWT / backend :8000).
"""
import asyncio
import os
import sys
from typing import List

# Windows: PGVectorStore (langchain-postgres) chạy psycopg async ngầm, không hợp
# ProactorEventLoop mặc định. Phải set trước khi import graph / gọi retrieval.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, APP)

from dotenv import load_dotenv
load_dotenv(os.path.join(APP, ".env"))

from pydantic import BaseModel, Field
from langsmith import evaluate

from my_agent.agent import graph
from my_agent.src.config import llm

DATASET = os.environ.get("EVAL_DATASET", "tcb-rag-accuracy")


def _text(content) -> str:
    """Lấy text từ content (có thể là list block khi bật thinking)."""
    if isinstance(content, list):
        return " ".join(
            (p.get("text", "") if isinstance(p, dict) else str(p)) for p in content
        ).strip()
    return str(content)


def target(inputs: dict) -> dict:
    """Chạy agent in-process, trả về câu trả lời cuối."""
    res = graph.invoke({"messages": [("user", inputs["question"])]})
    return {"answer": _text(res["messages"][-1].content)}


class _Coverage(BaseModel):
    covered: List[bool] = Field(
        description="Đúng thứ tự key_points: True nếu ý đó được câu trả lời nêu (kệ cách diễn đạt)."
    )


class _Hallu(BaseModel):
    asserts_wrong: List[bool] = Field(
        description="Đúng thứ tự danh sách ý sai: True nếu câu trả lời CÓ khẳng định ý sai đó."
    )


_judge = llm.with_structured_output(_Coverage)
_judge_hallu = llm.with_structured_output(_Hallu)


def key_points_coverage(outputs: dict, reference_outputs: dict) -> dict:
    pts = reference_outputs.get("key_points") or []
    if not pts:
        return {"key": "key_points_coverage", "score": None}
    listed = "\n".join(f"{i + 1}. {p}" for i, p in enumerate(pts))
    r = _judge.invoke(
        f'Câu trả lời của chatbot:\n"""\n{outputs["answer"]}\n"""\n\n'
        f"Với mỗi ý dưới đây, câu trả lời CÓ nêu đúng ý đó không (kệ cách diễn đạt)?\n{listed}\n\n"
        f"Trả về list 'covered' đúng thứ tự, độ dài = {len(pts)}."
    )
    covered = (list(r.covered) + [False] * len(pts))[: len(pts)]
    return {"key": "key_points_coverage", "score": sum(covered) / len(pts)}


def no_hallucination(outputs: dict, reference_outputs: dict) -> dict:
    forb = reference_outputs.get("must_not_include") or []
    if not forb:
        return {"key": "no_hallucination", "score": None}
    listed = "\n".join(f"{i + 1}. {p}" for i, p in enumerate(forb))
    r = _judge_hallu.invoke(
        f'Câu trả lời của chatbot:\n"""\n{outputs["answer"]}\n"""\n\n'
        f"Với mỗi ý SAI dưới đây, câu trả lời CÓ khẳng định ý đó không?\n{listed}\n\n"
        f"Trả về list 'asserts_wrong' đúng thứ tự, độ dài = {len(forb)}. "
        "Chỉ đánh True khi câu trả lời thực sự nói ý sai đó, KHÔNG suy diễn."
    )
    wrong = (list(r.asserts_wrong) + [False] * len(forb))[: len(forb)]
    # score 1 = không bịa (không khẳng định ý sai nào)
    return {"key": "no_hallucination", "score": 0 if any(wrong) else 1}


if __name__ == "__main__":
    evaluate(
        target,
        data=DATASET,
        evaluators=[key_points_coverage, no_hallucination],
        experiment_prefix="tcb-rag",
        max_concurrency=2,  # giới hạn để tránh 429 rate limit free tier
    )
    print("Done. Xem kết quả ở LangSmith -> Experiments.")
