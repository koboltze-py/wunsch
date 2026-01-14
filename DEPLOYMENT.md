# Deployment-Anleitung für Render.com

## Schritt 1: GitHub Repository erstellen

1. Gehen Sie zu https://github.com
2. Klicken Sie auf "New repository"
3. Name: `drk-dienstwuensche`
4. Privat oder Öffentlich wählen
5. "Create repository"

## Schritt 2: Code zu GitHub hochladen

Führen Sie im Projektordner aus:

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/IHR_USERNAME/drk-dienstwuensche.git
git push -u origin main
```

## Schritt 3: PostgreSQL-Datenbank auf Render erstellen

1. Gehen Sie zu https://render.com und melden Sie sich an
2. Klicken Sie auf "New +"  "PostgreSQL"
3. Name: `drk-dienstwuensche-db`
4. Database: `drk_db`
5. User: `drk_user`
6. Region: Frankfurt (Europe West)
7. Plan: **Free** auswählen
8. "Create Database"
9. **Wichtig**: Kopieren Sie die "Internal Database URL" (beginnt mit postgres://)

## Schritt 4: Web Service erstellen

1. Klicken Sie auf "New +"  "Web Service"
2. Wählen Sie "Connect a repository"
3. Verbinden Sie GitHub und wählen Sie Ihr Repository
4. Konfiguration:
   - **Name**: drk-dienstwuensche
   - **Region**: Frankfurt (Europe West)
   - **Branch**: main
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Plan**: Free

## Schritt 5: Umgebungsvariable hinzufügen

1. Scrollen Sie zu "Environment Variables"
2. Klicken Sie "Add Environment Variable"
3. **Key**: `DATABASE_URL`
4. **Value**: Die kopierte Internal Database URL aus Schritt 3
5. "Save Changes"

## Schritt 6: Deploy starten

1. Klicken Sie "Create Web Service"
2. Render startet automatisch das Deployment
3. Nach 2-3 Minuten ist Ihre App live!
4. URL: `https://drk-dienstwuensche.onrender.com`

## Wichtige Hinweise

- **Kostenlos**: Beide Services (PostgreSQL + Web) sind kostenlos
- **Auto-Deploy**: Bei jedem Git-Push wird automatisch neu deployed
- **Sleep-Modus**: Nach 15 Min Inaktivität schläft die App (erster Zugriff dauert ~30 Sek)
- **Datenbank**: Ihre Daten bleiben dauerhaft gespeichert

## Standard-Login

- Admin: Groß / mettwurst
- Neue Benutzer können sich selbst registrieren

## Support

Bei Problemen: https://render.com/docs
