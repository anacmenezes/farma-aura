
import json
from typing import Any, Protocol

from langchain.tools import tool


class AvailabilityService(Protocol):
    async def check_availability(
        self,
        product_name: str,
        cep: str,
    ) -> dict[str, Any]:
        ...


def create_check_availability_tool(
    availability_service: AvailabilityService,
):
    
    @tool("consultar_disponibilidade")
    async def consultar_disponibilidade(
        product_name: str,
        cep: str,
    ) -> str:
        product_name = product_name.strip()
        cep = "".join(
            character for character in cep
            if character.isdigit()
        )

        if not product_name:
            return json.dumps(
                {"erro": "Informe o nome do produto."},
                ensure_ascii=False,
            )

        if len(cep) != 8:
            return json.dumps(
                {"erro": "O CEP deve conter 8 dígitos."},
                ensure_ascii=False,
            )

        try:
            result = await availability_service.check_availability(
                product_name=product_name,
                cep=cep,
            )

            return json.dumps(
                {
                    "status": "consulta_concluida",
                    "resultado": result,
                },
                ensure_ascii=False,
                default=str,
            )

        except Exception as exc:
            return json.dumps(
                {
                    "status": "erro",
                    "mensagem": (
                        "Não foi possível verificar a disponibilidade "
                        "ou a entrega. Esses dados permanecem desconhecidos."
                    ),
                    "tipo_erro": type(exc).__name__,
                },
                ensure_ascii=False,
            )

    return consultar_disponibilidade
