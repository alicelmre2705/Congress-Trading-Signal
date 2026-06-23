"""PDF text quality audit and lightweight smoke extraction."""
from __future__ import annotations

import random
import re
from pathlib import Path
from typing import Any

import pandas as pd
from pypdf import PdfReader
from tqdm.auto import tqdm

from .utils import AUDIT_DIR, REPORTS_DIR, utc_now_iso

QUALITY_COLUMNS = [
    'year', 'doc_id', 'local_path', 'n_pages', 'text_chars_first_pages',
    'contains_periodic_transaction_report', 'contains_filer_information',
    'contains_transactions', 'contains_amount', 'text_extractable_flag',
    'quality_status', 'error_message'
]

SMOKE_COLUMNS = [
    'doc_id', 'year', 'declarant_name_raw', 'state_dst', 'text_chars',
    'tickers_seen_raw_regex', 'transaction_dates_seen_regex',
    'amount_ranges_seen_regex', 'notes'
]

TICKER_RE = re.compile(r'\(([A-Z][A-Z0-9\.\-/]{0,9})\)')
DATE_RE = re.compile(r'\b\d{1,2}/\d{1,2}/\d{4}\b')
AMOUNT_RE = re.compile(r'\$[0-9,]+\s*(?:-|–|—|to)\s*\$[0-9,]+|>\s*\$[0-9,]+|\$[0-9,]+\s*\+')


def extract_text_sample(pdf_path: Path, max_pages: int = 2) -> str:
    reader = PdfReader(str(pdf_path))
    texts = []
    for page in reader.pages[:max_pages]:
        texts.append(page.extract_text() or '')
    return '\n'.join(texts)


def compute_text_quality(row: pd.Series | dict[str, Any], max_pages: int = 2) -> dict[str, Any]:
    local_path = Path(str(row.get('local_path', '')))
    payload = {
        'year': row.get('year'),
        'doc_id': str(row.get('doc_id', '')).strip(),
        'local_path': str(local_path),
        'n_pages': row.get('n_pages'),
        'text_chars_first_pages': 0,
        'contains_periodic_transaction_report': False,
        'contains_filer_information': False,
        'contains_transactions': False,
        'contains_amount': False,
        'text_extractable_flag': False,
        'quality_status': 'missing_file',
        'error_message': '',
    }
    if not local_path.exists():
        return payload
    try:
        text = extract_text_sample(local_path, max_pages=max_pages)
        lower = text.lower()
        payload['text_chars_first_pages'] = len(text)
        payload['contains_periodic_transaction_report'] = 'periodic transaction report' in lower
        payload['contains_filer_information'] = 'filer information' in lower
        payload['contains_transactions'] = 'transactions' in lower
        payload['contains_amount'] = 'amount' in lower
        payload['text_extractable_flag'] = len(text) > 50
        if len(text) > 500:
            payload['quality_status'] = 'ok_text'
        elif len(text) > 50:
            payload['quality_status'] = 'weak_text'
        else:
            payload['quality_status'] = 'no_text'
    except Exception as exc:
        payload['quality_status'] = 'unreadable_pdf'
        payload['error_message'] = repr(exc)
    return payload


def run_pdf_quality_audit(manifest_df: pd.DataFrame, output_path: Path = AUDIT_DIR / 'house_pdf_text_quality.csv', max_files: int | None = None) -> pd.DataFrame:
    work = manifest_df.head(max_files).copy() if max_files else manifest_df.copy()
    rows = [compute_text_quality(row) for _, row in tqdm(work.iterrows(), total=len(work), desc='PDF quality')]
    quality = pd.DataFrame(rows, columns=QUALITY_COLUMNS)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    quality.to_csv(output_path, index=False)
    return quality


def summarize_pdf_quality(quality: pd.DataFrame) -> dict[str, Any]:
    counts = quality['quality_status'].value_counts(dropna=False).to_dict() if not quality.empty else {}
    total = int(len(quality))
    ok = int(counts.get('ok_text', 0))
    return {
        'timestamp': utc_now_iso(),
        'n_pdf_audited': total,
        'status_counts': {str(k): int(v) for k, v in counts.items()},
        'ok_text_rate': float(ok / total) if total else None,
        'weak_text_rate': float(counts.get('weak_text', 0) / total) if total else None,
        'no_text_rate': float(counts.get('no_text', 0) / total) if total else None,
        'unreadable_rate': float(counts.get('unreadable_pdf', 0) / total) if total else None,
        'n_pages_distribution': quality['n_pages'].describe().to_dict() if 'n_pages' in quality and not quality.empty else {},
    }


def choose_smoke_sample(manifest_df: pd.DataFrame, quality_df: pd.DataFrame, random_state: int = 42) -> pd.DataFrame:
    ok_manifest = manifest_df[manifest_df['download_status'].isin(['ok', 'skipped_existing'])].copy()
    if ok_manifest.empty:
        return ok_manifest
    sample_indices = set()
    sample_indices.update(ok_manifest.sample(min(20, len(ok_manifest)), random_state=random_state).index.tolist())
    recent = ok_manifest.sort_values('year', ascending=False).head(10)
    ancient = ok_manifest.sort_values('year', ascending=True).head(10)
    long_docs = ok_manifest.sort_values('n_pages', ascending=False).head(10)
    sample_indices.update(recent.index.tolist())
    sample_indices.update(ancient.index.tolist())
    sample_indices.update(long_docs.index.tolist())
    if not quality_df.empty:
        bad_ids = quality_df[~quality_df['quality_status'].eq('ok_text')]['doc_id'].head(5).astype(str).tolist()
        bad = ok_manifest[ok_manifest['doc_id'].astype(str).isin(bad_ids)]
        sample_indices.update(bad.index.tolist())
    return ok_manifest.loc[sorted(sample_indices)].copy()


def regex_smoke_extract(row: pd.Series, max_pages: int = 2) -> dict[str, Any]:
    path = Path(str(row['local_path']))
    notes = []
    text = ''
    try:
        text = extract_text_sample(path, max_pages=max_pages)
    except Exception as exc:
        notes.append(f'extract_error={repr(exc)}')
    return {
        'doc_id': str(row.get('doc_id', '')).strip(),
        'year': row.get('year'),
        'declarant_name_raw': row.get('declarant_name_raw', ''),
        'state_dst': row.get('state_dst', ''),
        'text_chars': len(text),
        'tickers_seen_raw_regex': sorted(set(TICKER_RE.findall(text))),
        'transaction_dates_seen_regex': sorted(set(DATE_RE.findall(text))),
        'amount_ranges_seen_regex': sorted(set(AMOUNT_RE.findall(text))),
        'notes': '; '.join(notes),
    }


def run_smoke_test(sample_df: pd.DataFrame, output_path: Path = AUDIT_DIR / 'house_sample_extraction_smoke_test.csv') -> pd.DataFrame:
    rows = [regex_smoke_extract(row) for _, row in tqdm(sample_df.iterrows(), total=len(sample_df), desc='Smoke regex')]
    smoke = pd.DataFrame(rows, columns=SMOKE_COLUMNS)
    for col in ['tickers_seen_raw_regex', 'transaction_dates_seen_regex', 'amount_ranges_seen_regex']:
        smoke[col] = smoke[col].apply(lambda xs: '|'.join(xs) if isinstance(xs, list) else xs)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    smoke.to_csv(output_path, index=False)
    return smoke


def append_quality_report(summary: dict[str, Any], report_path: Path = REPORTS_DIR / 'house_download_audit.md') -> Path:
    lines = [
        '', '---', '', '# PDF text quality addendum', '',
        f"Generated at: `{summary.get('timestamp')}`", '',
        f"- PDFs audited: `{summary.get('n_pdf_audited')}`",
        f"- ok_text rate: `{summary.get('ok_text_rate')}`",
        f"- weak_text rate: `{summary.get('weak_text_rate')}`",
        f"- no_text rate: `{summary.get('no_text_rate')}`",
        f"- unreadable rate: `{summary.get('unreadable_rate')}`",
        '', '## Status counts',
    ]
    for status, count in summary.get('status_counts', {}).items():
        lines.append(f'- {status}: {count}')
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open('a', encoding='utf-8') as handle:
        handle.write('\n'.join(lines) + '\n')
    return report_path
