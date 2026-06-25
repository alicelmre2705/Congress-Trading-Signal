# Congress-Trading-Signal

**Audit Congress Trading Signal — Couverture des PTR House (Jours 1–2)**

## But

Construire la *matrice de couverture* côté Chambre des représentants : combien de
**PTR** (`FilingType = "P"`) sont déposés **par année**, quels **autres codes** de dépôt
existent, et la **liste des PTR** à télécharger ensuite — le tout **sans télécharger un seul PDF**,
uniquement à partir des index XML annuels publiés par le Clerk.

## Source

Domaine public, pas de *terms gate* :  
`https://disclosures-clerk.house.gov/public_disc/financial-pdfs/<ANNÉE>FD.zip`

Chaque ZIP contient `<ANNÉE>FD.xml`. Schéma d'un enregistrement :

```xml
<Member>
  <Prefix>Hon.</Prefix><Last>Aderholt</Last><First>Robert</First><Suffix/>
  <FilingType>P</FilingType><StateDst>AL04</StateDst><Year>2025</Year>
  <FilingDate>9/10/2025</FilingDate><DocID>20032062</DocID>
</Member>
```

## Mode d'emploi

Exécute les cellules dans l'ordre (*Run All*). Il faut un accès réseau à `house.gov`. 
Si une année échoue, elle est journalisée et ignorée (le reste continue).

Pour re-agréger sans réseau à partir de ZIP déjà téléchargés, mets `OFFLINE = True`.

## Outputs

Dans `./out_house_audit/` :
- `coverage_by_year.csv` — **Matrice de couverture PTR par année** (livrable principal)
- `filing_type_legend.csv` — Énumération de tous les codes de dépôt rencontrés
- `manifest.csv` — Rapport de qualité par année (succès/échec, nombre de PTR)
- `ptr_index_<ANNÉE>.csv` (2013–2026) — Liste exacte des PTR à télécharger par année (pont vers Jours 3–4)
- `raw_zips/` — Cache des ZIP téléchargées (évite les re-téléchargements)

## Workflow détaillé

1. **Configuration** — Paramètres, dossiers, logging
2. **Téléchargement** — Récupère les ZIP annuels, idempotent + tolérant aux erreurs
3. **Parsing XML** — Extrait les enregistrements `<Member>` sans charger tout en mémoire
4. **Exécution** — Boucle sur chaque année, accumule les données
5. **Matrice de couverture** — Tableau croisé `année × FilingType`
6. **Légende des types** — Tous les codes de dépôt avec fréquences
7. **Visualisation** — Graphique en barres des PTR par année
8. **Index des PTR** — Export par année pour téléchargement ultérieur
9. **Contrôle de complétude** — Détecte années problématiques

## Contrôle de qualité

À interpréter une fois les vrais chiffres obtenus :

1. **En quelle année `P` devient-il dense ?**  
   Ça teste l'hypothèse « 2008 → » contre la réalité post-STOCK-Act.  
   (Le PTR n'existe qu'après 2012 ; attends-toi à du creux sur 2013.)

2. **Quels codes autres que `P` ressortent ?**  
   Amendements, originaux annuels, candidats…  
   → base de la future règle d'amendements / doublons.

3. **Une année a-t-elle échoué ou affiche 0 PTR ?**  
   Vérifie le manifeste (cellule 8) → trou à documenter, pas à masquer.

## Dépendances

```
pandas
matplotlib (optionnel, pour le graphique)
```

Les autres imports (`io`, `time`, `zipfile`, `logging`, `pathlib`, `urllib`, `xml.etree`) sont built-in Python.

---

*Jours 1–2 : Audit de couverture — Index XML uniquement.*  
*Jours 3–4 : Téléchargement des PTR-PDFs eux-mêmes (à partir des index).*
