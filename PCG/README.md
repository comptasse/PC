# Plan Comptable Général

## Informations
Le plan des comptes complet au format **JSON**.

Les données sont récupérées depuis le Plan Comptable Général (PCG) français émis chaque année par l'[Autorité des Normes Comptables](https://www.anc.gouv.fr) (ANC).


## Liens
| Version | Consolidée | Recueil  | Structure |
| ------- | -------------- | ----------- | --------- |
| 2026    | [.pdf](sources/2026/pcg_20260101.pdf) · [.html](sources/2026/pcg_20260101.html) · [.md](sources/2026/pcg_20260101.md) | [.pdf](sources/2026/recueil_20260101.pdf) · [.html](sources/2026/recueil_20260101.html) · [.md](sources/2026/recueil_20260101.md) | [README](versions/2026/README.md) |
| 2025    | [.pdf](sources/2025/pcg_20250101.pdf) · [.html](sources/2025/pcg_20250101.html) · [.md](sources/2025/pcg_20250101.md) | [.pdf](sources/2025/recueil_20250101.pdf) · [.html](sources/2025/recueil_20250101.html) · [.md](sources/2025/recueil_20250101.md) | [README](versions/2025/README.md) |
| 2024    | [.pdf](sources/2024/pcg_20240101.pdf) · [.html](sources/2024/pcg_20240101.html) · [.md](sources/2024/pcg_20240101.md) | [.pdf](sources/2024/recueil_20240101.pdf) · [.html](sources/2024/recueil_20240101.html) · [.md](sources/2024/recueil_20240101.md) | [README](versions/2024/README.md) |
| 2023    | [.pdf](sources/2023/pcg_20230101.pdf) · [.html](sources/2023/pcg_20230101.html) · [.md](sources/2023/pcg_20230101.md) | [.pdf](sources/2023/recueil_20230101.pdf) · [.html](sources/2023/recueil_20230101.html) · [.md](sources/2023/recueil_20230101.md) | [README](versions/2023/README.md) |

Les données sont également disponibles sur [data.gouv.fr](https://www.data.gouv.fr/datasets/plan-comptable-general).

Les documents en format `.pdf` proviennent de cette [source](https://www.anc.gouv.fr/normes-comptables-francaises/recueils-des-normes-comptables). Certains liens ne fonctionnent cependant plus. 
Nous avons contactés l'ANC à ce sujet, sans réponse pour le moment.


## Structure
Les différentes versions sont à retrouver dans le dossier [*versions*](versions), organisées par année. Chaque dossier contient les fichiers suivants ainsi qu'un `README.md` décrivant la structure des données :

- **`pcg_{année}.json`** — Fichier unique contenant le plan des comptes en formats hiérarchique et à plat, ainsi que les différences par rapport à la version précédente (absent pour la première version).
- **`pcg_{année}.schema.json`** — Schéma JSON ([json-schema.org](https://json-schema.org/)) décrivant la structure du fichier.

```
versions/
├── 2023/
│   ├── pcg_2023.json
│   ├── pcg_2023.schema.json
│   └── README.md
├── 2024/
│   ├── pcg_2024.json
│   ├── pcg_2024.schema.json
│   └── README.md
├── 2025/
│   ├── pcg_2025.json
│   ├── pcg_2025.schema.json
│   └── README.md
└── 2026/
    ├── pcg_2026.json
    ├── pcg_2026.schema.json
    └── README.md
```


## Projets similaires
- [PCG-GPL](https://github.com/SVGAnimate/PCG-GPL) — Plan Comptable Général sous GPL, avec scraping des données depuis les formats PDF et SVG (PHP).
