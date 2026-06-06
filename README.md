# BookmarkerDjango

BookmarkerDjango is a Django-based web application for managing bookmarks. Save, categorize, and mark your favorite links with ease.

## Features

- User authentication and registration
- Add, edit, and delete bookmarks
- Organize bookmarks into folders by category
- Search by title or URL
- YouTube video integration and comments
- Responsive design for mobile and desktop

## Installation

### Prerequisites

- Python 3.14+
- Django 6.0+
- PostgreSQL
- Node.js and npm (for frontend dependencies)
- YouTube Data API key

### Clone the Repository

```bash
git clone https://github.com/reiokr/BookmarkerDjango.git
cd BookmarkerDjango
```

### Environment Setup

Copy the template and fill in your data:

```bash
cp .env.example .env
```

Edit the `.env` file and fill in:
- `SECRET_KEY` - Django secret key
- `DB_NAME`, `DB_USER`, `DB_PASSWORD` - Database credentials
- `YOUTUBE_API_KEY` - YouTube Data API key
- `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` - Email account credentials

### Backend Setup

1. Create a virtual environment:

   ```bash
   python -m venv .venv
   ```

2. Activate the virtual environment:

   - Windows:

     ```bash
     .venv\Scripts\activate
     ```

   - macOS/Linux:

     ```bash
     source .venv/bin/activate
     ```

3. Install backend dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Apply database migrations:

   ```bash
   python manage.py migrate
   ```

5. Create a superuser for the admin panel:

   ```bash
   python manage.py createsuperuser
   ```

### Frontend Setup

1. Navigate to the `frontend` directory:

   ```bash
   cd frontend
   ```

2. Install frontend dependencies:

   ```bash
   npm install
   ```

3. Build frontend assets:

   ```bash
   npm run build
   ```

4. Return to the root directory:

   ```bash
   cd ..
   ```

## Running the Application

### Production

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` in your browser.

### Development

Open two terminal windows:

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

## Testing

To run tests:

```bash
python manage.py test
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
