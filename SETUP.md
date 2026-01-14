# Setup-Anleitung - Dienstwunsch Server Action

## 📦 Installation der Dependencies

```bash
npm install @prisma/client zod
npm install -D prisma

# Für Clerk Authentication
npm install @clerk/nextjs

# Alternativ für NextAuth
# npm install next-auth @next-auth/prisma-adapter
```

## 🗄️ Datenbank Setup

### 1. PostgreSQL Datenbank erstellen

```sql
CREATE DATABASE dienstwuensche;
```

### 2. .env Datei erstellen

Kopieren Sie `.env.example` zu `.env` und passen Sie die Werte an:

```bash
cp .env.example .env
```

Bearbeiten Sie die `DATABASE_URL`:
```
DATABASE_URL="postgresql://USER:PASSWORD@localhost:5432/dienstwuensche"
```

### 3. Prisma initialisieren und Migrationen ausführen

```bash
# Prisma Client generieren
npx prisma generate

# Erste Migration erstellen und ausführen
npx prisma migrate dev --name init

# Prisma Studio öffnen (GUI für Datenbank)
npx prisma studio
```

## 🔐 Authentication Setup

### Option 1: Clerk (Empfohlen)

1. Erstellen Sie einen Account bei [Clerk.dev](https://clerk.dev)
2. Erstellen Sie eine neue Application
3. Kopieren Sie die Keys in Ihre `.env` Datei
4. Installieren Sie Clerk: `npm install @clerk/nextjs`

In Ihrer `app/layout.tsx`:
```tsx
import { ClerkProvider } from '@clerk/nextjs';

export default function RootLayout({ children }) {
  return (
    <ClerkProvider>
      <html lang="de">
        <body>{children}</body>
      </html>
    </ClerkProvider>
  );
}
```

### Option 2: NextAuth

Falls Sie NextAuth bevorzugen, passen Sie `src/lib/auth.ts` entsprechend an.

## 🚀 Verwendung der Server Action

### In einem Client Component:

```tsx
'use client';

import { useState } from 'react';
import { createShiftRequest } from '@/actions/shift-request';
import { useRouter } from 'next/navigation';

export default function ShiftRequestForm() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setIsLoading(true);

    const formData = new FormData(e.currentTarget);
    const result = await createShiftRequest(formData);

    if (result.success) {
      alert('Dienstwunsch erfolgreich eingereicht!');
      router.push('/dashboard');
    } else {
      alert(result.error || 'Ein Fehler ist aufgetreten');
    }

    setIsLoading(false);
  }

  return (
    <form onSubmit={handleSubmit}>
      <input type="date" name="date" required />
      <select name="shiftType" required>
        <option value="">Bitte wählen...</option>
        <option value="Früh">Früh</option>
        <option value="Spät">Spät</option>
        <option value="Nacht">Nacht</option>
      </select>
      <textarea name="remarks" placeholder="Bemerkungen" />
      <button type="submit" disabled={isLoading}>
        {isLoading ? 'Wird gesendet...' : 'Einreichen'}
      </button>
    </form>
  );
}
```

### Mit React Hook Form und Zod:

```tsx
'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { shiftRequestSchema } from '@/lib/validations/shift-request';
import { createShiftRequest } from '@/actions/shift-request';

export default function ShiftRequestForm() {
  const { register, handleSubmit, formState: { errors } } = useForm({
    resolver: zodResolver(shiftRequestSchema),
  });

  const onSubmit = async (data) => {
    const result = await createShiftRequest(data);
    
    if (result.success) {
      // Erfolg behandeln
    } else {
      // Fehler behandeln
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      {/* Formularfelder */}
    </form>
  );
}
```

## 📊 Prisma Studio

Zum Verwalten der Daten in einer GUI:

```bash
npx prisma studio
```

Öffnet http://localhost:5555

## 🔄 Nützliche Prisma Befehle

```bash
# Neue Migration nach Schema-Änderung
npx prisma migrate dev --name beschreibung

# Prisma Client neu generieren
npx prisma generate

# Datenbank zurücksetzen (VORSICHT!)
npx prisma migrate reset

# Production-Migrations ausführen
npx prisma migrate deploy
```

## 🧪 Testing

Sie können die Server Action direkt testen:

```bash
# In einer Node.js Umgebung oder API Route
const result = await createShiftRequest({
  date: new Date('2026-01-20'),
  shiftType: 'Früh',
  remarks: 'Test'
});

console.log(result);
```

## 🔒 Sicherheit

- ✅ User-ID wird automatisch vom Server geholt (nicht vom Client)
- ✅ Validierung mit Zod auf Server-Seite
- ✅ Prisma schützt vor SQL-Injection
- ✅ 'use server' Direktive für Server Actions

## 📝 Weitere Features

Die Server Action enthält zusätzlich:

- `getUserShiftRequests()` - Alle Wünsche des Users abrufen
- `deleteShiftRequest(id)` - Dienstwunsch löschen

Siehe `src/actions/shift-request.ts` für Details.
