# 🚀 Supabase Migration - Schritt für Schritt

## 📋 Voraussetzungen
- Supabase-Account (kostenlos: https://supabase.com)
- Aktuelles Projekt auf GitHub gepusht ✅

## 1️⃣ Supabase-Projekt erstellen

1. Gehe zu https://supabase.com
2. Klicke auf **"Start your project"** oder **"New Project"**
3. Wähle einen Namen: z.B. `dienstwuensche-drk`
4. Wähle ein sicheres Passwort (WICHTIG: Gut aufbewahren!)
5. Wähle Region: **Frankfurt (eu-central-1)** (am nächsten zu Deutschland)
6. Klicke auf **"Create new project"**
7. Warte ~2 Minuten bis das Projekt bereit ist

## 2️⃣ Verbindungsdaten kopieren

1. Gehe in deinem Supabase-Projekt zu **Settings** → **Database**
2. Scrolle zu **Connection string** → **URI**
3. Klicke auf **"Copy"** bei der Connection String
4. Die URL sieht so aus:
   ```
   postgresql://postgres.[PROJECT-REF]:[YOUR-PASSWORD]@aws-0-eu-central-1.pooler.supabase.com:6543/postgres
   ```

## 3️⃣ Umgebungsvariable setzen

Öffne die Datei `.env` und ersetze die `DATABASE_URL`:

```env
# Alte SQLite-URL auskommentieren:
# DATABASE_URL="sqlite:///./instance/dienstwuensche.db"

# Neue Supabase PostgreSQL-URL einfügen:
DATABASE_URL="postgresql://postgres.[PROJECT-REF]:[YOUR-PASSWORD]@aws-0-eu-central-1.pooler.supabase.com:6543/postgres"
```

**WICHTIG:** Ersetze `[YOUR-PASSWORD]` mit deinem Supabase-Passwort!

## 4️⃣ PostgreSQL-Treiber installieren

**WICHTIG:** Wegen des langen Pfads kann die Installation fehlschlagen.

### Option A: Aktiviere Long Paths (Admin-Rechte erforderlich)

1. Öffne PowerShell **als Administrator**
2. Führe aus:
   ```powershell
   New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
   ```
3. Starte Computer neu
4. Installiere dann:
   ```powershell
   .\.venv\Scripts\python.exe -m pip install psycopg2-binary python-dotenv
   ```

### Option B: Nutze requirements.txt (einfacher)

Füge in `requirements.txt` hinzu:
```
psycopg2-binary==2.9.9
python-dotenv==1.0.0
```

Dann installiere:
```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt --no-deps
```

### Option C: Nutze Render direkt (empfohlen)

Skip die lokale Migration und nutze Supabase direkt auf Render:
1. Setze DATABASE_URL auf Render auf Supabase-URL
2. Render erstellt automatisch alle Tabellen beim ersten Start
3. Admin-Login: Groß / mettwurst wird automatisch erstellt

## 5️⃣ Datenbank migrieren

Führe das Migrationsskript aus:

```powershell
.\.venv\Scripts\python.exe migrate_to_supabase.py
```

Das Script erstellt automatisch:
- ✅ Alle Tabellen (users, shift_requests, shift_request_snapshots, shift_notes)
- ✅ Admin-Benutzer (Groß / mettwurst)
- ✅ Migriert alle vorhandenen Daten von SQLite

## 6️⃣ Server neu starten

```powershell
.\.venv\Scripts\python.exe app.py
```

Die App nutzt jetzt Supabase! 🎉

## 7️⃣ Render.com mit Supabase verbinden

1. Gehe zu https://dashboard.render.com
2. Wähle dein **"dienst"** Web Service
3. Gehe zu **Environment**
4. Ändere `DATABASE_URL`:
   ```
   postgresql://postgres.[PROJECT-REF]:[YOUR-PASSWORD]@aws-0-eu-central-1.pooler.supabase.com:6543/postgres
   ```
5. Klicke auf **"Save Changes"**
6. Render deployed automatisch neu

## ✅ Fertig!

Deine App läuft jetzt auf:
- **Lokal:** mit Supabase-Datenbank
- **Render:** mit Supabase-Datenbank
- **Datenbank:** Supabase (PostgreSQL)

## 🔍 Supabase-Dashboard nutzen

In Supabase kannst du:
- **Table Editor:** Daten direkt bearbeiten
- **SQL Editor:** SQL-Queries ausführen
- **Database → Backups:** Automatische Backups
- **API → Tables:** REST API (optional)

## 🆘 Probleme?

### Verbindung schlägt fehl
- Prüfe Passwort in DATABASE_URL
- Prüfe ob Supabase-Projekt läuft
- Stelle sicher, dass psycopg2-binary installiert ist

### Migration schlägt fehl
- Prüfe ob alte SQLite-Datenbank existiert
- Stelle sicher, dass Supabase-Datenbank leer ist
- Führe Script erneut aus

### Render deployed nicht
- Warte 2-3 Minuten nach Änderung der DATABASE_URL
- Prüfe Logs: **Logs** → **Deploy Logs**
