# Scripts

Outils pour traiter les fichiers sources des plans comptables. Les scripts `pdf2html.py` et `html2md.py` travaillent sur les sources du PCG (`PCG/sources`).

## Prérequis

- [uv](https://docs.astral.sh/uv/) (gestionnaire de paquets Python)

## Installation

```bash
cd scripts
uv sync
```

## Utilisation

### `pdf2html.py` — Conversion PDF vers HTML

Convertit les PDF sources en HTML à l'aide de [PyMuPDF](https://pymupdf.readthedocs.io/). La mise en forme (polices, couleurs), les images et la structure du document sont préservées.

```bash
# Convertir les PDF d'une année spécifique
uv run pdf2html.py --year 2026

# Convertir tous les PDF
uv run pdf2html.py --all

# Spécifier un répertoire de sortie
uv run pdf2html.py --all --output-dir out
```

Par défaut, les fichiers HTML sont créés dans le même répertoire que les PDF sources.

### `html2md.py` — Conversion HTML vers Markdown

Convertit les fichiers HTML (générés par `pdf2html.py`) en Markdown structuré. Le parseur analyse le positionnement CSS absolu et les styles inline pour reconstruire la structure du document :

- **Titres** détectés à partir de la taille des polices (20pt → h1, 14pt → h2, 12pt → h3, 10.6pt → h4)
- **Gras / italique** préservés (`<b>`, `font-style:italic`)
- **Liens internes** reconstitués à partir des surcouches `<a>` positionnées en absolu
- **Table des matières** : les points de suite (dot leaders) sont supprimés, les entrées restent du texte (non des titres)
- **Plan de comptes** : les fragments `<p>` à la même coordonnée verticale sont fusionnés sur une seule ligne
- **En-têtes / pieds de page** répétitifs supprimés automatiquement

```bash
# Convertir les HTML d'une année spécifique
uv run html2md.py --year 2026

# Convertir tous les HTML
uv run html2md.py --all

# Spécifier un répertoire de sortie
uv run html2md.py --all --output-dir out
```

Par défaut, les fichiers Markdown sont créés dans le même répertoire que les HTML sources.
