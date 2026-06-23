"""Quiver access diagnostic and House validation helpers."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from .utils import AUDIT_DIR, EXTERNAL_QUIVER_DIR, PROCESSED_HOUSE_DIR, REPORTS_DIR, normalize_text_key, to_iso_date, utc_now_iso

BASE_URL = 'https://api.quiverquant.com'
CONGRESS_TRADING_ENDPOINT = '/beta/bulk/congresstrading'

NORMALIZED_COLUMNS = [
    'source', 'quiver_schema_version', 'name', 'bioguide_id', 'chamber', 'party',
    'district', 'state', 'ticker', 'ticker_type', 'company', 'transaction_type',
    'transaction_date', 'disclosure_date', 'amount_range', 'amount_raw',
    'description', 'comments', 'status', 'raw_json'
]


def get_quiver_token(env_name: str = 'QUIVER_API_TOKEN') -> str | None:
    token = os.environ.get(env_name, '').strip()
    return token or None


def quiver_get(endpoint: str, params: dict[str, Any] | None = None, token: str | None = None, timeout: int = 30) -> dict[str, Any]:
    token = token or get_quiver_token()
    if not token:
        return {'ok': False, 'status_code': None, 'data': None, 'error': 'missing_token'}
    headers = {'Authorization': f'Bearer {token}'}
    url = f'{BASE_URL}{endpoint}'
    try:
        response = requests.get(url, headers=headers, params=params or {}, timeout=timeout)
        try:
            data = response.json()
        except Exception as exc:
            data = None
            return {'ok': False, 'status_code': response.status_code, 'data': data, 'error': f'json_error={repr(exc)}'}
        return {'ok': response.ok, 'status_code': response.status_code, 'data': data, 'error': '' if response.ok else str(data)[:500]}
    except Exception as exc:
        return {'ok': False, 'status_code': None, 'data': None, 'error': repr(exc)}


def extract_records(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if isinstance(data, dict):
        for key in ['results', 'data', 'records', 'items']:
            if isinstance(data.get(key), list):
                return [x for x in data[key] if isinstance(x, dict)]
    return []


def diagnose_congresstrading_access(token: str | None = None, output_path: Path = AUDIT_DIR / 'quiver_api_access_diagnostic.json') -> dict[str, Any]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not token:
        diagnostic = {'timestamp': utc_now_iso(), 'status': 'skipped_missing_token', 'endpoint': CONGRESS_TRADING_ENDPOINT, 'tests': []}
        output_path.write_text(json.dumps(diagnostic, indent=2, ensure_ascii=False), encoding='utf-8')
        return diagnostic
    tests = []
    accessible_version = None
    for version in ['V2', 'V1']:
        params = {'version': version, 'normalized': 'true', 'nonstock': 'false', 'page': 1, 'page_size': 5}
        result = quiver_get(CONGRESS_TRADING_ENDPOINT, params=params, token=token)
        records = extract_records(result.get('data'))
        columns = sorted({k for record in records for k in record.keys()})
        tests.append({
            'version': version,
            'params': params,
            'ok': result.get('ok'),
            'status_code': result.get('status_code'),
            'n_records': len(records),
            'columns': columns,
            'sample': records[:2],
            'error': result.get('error'),
        })
        if result.get('ok') and records and accessible_version is None:
            accessible_version = version
            break
    diagnostic = {'timestamp': utc_now_iso(), 'status': 'ok' if accessible_version else 'no_access', 'endpoint': CONGRESS_TRADING_ENDPOINT, 'accessible_version': accessible_version, 'tests': tests}
    output_path.write_text(json.dumps(diagnostic, indent=2, ensure_ascii=False), encoding='utf-8')
    return diagnostic


def fetch_congresstrading_pages(token: str, version: str, page_size: int = 500, max_pages: int = 3, output_raw_path: Path | None = None) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for page in range(1, max_pages + 1):
        params = {'version': version, 'normalized': 'true', 'nonstock': 'false', 'page': page, 'page_size': page_size}
        result = quiver_get(CONGRESS_TRADING_ENDPOINT, params=params, token=token)
        page_records = extract_records(result.get('data')) if result.get('ok') else []
        if not page_records:
            break
        records.extend(page_records)
        if output_raw_path:
            output_raw_path.parent.mkdir(parents=True, exist_ok=True)
            output_raw_path.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding='utf-8')
    return records


def _get(record: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in record and record[key] not in [None, '']:
            return record[key]
    return None


def normalize_quiver_records(records: list[dict[str, Any]], schema_version: str) -> pd.DataFrame:
    rows = []
    for record in records:
        if schema_version.upper() == 'V2':
            row = {
                'source': 'quiver', 'quiver_schema_version': 'V2',
                'name': _get(record, 'Name'), 'bioguide_id': _get(record, 'BioGuideID'),
                'chamber': _get(record, 'Chamber'), 'party': _get(record, 'Party'),
                'district': _get(record, 'District'), 'state': _get(record, 'State'),
                'ticker': _get(record, 'Ticker'), 'ticker_type': _get(record, 'TickerType'),
                'company': _get(record, 'Company'), 'transaction_type': _get(record, 'Transaction'),
                'transaction_date': to_iso_date(_get(record, 'Traded')),
                'disclosure_date': to_iso_date(_get(record, 'Filed')),
                'amount_range': _get(record, 'Range'), 'amount_raw': _get(record, 'Trade_Size_USD'),
                'description': _get(record, 'Description'), 'comments': _get(record, 'Comments'),
                'status': _get(record, 'Status'), 'raw_json': json.dumps(record, ensure_ascii=False),
            }
        else:
            row = {
                'source': 'quiver', 'quiver_schema_version': 'V1',
                'name': _get(record, 'Representative'), 'bioguide_id': _get(record, 'BioGuideID'),
                'chamber': _get(record, 'House'), 'party': _get(record, 'Party'),
                'district': _get(record, 'District'), 'state': _get(record, 'State'),
                'ticker': _get(record, 'Ticker'), 'ticker_type': _get(record, 'TickerType'),
                'company': _get(record, 'Company'), 'transaction_type': _get(record, 'Transaction'),
                'transaction_date': to_iso_date(_get(record, 'TransactionDate', 'Date')),
                'disclosure_date': to_iso_date(_get(record, 'ReportDate')),
                'amount_range': _get(record, 'Range'), 'amount_raw': _get(record, 'Amount'),
                'description': _get(record, 'Description'), 'comments': _get(record, 'Comments'),
                'status': _get(record, 'Status'), 'raw_json': json.dumps(record, ensure_ascii=False),
            }
        rows.append(row)
    return pd.DataFrame(rows, columns=NORMALIZED_COLUMNS)


def filter_house_year(df: pd.DataFrame, year: int) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    out = df.copy()
    out['disclosure_date_dt'] = pd.to_datetime(out['disclosure_date'], errors='coerce')
    chamber = out['chamber'].fillna('').astype(str).str.lower()
    is_house = chamber.str.contains('house|representatives', regex=True)
    is_year = out['disclosure_date_dt'].dt.year.eq(int(year))
    return out[is_house & is_year].drop(columns=['disclosure_date_dt']).reset_index(drop=True)


def compare_house_quiver_coverage(house_ptr_2024: pd.DataFrame, quiver_house_2024: pd.DataFrame, output_path: Path = AUDIT_DIR / 'quiver_house_validation_2024.csv') -> tuple[pd.DataFrame, dict[str, Any]]:
    house = house_ptr_2024.copy()
    quiver = quiver_house_2024.copy()
    house['declarant_key'] = house['declarant_name_raw'].apply(normalize_text_key)
    quiver['declarant_key'] = quiver['name'].apply(normalize_text_key)
    house_keys = set(house['declarant_key'].dropna()) - {''}
    quiver_keys = set(quiver['declarant_key'].dropna()) - {''}
    overlap = house_keys & quiver_keys
    metrics = {
        'timestamp': utc_now_iso(),
        'n_house_ptr_filings_2024': int(len(house)),
        'n_quiver_house_transactions_2024': int(len(quiver)),
        'n_unique_house_declarants_2024': int(len(house_keys)),
        'n_unique_quiver_declarants_2024': int(len(quiver_keys)),
        'overlap_declarants_count': int(len(overlap)),
        'house_only_declarants_count': int(len(house_keys - quiver_keys)),
        'quiver_only_declarants_count': int(len(quiver_keys - house_keys)),
        'house_disclosure_date_min': str(pd.to_datetime(house.get('filing_date'), errors='coerce').min()),
        'house_disclosure_date_max': str(pd.to_datetime(house.get('filing_date'), errors='coerce').max()),
        'quiver_disclosure_date_min': str(pd.to_datetime(quiver.get('disclosure_date'), errors='coerce').min()),
        'quiver_disclosure_date_max': str(pd.to_datetime(quiver.get('disclosure_date'), errors='coerce').max()),
    }
    rows = [{'metric': k, 'value': v} for k, v in metrics.items()]
    result = pd.DataFrame(rows)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_path, index=False)
    return result, metrics


def write_quiver_report(diagnostic: dict[str, Any], metrics: dict[str, Any] | None = None, report_path: Path = REPORTS_DIR / 'house_quiver_validation_report.md') -> Path:
    lines = [
        '# House vs Quiver validation', '',
        f"Generated at: `{utc_now_iso()}`", '',
        '## Rule',
        'House XML + PDF remains the canonical source. Quiver is used only as an external sanity-check.', '',
        '## Quiver access',
        f"- Status: `{diagnostic.get('status')}`",
        f"- Accessible version: `{diagnostic.get('accessible_version')}`",
        f"- Endpoint: `{diagnostic.get('endpoint')}`", '',
    ]
    if metrics:
        lines += ['## 2024 coverage metrics']
        for key, value in metrics.items():
            lines.append(f'- {key}: `{value}`')
    else:
        lines += ['## 2024 coverage metrics', 'Skipped because Quiver access or House 2024 input was unavailable.']
    lines += ['', '## Interpretation', '- A Quiver mismatch is not automatically a House error.', '- No transaction-level match is claimed at this stage.']
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return report_path
