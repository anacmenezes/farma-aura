
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[3]
ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(ENV_FILE)


@dataclass(frozen=True)
class PharmacyConfig:
    name: str
    base_url: str
    search_mode: str = "catalog"


PHARMACIES: tuple[PharmacyConfig, ...] = (
    PharmacyConfig(
        name="Pague Menos",
        base_url="https://www.paguemenos.com.br",
        search_mode="intelligent_search",
    ),
    PharmacyConfig(
        name="Drogaria São Paulo",
        base_url="https://www.drogariasaopaulo.com.br",
    ),
    PharmacyConfig(
        name="Drogarias Pacheco",
        base_url="https://www.drogariaspacheco.com.br",
    ),
    PharmacyConfig(
        name="Drogarias Tamoio",
        base_url="https://www.drogariastamoio.com.br",
    ),
    PharmacyConfig(
        name="Drogaria Venancio",
        base_url="https://www.drogariavenancio.com.br",
    ),
    PharmacyConfig(
        name="Droga Raia",
        base_url="https://www.drogaraia.com.br",
    ),
    PharmacyConfig(
        name="Drogasil",
        base_url="https://www.drogasil.com.br",
    ),
)


OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
REQUEST_TIMEOUT_SECONDS = 20.0
MAX_PRODUCTS_PER_PHARMACY = 10
MAX_CONCURRENT_REQUESTS = 5
