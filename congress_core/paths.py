"""Bootstrap chemins + secrets — source unique (remplace les 3 doctrines : BASE_DIR marqueur /
HERE codé en dur / sys.path.insert+monkeypatch).

`DataRoot` encapsule l'arborescence de données d'une chambre. Aujourd'hui House = `data_v1/`
(tables/pdfs/index/reference) ; la Phase 7 déplacera vers `data/house/`. On passe le `data_dir`
explicitement (ou on le découvre par marqueur) pour router 100 % des I/O sans chemin codé en dur.
"""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv as _load_dotenv
except Exception:  # dégradation gracieuse si python-dotenv absent
    def _load_dotenv(*a, **k):
        return False


def find_base_dir(start: Path, marker: str = "data_v1") -> Path:
    """Remonte depuis `start` jusqu'au premier dossier contenant `marker`. Ancrage robuste,
    indépendant du CWD. Reproduit house_multiyear.BASE_DIR."""
    start = Path(start).resolve()
    for p in [start, *start.parents]:
        if (p / marker).is_dir():
            return p
    return start


def load_env(base_dir: Path) -> None:
    """Charge `base_dir/.env` puis, si une clé manque encore, un `.env` ailleurs dans l'arbre."""
    _load_dotenv(Path(base_dir) / ".env")
    if not os.getenv("ANTHROPIC_API_KEY"):
        _load_dotenv()


def get_secret(key: str, base_dir: Path | None = None) -> str | None:
    """Secret depuis l'environnement, repli sur le `.env` local (parse simple). Unifie les
    `_api_key()` / parse `.env` dupliqués dans senate_ocr et senate_finalize."""
    v = os.environ.get(key)
    if v:
        return v
    if base_dir:
        envf = Path(base_dir) / ".env"
        if envf.exists():
            for line in envf.read_text().splitlines():
                if line.startswith(f"{key}="):
                    return line.split("=", 1)[1].strip() or None
    return None


class DataRoot:
    """Arborescence de données d'une chambre. `data_dir` pointe vers le dossier racine des données
    (ex. House actuel : <base>/data_v1 ; futur : <repo>/data/house). Toutes les I/O passent par ici."""

    def __init__(self, chamber: str, data_dir: Path):
        self.chamber = chamber
        self.data_dir = Path(data_dir)

    @classmethod
    def house_legacy(cls, start: Path | None = None) -> "DataRoot":
        """Construit le DataRoot House sur l'arbo ACTUELLE (data_v1/), par marqueur. Transitoire
        jusqu'à la Phase 7 (data/house/)."""
        base = find_base_dir(start or Path.cwd(), "data_v1")
        return cls("house", base / "data_v1")

    @property
    def tables(self) -> Path:
        return self.data_dir / "tables"

    def tables_dir(self, year=None) -> Path:
        return self.tables / str(year) if year is not None else self.tables

    @property
    def pdfs(self) -> Path:
        return self.data_dir / "pdfs"

    @property
    def index(self) -> Path:
        return self.data_dir / "index"

    @property
    def reference(self) -> Path:
        return self.data_dir / "reference"

    @property
    def ocr_cache(self) -> Path:
        return self.data_dir / "ocr_cache"

    @property
    def reports(self) -> Path:
        return self.data_dir / "reports"

    @property
    def media(self) -> Path:
        return self.reports / "media"

    @property
    def quiver_cache_path(self) -> Path:
        return self.tables / "_quiver_house_cache.csv"
