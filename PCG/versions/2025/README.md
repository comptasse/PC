# Version 2025

## Structure

Le fichier **`pcg_2025.json`** regroupe l'ensemble des données dans un unique fichier. Un schéma JSON **`pcg_2025.schema.json`** est également fourni.

### Racine
| Clé        | Type     | Description                                                       |
| ---------- | -------- | ----------------------------------------------------------------- |
| `version`  | `int`    | L'année de la version (`2025`).                                   |
| `flat`     | `array`  | Version à plat avec référence au compte parent.                   |
| `nested`   | `array`  | Version hiérarchique avec sous-comptes imbriqués.                 |
| `diff`     | `object` | Différences par rapport à la version précédente (2024).           |

### Comptes — format hiérarchique (`nested`)
| Clé        | Type                           | Description                                                                                                                                                                                                                                     |
| ---------- | ------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `number`   | `int`                          | Le numéro du compte.                                                                                                                                                                                                                            |
| `label`    | `string`                       | Le libellé du compte.                                                                                                                                                                                                                           |
| `system`   | `"minimal"` `"facultatif"`     | Le système dans lequel s'inscrit le compte. <br/> `minimal` si le compte fait partie du plan de comptes minimal. <br/> `facultatif` si le compte est facultatif (présenté en italique dans le recueil). Le plan minimal contient tous les comptes minimaux ; l'ensemble complet contient les comptes minimaux et facultatifs. |
| `accounts` | `array`                        | La liste des sous-comptes, reprenant la même structure de manière récursive.                                                                                                                                                                    |

### Comptes — format à plat (`flat`)
| Clé        | Type                           | Description                                                                                                                                                                                                                                     |
| ---------- | ------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `number`   | `int`                          | Le numéro du compte.                                                                                                                                                                                                                            |
| `label`    | `string`                       | Le libellé du compte.                                                                                                                                                                                                                           |
| `system`   | `"minimal"` `"facultatif"`     | Le système dans lequel s'inscrit le compte. <br/> `minimal` si le compte fait partie du plan de comptes minimal. <br/> `facultatif` si le compte est facultatif (présenté en italique dans le recueil). Le plan minimal contient tous les comptes minimaux ; l'ensemble complet contient les comptes minimaux et facultatifs. |
| `parent`   | `int` \| `null`                | Le numéro du compte parent, ou `null` pour les comptes racines (classes).                                                                                                                                                                       |

### Différences (`diff`)
| Clé        | Type    | Description                                                                                                                                                 |
| ---------- | ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `from`     | `int`   | L'année de la version précédente.                                                                                                                           |
| `to`       | `int`   | L'année de la version courante.                                                                                                                             |
| `added`    | `array` | Les comptes ajoutés. Chaque élément contient `number`, `label` et `system`.                                                                                 |
| `removed`  | `array` | Les comptes supprimés. Chaque élément contient `number`, `label` et `system` (tels qu'ils étaient dans la version précédente).                               |
| `modified` | `array` | Les comptes dont le libellé et/ou le système a changé. Chaque élément contient `number` et un objet `label` et/ou `system` avec les clés `from` et `to`.    |

## Extrait

```js
{
    "version": 2025,
    "flat": [
        {
            "number": 1,
            "label": "Comptes de capitaux",
            "system": "minimal",
            "parent": null
        },
        ...
    ],
    "nested": [
        {
            "number": 1,
            "label": "Comptes de capitaux",
            "system": "minimal",
            "accounts": [
                ...
            ]
        },
        ...
    ],
    "diff": {
        "from": 2024,
        "to": 2025,
        "added": [ ... ],
        "removed": [ ... ],
        "modified": [ ... ]
    }
}
```
