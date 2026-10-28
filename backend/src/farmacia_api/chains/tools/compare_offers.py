
import json
import re
import unicodedata
from decimal import Decimal, InvalidOperation
from typing import Any, Literal

from langchain.tools import tool


PRICE_FIELDS = (
    "preco",
    "price",
    "preco_total",
    "preco_vista",
    "valor",
    "sellingPrice",
)


def normalize_text(value: Any) -> str:
    text = str(value or "").casefold()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(
        char for char in text
        if not unicodedata.combining(char)
    )
    return re.sub(r"\s+", " ", text).strip()


def parse_price(offer: dict[str, Any]) -> Decimal | None:
    raw = next(
        (
            offer[field]
            for field in PRICE_FIELDS
            if offer.get(field) is not None
            and offer[field] != ""
        ),
        None,
    )

    if isinstance(raw, bool) or raw is None:
        return None

    if isinstance(raw, (int, float, Decimal)):
        try:
            price = Decimal(str(raw))
            return price if price.is_finite() and price >= 0 else None
        except (InvalidOperation, ValueError):
            return None

    if not isinstance(raw, str):
        return None

    cleaned = re.sub(r"[^\d,.\-]", "", raw.strip())

    if not cleaned or cleaned in {"-", ".", ","}:
        return None

    if "," in cleaned:
        cleaned = cleaned.replace(".", "").replace(",", ".")

    try:
        price = Decimal(cleaned)
        return price if price.is_finite() and price >= 0 else None
    except (InvalidOperation, ValueError):
        return None


def get_presentation(offer: dict[str, Any]) -> str:
    name = str(
        offer.get("nome")
        or offer.get("productName")
        or "Produto não identificado"
    )
    item = str(
        offer.get("apresentacao_item")
        or offer.get("item_name")
        or ""
    )

    return f"{name} {item}".strip()


def get_group_key(offer: dict[str, Any]) -> str:
    return normalize_text(get_presentation(offer))


def sort_and_group_offers(
    offers: list[dict[str, Any]],
    order_by: Literal["menor_preco", "maior_preco"] = "menor_preco",
) -> dict[str, Any]:

    if order_by not in {"menor_preco", "maior_preco"}:
        raise ValueError("Critério de ordenação inválido.")

    groups: dict[str, list[dict[str, Any]]] = {}
    display_names: dict[str, str] = {}

    for original_index, offer in enumerate(offers):
        if not isinstance(offer, dict):
            continue

        presentation = get_presentation(offer)
        key = get_group_key(offer)

        enriched = dict(offer)
        price = parse_price(offer)
        enriched["preco_numerico"] = (
            str(price) if price is not None else None
        )

        groups.setdefault(key, []).append(
            (original_index, enriched)
        )
        display_names.setdefault(key, presentation)

    output_groups = []

    for key, indexed_offers in groups.items():
        with_price = [
            pair for pair in indexed_offers
            if pair[1]["preco_numerico"] is not None
        ]
        without_price = [
            pair for pair in indexed_offers
            if pair[1]["preco_numerico"] is None
        ]

        with_price.sort(
            key=lambda pair: (
                Decimal(pair[1]["preco_numerico"]),
                pair[0],
            ),
            reverse=order_by == "maior_preco",
        )

        ordered = [
            offer for _, offer in with_price + without_price
        ]

        output_groups.append({
            "apresentacao": display_names[key],
            "total": len(ordered),
            "ofertas": ordered,
        })

    def group_sort_key(group: dict[str, Any]):
        prices = [
            parse_price(offer)
            for offer in group["ofertas"]
        ]
        valid_prices = [
            price for price in prices
            if price is not None
        ]

        if not valid_prices:
            return (
                1,
                Decimal("0"),
                normalize_text(group["apresentacao"]),
            )

        best_price = (
            min(valid_prices)
            if order_by == "menor_preco"
            else max(valid_prices)
        )

        return (
            0,
            best_price
            if order_by == "menor_preco"
            else -best_price,
            normalize_text(group["apresentacao"]),
        )

    output_groups.sort(key=group_sort_key)

    all_offers = [
        offer
        for group in output_groups
        for offer in group["ofertas"]
    ]

    return {
        "status": "sucesso",
        "ordenacao": order_by,
        "total": len(all_offers),
        "total_com_preco": sum(
            parse_price(offer) is not None
            for offer in all_offers
        ),
        "total_sem_preco": sum(
            parse_price(offer) is None
            for offer in all_offers
        ),
        "grupos": output_groups,
        "ofertas": all_offers,
    }


@tool("comparar_ofertas")
def compare_offers(
    offers: list[dict[str, Any]],
    order_by: Literal["menor_preco", "maior_preco"] = "menor_preco",
) -> str:
    """Ordena ofertas e agrupa nomes e apresentações idênticos.

    Não determina equivalência farmacêutica. Ofertas sem preço
    permanecem no final de cada grupo.
    """
    try:
        result = sort_and_group_offers(offers, order_by)
        return json.dumps(
            result,
            ensure_ascii=False,
            default=str,
        )
    except (TypeError, ValueError) as exc:
        return json.dumps(
            {
                "status": "erro",
                "mensagem": str(exc),
            },
            ensure_ascii=False,
        )
