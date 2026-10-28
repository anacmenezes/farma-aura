
import os

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "http://127.0.0.1:8000",
).rstrip("/")


class FarmaAuraAPIError(Exception):
    """Erro de comunicação com a API Farma Aura."""


def _request(method: str, path: str, **kwargs):
    url = f"{API_BASE_URL}{path}"

    try:
        response = requests.request(
            method,
            url,
            timeout=15,
            **kwargs,
        )
    except requests.RequestException as exc:
        raise FarmaAuraAPIError(
            "Não foi possível conectar à API. "
            "Confirme se a FastAPI está em execução."
        ) from exc

    if response.status_code >= 400:
        try:
            detail = response.json().get("detail", response.text)
        except ValueError:
            detail = response.text

        raise FarmaAuraAPIError(
            f"API retornou HTTP {response.status_code}: {detail}"
        )

    if response.status_code == 204:
        return None

    return response.json()


def listar_produtos() -> list[dict]:
    return _request("GET", "/produtos")


def cadastrar_produto(
    *,
    nome: str,
    principio_ativo: str,
    concentracao: str,
    apresentacao: str,
) -> dict:
    payload = {
        "nome": nome,
        "principio_ativo": principio_ativo,
        "concentracao": concentracao,
        "apresentacao": apresentacao,
    }

    return _request("POST", "/produtos", json=payload)


def consultar_produto(product_id: int) -> dict:
    return _request("GET", f"/produtos/{product_id}")
