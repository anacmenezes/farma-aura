
from typing import Any

from farmacia_api.chains.agents.product_agent import (
    create_product_agent,
    run_product_agent,
)
from farmacia_api.chains.agents.response_agent import (
    create_response_agent,
    generate_final_response,
)
from farmacia_api.chains.tools.compare_offers import sort_and_group_offers
from farmacia_api.graph.state import FarmaAuraState
from farmacia_api.services.product_search import ProductSearchService


def create_graph_nodes(
    search_service: ProductSearchService,
    response_agent: Any | None = None,
):

    if response_agent is None:
        response_agent = create_response_agent()

    async def search_node(state: FarmaAuraState) -> dict:
        query = state.get("user_request", "").strip()
        cep = state.get("cep")

        if not query:
            return {
                "search_results": {
                    "status": "esclarecimento_necessario",
                    "mensagem": "Informe o produto que deseja pesquisar.",
                    "total": 0,
                    "ofertas": [],
                    "farmacias": [],
                },
                "error": None,
            }

        result_store: dict[str, Any] = {}

        try:
            product_agent = create_product_agent(
                search_service=search_service,
                search_result_store=result_store,
            )

            await run_product_agent(
                agent=product_agent,
                user_request=query,
                cep=cep,
            )

        except Exception:
            
            if "search_results" not in result_store:
                try:
                    result_store["search_results"] = (
                        await search_service.search(
                            query=query,
                            cep=cep,
                        )
                    )
                    result_store["metodo_busca"] = (
                        "servico_direto_fallback"
                    )
                except Exception as exc:
                    return {
                        "search_results": {
                            "status": "falha_buscas",
                            "consulta": query,
                            "total": 0,
                            "ofertas": [],
                            "farmacias": [],
                        },
                        "error": (
                            "Não foi possível concluir a pesquisa. "
                            f"Tipo de erro: {type(exc).__name__}."
                        ),
                    }

        raw_results = result_store.get("search_results")

        if not isinstance(raw_results, dict):
            try:
                raw_results = await search_service.search(
                    query=query,
                    cep=cep,
                )
                result_store["metodo_busca"] = (
                    "servico_direto_fallback"
                )
            except Exception as exc:
                return {
                    "search_results": {
                        "status": "falha_buscas",
                        "consulta": query,
                        "total": 0,
                        "ofertas": [],
                        "farmacias": [],
                    },
                    "error": (
                        "Não foi possível concluir a pesquisa. "
                        f"Tipo de erro: {type(exc).__name__}."
                    ),
                }

        offers = raw_results.get("ofertas", [])

        if not isinstance(offers, list):
            offers = []

        comparison = sort_and_group_offers(
            offers,
            order_by="menor_preco",
        )

        structured_result = {
            **raw_results,
            "comparacao": comparison,
            "total_ofertas_originais": len(offers),
            "agente_pesquisa_executado": True,
            "metodo_busca": result_store.get(
                "metodo_busca",
                "ferramenta_langchain",
            ),
        }

        return {
            "search_results": structured_result,
            "error": None,
        }

    async def response_node(state: FarmaAuraState) -> dict:
        results = state.get("search_results", {})
        error = state.get("error")

        if error:
            return {"final_response": error}

        try:
            response = await generate_final_response(
                agent=response_agent,
                user_request=state.get("user_request", ""),
                search_results=results,
            )

            return {"final_response": response}

        except Exception as exc:
            return {
                "final_response": (
                    "A pesquisa foi concluída, mas não foi possível "
                    "gerar o resumo com IA. Consulte search_results "
                    "para acessar as ofertas estruturadas. "
                    f"Tipo de erro: {type(exc).__name__}."
                )
            }

    return {
        "search": search_node,
        "respond": response_node,
    }
