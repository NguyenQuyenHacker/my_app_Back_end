"""Agent bản OpenAI Agents SDK — GIỮ tool LangChain, chỉ convert FRAMEWORK agent.

So với my_agent/agent.py (LangChain create_agent + LangGraph):
  - Framework: create_agent  → agents.Agent (+ Runner ở tầng serving).
  - Model:     ChatGoogleGenerativeAI → LitellmModel("gemini/gemini-2.5-flash").
  - 6 tool:    GIỮ NGUYÊN @tool LangChain (embedding, langchain-postgres, requests, RRF...),
               chỉ BỌC @function_tool mỏng gọi lại qua .invoke() (hướng A').
  - JWT:       RunnableConfig  → RunContextWrapper[ChatContext] → dựng lại config dict.
  - Middleware: KHÔNG port (bỏ ModelFallback vô nghĩa; không port Summarization).

Kế thừa nguyên 6 tool LangChain ở my_agent/src/tool. Bản LangGraph (agent.py + langgraph.json)
đã được GỠ — đây là điểm khởi tạo agent duy nhất.
"""
from typing import Literal, Optional

from agents import Agent, ModelSettings, RunContextWrapper, function_tool, set_tracing_disabled
from agents.extensions.models.litellm_model import LitellmModel

from my_agent.src.config import GOOGLE_API_KEY, system_prompt_content
from my_agent.src.context import ChatContext
from my_agent.src.tool import (
    get_account_balance as _lc_get_account_balance,
    get_transaction_history as _lc_get_transaction_history,
    list_available_knowledge_bases as _lc_list_kbs,
    lookup_recipient as _lc_lookup_recipient,
    retrieve_context as _lc_retrieve_context,
    transfer_init as _lc_transfer_init,
)

# Dùng Gemini qua LiteLLM (không dùng OpenAI platform) → tắt tracing cho hết log spam.
set_tracing_disabled(True)

model = LitellmModel(model="gemini/gemini-2.5-flash", api_key=GOOGLE_API_KEY)


def _jwt_config(ctx: RunContextWrapper[ChatContext]) -> dict:
    """Dựng lại config dict mà @tool gốc mong đợi (get_jwt đọc configurable.jwt_token)."""
    jwt = ctx.context.jwt if ctx and ctx.context else None
    return {"configurable": {"jwt_token": jwt}}


# =========================================================================
# NHÓM A — 4 tool cần JWT: vỏ @function_tool gọi @tool gốc + bơm JWT qua config
# =========================================================================
@function_tool
def get_account_balance(ctx: RunContextWrapper[ChatContext], reason: Optional[str] = None) -> str:
    """Look up the logged-in customer's main account balance. Needs NO input (reads the JWT).
    Returns: account number, current balance, held amount, available balance, status.

    Args:
        reason: Lookup reason (optional, leave empty if none).
    """
    return _lc_get_account_balance.invoke({"reason": reason}, config=_jwt_config(ctx))


@function_tool
def get_transaction_history(
    ctx: RunContextWrapper[ChatContext],
    limit: int = 5,
    direction: Literal["IN", "OUT", "ALL"] = "ALL",
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
) -> str:
    """Look up the logged-in customer's SUCCESSFUL transaction history.
    Returns matching transactions (datetime, direction, amount, counterparty, description).
    Call with no arguments for the 5 most recent. See the system prompt for mapping
    Vietnamese time/amount phrases to the parameters below.

    Args:
        limit: Max transactions to return (default 5, max 20).
        direction: IN = money received; OUT = money sent; ALL = both.
        date_from: Start date YYYY-MM-DD; empty if no time range.
        date_to: End date YYYY-MM-DD inclusive; empty if no time range.
        min_amount: Only amount >= this (VND). E.g. 'trên 5 triệu' -> 5000000.
        max_amount: Only amount <= this (VND).
    """
    return _lc_get_transaction_history.invoke(
        {
            "limit": limit,
            "direction": direction,
            "date_from": date_from,
            "date_to": date_to,
            "min_amount": min_amount,
            "max_amount": max_amount,
        },
        config=_jwt_config(ctx),
    )


@function_tool
def lookup_recipient(ctx: RunContextWrapper[ChatContext], bank_input: str, account_no: str) -> str:
    """STEP 1 (mandatory before a transfer): verify the recipient exists in the DB.
    Normalizes the bank name/code (typos, abbreviations, no diacritics) and classifies internal (TCB) vs external.
    After it returns the recipient info, summarize for the customer and WAIT for confirmation before transfer_init.

    Args:
        bank_input: Bank name or code as entered by the user, passed VERBATIM (even if misspelled). The tool normalizes it.
        account_no: Recipient account number.
    """
    return _lc_lookup_recipient.invoke(
        {"bank_input": bank_input, "account_no": account_no},
        config=_jwt_config(ctx),
    )


@function_tool
def transfer_init(
    ctx: RunContextWrapper[ChatContext],
    receiver_bank_code: str,
    receiver_account_no: str,
    amount: float,
    description: Optional[str] = None,
) -> str:
    """STEP 2 (after lookup_recipient + customer confirmation): initialize the transfer session.
    On success the UI AUTOMATICALLY shows the confirmation form and collects the OTP.
    Never ask for the OTP and never call more tools — just summarize and wait for the result.

    Args:
        receiver_bank_code: Recipient bank code (SHORT code, e.g. TCB / VCB / BIDV). From lookup_recipient result.
        receiver_account_no: Recipient account number (from lookup_recipient).
        amount: Amount to transfer (VND).
        description: Transfer description/note (optional).
    """
    return _lc_transfer_init.invoke(
        {
            "receiver_bank_code": receiver_bank_code,
            "receiver_account_no": receiver_account_no,
            "amount": amount,
            "description": description,
        },
        config=_jwt_config(ctx),
    )


# =========================================================================
# NHÓM B — 2 tool RAG: không JWT, vỏ chỉ gọi .invoke()
# =========================================================================
@function_tool
def list_available_knowledge_bases() -> str:
    """Return the list of available Knowledge Bases (table name and description only)."""
    return _lc_list_kbs.invoke({})


@function_tool
def retrieve_context(query: str, kb_table_name: str) -> str:
    """Retrieve relevant context from a specific vector database to help answer the question. You must call list_available_knowledge_bases first to obtain kb_table_name.

    Args:
        query: The user's question / search query.
        kb_table_name: Table name from list_available_knowledge_bases.
    """
    return _lc_retrieve_context.invoke({"query": query, "kb_table_name": kb_table_name})


# =========================================================================
# AGENT — giữ thứ tự tool như bản LangGraph
# =========================================================================
TOOLS = [
    list_available_knowledge_bases,
    retrieve_context,
    lookup_recipient,
    transfer_init,
    get_account_balance,
    get_transaction_history,
]

chat_agent = Agent(
    name="TechcombankAgent",
    instructions=system_prompt_content,
    model=model,
    tools=TOOLS,
    model_settings=ModelSettings(
        temperature=0.2,
        # Có tool → cần chút reasoning để model quyết định gọi tool (tắt hẳn thì lười gọi).
        extra_args={"reasoning_effort": "low"},
    ),
)
