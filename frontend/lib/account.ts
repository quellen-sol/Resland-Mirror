// Account & Data page helpers — kept free of React and the API client so
// `node --test` can cover them.

/** What the user has to type before account deletion unlocks. */
export const DELETE_CONFIRMATION = "DELETE";

/** True once the confirmation box holds exactly DELETE_CONFIRMATION
 *  (surrounding spaces forgiven, case not). */
export function isDeleteConfirmed(typed: string): boolean {
  return typed.trim() === DELETE_CONFIRMATION;
}

/** The export's file name, matching what the API sends in
 *  Content-Disposition (UTC date): resland-data-YYYY-MM-DD.zip. */
export function exportFilename(now: Date): string {
  return `resland-data-${now.toISOString().slice(0, 10)}.zip`;
}

/** Whether a sign-in session belongs to an account that was deleted, given
 *  that account's account_deletion row. While Auth0 still has the old login
 *  (`auth0DeletedAt` null) every session does; after that, sessions created
 *  at or before that moment. A later sign-up with the same social login is a
 *  new account. `sessionCreatedAt` is epoch seconds (nextjs-auth0's
 *  `internal.createdAt`); missing counts as old. Mirrors the API's
 *  account.db.token_revoked. */
export function isRevokedByDeletion(
  sessionCreatedAt: number | undefined,
  auth0DeletedAt: Date | null,
): boolean {
  if (auth0DeletedAt === null || sessionCreatedAt === undefined) return true;
  // createdAt is whole seconds; the second Auth0 deleted the login counts as
  // old (a new sign-up can't happen that fast).
  return sessionCreatedAt <= Math.floor(auth0DeletedAt.getTime() / 1000);
}

/** The `detail` string from a FastAPI error body, or null when the body
 *  isn't one (a load balancer's HTML error page, a structured detail). */
export function apiErrorDetail(body: string): string | null {
  try {
    const parsed = JSON.parse(body) as { detail?: unknown } | null;
    const detail = parsed?.detail;
    return typeof detail === "string" && detail.trim() ? detail : null;
  } catch {
    return null;
  }
}
