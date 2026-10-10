"use client";

import { filenameFromContentDisposition } from "./download";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export function isInsufficientBalance(error: unknown) {
  return error instanceof ApiError && error.status === 402;
}

export function isApiUnreachable(error: unknown) {
  return (
    error instanceof ApiError &&
    (error.status === 0 || (error.status >= 502 && error.status <= 504))
  );
}

const API_UNAVAILABLE_MESSAGE =
  "We can't reach Resland's servers right now. Please try again in a moment.";

export function describeApiError(error: unknown): string {
  if (isApiUnreachable(error)) {
    return API_UNAVAILABLE_MESSAGE;
  }
  if (error instanceof ApiError) {
    if (error.status === 401)
      return "Your session expired. Please sign in again.";
    if (error.status === 404) return "That no longer exists.";
    const message = error.message.trim();
    try {
      const parsed = JSON.parse(message) as { detail?: unknown };
      if (typeof parsed.detail === "string") return parsed.detail;
    } catch {}
    return message || "The request failed.";
  }
  if (error instanceof Error) {
    const name = error.name;
    const message = error.message.trim();
    if (
      error instanceof TypeError ||
      name === "TypeError" ||
      name === "AbortError" ||
      name === "TimeoutError" ||
      message === "Failed to fetch" ||
      message === "Load failed"
    ) {
      return API_UNAVAILABLE_MESSAGE;
    }
    return message;
  }
  return String(error);
}

async function apiRequest(
  accessToken: string,
  path: string,
  init?: RequestInit,
): Promise<Response> {
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
  if (!apiBaseUrl) {
    throw new ApiError(0, "API base URL is not configured");
  }
  let res: Response;
  try {
    res = await fetch(`${apiBaseUrl}${path}`, {
      ...init,
      signal: init?.signal ?? AbortSignal.timeout(20_000),
      headers: {
        Authorization: `Bearer ${accessToken}`,
        "Content-Type": "application/json",
        ...(init?.headers ?? {}),
      },
    });
  } catch (error) {
    const errorName = error instanceof Error ? error.name : "";
    if (errorName === "AbortError" || errorName === "TimeoutError") {
      throw new ApiError(0, "The request timed out");
    }
    throw new ApiError(0, "Can't reach the Resland API");
  }
  if (!res.ok) throw new ApiError(res.status, await res.text());
  return res;
}

export async function apiFetch(
  accessToken: string,
  path: string,
  init?: RequestInit,
) {
  const res = await apiRequest(accessToken, path, init);
  if (res.status === 204) return null;
  return res.json();
}

/** GET a binary response (e.g. the data export) and hand it to the browser
 *  as a file download. Uses the server's Content-Disposition name when it's
 *  readable, else `fallbackFilename`; returns the name used. */
export async function apiDownload(
  accessToken: string,
  path: string,
  fallbackFilename: string,
  timeoutMs = 120_000,
): Promise<string> {
  const res = await apiRequest(accessToken, path, {
    signal: AbortSignal.timeout(timeoutMs),
  });
  const blob = await res.blob();
  const filename = filenameFromContentDisposition(
    res.headers.get("Content-Disposition"),
    fallbackFilename,
  );
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  // Revoking right away can cancel the download in some browsers.
  setTimeout(() => URL.revokeObjectURL(url), 60_000);
  return filename;
}

export interface ModelActionCost {
  job_kind: "SUGGESTION" | "TAILOR" | "SYSTEM_DESIGN";
  avg_cents: number;
}

export interface PricedModel {
  id: string;
  display_name: string;
  cents_per_1k_input: number;
  cents_per_1k_output: number;
  is_default: boolean;
  action_costs: ModelActionCost[];
}

export function fmtCents(cents: number) {
  return (cents / 100).toLocaleString("en-US", {
    style: "currency",
    currency: "USD",
  });
}
