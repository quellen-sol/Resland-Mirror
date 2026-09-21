"use client";

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
  "The Resland API is unavailable right now. Please try again in a moment.";

export function describeApiError(error: unknown): string {
  if (isApiUnreachable(error)) {
    return API_UNAVAILABLE_MESSAGE;
  }
  if (error instanceof ApiError) {
    if (error.status === 401)
      return "Your session expired — please sign in again.";
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

export async function apiFetch(
  accessToken: string,
  path: string,
  init?: RequestInit,
) {
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
  if (res.status === 204) return null;
  return res.json();
}

export interface PricedModel {
  id: string;
  display_name: string;
  cents_per_1k_input: number;
  cents_per_1k_output: number;
  is_default: boolean;
}

export function fmtCents(cents: number) {
  return (cents / 100).toLocaleString("en-US", {
    style: "currency",
    currency: "USD",
  });
}
