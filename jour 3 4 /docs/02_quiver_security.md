# Quiver — sécurité et usage

Le token Quiver ne doit jamais être écrit dans le code, un notebook ou Git.

## Configuration

Créer un fichier local `.env` :

```text
QUIVER_API_TOKEN=...
```

`.env` est ignoré par Git. `.env.example` reste vide et versionnable.

## Usage

Quiver sert uniquement de validation externe :

- diagnostic d’accès réel ;
- inspection des champs présents ;
- comparaison déclarants/dates sur 2025.

Quiver ne corrige jamais automatiquement la source House.
