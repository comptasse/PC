# Version 2024

## Structure

Le fichier **`pcg_2024.json`** regroupe l'ensemble des données dans un unique fichier. Un schéma JSON **`pcg_2024.schema.json`** est également fourni.

### Racine
| Clé        | Type     | Description                                                       |
| ---------- | -------- | ----------------------------------------------------------------- |
| `version`  | `int`    | L'année de la version (`2024`).                                   |
| `flat`     | `array`  | Version à plat avec référence au compte parent.                   |
| `nested`   | `array`  | Version hiérarchique avec sous-comptes imbriqués.                 |
| `diff`     | `object` | Différences par rapport à la version précédente (2023).           |

### Comptes — format hiérarchique (`nested`)
| Clé        | Type                                 | Description                                                                                                                                                                                                                                                                                                                                                                    |
| ---------- | ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `number`   | `int`                                | Le numéro du compte.                                                                                                                                                                                                                                                                                                                                                           |
| `label`    | `string`                             | Le libellé du compte.                                                                                                                                                                                                                                                                                                                                                          |
| `system`   | `"condensed"` `"base"` `"developed"` | Le système minimal dans lequel s'inscrit le compte. Notez bien que le système développé contient tous les comptes du système de base qui contient lui-même tous les comptes du système abrégé. <br/> `condensed` si le compte est dans le système abrégé. <br/> `base` si le compte est dans le système de base. <br/> `developed` si le compte est dans le système développé. |
| `accounts` | `array`                              | La liste des sous-comptes, reprenant la même structure de manière récursive.                                                                                                                                                                                                                                                                                                   |

### Comptes — format à plat (`flat`)
| Clé        | Type                                 | Description                                                                                                                                                                                                                                                                                                                                                                    |
| ---------- | ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `number`   | `int`                                | Le numéro du compte.                                                                                                                                                                                                                                                                                                                                                           |
| `label`    | `string`                             | Le libellé du compte.                                                                                                                                                                                                                                                                                                                                                          |
| `system`   | `"condensed"` `"base"` `"developed"` | Le système minimal dans lequel s'inscrit le compte. Notez bien que le système développé contient tous les comptes du système de base qui contient lui-même tous les comptes du système abrégé. <br/> `condensed` si le compte est dans le système abrégé. <br/> `base` si le compte est dans le système de base. <br/> `developed` si le compte est dans le système développé. |
| `parent`   | `int` \| `null`                      | Le numéro du compte parent, ou `null` pour les comptes racines (classes).                                                                                                                                                                                                                                                                                                      |

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
    "version": 2024,
    "flat": [
        {
            "number": 1,
            "label": "Comptes de capitaux",
            "system": "condensed",
            "parent": null
        },
        ...
    ],
    "nested": [
        {
            "number": 1,
            "label": "Comptes de capitaux",
            "system": "condensed",
            "accounts": [
                ...
            ]
        },
        ...
    ],
    "diff": {
        "from": 2023,
        "to": 2024,
        "added": [],
        "removed": [],
        "modified": [
            {
                "number": 1,
                "label": {
                    "from": "Capitaux",
                    "to": "Comptes de capitaux"
                }
            },
            ...
        ]
    }
}
```
