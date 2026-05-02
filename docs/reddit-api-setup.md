# Reddit r/battlemaps — Setup API autenticata

## Stato attuale

Lo scraper `grab-reddit.py` usa l'API pubblica Reddit (senza auth).
Limiti: max ~300 post unici, nessuna paginazione.

## Obiettivo

Accedere a tutti i post di r/battlemaps (~25.000) tramite API autenticata (gratuita).
Stima mappe indicizzabili: 5.000-10.000 (filtrando solo post con immagine e flair mappa).

## Setup Reddit API (5 minuti, una tantum)

1. Login su Reddit con il tuo account
2. Vai su https://www.reddit.com/prefs/apps/
3. Click "create another app..."
4. Compila:
   - **name**: `dnd-map-index`
   - **type**: `script`
   - **redirect uri**: `http://localhost:8080`
5. Click "create app"
6. Copia:
   - `client_id` — stringa corta sotto il nome dell'app
   - `client_secret` — campo "secret"
7. Crea il file `.env` nella root del progetto:

```
REDDIT_CLIENT_ID=il_tuo_client_id
REDDIT_CLIENT_SECRET=il_tuo_client_secret
REDDIT_USERNAME=il_tuo_username
REDDIT_PASSWORD=la_tua_password
```

Il file `.env` è già in `.gitignore` — non verrà mai committato.

## Cosa cambia con l'auth

| | Senza auth (ora) | Con auth |
|---|---|---|
| Post accessibili | ~300 | tutti (~25.000) |
| Paginazione | no | sì (parametro `after`) |
| Rate limit | ~10 req/min | 100 req/min |
| Ricerca per flair | no | sì |
| Costo | gratis | gratis |

## Modifiche allo script

Lo script `grab-reddit.py` va aggiornato per:
1. Leggere credenziali da `.env`
2. Ottenere token OAuth2
3. Paginare con `after` fino a esaurimento post
4. Usare `oauth.reddit.com` invece di `www.reddit.com`
5. Rispettare rate limit (1 req/sec)
6. Cache incrementale (non ri-scaricare post già indicizzati)

## Alternativa: libreria PRAW

```bash
pip install praw
```

Semplifica auth e paginazione. Valutare se aggiungere la dipendenza o restare con `requests`.

## Policy

Le regole restano le stesse:
- Solo metadati, nessun download di immagini
- Thumbnail: URL preview Reddit (già pubblici)
- Licenza: `all-rights-reserved` (default, nessun post specifica una licenza)
- Source URL: link al post Reddit originale
