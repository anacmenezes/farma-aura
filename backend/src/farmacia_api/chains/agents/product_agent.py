
import os
from typing import Any

from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from farmacia_api.chains.tools.search_products import (
    create_search_products_tool,
)


PRODUCT_AGENT_PROMPT = """
Você é o agente de pesquisa do Farma Aura.

Seu trabalho é executar pesquisas reais nos catálogos das farmácias
utilizando a ferramenta buscar_produtos.

Regras obrigatórias:
- Para uma solicitação de pesquisa válida, utilize buscar_produtos.
- Faça apenas uma chamada à ferramenta por solicitação.
- Não invente produtos, preços, links, estoque ou condições de entrega.
- Não diga que a pesquisa foi concluída se a ferramenta não tiver sido
  executada com sucesso.
- Informe quando o resultado for parcial ou quando farmácias falharem.
- Não declare que medicamentos são equivalentes apenas porque seus
  nomes são parecidos.
- Não recomende tratamentos nem doses de medicamentos.
- O preço de catálogo não confirma o preço final para o CEP.
- A ferramenta apresenta um resumo; o sistema mantém os resultados
  completos separadamente para comparação e exibição.
- Responda em português brasileiro, com clareza e objetividade.
"""


def create_product_agent(
    search_service: Any,
    model: BaseChatModel | None = None,
    search_result_store: dict[str, Any] | None = None,
):
    """Cria o agente de pesquisa com uma ferramenta de busca real."""

    if model is None:
        model = ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0,
        )

    search_tool = create_search_products_tool(
        search_service=search_service,
        search_result_store=search_result_store,
    )

    return create_agent(
        model=model,
        tools=[search_tool],
        system_prompt=PRODUCT_AGENT_PROMPT,
    )


async def run_product_agent(
    agent: Any,
    user_request: str,
    cep: str | None = None,
) -> dict[str, Any]:
    """Executa o agente e devolve o estado da conversa."""

    request = user_request.strip()

    if not request:
        raise ValueError("A solicitação não pode estar vazia.")

    if cep:
        request += f"\nCEP informado pelo usuário: {cep}"

    return await agent.ainvoke({
        "messages": [
            {
                "role": "user",
                "content": request,
            }
        ]
    })
