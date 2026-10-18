# Plan Comptable Minimum Normalisé (PCMN)

## Informations
Le plan comptable minimum normalisé belge (PCMN, *Minimumindeling van het algemeen rekeningenstelsel* ou MAR en néerlandais) au format **JSON**, en français, néerlandais, allemand et anglais.

Deux plans sont fournis :

- **Entreprises** — le PCMN des entreprises soumises à des obligations comptables autres que les associations et les fondations.
- **Associations et fondations** — le PCMN des associations et fondations (ASBL, AISBL, fondations).

Base légale : arrêté royal du 21 octobre 2018 portant exécution des articles III.82 à III.95 du Code de droit économique, tel que modifié (notamment pour le Code des sociétés et des associations). Les données proviennent des textes coordonnés publiés par la [Commission des Normes Comptables](https://www.cnc-cbn.be) (CNC).


## Liens
| Version | Plan | Source (CNC) | JSON | Structure |
| ------- | ---- | ------------ | ---- | --------- |
| 2019    | Entreprises | [FR · NL · DE](sources/2019/pcmn_entreprises_fr-nl-de.html) · [FR · EN](sources/2019/pcmn_entreprises_fr-en.html) · [en ligne](https://www.cnc-cbn.be/fr/node/2250) | [pcmn_entreprises_2019.json](versions/2019/pcmn_entreprises_2019.json) | [README](versions/2019/README.md) |
| 2019    | Associations et fondations | [FR · NL · DE](sources/2019/pcmn_asbl_fr-nl-de.html) · [FR · EN](sources/2019/pcmn_asbl_fr-en.html) · [en ligne](https://www.cnc-cbn.be/fr/node/2251) | [pcmn_asbl_2019.json](versions/2019/pcmn_asbl_2019.json) | [README](versions/2019/README.md) |

La version correspond à l'année du texte coordonné par la CNC (« Coordinated on 7 mai 2019 »), et non à l'année de téléchargement. Une nouvelle coordination donnera lieu à un nouveau dossier de version.

Les sources sont les pages « affichage multilingue » de la CNC, enregistrées le 18 octobre 2026. La CNC précise que ces textes coordonnés ne sont **pas officiels** : seul le texte publié au Moniteur belge fait foi. La traduction anglaise est celle de la CNC et n'a pas de valeur légale. Les textes légaux belges ne sont pas protégés par le droit d'auteur (art. XI.172, § 2 du Code de droit économique).


## Génération
Les fichiers JSON sont générés à partir des sources avec le script [`pcmn_html2json.py`](../scripts/pcmn_html2json.py) :

```bash
cd scripts
uv run pcmn_html2json.py
```


## Structure
```
PCMN/
├── README.md
├── sources/
│   └── 2019/
│       ├── pcmn_asbl_fr-en.html
│       ├── pcmn_asbl_fr-nl-de.html
│       ├── pcmn_entreprises_fr-en.html
│       └── pcmn_entreprises_fr-nl-de.html
└── versions/
    └── 2019/
        ├── pcmn_2019.schema.json
        ├── pcmn_asbl_2019.json
        ├── pcmn_entreprises_2019.json
        └── README.md
```
