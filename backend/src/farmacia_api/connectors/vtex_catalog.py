import re
import unicodedata
from typing import Any
from urllib.parse import urljoin

import httpx


class VtexCatalogConnector:

    FORM_TERMS = {
        "comprimido", "comprimidos",
        "capsula", "capsulas", "capsula mole",
        "gota", "gotas",
        "solucao oral", "xarope", "suspensao oral",
    }

    STRENGTH_PATTERN = re.compile(
        r"(?<![a-z0-9])"
        r"(\d+(?:[.,]\d+)?)\s*(mg|mcg|g|ml|ui)\b",
        re.IGNORECASE,
    )

    ADDITIONAL_INGREDIENTS = {
        "cafeina",
        "orfenadrina",
        "carisoprodol",
        "diclofenaco",
        "paracetamol",
        "fenilefrina",
    }

    FORM_PATTERNS = {
        "comprimidos": r"\bcomprimidos?\b",
        "capsulas": r"\bcapsulas?(?:\s+moles?)?\b",
        "gotas": r"\bgotas?\b",
        "xarope": r"\bxarope\b",
        "solucao oral": r"\bsolucao oral\b",
        "suspensao oral": r"\bsuspensao oral\b",
    }

    def __init__(
        self,
        pharmacy_name: str,
        base_url: str,
        timeout: float = 20.0,
        max_products: int = 10,
        search_mode: str = "catalog",
    ) -> None:
        self.pharmacy_name = pharmacy_name
        self.base_url = base_url.rstrip("/") + "/"
        self.timeout = timeout
        self.max_products = max(1, min(max_products, 50))
        self.search_mode = search_mode

    @staticmethod
    def _normalize(text: str) -> str:
        text = unicodedata.normalize("NFKD", text)
        text = "".join(
            char for char in text
            if not unicodedata.combining(char)
        )
        return re.sub(r"\s+", " ", text.casefold()).strip()

    @classmethod
    def _compact(cls, text: str) -> str:
        return re.sub(r"\s+", "", cls._normalize(text))

    @classmethod
    def _query_variants(cls, query: str) -> list[str]:
        variants: list[str] = []
        seen: set[str] = set()

        def add(value: str) -> None:
            value = value.strip()
            key = cls._normalize(value)
            if value and key and key not in seen:
                variants.append(value)
                seen.add(key)

        add(query)

        compact = re.sub(
            r"(\d+(?:[.,]\d+)?)\s+(mg|mcg|g|ml|ui)\b",
            r"\1\2",
            query,
            flags=re.IGNORECASE,
        )
        add(compact)

        broad = re.sub(
            r"\b\d+(?:[.,]\d+)?\s*(?:mg|mcg|g|ml|ui)\b",
            " ",
            query,
            flags=re.IGNORECASE,
        )

        for term in sorted(cls.FORM_TERMS, key=len, reverse=True):
            broad = re.sub(
                rf"\b{re.escape(term)}\b",
                " ",
                broad,
                flags=re.IGNORECASE,
            )

        add(re.sub(r"\s+", " ", broad).strip())
        return variants

    @classmethod
    def _item_text(cls, item: dict[str, Any]) -> str:
        parts: list[str] = []

        for key in ("name", "nameComplete", "complementName"):
            value = item.get(key)
            if isinstance(value, str):
                parts.append(value)

        variations = item.get("variations", [])
        if isinstance(variations, list):
            for variation in variations:
                if not isinstance(variation, dict):
                    continue

                values = variation.get("values", [])
                if isinstance(values, list):
                    parts.extend(
                        str(value)
                        for value in values
                        if isinstance(value, (str, int, float))
                    )

        return cls._normalize(" ".join(parts))

    @classmethod
    def _product_text(cls, product: dict[str, Any]) -> str:
        parts: list[str] = []

        for key in (
            "productName",
            "name",
            "product_name",
            "brand",
            "description",
        ):
            value = product.get(key)
            if isinstance(value, str):
                parts.append(value)

        items = product.get("items", [])
        if isinstance(items, list):
            parts.extend(
                cls._item_text(item)
                for item in items
                if isinstance(item, dict)
            )

        return cls._normalize(" ".join(parts))

    @classmethod
    def _requested_strengths(
        cls,
        query: str,
    ) -> list[tuple[str, str]]:
        matches = cls.STRENGTH_PATTERN.findall(cls._normalize(query))
        result: list[tuple[str, str]] = []

        for amount, unit in matches:
            amount = cls._normalize_amount(amount)
            unit = unit.casefold()
            pair = (amount, unit)

            if pair not in result:
                result.append(pair)

        return result

    @staticmethod
    def _normalize_amount(amount: str) -> str:
        amount = amount.replace(",", ".")
        if "." in amount:
            amount = amount.rstrip("0").rstrip(".")
        return amount

    @classmethod
    def _text_strengths(
        cls,
        text: str,
    ) -> list[tuple[str, str]]:
        matches = cls.STRENGTH_PATTERN.findall(cls._normalize(text))
        return [
            (cls._normalize_amount(amount), unit.casefold())
            for amount, unit in matches
        ]

    @classmethod
    def _has_requested_strength(
        cls,
        text: str,
        strengths: list[tuple[str, str]],
    ) -> bool:

        if not strengths:
            return True

        found = cls._text_strengths(text)

        for requested_amount, requested_unit in strengths:
            if (requested_amount, requested_unit) not in found:
                return False

        return True

    @classmethod
    def _base_terms(cls, query: str) -> list[str]:
        base = cls._normalize(query)

        base = cls.STRENGTH_PATTERN.sub(" ", base)

        for term in sorted(cls.FORM_TERMS, key=len, reverse=True):
            base = re.sub(
                rf"\b{re.escape(term)}\b",
                " ",
                base,
            )

        return [
            term
            for term in re.findall(r"[a-z0-9]+", base)
            if len(term) > 1
        ]

    @classmethod
    def _requested_forms(cls, query: str) -> set[str]:
        normalized = cls._normalize(query)
        requested: set[str] = set()

        for form, pattern in cls.FORM_PATTERNS.items():
            if re.search(pattern, normalized):
                requested.add(form)

        return requested

    @classmethod
    def _form_matches(cls, text: str, requested_forms: set[str]) -> bool:

        if not requested_forms:
            return True

        normalized = cls._normalize(text)
        detected_forms = {
            form
            for form, pattern in cls.FORM_PATTERNS.items()
            if re.search(pattern, normalized)
        }

        return requested_forms.issubset(detected_forms)

    @classmethod
    def _has_additional_ingredient(
        cls,
        text: str,
        requested_terms: set[str],
    ) -> bool:
        normalized = cls._normalize(text)

        for ingredient in cls.ADDITIONAL_INGREDIENTS:
            if re.search(rf"\b{re.escape(ingredient)}\b", normalized):
                if ingredient not in requested_terms:
                    return True

        return False

    @classmethod
    def _matches_candidate(
        cls,
        product_name: str,
        item_text: str,
        query: str,
    ) -> bool:

        normalized_name = cls._normalize(product_name)
        normalized_item = cls._normalize(item_text)
        combined = f"{normalized_name} {normalized_item}".strip()

        requested_terms = set(cls._base_terms(query))
        requested_strengths = cls._requested_strengths(query)
        requested_forms = cls._requested_forms(query)

        for term in requested_terms:
            if term not in normalized_name:
                return False

        item_strengths = cls._text_strengths(normalized_item)

        if requested_strengths:
            if item_strengths:
                if not all(
                    strength in item_strengths
                    for strength in requested_strengths
                ):
                    return False
            elif not cls._has_requested_strength(
                normalized_name,
                requested_strengths,
            ):
                return False

            if not cls._has_requested_strength(
                combined,
                requested_strengths,
            ):
                return False

        if requested_forms and not cls._form_matches(
            combined,
            requested_forms,
        ):
            return False

        if cls._has_additional_ingredient(combined, requested_terms):
            return False

        return True

    @classmethod
    def _matches_query(
        cls,
        product: dict[str, Any],
        query: str,
    ) -> bool:
        product_name = str(
            product.get("productName")
            or product.get("name")
            or product.get("product_name")
            or ""
        )
        brand = str(product.get("brand") or "")

        searchable_name = f"{product_name} {brand}".strip()

        items = product.get("items", [])
        item_list = [
            item for item in items
            if isinstance(item, dict)
        ] if isinstance(items, list) else []

        if not item_list:
            return cls._matches_candidate(
                searchable_name,
                "",
                query,
            )

        for item in item_list:
            item_text = cls._item_text(item)

            if cls._matches_candidate(
                searchable_name,
                item_text,
                query,
            ):
                return True

        return False

    @classmethod
    def _filter_matching_products(
        cls,
        products: list[dict[str, Any]],
        query: str,
    ) -> list[dict[str, Any]]:
        return [
            product
            for product in products
            if cls._matches_query(product, query)
        ]

    async def search(
        self,
        query: str,
        cep: str | None = None,
    ) -> dict[str, Any]:
        query = query.strip()

        if not query:
            return self._failure("A consulta não pode estar vazia.")

        endpoint = (
            "_v/api/intelligent-search/product_search"
            if self.search_mode == "intelligent_search"
            else "api/catalog_system/pub/products/search"
        )

        url = urljoin(self.base_url, endpoint)
        variants = self._query_variants(query)
        last_error = "A consulta não foi concluída."
        last_status: int | None = None
        attempts: list[dict[str, Any]] = []

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                headers={
                    "Accept": "application/json",
                    "User-Agent": "FarmaAura/1.0",
                },
            ) as client:
                for index, variant in enumerate(variants):
                    page_size = (
                        max(self.max_products, 50)
                        if index > 0
                        else self.max_products
                    )

                    if self.search_mode == "intelligent_search":
                        params = {
                            "query": variant,
                            "map": "ft",
                            "_from": "0",
                            "_to": str(page_size - 1),
                        }
                    else:
                        params = {
                            "ft": variant,
                            "_from": "0",
                            "_to": str(page_size - 1),
                        }

                    try:
                        response = await client.get(url, params=params)
                    except httpx.HTTPError as exc:
                        last_error = (
                            f"Falha de comunicação: {type(exc).__name__}."
                        )
                        attempts.append({
                            "consulta": variant,
                            "erro": type(exc).__name__,
                        })
                        continue

                    last_status = response.status_code

                    if response.status_code not in (200, 206):
                        last_error = (
                            f"A loja retornou HTTP {response.status_code}."
                        )
                        attempts.append({
                            "consulta": variant,
                            "http_status": response.status_code,
                        })

                        if response.status_code in (400, 404):
                            continue

                        return self._failure(
                            last_error,
                            http_status=response.status_code,
                            tentativas=attempts,
                        )

                    try:
                        data = response.json()
                    except ValueError:
                        return self._failure(
                            "A loja retornou conteúdo que não é JSON válido.",
                            http_status=response.status_code,
                            tentativas=attempts,
                        )

                    if isinstance(data, list):
                        products = data
                    elif isinstance(data, dict):
                        products = data.get("products")
                        if products is None:
                            products = data.get("records")
                    else:
                        products = None

                    if not isinstance(products, list):
                        return self._failure(
                            "A resposta não contém uma lista válida de produtos.",
                            http_status=response.status_code,
                            tentativas=attempts,
                        )

                    products = [
                        product
                        for product in products
                        if isinstance(product, dict)
                    ]

                    matching = self._filter_matching_products(
                        products,
                        query,
                    )

                    attempts.append({
                        "consulta": variant,
                        "http_status": response.status_code,
                        "quantidade_recebida": len(products),
                        "quantidade_correspondente": len(matching),
                    })

                    if not matching:
                        last_error = (
                            "Nenhum produto correspondeu aos critérios "
                            "informados nesta consulta."
                        )
                        continue

                    matching = matching[:self.max_products]

                    return {
                        "farmacia": self.pharmacy_name,
                        "status": "sucesso",
                        "erro": None,
                        "http_status": response.status_code,
                        "consulta_solicitada": query,
                        "consulta_utilizada": variant,
                        "consulta_alternativa": index > 0,
                        "resposta_parcial": (
                            response.status_code == 206 or index > 0
                        ),
                        "tentativas": attempts,
                        "quantidade": len(matching),
                        "produtos": matching,
                        "cep_consultado": cep,
                        "preco_por_cep_confirmado": False,
                    }

        except httpx.HTTPError as exc:
            return self._failure(
                f"Falha de comunicação: {type(exc).__name__}.",
                http_status=last_status,
                tentativas=attempts,
            )

        return self._failure(
            last_error,
            http_status=last_status,
            tentativas=attempts,
        )

    def _failure(
        self,
        message: str,
        http_status: int | None = None,
        tentativas: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        return {
            "farmacia": self.pharmacy_name,
            "status": "falha",
            "erro": message,
            "http_status": http_status,
            "resposta_parcial": False,
            "consulta_alternativa": False,
            "tentativas": tentativas or [],
            "quantidade": 0,
            "produtos": [],
            "preco_por_cep_confirmado": False,
        }