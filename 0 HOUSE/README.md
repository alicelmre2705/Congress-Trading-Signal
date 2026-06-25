# 0 HOUSE — Transactions boursières des représentants (PTR)

Extraction et validation des *Periodic Transaction Reports* de la Chambre des représentants
américaine, à partir des PDF du House Clerk.

## 📁 Deux dossiers, deux périmètres

| Dossier | Périmètre | Statut | À lire |
|---|---|---|---|
| **[`2025_test/`](2025_test/)** | Q1 2025 seulement (le **pilote** fiable) | ✅ Fini, figé, validé | [2025_test/README.md](2025_test/README.md) |
| **[`toutes_annees/`](toutes_annees/)** | 2020 → 2026 (multi-années) | 🟡 En cours | [toutes_annees/README.md](toutes_annees/README.md) |

## 🧭 La règle de travail

**Le notebook est la seule source de vérité.** On travaille **période par période**, dans des
notebooks **autonomes** (tout le code vit dans le notebook, qui se lit de bout en bout). C'est le
modèle de `2025_test/`, notre version la plus fiable.

> Les anciens scripts `.py` sont archivés dans `toutes_annees/_moteurs_py/` (fallback CLI), **pas**
> la surface de travail.
