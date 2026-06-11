# app-agent/my_agent/agent.py
from langchain.agents import create_agent
from langchain.agents.middleware import ModelFallbackMiddleware, SummarizationMiddleware
from langchain_core.messages.utils import count_tokens_approximately
from langchain_google_genai import ChatGoogleGenerativeAI

from my_agent.src.config import (
    llm,
    llm_fallback_1,
    llm_fallback_2,
    system_prompt_content,
    GOOGLE_API_KEY,
)
from my_agent.src.tool import (
    get_account_balance,
    get_transaction_history,
    list_available_knowledge_bases,
    retrieve_context,
    lookup_recipient,
    transfer_init,
)


class TechcombankAgent:
    def __init__(self):
        """
        Khởi tạo Agent. Toàn bộ llm, prompt và tools được class tự động nạp vào.
        Phần xác nhận OTP của giao dịch chuyển khoản được FE xử lý OUT-OF-BAND
        (gọi thẳng API confirm), KHÔNG đi qua agent — OTP không bao giờ vào state của LangGraph.
        """
        self.model = llm
        self.system_prompt = system_prompt_content
        self.tools = [
            list_available_knowledge_bases,
            retrieve_context,
            lookup_recipient,
            transfer_init,
            get_account_balance,
            get_transaction_history,
        ]

        self.summary_model = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.0,
            google_api_key=GOOGLE_API_KEY,
        )

    def build_graph(self):
        return create_agent(
            model=self.model,
            tools=self.tools,
            system_prompt=self.system_prompt,
            middleware=[
                ModelFallbackMiddleware(llm_fallback_1, llm_fallback_2),
                SummarizationMiddleware(
                    model=self.summary_model,
                    trigger=("messages", 14),
                    keep=("messages", 6),
                    token_counter=count_tokens_approximately,
                    trim_tokens_to_summarize=None,
                ),
            ],
        )


agent_instance = TechcombankAgent()

# LangGraph yêu cầu phải export đúng biến `graph`
graph = agent_instance.build_graph()
