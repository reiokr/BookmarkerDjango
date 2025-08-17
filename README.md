# BookmarkerDjango

BookmarkerDjango is a Django-based web application designed to manage and organize your bookmarks efficiently. It allows users to save, categorize, and retrieve their favorite links with ease.

## Features

- User authentication and registration
- Add, edit, and delete bookmarks
- Categorize bookmarks into folders
- Search bookmarks by title or URL
- Responsive design for mobile and desktop

## Installation

### Prerequisites

- Python 3.8+
- Django 3.2+
- Node.js and npm (for frontend dependencies)

### Clone the repository

```bash
git clone https://github.com/reiokr/BookmarkerDjango.git
cd BookmarkerDjango
```

### Backend setup

1. Create a virtual environment:

   ```bash
   python -m venv venv
   ```

2. Activate the virtual environment:

   - On Windows:

     ```bash
     venv\Scripts\activate
     ```

   - On macOS/Linux:

     ```bash
     source venv/bin/activate
     ```

3. Install backend dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Apply database migrations:

   ```bash
   python manage.py migrate
   ```

5. Create a superuser to access the admin panel:

   ```bash
   python manage.py createsuperuser
   ```

### Frontend setup

1. Navigate to the `frontend` directory:

   ```bash
   cd frontend
   ```

2. Install frontend dependencies:

   ```bash
   npm install
   ```

3. Build the frontend assets:

   ```bash
   npm run build
   ```

4. Return to the root directory:

   ```bash
   cd ..
   ```

### Run the development server

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` in your browser to access the application.

## Testing

To run tests:

```bash
python manage.py test
```

## Contributing

Contributions are welcome! Please fork the repository, create a new branch, and submit a pull request with your changes.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
