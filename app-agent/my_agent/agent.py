# app-agent/my_agent/agent.py
import os
import sys
import asyncio

from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware, HumanInTheLoopMiddleware
from langchain_core.messages.utils import count_tokens_approximately
from langchain_google_genai import ChatGoogleGenerativeAI
import os

# Import các tài nguyên từ src (Sử dụng Absolute Import chuẩn hóa)
from my_agent.src.config import llm, system_prompt_content, GOOGLE_API_KEY
from my_agent.src.tool import list_available_knowledge_bases, retrieve_context, create_transfer_request


class TechcombankAgent:
    def __init__(self):
        """
        Khởi tạo Agent. Toàn bộ llm, prompt và tools 
        được class tự động nạp vào, không cần truyền từ ngoài.
        """
        self.model = llm
        self.system_prompt = system_prompt_content
        print(f"DEBUG: System Prompt Loaded (Length: {len(self.system_prompt)})")
        print(f"DEBUG: Prompt Preview: {self.system_prompt[:100]}...")
        self.tools = [list_available_knowledge_bases, retrieve_context, create_transfer_request]
        
        # Khởi tạo mô hình chuyên biệt để tóm tắt
        self.summary_model = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.0,
            google_api_key=GOOGLE_API_KEY,
        )

    def build_graph(self):
        """Tạo và trả về graph của LangChain/LangGraph có kèm theo Middleware Summarization."""
        return create_agent(
            model=self.model,
            tools=self.tools,
            system_prompt=self.system_prompt,
            middleware=[
                SummarizationMiddleware(
                    model=self.summary_model,
                    trigger=("messages", 7),
                    keep=("messages", 4),
                    token_counter=count_tokens_approximately,
                    trim_tokens_to_summarize=None,
                ),
                HumanInTheLoopMiddleware(
                    interrupt_on={
                        "create_transfer_request": {
                            "allowed_decisions": ["edit", "reject", "approve"]
                        },
                    }
                )
            ],
        )

# =========================
# GRAPH
# =========================

# Khởi tạo nhanh gọn, class đã bao bọc hết mọi thứ
agent_instance = TechcombankAgent()

# LangGraph yêu cầu phải trả về đúng biến `graph`
graph = agent_instance.build_graph()