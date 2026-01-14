'use server';

import { revalidatePath } from 'next/cache';
import { prisma } from '@/lib/prisma';
import { getCurrentUserId } from '@/lib/auth';
import { shiftRequestSchema, type ShiftRequestInput } from '@/lib/validations/shift-request';

/**
 * Response Type für die Server Action
 */
type ActionResponse<T = unknown> = {
  success: boolean;
  data?: T;
  error?: string;
  fieldErrors?: Record<string, string[]>;
};

/**
 * Server Action: Erstellt einen neuen Dienstwunsch
 * 
 * @param formData - FormData aus dem Formular oder direkte Daten
 * @returns ActionResponse mit Erfolg oder Fehler
 * 
 * @example
 * // Verwendung in einem Client Component:
 * const result = await createShiftRequest(formData);
 * if (result.success) {
 *   toast.success('Dienstwunsch erfolgreich eingereicht!');
 * }
 */
export async function createShiftRequest(
  formData: FormData | ShiftRequestInput
): Promise<ActionResponse<{ id: string }>> {
  try {
    // 1. User-ID des eingeloggten Nutzers holen
    const userId = await getCurrentUserId();

    // 2. FormData in Objekt umwandeln (falls FormData übergeben wurde)
    let data: unknown;
    
    if (formData instanceof FormData) {
      data = {
        date: formData.get('date'),
        shiftType: formData.get('shiftType'),
        remarks: formData.get('remarks') || null,
      };
    } else {
      data = formData;
    }

    // 3. Daten mit Zod validieren
    const validationResult = shiftRequestSchema.safeParse(data);

    if (!validationResult.success) {
      // Validierungsfehler zurückgeben
      return {
        success: false,
        error: 'Validierungsfehler. Bitte überprüfen Sie Ihre Eingaben.',
        fieldErrors: validationResult.error.flatten().fieldErrors as Record<string, string[]>,
      };
    }

    const validatedData = validationResult.data;

    // 4. In Datenbank speichern mit Prisma
    const shiftRequest = await prisma.shiftRequest.create({
      data: {
        userId,
        date: validatedData.date,
        shiftType: validatedData.shiftType,
        remarks: validatedData.remarks,
        status: 'PENDING', // Standardstatus
      },
      select: {
        id: true,
        date: true,
        shiftType: true,
        status: true,
        createdAt: true,
      },
    });

    // 5. Cache revalidieren (optional - für Server Components)
    revalidatePath('/dienstwuensche');
    revalidatePath('/dashboard');

    // 6. Erfolgreiche Response zurückgeben
    return {
      success: true,
      data: { id: shiftRequest.id },
    };

  } catch (error) {
    // Fehlerbehandlung
    console.error('Fehler beim Erstellen des Dienstwunsches:', error);

    // Spezifische Fehler behandeln
    if (error instanceof Error) {
      // Auth-Fehler
      if (error.message.includes('Nicht autorisiert')) {
        return {
          success: false,
          error: 'Sie müssen angemeldet sein, um einen Dienstwunsch einzureichen.',
        };
      }

      // Prisma Unique Constraint Fehler (z.B. doppelter Eintrag)
      if (error.message.includes('Unique constraint')) {
        return {
          success: false,
          error: 'Sie haben bereits einen Dienstwunsch für dieses Datum eingereicht.',
        };
      }
    }

    // Generischer Fehler
    return {
      success: false,
      error: 'Ein unerwarteter Fehler ist aufgetreten. Bitte versuchen Sie es später erneut.',
    };
  }
}

/**
 * Server Action: Holt alle Dienstwünsche des aktuellen Nutzers
 * 
 * @param options - Optionen für Filterung und Sortierung
 * @returns ActionResponse mit Liste der Dienstwünsche
 */
export async function getUserShiftRequests(options?: {
  status?: 'PENDING' | 'APPROVED' | 'REJECTED';
  limit?: number;
}): Promise<ActionResponse<unknown[]>> {
  try {
    // User-ID holen
    const userId = await getCurrentUserId();

    // Dienstwünsche abrufen
    const shiftRequests = await prisma.shiftRequest.findMany({
      where: {
        userId,
        ...(options?.status && { status: options.status }),
      },
      orderBy: {
        date: 'desc',
      },
      take: options?.limit,
      select: {
        id: true,
        date: true,
        shiftType: true,
        remarks: true,
        status: true,
        createdAt: true,
        updatedAt: true,
      },
    });

    return {
      success: true,
      data: shiftRequests,
    };

  } catch (error) {
    console.error('Fehler beim Abrufen der Dienstwünsche:', error);
    
    return {
      success: false,
      error: 'Dienstwünsche konnten nicht geladen werden.',
    };
  }
}

/**
 * Server Action: Löscht einen Dienstwunsch
 * 
 * @param id - ID des zu löschenden Dienstwunsches
 * @returns ActionResponse
 */
export async function deleteShiftRequest(id: string): Promise<ActionResponse> {
  try {
    // User-ID holen
    const userId = await getCurrentUserId();

    // Prüfen ob der Dienstwunsch dem User gehört
    const shiftRequest = await prisma.shiftRequest.findUnique({
      where: { id },
      select: { userId: true, status: true },
    });

    if (!shiftRequest) {
      return {
        success: false,
        error: 'Dienstwunsch nicht gefunden.',
      };
    }

    if (shiftRequest.userId !== userId) {
      return {
        success: false,
        error: 'Sie sind nicht berechtigt, diesen Dienstwunsch zu löschen.',
      };
    }

    // Nur ausstehende Wünsche können gelöscht werden
    if (shiftRequest.status !== 'PENDING') {
      return {
        success: false,
        error: 'Nur ausstehende Dienstwünsche können gelöscht werden.',
      };
    }

    // Löschen
    await prisma.shiftRequest.delete({
      where: { id },
    });

    // Cache revalidieren
    revalidatePath('/dienstwuensche');

    return {
      success: true,
    };

  } catch (error) {
    console.error('Fehler beim Löschen des Dienstwunsches:', error);
    
    return {
      success: false,
      error: 'Dienstwunsch konnte nicht gelöscht werden.',
    };
  }
}
