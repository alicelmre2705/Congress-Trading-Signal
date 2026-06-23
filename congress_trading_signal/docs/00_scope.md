# Scope J1–J4

Phase actuelle : construire uniquement la fondation data officielle House.

## Inclus

- Index House ZIP/XML 2013–2026.
- Filtre PTR : `FilingType = P`.
- URLs PDF via `year + DocID`.
- Téléchargement PDF relançable avec manifest.
- Audit qualité texte/PDF.
- Validation Quiver 2024 au niveau couverture déclarants/dates.

## Exclus

- Senate.
- OCR.
- Extraction LLM massive.
- Backtest.
- Commissions.
- Mapping GICS/ETF.
- Table finale transaction par transaction.

## Règle critique

`disclosure_date = FilingDate` de l’index XML House. La colonne `Notification Date` du PDF n’est pas la date stratégique de publication.
