
import json
from typing import Any

from langchain.tools import tool


def create_search_products_tool(
    search_service: Any,
    search_result_store: dict[str, Any] | None = None,
):

    def price_key(offer: dict[str, Any]) -> tuple[int, float]:
        price = offer.get("preco")

        try:
            if price is None or isinstance(price, bool):
                return (1, 0.0)

            value = float(price)

            if value < 0:
                return (1, 0.0)

            return (0, value)
        except (TypeError, ValueError):
            return (1, 0.0)

    @tool("buscar_produtos")
    async def buscar_produtos(
        query: str,
        cep: str | None = None,
        max_results: int = 5,
    ) -> str:
        query = query.strip()

        if not query:
            return json.dumps(
                {
                    "status": "esclarecimento_necessario",
                    "mensagem": "Informe o nome do produto.",
                    "total": 0,
                },
                ensure_ascii=False,
            )

        try:
            max_results = int(max_results)
        except (TypeError, ValueError):
            max_results = 5

        max_results = max(1, min(max_results, 20))

        try:
            result = await search_service.search(
                query=query,
                cep=cep,
            )
        except Exception as exc:
            result = {
                "status": "falha_buscas",
                "consulta": query,
                "total": 0,
                "ofertas": [],
                "farmacias": [],
                "erro": type(exc).__name__,
            }

        if search_result_store is not None:
            search_result_store["search_results"] = result

        offers = result.get("ofertas", [])

        if not isinstance(offers, list):
            offers = []

        valid_offers = [
            offer for offer in offers
            if isinstance(offer, dict)
        ]

        cheapest_offers = sorted(
            valid_offers,
            key=price_key,
        )[:max_results]

        pharmacy_summary = []

        for pharmacy in result.get("farmacias", []):
            if not isinstance(pharmacy, dict):
                continue

            pharmacy_summary.append({
                "farmacia": pharmacy.get("farmacia"),
                "status": pharmacy.get("status"),
                "erro": pharmacy.get("erro"),
                "quantidade_ofertas": pharmacy.get(
                    "quantidade_ofertas", 0
                ),
            })

        summary = {
            "status": result.get("status", "indefinido"),
            "consulta": result.get("consulta", query),
            "total_ofertas": len(valid_offers),
            "farmacias_consultadas": result.get(
                "farmacias_consultadas", len(pharmacy_summary)
            ),
            "farmacias_com_sucesso": result.get(
                "farmacias_com_sucesso"
            ),
            "farmacias": pharmacy_summary,
            "menores_precos_encontrados": [
                {
                    "farmacia": offer.get("farmacia"),
                    "nome": offer.get("nome"),
                    "preco": offer.get("preco"),
                    "marca": offer.get("marca"),
                    "url": offer.get("url"),
                }
                for offer in cheapest_offers
            ],
            "observacao": (
                "Os preços são de catálogo e não confirmam preço final, "
                "estoque ou entrega para o CEP."
            ),
        }

        return json.dumps(
            summary,
            ensure_ascii=False,
            default=str,
        )

    return buscar_produtos
