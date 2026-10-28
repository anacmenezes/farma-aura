
from typing import Any

from langgraph.graph import END, START, StateGraph

from farmacia_api.graph.nodes import create_graph_nodes
from farmacia_api.graph.state import FarmaAuraState
from farmacia_api.services.product_search import ProductSearchService


def build_farma_aura_graph(
    search_service: ProductSearchService | None = None,
    response_agent: Any | None = None,
):

    if search_service is None:
        search_service = ProductSearchService()

    nodes = create_graph_nodes(
        search_service=search_service,
        response_agent=response_agent,
    )

    graph = StateGraph(FarmaAuraState)
    graph.add_node("search", nodes["search"])
    graph.add_node("respond", nodes["respond"])

    graph.add_edge(START, "search")
    graph.add_edge("search", "respond")
    graph.add_edge("respond", END)

    return graph.compile()
