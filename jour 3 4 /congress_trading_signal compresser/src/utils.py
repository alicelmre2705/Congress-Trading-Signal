"""Shared utilities for the House J1-J4 data foundation."""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

import pandas as pd


def find_project_root(start: Path | None = None) -> Path:
    """Find the repository root by looking for README.md or .gitignore."""
    current = (start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / 'README.md').exists() or (candidate / '.gitignore').exists():
            return candidate
    return current


ROOT = find_project_root()
DATA_DIR = ROOT / 'data'
RAW_HOUSE_INDEX_DIR = DATA_DIR / 'raw' / 'house' / 'index'
RAW_HOUSE_PDF_DIR = DATA_DIR / 'raw' / 'house' / 'ptr_pdfs'
PROCESSED_HOUSE_DIR = DATA_DIR / 'processed' / 'house'
EXTERNAL_QUIVER_DIR = DATA_DIR / 'external' / 'quiver'
AUDIT_DIR = DATA_DIR / 'audit'
REPORTS_DIR = ROOT / 'reports'
SRC_DIR = ROOT / 'src'

REQUIRED_DIRS = [
    RAW_HOUSE_INDEX_DIR,
    RAW_HOUSE_PDF_DIR,
    PROCESSED_HOUSE_DIR,
    EXTERNAL_QUIVER_DIR,
    AUDIT_DIR,
    REPORTS_DIR,
    SRC_DIR,
]


def ensure_project_dirs() -> list[Path]:
    """Create project directories and return them."""
    for path in REQUIRED_DIRS:
        path.mkdir(parents=True, exist_ok=True)
    return REQUIRED_DIRS


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding='utf-8')


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding='utf-8'))


def write_markdown(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + '\n', encoding='utf-8')


def token_present(env_name: str = 'QUIVER_API_TOKEN') -> bool:
    return bool(os.environ.get(env_name, '').strip())


def safe_to_datetime(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors='coerce', utc=False)


def to_iso_date(value: Any) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    ts = pd.to_datetime(value, errors='coerce')
    if pd.isna(ts):
        return None
    return ts.strftime('%Y-%m-%d')


def normalize_text_key(value: Any) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ''
    text = str(value).strip().lower()
    text = re.sub(r'\bhon\.?\b', '', text)
    text = re.sub(r'[^a-z0-9]+', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


def dataframe_overview(df: pd.DataFrame, name: str) -> dict[str, Any]:
    return {
        'name': name,
        'shape': list(df.shape),
        'columns': list(df.columns),
        'nulls': df.isna().sum().to_dict(),
    }


def require_file(path: Path, hint: str = '') -> None:
    if not path.exists():
        msg = f'Missing file: {path}'
        if hint:
            msg += f'\nHint: {hint}'
        raise FileNotFoundError(msg)
