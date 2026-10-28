import asyncio
import re
import unicodedata
from typing import Any
from urllib.parse import urljoin

from farmacia_api.config import (
    MAX_CONCURRENT_REQUESTS,
    MAX_PRODUCTS_PER_PHARMACY,
    PHARMACIES,
    REQUEST_TIMEOUT_SECONDS,
)
from farmacia_api.connectors.vtex_catalog import VtexCatalogConnector


class ProductSearchService:

    PACKAGING_PATTERN = re.compile(
        r"(?<!\d)(\d{1,4})\s*"
        r"(comprimidos?|capsulas?|cápsulas?|"
        r"unidades?|tabletes?|drágeas?|"
        r"sachês?|saches?|ampolas?|"
        r"flaconetes?|supositórios?|supositorios?)\b",
        re.IGNORECASE,
    )

    PACKAGING_UNIT_MAP = {
        "comprimido": "comprimidos",
        "comprimidos": "comprimidos",
        "capsula": "cápsulas",
        "capsulas": "cápsulas",
        "tablete": "tabletes",
        "tabletes": "tabletes",
        "unidade": "unidades",
        "unidades": "unidades",
        "drágea": "drágeas",
        "drágeas": "drágeas",
        "dragea": "drágeas",
        "drageas": "drágeas",
        "sachê": "sachês",
        "sachês": "sachês",
        "sache": "sachês",
        "saches": "sachês",
        "ampola": "ampolas",
        "ampolas": "ampolas",
        "flaconete": "flaconetes",
        "flaconetes": "flaconetes",
        "supositório": "supositórios",
        "supositórios": "supositórios",
        "supositorio": "supositórios",
        "supositorios": "supositórios",
    }

    def __init__(
        self,
        connectors: list[VtexCatalogConnector] | None = None,
        max_concurrent_requests: int = MAX_CONCURRENT_REQUESTS,
    ) -> None:
        if connectors is None:
            connectors = [
                VtexCatalogConnector(
                    pharmacy_name=pharmacy.name,
                    base_url=pharmacy.base_url,
                    timeout=REQUEST_TIMEOUT_SECONDS,
                    max_products=MAX_PRODUCTS_PER_PHARMACY,
                    search_mode=pharmacy.search_mode,
                )
                for pharmacy in PHARMACIES
            ]

        self.connectors = connectors
        self.max_concurrent_requests = max(1, max_concurrent_requests)

    @classmethod
    def _extract_packaging_quantity(
        cls,
        product_name: Any,
        item_name: Any = None,
    ) -> dict[str, Any]:

        texts = [
            str(value).strip()
            for value in (item_name, product_name)
            if value is not None and str(value).strip()
        ]

        for text in texts:
            match = cls.PACKAGING_PATTERN.search(text)
            if not match:
                continue

            quantity = int(match.group(1))
            raw_unit = cls._normalize_text(match.group(2))
            unit = cls.PACKAGING_UNIT_MAP.get(raw_unit)

            if quantity <= 0 or unit is None:
                continue

            return {
                "quantidade_embalagem": quantity,
                "unidade_embalagem": unit,
                "embalagem_identificada": True,
            }

        return {
            "quantidade_embalagem": None,
            "unidade_embalagem": None,
            "embalagem_identificada": False,
        }

    @staticmethod
    def _normalize_text(value: str) -> str:
        normalized = unicodedata.normalize("NFKD", value.casefold())
        return "".join(
            char
            for char in normalized
            if not unicodedata.combining(char)
        )

    async def search(
        self,
        query: str,
        cep: str | None = None,
    ) -> dict[str, Any]:
        query = query.strip()

        if not query:
            return self._empty_result(
                query,
                "esclarecimento_necessario",
                "Informe o nome do produto que deseja pesquisar.",
            )

        if cep is not None:
            cep = "".join(char for char in cep if char.isdigit())
            if len(cep) != 8:
                return self._empty_result(
                    query,
                    "esclarecimento_necessario",
                    "Informe um CEP válido com 8 dígitos.",
                )

        semaphore = asyncio.Semaphore(self.max_concurrent_requests)

        results = await asyncio.gather(
            *[
                self._search_connector(connector, query, cep, semaphore)
                for connector in self.connectors
            ],
            return_exceptions=True,
        )

        pharmacy_statuses: list[dict[str, Any]] = []
        offers: list[dict[str, Any]] = []

        for connector, result in zip(self.connectors, results):
            if isinstance(result, BaseException):
                pharmacy_statuses.append({
                    "farmacia": connector.pharmacy_name,
                    "status": "falha",
                    "erro": "Falha inesperada durante a pesquisa.",
                    "quantidade_ofertas": 0,
                    "consulta_alternativa": False,
                    "resposta_parcial": False,
                })
                continue

            pharmacy_statuses.append({
                "farmacia": result["farmacia"],
                "status": result["status"],
                "erro": result.get("erro"),
                "quantidade_ofertas": len(result["ofertas"]),
                "consulta_solicitada": result.get("consulta_solicitada"),
                "consulta_utilizada": result.get("consulta_utilizada"),
                "consulta_alternativa": result.get(
                    "consulta_alternativa", False
                ),
                "resposta_parcial": result.get(
                    "resposta_parcial", False
                ),
                "http_status": result.get("http_status"),
                "tentativas": result.get("tentativas", []),
            })
            offers.extend(result["ofertas"])

        successful = sum(
            pharmacy["status"] in {"sucesso", "sucesso_parcial"}
            for pharmacy in pharmacy_statuses
        )
        partial = sum(
            pharmacy["status"] == "sucesso_parcial"
            for pharmacy in pharmacy_statuses
        )

        if successful == 0:
            status = "falha_buscas"
        elif successful < len(self.connectors) or partial:
            status = "sucesso_parcial"
        elif not offers:
            status = "sem_resultados"
        else:
            status = "sucesso"

        return {
            "status": status,
            "consulta": query,
            "cep_consultado": cep,
            "total": len(offers),
            "farmacias_consultadas": len(self.connectors),
            "farmacias_com_sucesso": successful,
            "farmacias_com_resultado_parcial": partial,
            "ofertas": offers,
            "farmacias": pharmacy_statuses,
            "observacao_preco": (
                "Os preços são valores de catálogo, quando disponíveis. "
                "Não confirmam preço final, estoque ou entrega para o CEP."
            ),
        }

    async def _search_connector(
        self,
        connector: VtexCatalogConnector,
        query: str,
        cep: str | None,
        semaphore: asyncio.Semaphore,
    ) -> dict[str, Any]:
        async with semaphore:
            try:
                result = await connector.search(query=query, cep=cep)
            except Exception:
                return self._failure_result(
                    connector,
                    "Não foi possível consultar esta farmácia.",
                )

        if not isinstance(result, dict):
            return self._failure_result(
                connector,
                "A resposta da farmácia possui formato inválido.",
            )

        if result.get("status") != "sucesso":
            return {
                "farmacia": connector.pharmacy_name,
                "status": "falha",
                "erro": result.get("erro") or "Consulta não concluída.",
                "ofertas": [],
                "consulta_solicitada": result.get("consulta_solicitada"),
                "consulta_utilizada": result.get("consulta_utilizada"),
                "consulta_alternativa": result.get(
                    "consulta_alternativa", False
                ),
                "resposta_parcial": result.get(
                    "resposta_parcial", False
                ),
                "http_status": result.get("http_status"),
                "tentativas": result.get("tentativas", []),
            }

        products = result.get("produtos", [])
        if not isinstance(products, list):
            return self._failure_result(
                connector,
                "A lista de produtos retornada é inválida.",
            )

        alternative = bool(result.get("consulta_alternativa", False))
        partial_response = bool(result.get("resposta_parcial", False))
        offers: list[dict[str, Any]] = []

        for product in products:
            if not isinstance(product, dict):
                continue

            for offer in self._normalize_product(
                product=product,
                pharmacy_name=connector.pharmacy_name,
                base_url=connector.base_url,
            ):
                offer["consulta_alternativa"] = alternative
                offer["resposta_parcial"] = partial_response
                offer["consulta_solicitada"] = result.get(
                    "consulta_solicitada", query
                )
                offer["consulta_utilizada"] = result.get(
                    "consulta_utilizada"
                )
                offer["validacao_textual_conector"] = True
                offer["correspondencia_exata_confirmada"] = False
                offers.append(offer)

        is_partial = alternative or partial_response

        return {
            "farmacia": connector.pharmacy_name,
            "status": "sucesso_parcial" if is_partial else "sucesso",
            "erro": None,
            "ofertas": offers,
            "consulta_solicitada": result.get("consulta_solicitada", query),
            "consulta_utilizada": result.get("consulta_utilizada"),
            "consulta_alternativa": alternative,
            "resposta_parcial": partial_response,
            "http_status": result.get("http_status"),
            "tentativas": result.get("tentativas", []),
        }

    @staticmethod
    def _failure_result(
        connector: VtexCatalogConnector,
        message: str,
    ) -> dict[str, Any]:
        return {
            "farmacia": connector.pharmacy_name,
            "status": "falha",
            "erro": message,
            "ofertas": [],
            "consulta_alternativa": False,
            "resposta_parcial": False,
        }

    @classmethod
    def _normalize_product(
        cls,
        product: dict[str, Any],
        pharmacy_name: str,
        base_url: str,
    ) -> list[dict[str, Any]]:
        product_name = (
            product.get("productName")
            or product.get("name")
            or product.get("product_name")
            or "Nome não informado"
        )
        brand = product.get("brand")
        product_link = (
            product.get("link")
            or product.get("productLink")
            or product.get("url")
        )

        if product_link:
            product_link = urljoin(base_url, product_link)

        items = product.get("items", [])
        if not isinstance(items, list) or not items:
            return [
                cls._build_offer(
                    pharmacy_name, product_name, brand, product_link,
                    None, None, None, None,
                )
            ]

        offers: list[dict[str, Any]] = []

        for item in items:
            if not isinstance(item, dict):
                continue

            item_name = (
                item.get("nameComplete")
                or item.get("name")
                or item.get("complementName")
            )
            sellers = item.get("sellers", [])

            if not isinstance(sellers, list) or not sellers:
                offers.append(
                    cls._build_offer(
                        pharmacy_name, product_name, brand, product_link,
                        item_name, None, None, None,
                    )
                )
                continue

            for seller in sellers:
                if not isinstance(seller, dict):
                    continue

                commercial_offer = seller.get(
                    "commertialOffer",
                    seller.get("commercialOffer", {}),
                )
                if not isinstance(commercial_offer, dict):
                    commercial_offer = {}

                offers.append(
                    cls._build_offer(
                        pharmacy_name,
                        product_name,
                        brand,
                        product_link,
                        item_name,
                        (
                            seller.get("sellerName")
                            or seller.get("name")
                            or seller.get("sellerId")
                        ),
                        cls._valid_price(commercial_offer.get("Price")),
                        commercial_offer.get("AvailableQuantity"),
                    )
                )

        return offers

    @staticmethod
    def _valid_price(value: Any) -> float | None:
        if isinstance(value, bool) or value is None:
            return None
        try:
            price = float(value)
        except (TypeError, ValueError):
            return None
        if price < 0 or price == float("inf") or price != price:
            return None
        return price

    @classmethod
    def _build_offer(
        cls,
        pharmacy_name: str,
        product_name: str,
        brand: Any,
        product_url: Any,
        item_name: Any,
        seller_name: Any,
        price: float | None,
        available_quantity: Any,
    ) -> dict[str, Any]:
        packaging = cls._extract_packaging_quantity(
            product_name=product_name,
            item_name=item_name,
        )

        return {
            "farmacia": pharmacy_name,
            "nome": product_name,
            "marca": brand,
            "apresentacao_item": item_name,
            "vendedor": seller_name,
            "preco": price,
            "moeda": "BRL",
            "url": product_url,
            **packaging,
            "quantidade_disponivel_catalogo": available_quantity,
            "consulta_alternativa": False,
            "resposta_parcial": False,
            "consulta_solicitada": None,
            "consulta_utilizada": None,
            "validacao_textual_conector": False,
            "correspondencia_exata_confirmada": False,
            "preco_por_cep_confirmado": False,
            "estoque_por_cep_confirmado": False,
            "entrega_confirmada": False,
        }

    @staticmethod
    def _empty_result(
        query: str,
        status: str,
        message: str,
    ) -> dict[str, Any]:
        return {
            "status": status,
            "mensagem": message,
            "consulta": query,
            "total": 0,
            "ofertas": [],
            "farmacias": [],
        }