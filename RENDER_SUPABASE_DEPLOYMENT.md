# 🚀 Render.com mit Supabase PostgreSQL verbinden

Diese Anleitung zeigt, wie du deine bestehende Flask-Anwendung auf **Render.com** so konfigurierst, dass sie die **Supabase PostgreSQL-Datenbank** nutzt.

---

## ✅ Voraussetzungen

- ✓ Render.com Account vorhanden
- ✓ Projekt bereits auf Render deployed: https://dienst.onrender.com
- ✓ Supabase PostgreSQL-Datenbank eingerichtet
- ✓ Supabase Connection String verfügbar:
  ```
  postgresql://postgres:Tgr482akk14!@db.pnvvynnsfylepqvgyduy.supabase.co:5432/postgres
  ```

---

## 📝 Schritt-für-Schritt-Anleitung

### 1️⃣ Render.com Dashboard öffnen

1. Gehe zu: https://dashboard.render.com/
2. Melde dich mit deinem Account an
3. Klicke auf dein Service **"dienst"**

### 2️⃣ Environment Variable aktualisieren

1. Im Service-Dashboard klicke auf **"Environment"** im linken Menü
2. Suche die Variable **`DATABASE_URL`**
3. Klicke auf **"Edit"** (Stift-Symbol) neben DATABASE_URL
4. Ersetze den alten Wert mit:
   ```
   postgresql://postgres:Tgr482akk14!@db.pnvvynnsfylepqvgyduy.supabase.co:5432/postgres
   ```
5. Klicke auf **"Save Changes"**

### 3️⃣ Deployment auslösen

**Option A: Automatisches Deployment (empfohlen)**
- Render erkennt die Änderung automatisch und startet ein neues Deployment
- Warte 2-3 Minuten bis "Live" Status angezeigt wird

**Option B: Manuelles Deployment**
1. Klicke oben rechts auf **"Manual Deploy"**
2. Wähle **"Deploy latest commit"**
3. Warte auf erfolgreichen Deployment-Status

### 4️⃣ Deployment-Logs überprüfen

1. Klicke auf **"Logs"** im linken Menü
2. Überprüfe, dass keine Fehler auftreten
3. Suche nach erfolgreicher Meldung:
   ```
   ✅ Datenbank-Migration erfolgreich abgeschlossen
   ```

### 5️⃣ Anwendung testen

1. Öffne: https://dienst.onrender.com
2. Teste Admin-Login:
   - Benutzername: `Groß`
   - Passwort: `mettwurst`
3. Verifiziere, dass das Admin-Dashboard lädt
4. Teste Dienstwunsch-Formular als Benutzer

---

## 🔧 Troubleshooting

### ❌ Fehler: "could not connect to server"

**Problem:** Supabase Connection String ist falsch

**Lösung:**
1. Gehe zu Supabase Dashboard: https://supabase.com/dashboard
2. Wähle dein Projekt: `pnvvynnsfylepqvgyduy`
3. Gehe zu **Settings** → **Database** → **Connection String**
4. Wähle **"URI"** und kopiere den Connection String
5. Ersetze `[YOUR-PASSWORD]` mit: `Tgr482akk14!`
6. Aktualisiere DATABASE_URL auf Render

### ❌ Fehler: "relation does not exist"

**Problem:** Datenbank-Tabellen existieren noch nicht

**Lösung:**
- Kein Problem! SQLAlchemy erstellt die Tabellen automatisch beim ersten Request
- Warte 30 Sekunden und lade die Seite neu
- Die Tabellen werden automatisch angelegt

### ❌ Deployment läuft nicht durch

**Problem:** Build schlägt fehl

**Lösung:**
1. Überprüfe `requirements.txt` enthält:
   ```
   psycopg2-binary==2.9.9
   python-dotenv==1.0.0
   ```
2. Trigger manuelles Deployment neu
3. Kontrolliere Logs auf spezifische Fehlermeldungen

### ❌ Admin-Login funktioniert nicht

**Problem:** Admin-Benutzer existiert nicht in neuer Datenbank

**Lösung:**
- Der Admin-Account wird automatisch beim ersten Start erstellt
- Warte 1 Minute nach erfolgreichem Deployment
- Versuche erneut einzuloggen mit:
  - Benutzername: `Groß`
  - Passwort: `mettwurst`

---

## 📊 Was passiert beim Deployment?

1. **Render baut Container neu:**
   - Installiert Python-Dependencies aus requirements.txt
   - Kopiert Flask-Code in Container

2. **Anwendung startet:**
   - Liest DATABASE_URL aus Environment
   - Verbindet zu Supabase PostgreSQL
   - Führt `migrate_database()` aus

3. **Datenbank-Migration:**
   - Prüft ob Tabellen existieren
   - Erstellt fehlende Tabellen (users, shift_requests, shift_request_snapshots, shift_notes)
   - Legt Admin-Benutzer an falls nicht vorhanden

4. **Anwendung ist live:**
   - Verfügbar unter: https://dienst.onrender.com
   - Nutzt Supabase PostgreSQL für alle Daten

---

## 🎉 Vorteile der Supabase-Integration

✅ **Bessere Performance:** Dedizierte PostgreSQL-Datenbank  
✅ **Mehr Features:** Supabase Dashboard für SQL-Abfragen  
✅ **Backups:** Automatische Backups von Supabase  
✅ **Skalierbarkeit:** Einfach auf größere Pläne upgraden  
✅ **Monitoring:** Echtzeit-Monitoring in Supabase Dashboard  

---

## 📚 Nächste Schritte

### Daten von Render PostgreSQL migrieren (optional)

Falls du bereits Daten in der alten Render PostgreSQL-Datenbank hast:

1. Nutze das Migrations-Script:
   ```bash
   python migrate_to_supabase.py
   ```
   
2. Das Script kopiert:
   - Alle Benutzer
   - Alle Dienstwünsche
   - Alle Änderungs-Snapshots
   - Alle Notizen

### Supabase Dashboard nutzen

1. Öffne: https://supabase.com/dashboard/project/pnvvynnsfylepqvgyduy
2. Gehe zu **Table Editor** um Daten direkt anzusehen
3. Nutze **SQL Editor** für komplexe Abfragen
4. Überwache Performance unter **Reports**

---

## 🔒 Sicherheitshinweise

⚠️ **WICHTIG:**
- Die Datenbankverbindung ist verschlüsselt (SSL)
- Speichere das Passwort `Tgr482akk14!` sicher
- Teile den Connection String NICHT öffentlich
- Nutze Environment Variables (wie auf Render) statt Hardcoding

---

## 📞 Support

Bei Problemen:
1. Überprüfe Render Logs: https://dashboard.render.com/
2. Überprüfe Supabase Logs: https://supabase.com/dashboard/project/pnvvynnsfylepqvgyduy/logs
3. Kontrolliere GitHub Issues: https://github.com/koboltze-py/dienst/issues

---

**Deployment-Status:** ✅ Bereit für Produktion  
**Letzte Aktualisierung:** 17.01.2026  
**Version:** 2.5 (mit Änderungsverfolgung)
