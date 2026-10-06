// Account & Data page helpers — kept free of React and the API client so
// `node --test` can cover them.

/** What the user has to type before account deletion unlocks. */
export const DELETE_CONFIRMATION = "DELETE";

/** True once the confirmation box holds exactly DELETE_CONFIRMATION
 *  (surrounding spaces forgiven, case not). */
export function isDeleteConfirmed(typed: string): boolean {
  throw new Error("not implemented");
}

/** The export's file name, matching what the API sends in
 *  Content-Disposition (UTC date): resland-data-YYYY-MM-DD.zip. */
export function exportFilename(now: Date): string {
  throw new Error("not implemented");
}

/** The `detail` string from a FastAPI error body, or null when the body
 *  isn't one (a load balancer's HTML error page, a structured detail). */
export function apiErrorDetail(body: string): string | null {
  throw new Error("not implemented");
}
