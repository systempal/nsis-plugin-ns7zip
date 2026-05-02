# update_gitea_releases.py

Script one-shot per aggiornare il body delle release Gitea esistenti con il testo del CHANGELOG.

## Quando usarlo

Il workflow `release.yml` aggiorna automaticamente il body delle release **nuove** su Gitea.
Questo script serve per le release **già esistenti**, create prima che quella funzionalità fosse aggiunta.

## Prerequisiti

- Python 3.8+
- Un Gitea API token con permesso **Repository → Read and Write**

### Creare il token su Gitea

1. Gitea → avatar → **Settings** → **Applications**
2. Sezione **"Manage Access Tokens"** → nome a piacere (es. `release-body-update`)
3. Permission: **Repository** → `Read and Write`
4. **Generate Token** → copia il valore (mostrato una sola volta)

## Uso

```bash
# Tramite variabile d'ambiente
GITEA_TOKEN=<token> python3 tools/update_gitea_releases.py

# Tramite argomento
python3 tools/update_gitea_releases.py --token <token>
```

## Output atteso

```
[v2.0.0] recupero release... id=1, aggiorno body... OK
[v2.0.1] recupero release... id=2, aggiorno body... OK
[v2.1.0] recupero release... id=3, aggiorno body... OK
[v2.2.0] recupero release... id=4, aggiorno body... OK
[v2.2.1] recupero release... id=5, aggiorno body... OK
```

Se una release non esiste su Gitea per quel tag, la riga mostra `SALTATO`.

## Come funziona

Per ogni file `tools/release-notes/vX.Y.Z.md`:

1. Chiama `GET /api/v1/repos/{owner}/{repo}/releases/tags/vX.Y.Z` per ottenere l'ID
2. Chiama `PATCH /api/v1/repos/{owner}/{repo}/releases/{id}` con il body del file `.md`

## Aggiungere nuove versioni

Crea un file `tools/release-notes/vX.Y.Z.md` con il contenuto desiderato, poi riesegui lo script.
Per le release future il workflow lo fa automaticamente — questo script non è necessario.
