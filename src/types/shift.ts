export type ShiftType = 'Früh' | 'Spät' | 'Nacht';

export interface ShiftRequest {
  date: Date | null;
  shiftType: ShiftType | '';
  remarks: string;
}
