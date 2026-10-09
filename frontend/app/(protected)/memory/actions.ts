"use server";

import { Temporal } from "temporal-polyfill";
import { getUser } from "@/lib/db";
import {
  MAX_MEMORY_FACTS,
  parseFactInput,
  type MemoryFact,
} from "@/lib/memory";
import { db } from "@/prisma/db";

export type FactResult =
  | { ok: true; fact: MemoryFact }
  | { ok: false; error: string };

async function requireUserId() {
  const user = await getUser();
  if (!user) throw new Error("Unauthorized");
  return user.auth0_id;
}

function toFact(row: {
  id: number;
  topic: string;
  content: string;
  source: MemoryFact["source"];
}): MemoryFact {
  // Plain fields only — the row's Temporal timestamps can't cross to the
  // client.
  return {
    id: row.id,
    topic: row.topic,
    content: row.content,
    source: row.source,
  };
}

export async function addMemoryFact(
  topic: string,
  content: string,
): Promise<FactResult> {
  const userId = await requireUserId();
  const input = parseFactInput(topic, content);
  if (!input.ok) return input;

  const { count } = await db.orm.public.UserMemoryFact.where((f) =>
    f.user_id.eq(userId),
  ).aggregate((a) => ({ count: a.count() }));
  if (count >= MAX_MEMORY_FACTS) {
    return {
      ok: false,
      error: `Memory holds up to ${MAX_MEMORY_FACTS} facts. Delete or merge some first.`,
    };
  }

  const row = await db.orm.public.UserMemoryFact.create({
    user_id: userId,
    topic: input.topic,
    content: input.content,
    source: "USER",
  });
  return { ok: true, fact: toFact(row) };
}

export async function updateMemoryFact(
  id: number,
  topic: string,
  content: string,
): Promise<FactResult> {
  const userId = await requireUserId();
  const input = parseFactInput(topic, content);
  if (!input.ok) return input;

  // Scoped to the signed-in user, so another user's id matches nothing.
  const row = await db.orm.public.UserMemoryFact.where({
    id,
    user_id: userId,
  }).update({
    topic: input.topic,
    content: input.content,
    updated_at: Temporal.Now.instant(),
  });
  if (!row) return { ok: false, error: "That fact no longer exists." };
  return { ok: true, fact: toFact(row) };
}

export async function deleteMemoryFact(id: number): Promise<void> {
  const userId = await requireUserId();
  await db.orm.public.UserMemoryFact.where({ id, user_id: userId }).deleteAll();
}
