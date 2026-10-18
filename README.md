# Plans Comptables

## Informations
Des plans de comptes officiels au format **JSON**, organisés par plan comptable.

| Plan | Pays | Autorité | Dossier |
| ---- | ---- | -------- | ------- |
| Plan Comptable Général (PCG) | 🇫🇷 France | [Autorité des Normes Comptables](https://www.anc.gouv.fr) (ANC) | [PCG](PCG/README.md) |
| Plan Comptable Minimum Normalisé (PCMN) | 🇧🇪 Belgique | [Commission des Normes Comptables](https://www.cnc-cbn.be) (CNC) | [PCMN](PCMN/README.md) |


## Structure
Chaque plan comptable dispose de son propre dossier, contenant :

- **`README.md`** — Présentation du plan, liens vers les sources et les versions.
- **`sources/`** — Les documents officiels d'origine, organisés par version.
- **`versions/`** — Les fichiers JSON et leurs schémas ([json-schema.org](https://json-schema.org/)), organisés par version. Chaque version contient un `README.md` décrivant la structure des données.

```
PCG/
├── README.md
├── sources/
└── versions/
PCMN/
├── README.md
├── sources/
└── versions/
scripts/
```

Les formats JSON suivent une même logique (`flat`, `nested`), mais chaque plan a ses particularités, décrites dans le `README.md` de chaque version. Par exemple, les numéros de compte sont des entiers dans le PCG et des textes dans le PCMN (pour distinguer `0`, `00` et `000`).

Le dossier [*scripts*](scripts) contient les outils de conversion des sources.


## Projets similaires
- [PCG-GPL](https://github.com/SVGAnimate/PCG-GPL) — Plan Comptable Général sous GPL, avec scraping des données depuis les formats PDF et SVG (PHP).
