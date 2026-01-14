import { auth } from '@clerk/nextjs/server';
// Alternative für next-auth:
// import { getServerSession } from 'next-auth';
// import { authOptions } from '@/app/api/auth/[...nextauth]/route';

/**
 * Holt die User-ID des aktuell eingeloggten Nutzers
 * 
 * @returns User-ID oder null wenn nicht eingeloggt
 * @throws Error wenn kein Nutzer eingeloggt ist (optional)
 */
export async function getCurrentUserId(): Promise<string> {
  // Variante 1: Mit Clerk
  const { userId } = await auth();
  
  if (!userId) {
    throw new Error('Nicht autorisiert. Bitte melden Sie sich an.');
  }
  
  return userId;
  
  /* Variante 2: Mit NextAuth
  const session = await getServerSession(authOptions);
  
  if (!session?.user?.id) {
    throw new Error('Nicht autorisiert. Bitte melden Sie sich an.');
  }
  
  return session.user.id;
  */
}

/**
 * Prüft ob ein Nutzer eingeloggt ist
 * 
 * @returns true wenn eingeloggt, sonst false
 */
export async function isAuthenticated(): Promise<boolean> {
  try {
    await getCurrentUserId();
    return true;
  } catch {
    return false;
  }
}
