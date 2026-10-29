# Version 2023

## Structure

Le fichier **`pcg_2023.json`** regroupe l'ensemble des données dans un unique fichier. Un schéma JSON **`pcg_2023.schema.json`** est également fourni.

### Racine
| Clé        | Type     | Description                                                       |
| ---------- | -------- | ----------------------------------------------------------------- |
| `version`  | `int`    | L'année de la version (`2023`).                                   |
| `flat`     | `array`  | Version à plat avec référence au compte parent.                   |
| `nested`   | `array`  | Version hiérarchique avec sous-comptes imbriqués.                 |

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

## Extrait

```js
{
    "version": 2023,
    "flat": [
        {
            "number": 1,
            "label": "Capitaux",
            "system": "condensed",
            "parent": null
        },
        {
            "number": 10,
            "label": "Capital et réserves",
            "system": "base",
            "parent": 1
        },
        ...
    ],
    "nested": [
        {
            "number": 1,
            "label": "Capitaux",
            "system": "condensed",
            "accounts": [
                {
                    "number": 10,
                    "label": "Capital et réserves",
                    "system": "base",
                    "accounts": [
                        ...
                    ]
                },
                ...
            ]
        },
        ...
    ]
}
```
