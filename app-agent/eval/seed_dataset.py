"""Seed dataset RAG từ TEST_DATA/*.json lên LangSmith.

Chạy:  python eval/seed_dataset.py
(các file .json là nhiều object JSON nối nhau, không phải array/JSONL)
"""
import glob
import json
import os
import sys

APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, APP)

from dotenv import load_dotenv
load_dotenv(os.path.join(APP, ".env"))

from langsmith import Client

DATA_GLOB = r"F:\QUYEN\DAI_HOC\LAP TRINH JAVA\WD\TEST_DATA\kb*.json"  # chỉ file KB cho RAG
DATASET = "tcb-rag-accuracy-v2"

_dec = json.JSONDecoder()


def parse_file(txt: str) -> list:
    """Đọc JSON array chuẩn; fallback dạng nhiều object nối nhau (legacy)."""
    data = None
    try:
        data = json.loads(txt)
    except json.JSONDecodeError:
        data = None
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return [data]
    # fallback: nhiều object nối nhau, không bọc array
    out, i, n = [], 0, len(txt)
    while i < n:
        while i < n and txt[i] in " \t\r\n,":
            i += 1
        if i >= n:
            break
        obj, end = _dec.raw_decode(txt, i)
        out.append(obj)
        i = end
    return out


def main():
    examples = []
    for f in sorted(glob.glob(DATA_GLOB)):
        items = parse_file(open(f, encoding="utf-8").read())
        examples += items
        print(f"  {os.path.basename(f)}: {len(items)} examples")

    client = Client()
    if client.has_dataset(dataset_name=DATASET):
        print(f"Dataset '{DATASET}' đã tồn tại. Xoá trên UI rồi chạy lại nếu muốn seed mới.")
        return
    ds = client.create_dataset(DATASET, description="RAG key-points eval cho TCB agent")
    client.create_examples(
        dataset_id=ds.id,
        examples=[
            {
                "inputs": e["inputs"],
                "outputs": e["outputs"],
                "metadata": e.get("metadata", {}),
            }
            for e in examples
        ],
    )
    print(f"Seeded {len(examples)} examples -> dataset '{DATASET}'")


if __name__ == "__main__":
    main()
