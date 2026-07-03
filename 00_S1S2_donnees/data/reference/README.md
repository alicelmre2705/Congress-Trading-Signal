# Référentiels transverses (House + Sénat)

## `ticker_renames.csv` — renommages, rachats, faillites, recyclages de symboles

Créé lors de l'audit données du 2026-07-03 (finding REN-01 : 18,9 % des lignes du backtest Quiver
n'avaient aucun prix utilisable, faute de référentiel de renommages — FB/Meta, PCLN/BKNG, ATVI…).

| Colonne | Sens |
|---|---|
| `ticker_ancien` | symbole tel qu'il apparaît dans les déclarations (PTR/Quiver) |
| `ticker_nouveau` | symbole ACTUEL du même émetteur (vide si plus coté) |
| `type` | `renommage` (même société), `fusion_echange` (actionnaires payés en titres de l'absorbeur), `rachat_delisting` (sortie de cote — position à clôturer au dernier prix/à la date du deal), `faillite_delisting` (perte quasi totale — NE PAS exclure du backtest, c'est le biais de survie), `recyclage_attention` (le même symbole a désigné DEUX émetteurs différents — joindre les prix par période, jamais en aveugle) |
| `date_effet` | mois de l'événement (précision au mois, suffisant pour le join backtest) |
| `historique_valide` | `complet` = le successeur porte tout l'historique du listing (renommage pur ou jambe survivante de la fusion — vérifié : META remonte à 2012, RTX à 1962) ; `post_fusion_seulement` = jambe ABSORBÉE (RTN, STI, MYL, LLL, DISCK) : le prix du successeur avant la fusion est celui d'une AUTRE société — ne jamais l'utiliser pré-fusion |

Usage prévu (chaîne de nettoyage canonique) : le champ `ticker` reste FIDÈLE à la déclaration ;
le champ `ticker_yahoo` (join prix) applique `renommage`/`fusion_echange` ; les `*_delisting`
alimentent `is_delisted` (traitement explicite dans le backtest au lieu d'une disparition silencieuse) ;
les `recyclage_attention` exigent un contrôle de recouvrement de dates avant tout join prix.

Sources : événements de marché publics (dates vérifiées au mois près). Toute entrée douteuse a été
OMISE plutôt que devinée — compléter au fil des besoins, jamais en aveugle.
