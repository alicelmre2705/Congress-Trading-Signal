"""House financial disclosure index download, parsing, and audit."""
from __future__ import annotations

import time
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import pandas as pd
import requests
from tqdm.auto import tqdm

from .utils import RAW_HOUSE_INDEX_DIR, PROCESSED_HOUSE_DIR, REPORTS_DIR, to_iso_date, utc_now_iso

HOUSE_ZIP_TEMPLATE = 'https://disclosures-clerk.house.gov/public_disc/financial-pdfs/{year}FD.zip'
HOUSE_PDF_TEMPLATE = 'https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/{year}/{doc_id}.pdf'

HOUSE_INDEX_COLUMNS = [
    'year', 'filing_type', 'filing_date_raw', 'filing_date', 'doc_id',
    'last_name', 'first_name', 'declarant_name_raw', 'state_dst',
    'pdf_url', 'source_xml_path'
]


def build_house_zip_url(year: int) -> str:
    return HOUSE_ZIP_TEMPLATE.format(year=int(year))


def build_house_pdf_url(year: int, doc_id: Any) -> str:
    return HOUSE_PDF_TEMPLATE.format(year=int(year), doc_id=str(doc_id).strip())


def _request_get(url: str, timeout: int = 30, retries: int = 3) -> requests.Response:
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, timeout=timeout)
            return response
        except Exception as exc:  # network layer
            last_error = exc
            time.sleep(min(2 ** attempt, 8))
    raise RuntimeError(f'GET failed after {retries} retries: {url}') from last_error


def download_house_zip(year: int, output_dir: Path = RAW_HOUSE_INDEX_DIR, force: bool = False) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    url = build_house_zip_url(year)
    path = output_dir / f'{year}FD.zip'
    tmp_path = path.with_suffix(path.suffix + '.tmp')
    if path.exists() and path.stat().st_size > 0 and not force:
        return {'year': year, 'url': url, 'path': str(path), 'status': 'skipped_existing', 'http_status': None, 'error': ''}
    try:
        response = _request_get(url)
        if response.status_code != 200:
            return {'year': year, 'url': url, 'path': str(path), 'status': 'http_error', 'http_status': response.status_code, 'error': response.text[:300]}
        tmp_path.write_bytes(response.content)
        tmp_path.replace(path)
        return {'year': year, 'url': url, 'path': str(path), 'status': 'ok', 'http_status': response.status_code, 'error': ''}
    except Exception as exc:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        return {'year': year, 'url': url, 'path': str(path), 'status': 'exception', 'http_status': None, 'error': repr(exc)}


def extract_xml_from_zip(zip_path: Path, year: int, output_dir: Path = RAW_HOUSE_INDEX_DIR) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    expected_name = f'{year}FD.xml'
    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
        xml_names = [n for n in names if n.lower().endswith('.xml')]
        if not xml_names:
            raise FileNotFoundError(f'No XML found in {zip_path}')
        selected = expected_name if expected_name in names else xml_names[0]
        target = output_dir / expected_name
        with zf.open(selected) as src:
            target.write_bytes(src.read())
    return target


def _child_text(node: ET.Element, tag: str) -> str:
    child = node.find(tag)
    return (child.text or '').strip() if child is not None else ''


def parse_house_xml(xml_path: Path, year: int) -> pd.DataFrame:
    tree = ET.parse(xml_path)
    root = tree.getroot()
    members = root.findall('.//Member')
    rows: list[dict[str, Any]] = []
    for member in members:
        first = _child_text(member, 'First')
        last = _child_text(member, 'Last')
        doc_id = _child_text(member, 'DocID')
        raw_date = _child_text(member, 'FilingDate')
        rows.append({
            'year': int(year),
            'filing_type': _child_text(member, 'FilingType'),
            'filing_date_raw': raw_date,
            'filing_date': to_iso_date(raw_date),
            'doc_id': str(doc_id).strip(),
            'last_name': last,
            'first_name': first,
            'declarant_name_raw': ' '.join([x for x in [first, last] if x]).strip(),
            'state_dst': _child_text(member, 'StateDst'),
            'source_xml_path': str(xml_path),
        })
    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(columns=HOUSE_INDEX_COLUMNS)
    df['pdf_url'] = df.apply(lambda r: build_house_pdf_url(r['year'], r['doc_id']), axis=1)
    return df[HOUSE_INDEX_COLUMNS]


def build_house_filings_index(start_year: int = 2013, end_year: int = 2026, sleep_seconds: float = 0.25, force: bool = False) -> tuple[pd.DataFrame, pd.DataFrame]:
    all_frames: list[pd.DataFrame] = []
    logs: list[dict[str, Any]] = []
    for year in tqdm(range(start_year, end_year + 1), desc='House years'):
        log = download_house_zip(year, force=force)
        try:
            if log['status'] in {'ok', 'skipped_existing'}:
                xml_path = extract_xml_from_zip(Path(log['path']), year)
                df_year = parse_house_xml(xml_path, year)
                all_frames.append(df_year)
                log.update({'xml_path': str(xml_path), 'n_filings': len(df_year)})
        except Exception as exc:
            log.update({'status': 'parse_exception', 'error': repr(exc)})
        logs.append(log)
        time.sleep(sleep_seconds)
    df_all = pd.concat(all_frames, ignore_index=True) if all_frames else pd.DataFrame(columns=HOUSE_INDEX_COLUMNS)
    return df_all, pd.DataFrame(logs)


def filter_ptr_filings(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    return df[df['filing_type'].astype(str).str.upper().eq('P')].copy().reset_index(drop=True)


def save_index_outputs(df_all: pd.DataFrame, df_ptr: pd.DataFrame, output_dir: Path = PROCESSED_HOUSE_DIR) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        'house_filings_index': output_dir / 'house_filings_index.csv',
        'house_ptr_index': output_dir / 'house_ptr_index.csv',
    }
    df_all.to_csv(paths['house_filings_index'], index=False)
    df_ptr.to_csv(paths['house_ptr_index'], index=False)
    for year, df_year in df_ptr.groupby('year'):
        path = output_dir / f'ptr_index_{int(year)}.csv'
        df_year.to_csv(path, index=False)
        paths[f'ptr_index_{int(year)}'] = path
    return {k: str(v) for k, v in paths.items()}


def summarize_house_index(df_all: pd.DataFrame, df_ptr: pd.DataFrame, logs: pd.DataFrame | None = None) -> dict[str, Any]:
    dup_count = int(df_all.duplicated(['year', 'doc_id']).sum()) if not df_all.empty else 0
    filing_type_by_year = pd.crosstab(df_all['year'], df_all['filing_type']).to_dict() if not df_all.empty else {}
    ptr_by_year = df_ptr.groupby('year').size().astype(int).to_dict() if not df_ptr.empty else {}
    years_ok = int(logs['status'].isin(['ok', 'skipped_existing']).sum()) if logs is not None and not logs.empty else int(df_all['year'].nunique())
    return {
        'timestamp': utc_now_iso(),
        'years_ok': years_ok,
        'n_total_filings': int(len(df_all)),
        'n_total_ptr': int(len(df_ptr)),
        'ptr_by_year': {str(k): int(v) for k, v in ptr_by_year.items()},
        'filing_type_by_year': filing_type_by_year,
        'missing_doc_id_count': int((df_all['doc_id'].astype(str).str.strip() == '').sum()) if not df_all.empty else 0,
        'missing_filing_date_count': int(df_all['filing_date'].isna().sum()) if not df_all.empty else 0,
        'duplicate_year_doc_id_count': dup_count,
    }


def write_house_index_report(summary: dict[str, Any], output_paths: dict[str, str], report_path: Path = REPORTS_DIR / 'house_index_audit.md') -> Path:
    lines = [
        '# House index audit',
        '',
        f"Generated at: `{summary.get('timestamp')}`",
        '',
        '## Scope',
        '- Source officielle House uniquement.',
        '- Filtre PTR: `FilingType = P`.',
        '- Les chiffres historiques sont des repères, pas des constantes hardcodées.',
        '',
        '## Metrics',
        f"- Years OK: `{summary.get('years_ok')}`",
        f"- Total filings: `{summary.get('n_total_filings')}`",
        f"- Total PTR: `{summary.get('n_total_ptr')}`",
        f"- Missing DocID: `{summary.get('missing_doc_id_count')}`",
        f"- Missing FilingDate: `{summary.get('missing_filing_date_count')}`",
        f"- Duplicates year + doc_id: `{summary.get('duplicate_year_doc_id_count')}`",
        '',
        '## PTR by year',
    ]
    for year, count in summary.get('ptr_by_year', {}).items():
        lines.append(f'- {year}: {count}')
    lines += ['', '## Files produced']
    for name, path in output_paths.items():
        lines.append(f'- `{name}`: `{path}`')
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return report_path
