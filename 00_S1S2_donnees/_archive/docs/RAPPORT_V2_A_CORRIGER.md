# Rapport V2 — changements à faire (À APPLIQUER À LA FIN)

> On **n'édite pas** le rapport tout de suite. On accumule ici, on applique **tout en une fois à la fin**.
> Deux catégories de *changements au rapport* :
> - **Cat. 1 — FAUX / incohérent** : à corriger.
> - **Cat. 2 — pas assez détaillé** : à compléter.
>
> Les notions que tu veux juste **comprendre** (sans changer le rapport) sont dans
> [`RAPPORT_V2_EXPLICATIONS.md`](RAPPORT_V2_EXPLICATIONS.md) (cat. 3). Tu peux promouvoir n'importe quel
> point de la cat. 3 vers ici si tu décides qu'il manque au rapport.

---

## Catégorie 1 — FAUX / incohérent (à corriger)

- [ ] **§3.2 (schéma)** — La boîte 2 (Chambre OCR) dit « scans », la boîte 4 (Sénat OCR) dit
  « PTR papier ». C'est **la même chose** (un PTR papier scanné, sans couche texte → OCR). Seul le
  format d'image diffère (PDF côté Chambre, `.gif` côté Sénat), ce qui ne justifie pas deux mots.
  **Action** : même libellé des deux côtés, p. ex. « PTR papier scanné → Vision ».

## Catégorie 2 — pas assez détaillé (à compléter dans le rapport)

- [ ] **§4.1 — `bioguide_id` jamais défini.** Le terme est utilisé partout (et dans tout le rapport)
  mais sa définition a disparu quand on a retiré les encadrés. **Action** : remettre une définition
  d'une ligne, p. ex. « identifiant officiel unique d'un parlementaire (`P000197` = Pelosi) ».

- [ ] **§2 — acquisition Chambre mal détaillée.** Décrire le vrai parcours : le *Clerk* publie un
  **ZIP par année** → qui contient l'**index XML** `{an}FD.xml` (une ligne par dépôt : `DocID`,
  nom, `StateDst`, `FilingType`, `FilingDate`) → on filtre `FilingType=P` → chaque `DocID` donne une
  **URL de PDF** (`disclosures-clerk.house.gov/.../ptr-pdfs/{an}/{DocID}.pdf`) → on télécharge le PDF
  → **c'est en l'ouvrant** qu'on décide lisible vs scanné (`bool(text.strip())`). *Réf :*
  `house/digital.py:load_ptr_index`, `resolve_pdf_path`, `build_manifest`.

- [ ] **§2 — acquisition Sénat mal détaillée.** Décrire : portail **eFD** (`efdsearch.senate.gov`) →
  on accepte l'accord (CSRF) → une **recherche** (`report_types=[11]`) renvoie une **liste de
  rapports** → chaque entrée pointe vers `/view/**ptr**/…` (électronique, **HTML**) ou
  `/view/**paper**/…` (papier **scanné**, servi en images **`.gif`** par `efd-media-public.senate.gov`).
  L'électronique est lu par `pd.read_html`, le papier part à l'OCR. *Réf :* `senate/digital.py:
  accept_agreement`, `fetch_ptr_list` (champ `kind` = `ptr`/`paper`), `fetch_report`.

- [ ] **§2/§3.3 — rendre explicite « pourquoi un `04_` côté Chambre et pas côté Sénat ».** Côté
  Chambre, le tri lisible/scanné est un **verdict calculé** (il faut ouvrir chaque PDF) → écrit dans
  `04_download_manifest.csv`. Côté Sénat, le tri est **donné d'avance** par la liste eFD (le `kind`
  `ptr`/`paper`) → pas besoin de manifeste `04_`.

- [ ] `[optionnel]` **§2 / galerie — « première vision du site ».** Éventuellement ajouter une capture
  de l'**index/liste** côté acquisition (l'index XML Chambre, et la **page de résultats** eFD du Sénat)
  pour montrer ce qu'on obtient *avant* d'ouvrir un dépôt. (À fournir par Alice ou à rendre depuis le
  dépôt.)

- [ ] **§4.3 — clé naturelle / `occurrence_index` utilisées avant d'être expliquées.** Le « pourquoi »
  (déduplication non destructrice) n'arrive qu'en §4.8. **Action** : en §4.3, ajouter une phrase de
  « pourquoi » courte **ou** un renvoi explicite vers §4.8 (« voir la déduplication, §4.8 »).

- [ ] `[optionnel]` **§4.3 — gloser « taux de parsing ».** Préciser en une incise : « part des PDF
  lisibles dont on a réussi à extraire les transactions (le reste → `05_parse_failures`) ».

- [ ] **§4.6 — dire que l'OCR Sénat est le *même mécanisme* qu'en §4.5.** Actuellement §4.6 dit juste
  « lit les `.gif` par Vision → 06b ». Ajouter : **même principe Vision** (tool\_use forcé
  `record_transactions`, cache `prompt_sha`) qu'en §4.5, via `senate/ocr_engine.py`, **mais sans
  deskew** (les `.gif` Sénat sont droits ; le deskew était propre aux scans *couchés* de la Chambre).
  → lève l'ambiguïté « est-ce pareil que House, et c'est pour ça qu'on ne le redit pas ? ».

- [ ] **Définir « couverture » (ticker / secteur) une fois.** Terme récurrent jamais défini :
  **couverture = taux de remplissage = part des lignes pour lesquelles le champ est renseigné**
  (ex. ticker 85,3 % = 85,3 % des lignes ont un symbole). Rappeler la nuance : les actifs non cotés
  n'ont **légitimement** pas de ticker → la couverture ne peut pas être 100 % par nature.

- [ ] `[optionnel]` **§4.7 — expliciter ce qu'est la « passe LLM » (ticker).** Une incise : « un appel
  à Claude qui, à partir du **nom de l'actif**, propose le symbole boursier, filtré aux actions
  (`is_equity`) ; caché et versionné ».

- [ ] `[optionnel]` **§4.7 — gloser ETF / GICS / SPDR en une ligne (1re utilisation).** Si on veut le
  rapport lisible par un non-financier : « un **secteur GICS** = l'un des 11 grands domaines (Tech,
  Santé…) ; un **ETF sectoriel** = un fonds qui suit tout un secteur ; les **SPDR Select Sector** = la
  famille avec 1 ETF par secteur (XLK=Tech, XLE=Énergie…) ». *(Sinon, OK tel quel pour un lecteur Ramify.)*

<!-- La revue continue ; on ajoutera les points suivants au fil des sections. -->
