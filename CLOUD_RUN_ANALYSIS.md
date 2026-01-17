# Anpassungen für Google Cloud Run

## 🔧 Notwendige Änderungen:

### 1. Session-Management umstellen
**Problem**: Flask Sessions sind nicht persistent über Container-Neustarts

**Lösung A - Redis Sessions** (Empfohlen):
```python
# requirements.txt hinzufügen:
Flask-Session==0.8.0
redis==5.0.0

# In app.py:
from flask_session import Session
import redis

app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_REDIS'] = redis.from_url(
    os.environ.get('REDIS_URL', 'redis://localhost:6379')
)
Session(app)
```

**Lösung B - JWT Tokens** (Stateless):
```python
# requirements.txt hinzufügen:
Flask-JWT-Extended==4.6.0

# Verwende JWT statt Sessions für Authentication
```

### 2. Datenbank MUSS PostgreSQL sein
**Wichtig**: DATABASE_URL Environment Variable in Cloud Run setzen!

```bash
# Cloud SQL Instanz erstellen:
gcloud sql instances create wunsch-db \
  --database-version=POSTGRES_15 \
  --region=europe-west1 \
  --tier=db-f1-micro

# Datenbank erstellen:
gcloud sql databases create dienstwuensche --instance=wunsch-db

# Connection String holen und als ENV Variable setzen
```

### 3. File Uploads (falls vorhanden)
- Verwende **Google Cloud Storage** statt lokalem Dateisystem
- Exportierte Dateien (Excel/PDF) sollten temporär generiert werden (BytesIO) ✅ (bereits implementiert!)

---

## ⚙️ Cloud Run Service Konfiguration

```yaml
# cloudbuild.yaml - Update args:
- '--set-env-vars=DATABASE_URL=postgresql://USER:PASS@HOST/DB'
- '--set-env-vars=REDIS_URL=redis://REDIS_HOST:6379'
- '--add-cloudsql-instances=PROJECT:REGION:INSTANCE'
```

---

## 💰 Kosten-Schätzung

**Minimale Setup**:
- Cloud Run: ~0-5€/Monat (Pay-per-use)
- Cloud SQL (db-f1-micro): ~10€/Monat
- Redis (Memorystore basic): ~25€/Monat

**GESAMT**: ~35-40€/Monat

---

## 🔄 Alternative: Bessere Plattformen für diese App

### 1. **Render.com** (AKTUELL EMPFOHLEN)
- ✅ Persistent disk verfügbar
- ✅ PostgreSQL inkludiert (kostenlos)
- ✅ Einfaches Session-Management
- ✅ Keine Code-Änderungen nötig!
- 💰 Kostenlos für kleine Apps

### 2. **Heroku**
- ✅ Ähnlich wie Render
- ✅ Postgres-Add-on
- ✅ Redis-Add-on verfügbar
- 💰 ~7€/Monat (Hobby tier)

### 3. **Railway.app**
- ✅ Modern, einfach
- ✅ PostgreSQL inkludiert
- ✅ Gutes Developer Experience
- 💰 Pay-per-use ab $5

### 4. **Fly.io**
- ✅ Persistent volumes
- ✅ PostgreSQL Cluster
- ✅ Global deployment
- 💰 Kostenlos für kleine Apps

---

## 📋 Schnell-Entscheidung

**WENN**:
- ✅ Du willst die App JETZT deployen ohne Änderungen → **Render.com oder Railway**
- ✅ Du bist OK mit Code-Änderungen → **Cloud Run + Cloud SQL + Redis**
- ✅ Du brauchst Google Cloud Integration → **Cloud Run (mit Anpassungen)**
- ✅ Budget ist wichtig → **Render.com (kostenlos) oder Fly.io**

**Cloud Run macht nur Sinn wenn**:
- Du bereits andere Google Cloud Services nutzt
- Du extreme Skalierung brauchst (0 → 1000 Instanzen)
- Du Pay-per-Request bevorzugst
