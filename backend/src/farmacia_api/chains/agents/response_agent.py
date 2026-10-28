
import json
import os
from typing import Any

from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI


RESPONSE_AGENT_PROMPT = """
Você é o agente redator do Farma Aura.

Sua função é apresentar os resultados da pesquisa de forma clara,
organizada e fiel aos dados recebidos.

Regras:
- Não invente nem estime preços, produtos, links ou disponibilidade.
- Preserve os dados fornecidos pelas ferramentas.
- Identifique as farmácias que falharam quando essa informação estiver
  disponível.
- Diferencie preço de catálogo de preço final confirmado para o CEP.
- Não afirme que há estoque ou entrega confirmados sem evidência.
- Não declare equivalência entre medicamentos sem validação confiável.
- Se os resultados forem insuficientes, explique a limitação.
- Responda em português brasileiro.
"""


def create_response_agent(
    model: BaseChatModel | None = None,
):
    """Cria o agente que redige a resposta final."""

    if model is None:
        model = ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0,
        )

    return create_agent(
        model=model,
        tools=[],
        system_prompt=RESPONSE_AGENT_PROMPT,
    )


async def generate_final_response(
    agent: Any,
    user_request: str,
    search_results: dict[str, Any],
) -> str:
    """Redige a resposta usando os resultados reais da pesquisa."""

    payload = {
        "solicitacao": user_request,
        "resultados": search_results,
    }

    result = await agent.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "Apresente os resultados abaixo sem alterar "
                        "os dados factuais:\n\n"
                        + json.dumps(
                            payload,
                            ensure_ascii=False,
                            default=str,
                        )
                    ),
                }
            ]
        }
    )

    for message in reversed(result.get("messages", [])):
        if getattr(message, "type", "") != "ai":
            continue

        content = message.content

        if isinstance(content, str):
            return content

        if isinstance(content, list):
            parts = [
                part.get("text", "")
                for part in content
                if isinstance(part, dict)
                and isinstance(part.get("text"), str)
            ]
            return "\n".join(parts)

    return "Não foi possível gerar a resposta final."
