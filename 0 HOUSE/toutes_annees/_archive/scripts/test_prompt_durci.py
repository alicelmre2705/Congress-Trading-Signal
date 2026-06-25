#!/usr/bin/env python
"""A/B test du durcissement du prompt OCR sur un échantillon représentatif, AVANT de scaler.
Compare : (baseline = prompt actuel, DPI 200, déjà en cache) vs (DURCI = prompt renforcé + DPI 300).
Métriques : nb txns, dates hors fenêtre, et sortie brute pour vérif visuelle des noms.
"""
import base64, json, time, sys
import pymupdf, pandas as pd, anthropic
import house_ocr_multiyear as ocr   # client key, TXN_TOOL, AMOUNT_MAP
import house_multiyear as hm

# ───── prompt DURCI : ajoute (1) garde-fou date dans la fenêtre, (2) transcription fidèle, (3) 1 ligne = 1 txn
HARDENED = """\
Tu lis les pages scannées d'un formulaire PTR (Periodic Transaction Report — US House of
Representatives) déposé par {member_name}, DÉPOSÉ EN {filing_year}. Reporte TOUTES les transactions
en appelant l'outil record_transactions.

STRUCTURE :
  Colonne propriétaire (gauche) : DC=Dependent Child | JT=Joint | SP=Spouse | vide=Self
  FULL ASSET NAME : nom complet tel qu'écrit (jamais de ticker inventé)
  TYPE (cases) : Purchase | Sale | Partial Sale | Exchange
  DATE OF TRANSACTION et DATE NOTIFIED : MM/DD/YY (deux dates par ligne)
  AMOUNT (cases A–K) : A=$1,001–15k B=15k–50k C=50k–100k D=100k–250k E=250k–500k F=500k–1M
    G=1M–5M H=5M–25M I=25M–50M J=>50M K=SP/DC >1M

RÈGLES CRITIQUES :
  1. Orientation : la page peut être tournée 90°/180° — lis-la droite.
  2. LIGNE D'EXEMPLE pré-imprimée « Example: Mega Corp. Common Stock » → JAMAIS une transaction, ignore-la.
  3. « Nothing to report » → aucune transaction sur cette page. Ignore couvertures/certifications.
  4. CHAQUE ligne numérotée du tableau = UNE transaction. Ne fusionne PAS deux lignes ; ne scinde PAS
     un actif sur deux lignes. Reporte les lignes répétées à l'identique (ce sont de vrais lots).
  5. TRANSCRIPTION FIDÈLE : transcris le FULL ASSET NAME EXACTEMENT, caractère par caractère. Ne devine
     pas et ne remplace JAMAIS par une société ressemblante (ex. ne confonds pas « Becton » avec
     « Blackstone », « KKR » avec « KnR », « Rooney » avec « Rooster », « 1831 » avec « 1351 »). Si une
     partie est illisible, transcris seulement ce que tu lis, sans inventer.
  6. DATES — GARDE-FOU : ce dépôt date de {filing_year}. Les transactions sont récentes : leur année est
     quasiment toujours {filing_year} ou {prev_year}. Si tu crois lire une année très différente
     (autre décennie, ou postérieure au dépôt), c'est une ERREUR de lecture des chiffres manuscrits
     — relis le chiffre attentivement (un « 1 » se confond avec « 7 », « 5 » avec « 9 », « 0 » avec « 8 »).
     Convertis MM/DD/YY → YYYY-MM-DD. Lis transaction_date ET notification_date ligne par ligne.
  7. amount_code = UNIQUEMENT la lettre cochée (A–K). Si illisible, omets le champ.
"""

def call(client, images_b64, member, year, max_retries=6):
    content = [{"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": b}} for b in images_b64]
    content.append({"type": "text", "text": HARDENED.format(member_name=member, filing_year=year, prev_year=year-1)})
    for attempt in range(max_retries):
        try:
            r = client.messages.create(model=ocr.MODEL, max_tokens=ocr.MAX_TOKENS, tools=[ocr.TXN_TOOL],
                                       tool_choice={"type": "tool", "name": "record_transactions"},
                                       messages=[{"role": "user", "content": content}])
            for b in r.content:
                if getattr(b, "type", None) == "tool_use" and b.name == "record_transactions":
                    return b.input.get("transactions", [])
            return []
        except (anthropic.RateLimitError, anthropic.APIStatusError, anthropic.APIConnectionError) as e:
            if attempt < max_retries - 1:
                time.sleep(min(2 ** attempt, 30)); continue
            raise

def render(path, dpi):
    d = pymupdf.open(path)
    return [base64.b64encode(p.get_pixmap(dpi=dpi).tobytes("png")).decode() for p in d]

SAMPLE = [("2020", "8217692", "Francis Rooney"), ("2020", "8217113", "James Comer"),
          ("2020", "8217740", "Rohit Khanna"), ("2026", sys.argv[1] if len(sys.argv) > 1 else None, "?2026")]

client = anthropic.Anthropic(api_key=ocr.ANTHROPIC_API_KEY)
for year, doc, nm in SAMPLE:
    if not doc:
        continue
    path = hm.SEM1_PDF / year / f"{doc}.pdf"
    imgs = render(path, 300)
    batches = [imgs[i:i + ocr.MAX_IMG_PER_CALL] for i in range(0, len(imgs), ocr.MAX_IMG_PER_CALL)]
    txns = []
    for b in batches:
        txns += call(client, b, nm, int(year))
    df = pd.DataFrame(txns)
    # baseline (cache actuel)
    base = pd.read_csv(f"../data_v1/tables/{year}/06b_house_{year}_ocr_transactions.csv", dtype={"doc_id": str})
    base = base[base["doc_id"] == doc]
    # dates hors fenêtre
    def badyear(s):
        try:
            yy = int(str(s)[:4]); return not (int(year) - 1 <= yy <= int(year) + 1)
        except: return False
    nb_h = sum(badyear(t.get("transaction_date")) for t in txns)
    nb_b = base["transaction_date"].apply(badyear).sum() if len(base) else 0
    out = pd.DataFrame(txns).to_csv(f"/tmp/durci_{doc}.csv", index=False)
    print(f"\n===== {nm} {doc} ({year}) =====")
    print(f"  txns : DURCI {len(txns)} vs baseline {len(base)} | dates suspectes : DURCI {nb_h} vs baseline {nb_b}")
    if not df.empty:
        print(df[["asset_description", "transaction_type", "transaction_date", "amount_code"]].head(12).to_string(index=False))
    print(f"  (sortie complète DURCI -> /tmp/durci_{doc}.csv)")
