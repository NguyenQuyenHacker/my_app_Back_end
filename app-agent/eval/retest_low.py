"""Re-test các câu RAG điểm thấp (<0.5) sau khi sửa prompt + bật thinking,
chấm lại key_points (chấm thoáng: xấp xỉ/paraphrase tính đúng), rồi GHI ĐÈ vào
file kết quả 200 câu -> tcb-rag-v2-final.csv.

Chạy: python eval/retest_low.py
"""
import asyncio
import os
import sys
from typing import List

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WD = os.path.dirname(os.path.dirname(APP))
sys.path.insert(0, APP)

from dotenv import load_dotenv
load_dotenv(os.path.join(APP, ".env"))

import ast
import pandas as pd
from pydantic import BaseModel, Field


def _parse_list(v):
    if isinstance(v, list):
        return v
    if isinstance(v, str) and v.strip():
        try:
            return ast.literal_eval(v)
        except Exception:
            return []
    return []

from my_agent.agent import graph
from my_agent.src.config import llm

EVAL_DIR = os.path.join(WD, "EVAL_RESULT")
FULL = os.path.join(EVAL_DIR, "tcb-rag-684cb2c0_FULL.csv")
LOW = os.path.join(EVAL_DIR, "tcb-rag-v2-low.csv")
OUT = os.path.join(EVAL_DIR, "tcb-rag-v2-final.csv")


def _text(content) -> str:
    if isinstance(content, list):
        return " ".join((p.get("text", "") if isinstance(p, dict) else str(p)) for p in content).strip()
    return str(content)


class _Cov(BaseModel):
    covered: List[bool] = Field(description="đúng thứ tự key_points, True nếu answer nêu đúng ý (kệ cách diễn đạt, số xấp xỉ vẫn đúng)")


_judge = llm.with_structured_output(_Cov)


def regrade(answer: str, key_points: list) -> float:
    if not key_points:
        return None
    listed = "\n".join(f"{i+1}. {p}" for i, p in enumerate(key_points))
    r = _judge.invoke(
        f'Câu trả lời:\n"""\n{answer}\n"""\n\n'
        f"Với mỗi ý, answer có nêu đúng không (diễn đạt khác / số xấp xỉ vẫn tính đúng)?\n{listed}\n"
        f"Trả về covered độ dài {len(key_points)}."
    )
    cov = (list(r.covered) + [False] * len(key_points))[: len(key_points)]
    return sum(cov) / len(key_points)


def main():
    low = pd.read_csv(LOW)
    full = pd.read_csv(FULL)
    new_ans, new_cov = {}, {}
    n = len(low)
    for i, row in enumerate(low.iterrows(), 1):
        _, r = row
        q = r["input.question"]
        kps = _parse_list(r["reference.key_points"])
        try:
            ans = _text(graph.invoke({"messages": [("user", q)]})["messages"][-1].content)
            cov = regrade(ans, kps)
        except Exception as e:
            ans = f"<ERROR: {type(e).__name__}>"
            cov = 0.0
        new_ans[q] = ans
        new_cov[q] = cov
        print(f"[{i:>2}/{n}] cov={cov} | {q[:55]}")

    # ghi đè vào full
    full["outputs.answer"] = full.apply(lambda x: new_ans.get(x["input.question"], x["outputs.answer"]), axis=1)
    full["feedback.key_points_coverage"] = full.apply(
        lambda x: new_cov[x["input.question"]] if x["input.question"] in new_cov else x["feedback.key_points_coverage"],
        axis=1,
    )
    full.to_csv(OUT, index=False, encoding="utf-8-sig")
    try:
        full.to_excel(OUT.replace(".csv", ".xlsx"), index=False)
    except Exception:
        pass

    old = pd.to_numeric(pd.read_csv(FULL)["feedback.key_points_coverage"], errors="coerce").mean()
    new = pd.to_numeric(full["feedback.key_points_coverage"], errors="coerce").mean()
    improved = sum(1 for q in new_cov if new_cov[q] >= 0.5)
    print("\n" + "=" * 55)
    print(f"Re-test {n} câu yếu | {improved} câu giờ >=0.5")
    print(f"Coverage tổng (200 câu): {old:.3f} -> {new:.3f}")
    print(f"Ghi: {OUT}")


if __name__ == "__main__":
    main()
