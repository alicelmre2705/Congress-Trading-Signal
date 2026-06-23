"""House PTR PDF download and manifest generation."""
from __future__ import annotations

import hashlib
import time
from pathlib import Path
from typing import Any

import pandas as pd
import requests
from pypdf import PdfReader
from tqdm.auto import tqdm

from .utils import AUDIT_DIR, RAW_HOUSE_PDF_DIR, REPORTS_DIR, utc_now_iso

MANIFEST_COLUMNS = [
    'year', 'doc_id', 'filing_date', 'declarant_name_raw', 'state_dst', 'pdf_url',
    'local_path', 'http_status', 'download_status', 'file_size_bytes', 'sha256',
    'content_type', 'n_pages', 'text_extractable_flag', 'downloaded_at', 'error_message'
]

VALID_DOWNLOAD_STATUS = {'ok', 'skipped_existing', 'http_error', 'invalid_pdf', 'zero_byte', 'exception'}


def _request_get(url: str, timeout: int = 30, retries: int = 3) -> requests.Response:
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            return requests.get(url, timeout=timeout)
        except Exception as exc:
            last_error = exc
            time.sleep(min(2 ** attempt, 8))
    raise RuntimeError(f'GET failed after {retries} retries: {url}') from last_error


def local_pdf_path(row: pd.Series, output_base_dir: Path = RAW_HOUSE_PDF_DIR) -> Path:
    return output_base_dir / str(int(row['year'])) / f"{str(row['doc_id']).strip()}.pdf"


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b''):
            h.update(chunk)
    return h.hexdigest()


def get_file_size(path: Path) -> int:
    return int(path.stat().st_size) if path.exists() else 0


def get_pdf_page_count(path: Path) -> int | None:
    try:
        return len(PdfReader(str(path)).pages)
    except Exception:
        return None


def is_valid_pdf(path: Path) -> bool:
    if not path.exists() or path.stat().st_size == 0:
        return False
    try:
        with path.open('rb') as handle:
            if handle.read(5) != b'%PDF-':
                return False
        return get_pdf_page_count(path) is not None
    except Exception:
        return False


def text_extractable_flag(path: Path, max_pages: int = 1) -> bool:
    try:
        reader = PdfReader(str(path))
        chars = 0
        for page in reader.pages[:max_pages]:
            chars += len(page.extract_text() or '')
        return chars > 50
    except Exception:
        return False


def _base_manifest_row(row: pd.Series, path: Path) -> dict[str, Any]:
    return {
        'year': int(row['year']),
        'doc_id': str(row['doc_id']).strip(),
        'filing_date': row.get('filing_date', ''),
        'declarant_name_raw': row.get('declarant_name_raw', ''),
        'state_dst': row.get('state_dst', ''),
        'pdf_url': row.get('pdf_url', ''),
        'local_path': str(path),
        'http_status': None,
        'download_status': 'exception',
        'file_size_bytes': None,
        'sha256': None,
        'content_type': None,
        'n_pages': None,
        'text_extractable_flag': None,
        'downloaded_at': utc_now_iso(),
        'error_message': '',
    }


def _enrich_file_fields(payload: dict[str, Any], path: Path) -> dict[str, Any]:
    payload['file_size_bytes'] = get_file_size(path)
    payload['sha256'] = sha256_file(path) if path.exists() and path.stat().st_size > 0 else None
    payload['n_pages'] = get_pdf_page_count(path)
    payload['text_extractable_flag'] = text_extractable_flag(path) if is_valid_pdf(path) else False
    return payload


def download_pdf(row: pd.Series, output_base_dir: Path = RAW_HOUSE_PDF_DIR, force: bool = False, timeout: int = 30) -> dict[str, Any]:
    path = local_pdf_path(row, output_base_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = _base_manifest_row(row, path)
    if path.exists() and not force:
        if is_valid_pdf(path):
            payload['download_status'] = 'skipped_existing'
            return _enrich_file_fields(payload, path)
        path.unlink(missing_ok=True)
    tmp_path = path.with_suffix(path.suffix + '.tmp')
    try:
        response = _request_get(str(row['pdf_url']), timeout=timeout)
        payload['http_status'] = response.status_code
        payload['content_type'] = response.headers.get('content-type', '')
        if response.status_code != 200:
            payload['download_status'] = 'http_error'
            payload['error_message'] = response.text[:300]
            return payload
        tmp_path.write_bytes(response.content)
        if tmp_path.stat().st_size == 0:
            payload['download_status'] = 'zero_byte'
            tmp_path.unlink(missing_ok=True)
            return payload
        tmp_path.replace(path)
        if not is_valid_pdf(path):
            payload['download_status'] = 'invalid_pdf'
            return _enrich_file_fields(payload, path)
        payload['download_status'] = 'ok'
        return _enrich_file_fields(payload, path)
    except Exception as exc:
        tmp_path.unlink(missing_ok=True)
        payload['download_status'] = 'exception'
        payload['error_message'] = repr(exc)
        return payload


def download_all_pdfs(ptr_index_df: pd.DataFrame, output_base_dir: Path = RAW_HOUSE_PDF_DIR, manifest_path: Path = AUDIT_DIR / 'house_pdf_manifest.csv', sleep_seconds: float = 0.25, force: bool = False, max_files: int | None = None, save_every: int = 100) -> pd.DataFrame:
    rows = []
    work = ptr_index_df.head(max_files).copy() if max_files else ptr_index_df.copy()
    for i, (_, row) in enumerate(tqdm(work.iterrows(), total=len(work), desc='House PTR PDFs'), start=1):
        rows.append(download_pdf(row, output_base_dir=output_base_dir, force=force))
        if i % save_every == 0:
            pd.DataFrame(rows, columns=MANIFEST_COLUMNS).to_csv(manifest_path, index=False)
        time.sleep(sleep_seconds)
    manifest = pd.DataFrame(rows, columns=MANIFEST_COLUMNS)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest.to_csv(manifest_path, index=False)
    return manifest


def summarize_manifest(manifest: pd.DataFrame, expected_count: int | None = None) -> dict[str, Any]:
    counts = manifest['download_status'].value_counts(dropna=False).to_dict() if not manifest.empty else {}
    ok_like = int(counts.get('ok', 0) + counts.get('skipped_existing', 0))
    expected = int(expected_count if expected_count is not None else len(manifest))
    return {
        'timestamp': utc_now_iso(),
        'expected_pdf_count': expected,
        'manifest_rows': int(len(manifest)),
        'downloaded_or_existing_count': ok_like,
        'missing_count': int(max(expected - ok_like, 0)),
        'invalid_pdf_count': int(counts.get('invalid_pdf', 0)),
        'zero_byte_count': int(counts.get('zero_byte', 0)),
        'exception_count': int(counts.get('exception', 0)),
        'http_error_count': int(counts.get('http_error', 0)),
        'success_rate': float(ok_like / expected) if expected else None,
        'status_counts': {str(k): int(v) for k, v in counts.items()},
        'problems_by_year': manifest[~manifest['download_status'].isin(['ok', 'skipped_existing'])].groupby('year').size().astype(int).to_dict() if not manifest.empty else {},
    }


def write_download_report(summary: dict[str, Any], manifest_path: Path = AUDIT_DIR / 'house_pdf_manifest.csv', report_path: Path = REPORTS_DIR / 'house_download_audit.md') -> Path:
    lines = [
        '# House PDF download audit', '',
        f"Generated at: `{summary.get('timestamp')}`", '',
        '## Completeness',
        f"- Expected PDFs: `{summary.get('expected_pdf_count')}`",
        f"- Manifest rows: `{summary.get('manifest_rows')}`",
        f"- Downloaded or existing: `{summary.get('downloaded_or_existing_count')}`",
        f"- Missing: `{summary.get('missing_count')}`",
        f"- Success rate: `{summary.get('success_rate')}`",
        '', '## Status counts',
    ]
    for status, count in summary.get('status_counts', {}).items():
        lines.append(f'- {status}: {count}')
    lines += ['', '## Problem files by year']
    for year, count in summary.get('problems_by_year', {}).items():
        lines.append(f'- {year}: {count}')
    lines += ['', f'Manifest: `{manifest_path}`']
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return report_path
