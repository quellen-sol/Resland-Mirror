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

export async function apiFetch(
  accessToken: string,
  path: string,
  init?: RequestInit,
) {
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
  const res = await fetch(`${apiBaseUrl}${path}`, {
    ...init,
    headers: {
      Authorization: `Bearer ${accessToken}`,
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });
  if (!res.ok) throw new ApiError(res.status, await res.text());
  if (res.status === 204) return null;
  return res.json();
}

export interface PricedModel {
  id: string;
  display_name: string;
  cents_per_1k_input: number;
  cents_per_1k_output: number;
}

export function fmtCents(cents: number) {
  return (cents / 100).toLocaleString("en-US", {
    style: "currency",
    currency: "USD",
  });
}
