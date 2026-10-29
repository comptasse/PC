# Version 2019

## Structure

Chaque plan est regroupé dans un unique fichier :

- **`pcmn_entreprises_2019.json`** — entreprises autres que les associations et fondations (477 comptes).
- **`pcmn_asbl_2019.json`** — associations et fondations (449 comptes).

Les deux fichiers partagent le schéma JSON **`pcmn_2019.schema.json`**.

### Racine
| Clé           | Type     | Description                                                                                   |
| ------------- | -------- | --------------------------------------------------------------------------------------------- |
| `version`     | `int`    | L'année du texte coordonné (`2019`).                                                          |
| `plan`        | `string` | `"entreprises"` ou `"asbl"`.                                                                  |
| `coordinated` | `string` | La date de coordination du texte par la CNC (`"2019-05-07"`).                                 |
| `footnotes`   | `object` | Les notes de bas de page, indexées par leur numéro officiel (`"1"`, `"2"`…), dans chaque langue. |
| `flat`        | `array`  | Version à plat avec référence au compte parent.                                               |
| `nested`      | `array`  | Version hiérarchique avec sous-comptes imbriqués.                                             |

### Comptes
| Clé            | Type                         | Description |
| -------------- | ---------------------------- | ----------- |
| `number`       | `string`                     | Le numéro du compte. C'est un texte pour conserver les zéros de tête de la classe 0 (`"0"`, `"00"`, `"000"` sont trois comptes distincts). Une plage de comptes s'écrit `"164-165"`. |
| `label`        | `object`                     | Le libellé dans chaque langue : `fr`, `nl`, `de`, `en`. Une valeur vaut `null` lorsque le texte ne donne pas de libellé (numéro non utilisé par ce plan, par exemple le compte `11` des associations) ou que la langue omet le compte. |
| `range`        | `object` (optionnel)         | Les bornes d'une plage de comptes : `from` et `to`. |
| `rubric`       | `object` (optionnel)         | Associations et fondations uniquement : la rubrique correspondante du schéma complet des comptes annuels, à l'actif (`asset`), au passif (`liability`) ou au compte de résultats (`income_statement`). Deux rubriques possibles sont séparées par `/` (`"II.I/V.D"`). |
| `notes`        | `array` (optionnel)          | Les numéros des notes de bas de page associées au compte, à retrouver dans `footnotes`. |
| `subdivisions` | `array` (optionnel)          | Les subdivisions génériques d'une plage, par exemple `...1 Chèques émis` sous `550-559` : `suffix` (dernier chiffre), `label` et `notes`. |
| `description`  | `object` (optionnel)         | Le contenu du compte, tel que décrit dans la section « Détermination du contenu de certains comptes » (comptes `00` à `07`), dans chaque langue. |
| `parent`       | `string` \| `null`           | Format à plat (`flat`) : le numéro du compte parent, ou `null` pour les classes. Le parent d'une plage est le plus long préfixe commun existant (`"16"` pour `"164-165"`). |
| `accounts`     | `array`                      | Format hiérarchique (`nested`) : la liste des sous-comptes, reprenant la même structure de manière récursive. |

Les comptes sont triés par numéro (ordre lexical) : la classe 0 (droits et engagements hors bilan) apparaît donc en premier. Les classes 8 et 9 ne sont pas définies ; la note (29) permet de les utiliser pour coder les comptes de la classe 0.

### Différences par rapport au PCG
| PCG                                  | PCMN                                                  |
| ------------------------------------ | ----------------------------------------------------- |
| `number` : `int`                     | `number` : `string`                                   |
| `label` : `string`                   | `label` : objet `{ fr, nl, de, en }`                  |
| `system` : `minimal` / `facultatif`  | absent (cette distinction n'existe pas dans le PCMN)  |
| —                                    | `range`, `rubric`, `notes`, `subdivisions`, `description`, `footnotes` |

## Écarts dans les sources
Les versions linguistiques publiées par la CNC ne sont pas toujours identiques. Le script les signale et les traite ainsi :

- **Entreprises** — les notes (14) et (18) n'existent qu'en allemand et en anglais, et la note (31) n'existe pas en allemand : ces textes valent `null` dans les langues concernées. Les références aux notes reprises dans `notes` sont celles du texte français. Le compte `203`, abrogé (`[...]`), est omis. La référence à la note abrogée (27bis) est supprimée.
- **Associations et fondations** — la plage `550-559` est absente du texte français (son libellé `fr` vaut `null`, ses subdivisions sont conservées). Le texte néerlandais numérote par erreur `6701` le compte « Geraamde belastingen », corrigé en `6702`.
- Les mentions `[...]` (texte supprimé par une modification) sont retirées des libellés.

## Extrait

```js
{
    "version": 2019,
    "plan": "asbl",
    "coordinated": "2019-05-07",
    "footnotes": {
        "15": {
            "fr": "Clients dont le compte présente un solde créditeur.",
            ...
        },
        ...
    },
    "flat": [
        ...
        {
            "number": "400",
            "label": {
                "fr": "Clients",
                "nl": "Handelsdebiteuren",
                "de": "Kunden",
                "en": "Customers"
            },
            "rubric": {
                "asset": "VII.A",
                "liability": "IX.C.1"
            },
            "notes": ["15"],
            "parent": "40"
        },
        ...
    ],
    "nested": [ ... ]
}
```
