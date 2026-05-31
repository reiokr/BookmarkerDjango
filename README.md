# BookmarkerDjango

BookmarkerDjango on Django-põhine veebirakendus järjehoidjate haldamiseks. Salvesta, kategoriseeri ja lemmikute oma lemmiklinke lihtsalt.

## Funktsioonid

- Kasutaja autentimine ja registreerimine
- Järjehoidjate lisamine, muutmine ja kustutamine
- Järjehoidjate kategoriseerimine kaustadesse
- Otsing pealkirja või URL-i järgi
- YouTube videote integreerimine ja kommentaarid
- Reageeriv disain mobiili ja lauaarvuti jaoks

## Paigaldus

### Eeldused

- Python 3.14+
- Django 6.0+
- PostgreSQL
- Node.js ja npm (frontend sõltuvuste jaoks)
- YouTube Data API võti

### Repo kloonimine

```bash
git clone https://github.com/reiokr/BookmarkerDjango.git
cd BookmarkerDjango
```

### .env seadistus

Kopeeri mall ja täida oma andmed:

```bash
cp .env.example .env
```

Redigeeri `.env` faili ja täida:
- `SECRET_KEY` - Django saladusvõti
- `DB_NAME`, `DB_USER`, `DB_PASSWORD` - andmebaasi andmed
- `YOUTUBE_API_KEY` - YouTube Data API võti
- `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` - e-posti konto andmed

### Backend seadistus

1. Loo virtuaalkeskkond:

   ```bash
   python -m venv .venv
   ```

2. Aktiveeri virtuaalkeskkond:

   - Windows:

     ```bash
     .venv\Scripts\activate
     ```

   - macOS/Linux:

     ```bash
     source .venv/bin/activate
     ```

3. Paigalda backend sõltuvused:

   ```bash
   pip install -r requirements.txt
   ```

4. Rakenda andmebaasi migratsioonid:

   ```bash
   python manage.py migrate
   ```

5. Loo superkasutaja admin paneeli jaoks:

   ```bash
   python manage.py createsuperuser
   ```

### Frontend seadistus

1. Mine `frontend` kataloogi:

   ```bash
   cd frontend
   ```

2. Paigalda frontend sõltuvused:

   ```bash
   npm install
   ```

3. Kompileeri frontend varad:

   ```bash
   npm run build
   ```

4. Naase juurkataloogi:

   ```bash
   cd ..
   ```

## Käivitamine

### Tootmine

```bash
python manage.py runserver
```

Külasta `http://127.0.0.1:8000/` oma brauseris.

### Arendus

Ava kaks terminali akent:

**Terminal 1 - Django server:**
```bash
source .venv/bin/activate
python manage.py runserver
```

**Terminal 2 - React dev server:**
```bash
cd frontend
npm start
```

## testimine

Testide käivitamiseks:

```bash
python manage.py test
```

## Litsents

See projekt on litsentseeritud MIT litsentsi alla - vaata [LICENSE](LICENSE) faili üksikasju.
