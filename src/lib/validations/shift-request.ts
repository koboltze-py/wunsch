import { z } from 'zod';

/**
 * Zod Schema für die Validierung von Dienstwunsch-Formulardaten
 */
export const shiftRequestSchema = z.object({
  date: z.coerce.date({
    required_error: 'Bitte wählen Sie ein Datum aus',
    invalid_type_error: 'Ungültiges Datumsformat',
  }).refine((date) => {
    // Datum darf nicht in der Vergangenheit liegen
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    return date >= today;
  }, {
    message: 'Das Datum darf nicht in der Vergangenheit liegen',
  }),
  
  shiftType: z.enum(['Früh', 'Spät', 'Nacht'], {
    required_error: 'Bitte wählen Sie eine Schichtart aus',
    invalid_type_error: 'Ungültige Schichtart',
  }),
  
  remarks: z.string().max(500, {
    message: 'Bemerkungen dürfen maximal 500 Zeichen lang sein',
  }).optional().nullable(),
});

/**
 * TypeScript Type aus dem Zod Schema
 */
export type ShiftRequestInput = z.infer<typeof shiftRequestSchema>;
