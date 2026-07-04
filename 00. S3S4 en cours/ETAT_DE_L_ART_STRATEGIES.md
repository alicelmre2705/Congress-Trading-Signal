# État de l'art — copier les trades du Congrès : ce qui est prouvé, ce qui est mort, ce qui reste à tester

*66 fiches de lecture (59 vérifiées à la source primaire) : 20+ papiers académiques, stratégies
publiques (QuantConnect/GitHub/Kaggle), produits réels (NANC/GOP, Autopilot, Quiver), et nos 8 essais
internes. Chaque chiffre ci-dessous vient du document primaire. Rédigé le 2026-07-04 pour décider de la
structure du notebook de recherche.*

---

## 1. Le paysage en un clin d'œil

- **Le mythe fondateur est mort** : le « Sénat +12 %/an » (Ziobrowski 2004) est mesuré à la date de
  TRANSACTION (divulguée 5-17 mois plus tard à l'époque — jamais copiable), porté par la pondération
  taille et 4 sénateurs, et disparaît dans son propre échantillon dès 1997. La version House (2011) :
  les titres VENDUS battent aussi le marché de ~5 %/an → signal directionnel nul (Eggers & Hainmueller).
- **Le consensus post-STOCK Act est un null** : Belmont et al. 2022 (JPubE, 2012-2020) — aucune
  surperformance, même chez les sénateurs accusés, même aux 95e/99e percentiles ; achats House −26 bps
  à 6 mois vs benchmark industrie-taille. Karadas : son propre alpha s'éteint après avril 2012.
  Chen & Sacerdote 2026 : les élus achètent APRÈS le pic d'attention retail. ML (arXiv 2602.05514) :
  AUROC ≈ 0,52 pour prédire les trades gagnants. **Nos essais (03/04/05, RAMIFY_V1) répliquent ce
  consensus — « pas d'alpha » n'était pas une erreur de pipeline.**
- **MAIS trois poches documentées survivent — et deux sont à la DISCLOSURE (copiables)** :
  1. **Le drift post-publication** (l'événement que notre 05 ne pouvait pas voir) : Lazzaretto 2024 —
     ~90 bps le mois suivant la disclosure, ABSENT après la transaction ; effet temporaire (réversion) →
     horizons courts. Abdurakhmonov 2023 (SMJ) : +12-21 bps en 1-3 jours au dépôt (achats seulement,
     rien sur les ventes), **~+50 bps quand le membre a juridiction de comité sur l'industrie**.
     Pyun 2025 : l'alpha post-disclosure d'un portefeuille value-weighted d'achats est positif —
     plus fort sur **large caps, House, post-2020** (notre terrain exact).
  2. **Les 12 leaders de parti** (Wei & Zhou, NBER w34524, 1995-2021) : Speaker/floor leaders/whips/
     conference chairs — PAS les chairs de commissions. Achats +47 pp vs pairs sur 12 mois ; et surtout
     **l'effet persiste aux dates de disclosure : ≈ +10,5 %/an brut, equal-weight** — le seul alpha
     « copiable publiquement » revendiqué par un papier sérieux. Footnote 31 : aucun produit ne le suit.
     ⚠ Notre SUPP_A l'infirmait sur l'ancienne donnée (effet porté par 1 membre) — mais avec une autre
     définition du « leader » : re-test propre obligatoire (liste CRS point-in-time).
  3. **Les trades × jalons législatifs** (Li et al. 2025, JBE — fenêtre 2014-2021 = la nôtre) : trades
     dans une industrie affectée 1-30 j avant un jalon de bill → +3-5 % sur 12 mois ; Cohen-Diether-
     Malloy 2012 : les VOTES prédisent +11-15 %/an (hors PTR — piste d'élargissement).
- **Contre-intuitions établies** : le co-achat par plusieurs membres DÉGRADE les rendements
  (« Congressional Herding », FM 2026) ; les gros montants font PIRE (Belmont : achats >250 k$ −3,9 % à
  6 mois) ; le benchmark peut créer l'alpha (Hanousek 2023 : +4,9 % market-adjusted → −0,28 %
  industry-size sur les MÊMES trades).
- **La littérature 13F dit que le délai n'est pas le problème** : copier des dépôts publics retardés
  coûte 13-42 bps/6 mois (Frank et al. 2004) et peut battre le marché si la source a un horizon long
  (Barclays QIS : +3,8 %/an net de délai) ; la conviction par TAILLE de position survit des années à la
  publication (« Best Ideas » : alpha 6F 37 bps/mois, t=3,3). Le problème du Congrès n'est pas le délai
  de 45 j — c'est le talent moyen nul de la source.
- **Les produits réels encadrent le S&P** : NANC +23,6 %/an depuis 2023 (= +2,7 pp vs SPY mais −3,8 pp
  vs QQQ : beta tech, turnover 10 %) ; GOP (ex-KRUZ) −6,2 pp/an vs SPY, mêmes règles → pas d'« alpha du
  Congrès » générique. Autopilot (460 M$+) ne publie pas de perf vérifiable. Quiver « 37 % CAGR » =
  fenêtre choisie + zéro coûts. Unusual Whales 2025 : 32 % seulement des membres battent le marché.
- **Risque existentiel produit** : le HONEST Act (ban du trading par les élus) a passé la commission
  sénatoriale en 2025 — première fois ; les prospectus NANC/GOP disclosent le risque de liquidation.

## 2. Ce que le brief Ramify impose (0.Notion_Ramify.pdf, relu)

- **Trade-based, chaque trade = une observation** : entrée à la `disclosure_date` d'un « Purchase » d'un
  membre suivi ; sortie à la `disclosure_date` de la « Sale » du même membre sur ce ticker, sinon
  **sortie forcée +12 mois**.
- **Sélection annuelle** de K ∈ [4, 10] membres, éligibilité ≥ 10 trades, positions des sortants
  laissées courir ; critère = **Sharpe de la série de trades** ; « l'alpha vs SPX est ce qui compte » ;
  filtre recommandé : ≥ ½ des K dans Finance/Defense/Intelligence.
- **V1 actions directes** (valider le signal + track records) → **V2 ETF sectoriels** (GICS→SPDR).
- Cadres cités : Mauboussin (skill vs luck), Grinold-Kahn (Fundamental Law), Sutton & Barto ch. 2
  (confiance dynamique), De Prado (pièges du backtest).

## 3. Nos huit essais — ce qu'on garde, ce qu'on ne refait pas

| Essai (ancienne donnée Quiver) | Résultat | Leçon |
|---|---|---|
| 03 — event-study + 11 critères × 4 K walk-forward + GRS | aucun critère significatif, DSR 0,94 | LA boîte à outils maison à réutiliser : t clusterisé par membre, walk-forward à trades clôturés, benchmark style-matched, Brinson |
| 03 §5bis — portefeuille complet au plafond `traded` | allocation +1,98 %/an, sélection ≈ 0 | même l'info parfaite ne montre pas de talent de sélection |
| 04 — copier tout (A) vs top-10 (B) | B : +16,2 %/an mais Sharpe 0,82 < SPY 0,86 | le surplus de rendement = du risque, pas du talent ; format « 3 chiffres, 1 verdict » à garder |
| 05 — portefeuille par membre time-weighted, IR, top-K | top-4 +4,0 %/an, t=1,32 | mesure gonflée (multiplicité, autocorr., traded) ET bruitée (17 % de trades sans prix, sizing borne-basse binaire) ; répond à une autre question que le brief ; **ne voit PAS le drift court post-disclosure** |
| RAMIFY_V1 (la stratégie du brief, ancienne donnée) | meilleur K=8 : α +4,0 %/an t=0,88 ; aucun K ne bat le Sharpe SPY ; pas de persistance | à RE-TESTER sur la table canonique — c'est le cœur du livrable |
| RAMIFY_V2 (ETF) | dilution −4,5 à −5,8 pp d'alpha à chaque K | le peu de signal est firm-specific ; V2 = décision produit, pas alpha |
| SUPP_B (chasse au signal, 6 angles) | seul survivant : breadth IC ≈ 0,02 | imposer partout contrôle secteur×année + clustering membre ; borne Grinold-Kahn : α > 3-4 %/an = suspect par construction |
| SUPP_A/C (9 variantes + approfondissement) | rien net de coûts ; « leadership » porté par 1 membre | pondération size = piège méga-trades ; à re-tester avec la définition Wei-Zhou du leadership |

**Et la donnée a changé depuis** : table canonique 134 464 × 36 (vs 108 916) — pré-2020 +13,5 %, ventes
pré-2018 récupérées (parité P/S restaurée), `amount_midpoint` réel (fini le sizing binaire),
`ticker_yahoo`+renommages (fini les 17-19 % de trades sans prix), parti/commissions point-in-time,
flags délistés/tardifs/lots. **Tout résultat ancien est à re-mesurer.**

## 4. Règles d'or extraites (à respecter dans le notebook, même en v1 simple)

1. **Toujours achats ET ventes séparés + le spread** (le test qui a tué Ziobrowski-House).
2. **Toujours ≥ 2 benchmarks** : SPY + apparié style/secteur (Hanousek : le signe bascule sinon).
3. **Entrée à `disclosure_date`+1** partout ; `transaction_date` = uniquement pour le plafond théorique.
4. **Compter les essais** (K, critères, variantes) et le dire — même sans machinerie DSR en v1.
5. **Horizons courts ET longs** : le drift post-disclosure est court et réverse (Lazzaretto) — un
   backtest 12 mois peut le rater ; le brief impose 12 mois → tester les deux.
6. **Coûts dès la v1** (20 bps aller simple ; la réplication trimestrielle 13F coûte ~0,6 %/an).
7. **Capacité** : un signal en % peut être infaisable en $ (Oenschläger) — au moins un chiffrage ADV.
8. Le sizing par `amount_midpoint` (pas equal-weight seul) : chez Ziobrowski c'est LA charnière.

## 5. Trois structures possibles pour le notebook (à choisir ensemble)

**A — « Le brief, simplement »** (~35 cellules) : données → la stratégie exacte du brief (entrée/sortie
trade-based) → track records par membre (Sharpe des trades) → sélection top-K walk-forward → V1 → V2
ETF → verdict. La littérature n'apparaît qu'en cadrage. *Le plus court ; risque : passe à côté de la
question « drift court » et on conclut encore « pas d'alpha » sans avoir testé la vraie nouveauté.*

**B — « La question avant la stratégie »** (~55 cellules, recommandée) :
1. Cadrage (1 cellule) : ce que dit la littérature, ce que le brief demande.
2. **L'événement disclosure** : que se passe-t-il dans les 5 j / 1 m / 3 m / 6 m / 12 m après une
   publication d'achat ? (event-study simple, achats vs ventes, House vs Sénat — répond à la question
   d'Alice « traded vs filed » ET teste Lazzaretto/Pyun sur nos données).
3. **La stratégie du brief** (V1 exacte, trade-based, top-K Sharpe walk-forward, coûts).
4. **Deux variantes ciblées** issues de l'état de l'art : (a) les 12 leaders de parti à la disclosure
   (Wei-Zhou — liste CRS point-in-time) ; (b) horizon court (sortie 1 mois au lieu de 12).
5. V2 ETF sectoriels (dilution mesurée).
6. Verdict situé dans la littérature.

**C — « Recherche complète »** (~85 cellules) : B + cartographie conditionnelle (comité×industrie —
le +50 bps d'Abdurakhmonov, trades×jalons de bills via congress.gov, conviction « Best Ideas » par
midpoint, herding négatif, capacité ADV, split pré/post-2021). *Exhaustif mais long — peut être la v2
si B ne suffit pas.*
