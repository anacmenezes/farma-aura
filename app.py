import asyncio
from decimal import Decimal, InvalidOperation

import streamlit as st

from backend.src.farmacia_api.graph import build_farma_aura_graph
from backend.src.farmacia_api.services.api_client import (
    listar_produtos,
    cadastrar_produto,
    FarmaAuraAPIError,
)

st.set_page_config(
    page_title="Farma Aura | Comparador de preços",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
        .block-container {
            max-width: 1200px;
            padding-top: 2rem;
            padding-bottom: 3rem;
        }

        .hero {
            padding: 1.5rem;
            border-radius: 16px;
            background: linear-gradient(120deg, #e8f7f1, #f4f8ff);
            margin-bottom: 1rem;
        }

        .hero h1 {
            color: #153e35;
            margin-bottom: 0.35rem;
        }

        .hero p {
            color: #42635a;
            margin-bottom: 0;
        }

        .price {
            color: #13845c;
            font-size: 1.8rem;
            font-weight: 750;
            margin: 0.5rem 0;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
        <h1>💊 Farma Aura</h1>
        <p>Compare ofertas de farmácias e encontre opções para consultar diretamente nas lojas.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.caption(
    "Os valores são provenientes dos catálogos consultados. "
    "Preço final, estoque e entrega podem variar."
)


with st.expander("📚 Catálogo de produtos", expanded=False):
    st.write(
        "Cadastre produtos no banco de dados ou consulte "
        "os produtos que já estão registrados."
    )

    with st.form("cadastro_produto_form"):
        nome = st.text_input(
            "Nome do produto",
            placeholder="Ex.: Dipirona 500 mg",
        )

        principio_ativo = st.text_input(
            "Princípio ativo",
            placeholder="Ex.: Dipirona sódica",
        )

        concentracao = st.text_input(
            "Concentração",
            placeholder="Ex.: 500 mg",
        )

        apresentacao = st.text_input(
            "Apresentação",
            placeholder="Ex.: Comprimidos",
        )

        cadastrar = st.form_submit_button(
            "Cadastrar produto",
            use_container_width=True,
        )

    if cadastrar:
        campos = {
            "Nome": nome,
            "Princípio ativo": principio_ativo,
            "Concentração": concentracao,
            "Apresentação": apresentacao,
        }

        campos_vazios = [
            campo
            for campo, valor in campos.items()
            if not valor.strip()
        ]

        if campos_vazios:
            st.warning(
                "Preencha os campos: "
                + ", ".join(campos_vazios)
            )
        else:
            try:
                with st.spinner("Cadastrando produto..."):
                    produto = cadastrar_produto(
                        nome=nome.strip(),
                        principio_ativo=principio_ativo.strip(),
                        concentracao=concentracao.strip(),
                        apresentacao=apresentacao.strip(),
                    )

                st.success(
                    f"Produto '{produto['nome']}' cadastrado "
                    "com sucesso no banco de dados!"
                )
                st.json(produto)

            except FarmaAuraAPIError as exc:
                st.error(f"Erro ao cadastrar: {exc}")

    st.divider()

    if st.button(
        "🔄 Consultar produtos cadastrados",
        key="consultar_catalogo",
        use_container_width=True,
    ):
        try:
            with st.spinner("Consultando o catálogo..."):
                produtos = listar_produtos()

            if produtos:
                st.dataframe(
                    produtos,
                    use_container_width=True,
                    hide_index=True,
                )
                st.caption(
                    f"Total de produtos cadastrados: {len(produtos)}"
                )
            else:
                st.info(
                    "Nenhum produto cadastrado no catálogo ainda."
                )

        except FarmaAuraAPIError as exc:
            st.error(f"Erro ao consultar o catálogo: {exc}")

@st.cache_resource
def get_graph():
    """Cria o grafo uma vez por sessão da aplicação."""
    return build_farma_aura_graph()


def run_search(query: str, cep: str | None) -> dict:
    """Executa a pesquisa assíncrona do LangGraph."""
    graph = get_graph()

    return asyncio.run(
        graph.ainvoke({
            "user_request": query,
            "cep": cep,
        })
    )


def valid_price(offer: dict) -> Decimal | None:
    """Converte o preço para Decimal quando válido."""
    try:
        value = offer.get("preco")

        if value is None or isinstance(value, bool):
            return None

        price = Decimal(str(value))

        if not price.is_finite() or price < 0:
            return None

        return price

    except (InvalidOperation, ValueError, TypeError):
        return None


def format_price(value) -> str:
    """Formata valores no padrão monetário brasileiro."""
    if value is None:
        return "Preço indisponível"

    try:
        price = Decimal(str(value))
        formatted = f"{price:,.2f}"

        formatted = (
            formatted.replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )

        return f"R$ {formatted}"

    except (InvalidOperation, ValueError, TypeError):
        return "Preço indisponível"


def get_offer_list(search: dict) -> list[dict]:
    """Obtém as ofertas da estrutura retornada pelo grafo."""
    comparison = search.get("comparacao") or {}
    offers = comparison.get("ofertas")

    if offers is None:
        offers = search.get("ofertas", [])

    if not isinstance(offers, list):
        return []

    return [
        offer for offer in offers
        if isinstance(offer, dict)
    ]


def has_textual_validation(offer: dict) -> bool:
    """
    Verifica se o conector registrou a validação textual.
    Isso não comprova equivalência farmacêutica.
    """
    return offer.get("validacao_textual_conector") is True


def packaging_label(offer: dict) -> str | None:
    """Monta o texto da embalagem quando a quantidade é conhecida."""
    quantity = offer.get("quantidade_embalagem")
    unit = offer.get("unidade_embalagem")

    if (
        isinstance(quantity, int)
        and not isinstance(quantity, bool)
        and quantity > 0
        and isinstance(unit, str)
        and unit.strip()
    ):
        return f"Embalagem: {quantity} {unit}"

    return None


def unit_price_label(offer: dict) -> str | None:
    """
    Calcula o preço por unidade contável da embalagem.
    Não usa o estoque da farmácia como quantidade da embalagem.
    """
    price = valid_price(offer)
    quantity = offer.get("quantidade_embalagem")
    unit = offer.get("unidade_embalagem")

    if (
        price is None
        or not isinstance(quantity, int)
        or isinstance(quantity, bool)
        or quantity <= 0
        or not isinstance(unit, str)
    ):
        return None

    countable_units = {
        "comprimidos": "comprimido",
        "cápsulas": "cápsula",
        "tabletes": "tablete",
        "unidades": "unidade",
        "drágeas": "drágea",
        "sachês": "sachê",
        "ampolas": "ampola",
        "flaconetes": "flaconete",
        "supositórios": "supositório",
    }

    singular = countable_units.get(unit)

    if singular is None:
        return None

    unit_price = price / Decimal(quantity)

    return f"{format_price(unit_price)}/{singular}"


with st.form("product_search_form"):
    st.subheader("O que você está procurando?")

    query = st.text_input(
        "Nome do produto",
        placeholder="Ex.: dipirona 500 mg comprimido",
    )

    cep_input = st.text_input(
        "CEP (opcional)",
        placeholder="Ex.: 28016812",
        max_chars=9,
        help=(
            "Informar o CEP não garante confirmação de preço regional, "
            "estoque ou prazo de entrega."
        ),
    )

    submitted = st.form_submit_button(
        "🔎 Pesquisar ofertas",
        type="primary",
        use_container_width=True,
    )


if submitted:
    query = query.strip()

    cep_digits = "".join(
        character for character in cep_input
        if character.isdigit()
    )

    if not query:
        st.warning("Digite o nome de um produto para pesquisar.")

    elif cep_digits and len(cep_digits) != 8:
        st.warning("O CEP deve conter oito dígitos.")

    else:
        try:
            with st.spinner(
                "Consultando as farmácias e comparando os preços..."
            ):
                result = run_search(query, cep_digits or None)

            st.session_state["farma_aura_result"] = result
            st.session_state["farma_aura_query"] = query

        except Exception as exc:
            st.error(
                "Não foi possível executar a pesquisa. "
                f"Erro: {type(exc).__name__}: {exc}"
            )


result = st.session_state.get("farma_aura_result")

if result:
    search = result.get("search_results") or {}
    offers = get_offer_list(search)
    pharmacies = search.get("farmacias") or []

    query_label = st.session_state.get(
        "farma_aura_query",
        "",
    )

    st.divider()
    st.subheader("Resultados da pesquisa")
    st.write(f"Busca: **{query_label}**")

    status = search.get("status", "indefinido")
    successful = search.get("farmacias_com_sucesso", 0)
    consulted = search.get(
        "farmacias_consultadas",
        len(pharmacies),
    )

    metric1, metric2, metric3 = st.columns(3)

    metric1.metric("Ofertas encontradas", len(offers))
    metric2.metric("Farmácias com sucesso", successful)
    metric3.metric("Farmácias consultadas", consulted)

    if status == "sucesso":
        st.success("Pesquisa concluída.")

    elif status in ("sucesso_parcial", "falha_parcial"):
        st.warning(
            "Pesquisa parcial: algumas farmácias não responderam."
        )

    elif status == "sem_resultados":
        st.info(
            "Nenhuma oferta foi encontrada para essa pesquisa."
        )

    elif status == "falha_buscas":
        st.error(
            "Não foi possível obter ofertas das farmácias. "
            "Tente novamente mais tarde."
        )

    elif status == "esclarecimento_necessario":
        st.info(
            search.get("mensagem")
            or search.get("pergunta")
            or "Informe mais detalhes sobre o produto."
        )

    if offers:
        filter_col, sort_col = st.columns([2, 1])

        with filter_col:
            pharmacy_names = sorted({
                str(
                    offer.get("farmacia")
                    or "Farmácia não identificada"
                )
                for offer in offers
            })

            selected_pharmacy = st.selectbox(
                "Filtrar por farmácia",
                ["Todas as farmácias"] + pharmacy_names,
            )

        with sort_col:
            sort_order = st.selectbox(
                "Ordenar ofertas",
                [
                    "Menor preço",
                    "Maior preço",
                    "Nome do produto",
                ],
            )

        visible_offers = offers.copy()

        if selected_pharmacy != "Todas as farmácias":
            visible_offers = [
                offer for offer in visible_offers
                if (
                    offer.get("farmacia")
                    or "Farmácia não identificada"
                ) == selected_pharmacy
            ]

        if sort_order == "Menor preço":
            visible_offers.sort(
                key=lambda offer: (
                    valid_price(offer) is None,
                    valid_price(offer)
                    if valid_price(offer) is not None
                    else Decimal("Infinity"),
                )
            )

        elif sort_order == "Maior preço":
            visible_offers.sort(
                key=lambda offer: (
                    valid_price(offer) is None,
                    -valid_price(offer)
                    if valid_price(offer) is not None
                    else Decimal("0"),
                )
            )

        else:
            visible_offers.sort(
                key=lambda offer: str(
                    offer.get("nome") or ""
                ).casefold()
            )

        # Calcula o menor preço depois do filtro por farmácia.
        eligible_offers = [
            offer for offer in visible_offers
            if (
                has_textual_validation(offer)
                and valid_price(offer) is not None
            )
        ]

        lowest_price = (
            min(valid_price(offer) for offer in eligible_offers)
            if eligible_offers
            else None
        )

        st.subheader("Ofertas disponíveis")

        if lowest_price is not None:
            st.caption(
                "Menor preço entre ofertas com validação textual: "
                f"**{format_price(lowest_price)}**. "
                "Confira a apresentação e a embalagem na loja."
            )

        else:
            st.info(
                "Não há ofertas com preço válido e validação textual "
                "registrada para destacar um menor preço."
            )

        for start in range(0, len(visible_offers), 3):
            row_offers = visible_offers[start:start + 3]
            columns = st.columns(3)

            for column, offer in zip(columns, row_offers):
                price = valid_price(offer)

                is_best = (
                    has_textual_validation(offer)
                    and price is not None
                    and lowest_price is not None
                    and price == lowest_price
                )

                pharmacy = (
                    offer.get("farmacia")
                    or "Farmácia não identificada"
                )

                name = offer.get("nome") or "Produto sem nome"
                brand = offer.get("marca") or ""
                presentation = offer.get("apresentacao_item") or ""
                url = offer.get("url") or ""

                package = packaging_label(offer)
                unit_label = unit_price_label(offer)

                with column:
                    with st.container(border=True):
                        if is_best:
                            st.success("★ Menor preço")

                        st.caption(pharmacy)
                        st.markdown(f"**{name}**")

                        details = " · ".join(
                            item
                            for item in (brand, presentation)
                            if item
                        )

                        if details:
                            st.caption(details)

                        if package:
                            st.caption(package)
                        else:
                            st.caption(
                                "Quantidade da embalagem não identificada."
                            )

                        if unit_label:
                            st.caption(
                                f"Preço por unidade: {unit_label}"
                            )
                        else:
                            st.caption(
                                "Preço por unidade indisponível."
                            )

                        if offer.get("consulta_alternativa"):
                            st.caption(
                                "Resultado encontrado por busca alternativa."
                            )

                        st.markdown(
                            f'<div class="price">{format_price(price)}</div>',
                            unsafe_allow_html=True,
                        )

                        if url.startswith(("https://", "http://")):
                            st.link_button(
                                "Consultar na farmácia ↗",
                                url,
                                use_container_width=True,
                            )
                        else:
                            st.caption(
                                "Link do produto indisponível."
                            )

        st.caption(
            "O preço por unidade é calculado com base na quantidade "
            "extraída do texto do catálogo. Confirme a embalagem na loja. "
            "Validação textual não comprova equivalência farmacêutica."
        )

    if pharmacies:
        with st.expander("Status das farmácias consultadas"):
            for pharmacy in pharmacies:
                name = pharmacy.get("farmacia", "Farmácia")
                pharmacy_status = pharmacy.get(
                    "status",
                    "indefinido",
                )
                quantity = pharmacy.get("quantidade_ofertas", 0)
                error = pharmacy.get("erro")
                alternative = pharmacy.get(
                    "consulta_alternativa",
                    False,
                )

                if pharmacy_status in {"sucesso", "sucesso_parcial"}:
                    label = f"🟢 **{name}** — {quantity} ofertas"

                    if alternative:
                        label += " · busca alternativa"

                    st.write(label)

                else:
                    st.write(
                        f"🔴 **{name}** — consulta não concluída"
                    )

                    if error:
                        st.caption(f"Detalhe: {error}")

    response = result.get("final_response")

    if response:
        with st.expander("Resumo gerado pelo agente"):
            st.markdown(response)


st.divider()

st.caption(
    "Farma Aura compara ofertas de catálogo. Confirme preço final, "
    "disponibilidade e entrega diretamente com a farmácia. "
    "A ferramenta não substitui a orientação de um profissional de saúde."
)