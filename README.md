# DRK Köln - Dienstwunsch-Anwendung

Webbasierte Anwendung für die Verwaltung von Dienstwünschen beim Deutschen Roten Kreuz Köln.

## Features

- Multi-User-System mit Passwort-Authentifizierung
- Admin-Dashboard für Übersicht aller Dienstwünsche
- Benutzer können eigene Dienstwünsche erstellen und verwalten
- PostgreSQL-Datenbank für dauerhaften Speicher
- Responsive Design mit Tailwind CSS

## Deployment auf Render.com

1. Repository auf GitHub erstellen und Code hochladen
2. Auf [render.com](https://render.com) einloggen
3. ''New''  ''PostgreSQL''  Datenbank erstellen (kostenlos)
4. ''New''  ''Web Service''  Repository verbinden
5. Render erkennt automatisch Python und richtet alles ein
6. Datenbank-URL wird automatisch als DATABASE_URL übergeben

## Lokal starten

\\\ash
pip install -r requirements.txt
python app.py
\\\

## Standard-Admin

- Benutzername: **Groß**
- Passwort: **mettwurst**

## Technologie

- Backend: Flask + SQLAlchemy
- Datenbank: PostgreSQL (online) / SQLite (lokal)
- Frontend: HTML + Tailwind CSS + Vanilla JavaScript
