#!/usr/bin/env python3
"""
Migration Script: SQLite → Supabase PostgreSQL
Migriert alle Daten von der lokalen SQLite-Datenbank zu Supabase
"""

import os
import sys
from datetime import datetime
import sqlite3

print("=" * 60)
print("🚀 SUPABASE MIGRATION")
print("=" * 60)
print()

# Prüfe ob .env Datei existiert
if not os.path.exists('.env'):
    print("❌ Fehler: .env Datei nicht gefunden!")
    print("Erstelle zuerst eine .env Datei mit deiner Supabase DATABASE_URL")
    sys.exit(1)

# Lade Umgebungsvariablen
from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL or 'sqlite' in DATABASE_URL:
    print("❌ Fehler: DATABASE_URL muss auf Supabase PostgreSQL zeigen!")
    print()
    print("Aktuelle DATABASE_URL:", DATABASE_URL)
    print()
    print("Erwartetes Format:")
    print("postgresql://postgres.[REF]:[PASSWORD]@...pooler.supabase.com:6543/postgres")
    print()
    print("Bitte aktualisiere die .env Datei mit deiner Supabase-URL!")
    sys.exit(1)

print(f"✅ DATABASE_URL gefunden: {DATABASE_URL[:50]}...")
print()

# Prüfe ob psycopg2 installiert ist
try:
    import psycopg2
    from psycopg2.extras import execute_values
    print("✅ psycopg2 ist installiert")
except ImportError:
    print("❌ psycopg2-binary ist nicht installiert!")
    print()
    print("Installiere es mit:")
    print("  .venv\\Scripts\\python.exe -m pip install psycopg2-binary")
    sys.exit(1)

# Prüfe ob SQLite-Datenbank existiert
SQLITE_DB = 'instance/dienstwuensche.db'
if not os.path.exists(SQLITE_DB):
    print(f"⚠️  Keine SQLite-Datenbank gefunden: {SQLITE_DB}")
    print("Erstelle leere Datenbank in Supabase...")
    
    # Verbinde zu Supabase und erstelle Schema
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # Erstelle Tabellen (ohne Daten zu migrieren)
        from app import app, db
        with app.app_context():
            db.create_all()
            print("✅ Datenbank-Schema in Supabase erstellt")
        
        conn.close()
        print()
        print("✅ Migration abgeschlossen (keine Daten vorhanden)")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Fehler: {e}")
        sys.exit(1)

print(f"✅ SQLite-Datenbank gefunden: {SQLITE_DB}")
print()

# Starte Migration
print("🔄 Starte Migration...")
print()

try:
    # Verbinde zu SQLite
    sqlite_conn = sqlite3.connect(SQLITE_DB)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cur = sqlite_conn.cursor()
    
    # Verbinde zu Supabase
    pg_conn = psycopg2.connect(DATABASE_URL)
    pg_cur = pg_conn.cursor()
    
    print("✅ Verbindung zu beiden Datenbanken hergestellt")
    print()
    
    # Lösche alte Tabellen in Supabase (falls vorhanden)
    print("🗑️  Lösche alte Tabellen in Supabase...")
    pg_cur.execute("DROP TABLE IF EXISTS shift_notes CASCADE;")
    pg_cur.execute("DROP TABLE IF EXISTS shift_request_snapshots CASCADE;")
    pg_cur.execute("DROP TABLE IF EXISTS shift_requests CASCADE;")
    pg_cur.execute("DROP TABLE IF EXISTS users CASCADE;")
    pg_conn.commit()
    print("✅ Alte Tabellen gelöscht")
    print()
    
    # Erstelle neue Tabellen mit SQLAlchemy
    print("📋 Erstelle Tabellen-Schema...")
    from app import app, db
    with app.app_context():
        db.create_all()
    print("✅ Tabellen erstellt")
    print()
    
    # Migriere Users
    print("👥 Migriere Benutzer...")
    sqlite_cur.execute("SELECT * FROM users")
    users = sqlite_cur.fetchall()
    
    for user in users:
        pg_cur.execute(
            """INSERT INTO users (id, name, password, is_admin, created_at, first_submission_at) 
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (user['id'], user['name'], user['password'], user['is_admin'], 
             user['created_at'], user.get('first_submission_at'))
        )
    
    pg_conn.commit()
    print(f"✅ {len(users)} Benutzer migriert")
    print()
    
    # Migriere Shift Requests
    print("📅 Migriere Dienstwünsche...")
    sqlite_cur.execute("SELECT * FROM shift_requests")
    shifts = sqlite_cur.fetchall()
    
    for shift in shifts:
        pg_cur.execute(
            """INSERT INTO shift_requests 
               (id, user_id, date, shift_type, remarks, status, confirmed, created_at, updated_at) 
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (shift['id'], shift['user_id'], shift['date'], shift['shift_type'], 
             shift.get('remarks'), shift.get('status', 'pending'), shift.get('confirmed', False),
             shift['created_at'], shift.get('updated_at') or shift['created_at'])
        )
    
    pg_conn.commit()
    print(f"✅ {len(shifts)} Dienstwünsche migriert")
    print()
    
    # Migriere Snapshots (falls vorhanden)
    try:
        print("📸 Migriere Snapshots...")
        sqlite_cur.execute("SELECT * FROM shift_request_snapshots")
        snapshots = sqlite_cur.fetchall()
        
        for snapshot in snapshots:
            pg_cur.execute(
                """INSERT INTO shift_request_snapshots 
                   (id, user_id, date, shift_type, created_at) 
                   VALUES (%s, %s, %s, %s, %s)""",
                (snapshot['id'], snapshot['user_id'], snapshot['date'], 
                 snapshot['shift_type'], snapshot['created_at'])
            )
        
        pg_conn.commit()
        print(f"✅ {len(snapshots)} Snapshots migriert")
        print()
    except sqlite3.OperationalError:
        print("⚠️  Keine Snapshots gefunden (Tabelle existiert nicht)")
        print()
    
    # Migriere Notes (falls vorhanden)
    try:
        print("💬 Migriere Notizen...")
        sqlite_cur.execute("SELECT * FROM shift_notes")
        notes = sqlite_cur.fetchall()
        
        for note in notes:
            pg_cur.execute(
                """INSERT INTO shift_notes 
                   (id, shift_request_id, user_id, content, created_at) 
                   VALUES (%s, %s, %s, %s, %s)""",
                (note['id'], note['shift_request_id'], note['user_id'], 
                 note['content'], note['created_at'])
            )
        
        pg_conn.commit()
        print(f"✅ {len(notes)} Notizen migriert")
        print()
    except sqlite3.OperationalError:
        print("⚠️  Keine Notizen gefunden (Tabelle existiert nicht)")
        print()
    
    # Aktualisiere Sequences
    print("🔢 Aktualisiere ID-Sequenzen...")
    tables = [
        ('users', 'id'),
        ('shift_requests', 'id'),
        ('shift_request_snapshots', 'id'),
        ('shift_notes', 'id')
    ]
    
    for table, id_col in tables:
        try:
            pg_cur.execute(f"SELECT MAX({id_col}) FROM {table}")
            max_id = pg_cur.fetchone()[0]
            if max_id:
                pg_cur.execute(f"SELECT setval(pg_get_serial_sequence('{table}', '{id_col}'), {max_id})")
        except:
            pass
    
    pg_conn.commit()
    print("✅ Sequenzen aktualisiert")
    print()
    
    # Schließe Verbindungen
    sqlite_conn.close()
    pg_conn.close()
    
    print("=" * 60)
    print("✅ MIGRATION ERFOLGREICH ABGESCHLOSSEN!")
    print("=" * 60)
    print()
    print("📊 Zusammenfassung:")
    print(f"   • {len(users)} Benutzer migriert")
    print(f"   • {len(shifts)} Dienstwünsche migriert")
    print()
    print("🚀 Nächste Schritte:")
    print("   1. Starte den Server: .venv\\Scripts\\python.exe app.py")
    print("   2. Teste die Anwendung auf http://localhost:5000")
    print("   3. Deploye zu Render.com mit der Supabase DATABASE_URL")
    print()
    print("🎉 Deine App nutzt jetzt Supabase PostgreSQL!")
    
except Exception as e:
    print()
    print("=" * 60)
    print("❌ MIGRATION FEHLGESCHLAGEN")
    print("=" * 60)
    print()
    print(f"Fehler: {e}")
    print()
    import traceback
    traceback.print_exc()
    sys.exit(1)
