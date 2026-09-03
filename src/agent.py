"""Agente de atendimento da Empório da Música"""
import os

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model

from src.tools import TOOLS

SYSTEM_PROMPT = """Você é um assistente virtual da Empório da Música, uma loja de
instrumentos musicais em Campo Grande/MS.

Seu papel é ajudar clientes com:
- Dúvidas sobre produtos, preços e disponibilidade (consulte o banco de dados).
- Dúvidas sobre políticas da loja (consulte o manual: trocas, devoluções,
  pagamento, horários, entrega, garantia).
- Acompanhamento de pedidos.

Regras:
- Responda em português do Brasil.
- Se não souber algo, diga que não tem essa informação. NUNCA invente.
- Se a pergunta for fora do escopo da loja, recuse educadamente e volte ao assunto."""


def build_model():
    """Configura o modelo"""
    return init_chat_model(
        os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini"),
        model_provider="openai",
        temperature=0.2,
    )


_agent = None


def get_agent():
    """Retorna o agente, criando-o na primeira chamada (cache em memória)."""
    global _agent
    if _agent is None:
        _agent = create_agent(
            model=build_model(),
            tools=TOOLS,
            system_prompt=SYSTEM_PROMPT,
        )
    return _agent


def interact_with_agent(user_text: str) -> str:
    """Recebe uma mensagem e retorna a resposta do agente (invocação única)."""
    agent = get_agent()
    result = agent.invoke({"messages": [{"role": "user", "content": user_text}]})
    last = result["messages"][-1]
    return str(getattr(last, "content", "")).strip()
