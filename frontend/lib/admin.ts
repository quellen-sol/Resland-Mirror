import { NextResponse } from "next/server";
import { getUser } from "./db";

/** The signed-in user if they're a site admin, else null. */
export async function requireAdmin() {
  const user = await getUser();
  return user?.site_admin ? user : null;
}

/** Admin routes are hidden like the /admin page itself: pretend they don't
 *  exist. */
export function hidden() {
  return NextResponse.json({ detail: "Not found" }, { status: 404 });
}
