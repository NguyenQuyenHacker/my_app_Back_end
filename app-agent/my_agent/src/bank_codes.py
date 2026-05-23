"""Loader + helpers cho danh sách mã ngân hàng. Nguồn dữ liệu: my_agent/data/bank_codes.json."""
import json
import os
import unicodedata
from typing import Optional

_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_BANK_CODES_PATH = os.path.join(os.path.dirname(_CURRENT_DIR), "data", "bank_codes.json")

_FUZZY_CUTOFF = 0.72


def _load() -> dict[str, dict]:
    if not os.path.exists(_BANK_CODES_PATH):
        raise FileNotFoundError(f"bank_codes.json not found at {_BANK_CODES_PATH}")
    with open(_BANK_CODES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


BANK_CODES: dict[str, dict] = _load()


def _normalize_text(s: str) -> str:
    """Lowercase, bỏ dấu tiếng Việt, giữ lại chữ-số."""
    s = unicodedata.normalize("NFD", s.strip().lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return "".join(c for c in s if c.isalnum())


def normalize_bank_code(raw: str) -> Optional[str]:
    """Trả về mã chuẩn (TCB, VCB, ...) cho mọi cách viết / typo. None nếu không nhận diện được."""
    if not raw:
        return None
    norm = _normalize_text(raw)
    if not norm:
        return None

    # 1) Trùng mã ngắn
    for code in BANK_CODES:
        if norm == code.lower():
            return code

    # 2) Trùng alias (so sánh sau khi normalize cả 2 vế)
    for code, info in BANK_CODES.items():
        for alias in info.get("aliases", []):
            if norm == _normalize_text(alias):
                return code

    # 3) Fuzzy match cho typo
    import difflib

    candidates: list[tuple[str, str]] = []
    for code, info in BANK_CODES.items():
        candidates.append((code.lower(), code))
        for alias in info.get("aliases", []):
            candidates.append((_normalize_text(alias), code))

    cand_strs = [c[0] for c in candidates]
    matches = difflib.get_close_matches(norm, cand_strs, n=1, cutoff=_FUZZY_CUTOFF)
    if matches:
        for cand_str, code in candidates:
            if cand_str == matches[0]:
                return code
    return None


def bank_list_for_prompt() -> str:
    """Format danh sách ngân hàng để chèn vào system prompt."""
    lines = []
    for code, info in BANK_CODES.items():
        name = info.get("name", code)
        lines.append(f"- `{code}` — {name}")
    return "\n".join(lines)
