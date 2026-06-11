"""Eval TOOL-CALLING (LOCAL, KHÔNG cần LangSmith).

Chỉ kiểm tra agent có gọi ĐÚNG tool hay không:
- Chạy agent từng câu -> bắt danh sách tool đã gọi trong trajectory.
- So với `must_call` trong dataset (rule-based, không dùng judge LLM).
- Không cần backend :8000 / JWT thật (tool chạy lỗi cũng không sao, tên tool vẫn ghi nhận).

Chạy:
    python eval/eval_tools.py            # chạy hết dataset
    python eval/eval_tools.py --limit 10 # chỉ chạy 10 câu đầu (test nhanh)

Kết quả: in bảng tóm tắt + ghi EVAL_RESULT/tool_call_result.csv
"""
import asyncio
import csv
import json
import os
import sys
import time

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WD = os.path.dirname(os.path.dirname(APP))  # .../WD
sys.path.insert(0, APP)

from dotenv import load_dotenv
load_dotenv(os.path.join(APP, ".env"))

from my_agent.agent import graph

DATA_FILE = os.path.join(WD, "TEST_DATA", "tool_call_dataset.json")
OUT_CSV = os.path.join(WD, "EVAL_RESULT", "tool_call_result.csv")


def get_tools_called(question: str) -> list:
    """Chạy agent 1 lượt, trả về danh sách tên tool đã gọi."""
    res = graph.invoke(
        {"messages": [("user", question)]},
        config={"configurable": {"jwt_token": "dummy-for-tool-selection"}},
    )
    tools = []
    for m in res["messages"]:
        for tc in getattr(m, "tool_calls", None) or []:
            tools.append(tc["name"])
    return tools


def is_correct(tools_called: list, must_call: str) -> bool:
    if must_call in (None, "", "NONE"):
        return len(tools_called) == 0          # out-of-scope: không được gọi tool nào
    return must_call in tools_called           # nghiệp vụ: phải có tool đúng


def run(limit: int | None = None):
    items = json.load(open(DATA_FILE, encoding="utf-8"))
    if not items:
        print(f"Dataset rỗng: {DATA_FILE}")
        print("=> Dán câu hỏi vào file đó rồi chạy lại. Format mỗi câu:")
        print('   {"inputs":{"question":"..."},"outputs":{"must_call":"get_account_balance"},"metadata":{"group":"balance"}}')
        return
    if limit:
        items = items[:limit]

    rows = []
    for i, e in enumerate(items, 1):
        q = e["inputs"]["question"]
        must = e["outputs"]["must_call"]
        group = e.get("metadata", {}).get("group", "")
        # retry nhẹ nếu lỗi tạm thời (vd 429)
        for attempt in range(2):
            try:
                called = get_tools_called(q)
                break
            except Exception as ex:
                if attempt == 0:
                    time.sleep(5)
                else:
                    called = [f"<ERROR: {type(ex).__name__}>"]
        ok = is_correct(called, must)
        rows.append({
            "group": group,
            "question": q,
            "must_call": must,
            "tools_called": "|".join(called),
            "correct": int(ok),
        })
        print(f"[{i:>2}/{len(items)}] {'OK ' if ok else 'SAI'} | {group:12s} | must={must:24s} | called={called}")

    # ghi CSV
    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    with open(OUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["group", "question", "must_call", "tools_called", "correct"])
        w.writeheader()
        w.writerows(rows)

    # tóm tắt
    print("\n" + "=" * 60)
    total = len(rows)
    correct = sum(r["correct"] for r in rows)
    print(f"TỔNG: {correct}/{total} đúng  ({correct/total*100:.1f}%)")
    groups = {}
    for r in rows:
        g = groups.setdefault(r["group"], [0, 0])
        g[0] += r["correct"]
        g[1] += 1
    print("Theo nhóm:")
    for g, (c, n) in groups.items():
        print(f"  {g:14s}: {c}/{n}  ({c/n*100:.0f}%)")
    print(f"\nĐã ghi: {OUT_CSV}")


if __name__ == "__main__":
    lim = None
    if "--limit" in sys.argv:
        lim = int(sys.argv[sys.argv.index("--limit") + 1])
    run(lim)
