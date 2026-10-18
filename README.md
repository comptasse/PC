# Plans Comptables

## Informations
Des plans de comptes officiels au format **JSON**, organisés par plan comptable.

| Plan | Pays | Autorité | Dossier |
| ---- | ---- | -------- | ------- |
| Plan Comptable Général (PCG) | 🇫🇷 France | [Autorité des Normes Comptables](https://www.anc.gouv.fr) (ANC) | [PCG](PCG/README.md) |


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
scripts/
```

Le dossier [*scripts*](scripts) contient les outils de conversion des sources.


## Projets similaires
- [PCG-GPL](https://github.com/SVGAnimate/PCG-GPL) — Plan Comptable Général sous GPL, avec scraping des données depuis les formats PDF et SVG (PHP).
