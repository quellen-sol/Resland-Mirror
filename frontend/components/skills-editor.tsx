"use client";

import { useRef, useState } from "react";
import { ArrowDown, ArrowUp, GripVertical, Plus, Trash2 } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { cn } from "cn";
import type { SkillGroupForm } from "@/lib/skills";
import { newGroupId, ungroupedGroup } from "@/lib/skills";

const inputCls =
  "border-zinc-700 bg-zinc-950/50 text-zinc-200 placeholder:text-zinc-600 focus-visible:border-purple-500 focus-visible:ring-purple-500/30";

const chipCls =
  "inline-flex items-center gap-1.5 rounded-md border border-purple-500/30 bg-purple-500/10 px-2 py-0.5 text-sm text-purple-200";

type DragPayload =
  | { kind: "skill"; group: number; index: number }
  | { kind: "group"; group: number };

// Where a drop would land: before chip `index` in `group`, or at the end of
// `group` when index is null, or before `group` when dragging a group.
type DropTarget = { group: number; index: number | null };

function insertAt<T>(items: T[], index: number, item: T): T[] {
  return [...items.slice(0, index), item, ...items.slice(index)];
}

export default function SkillsEditor({
  groups,
  onChange,
}: {
  groups: SkillGroupForm[];
  onChange: (groups: SkillGroupForm[]) => void;
}) {
  const [drag, setDrag] = useState<DragPayload | null>(null);
  const [dropTarget, setDropTarget] = useState<DropTarget | null>(null);
  const [drafts, setDrafts] = useState<Record<string, string>>({});
  const groupEls = useRef<(HTMLDivElement | null)[]>([]);

  function moveSkill(fromG: number, fromI: number, toG: number, toI: number) {
    // toI is an insert-before position measured on the pre-removal list.
    const skill = groups[fromG].skills[fromI];
    if (fromG === toG && fromI === toI - 1) return; // dropped after itself
    const next = groups.map((g) => ({ ...g, skills: [...g.skills] }));
    next[fromG].skills.splice(fromI, 1);
    const adjusted = fromG === toG && fromI < toI ? toI - 1 : toI;
    next[toG].skills.splice(adjusted, 0, skill);
    onChange(next);
  }

  function moveGroup(from: number, to: number) {
    if (from === to || from === to - 1) return; // already in place
    const next = groups.map((g) => ({ ...g, skills: [...g.skills] }));
    const [moved] = next.splice(from, 1);
    next.splice(from < to ? to - 1 : to, 0, moved);
    onChange(next);
  }

  function handleDrop(target: DropTarget) {
    if (!drag) return;
    if (drag.kind === "skill") {
      const toG = Math.min(target.group, groups.length - 1);
      const index = target.index ?? groups[toG].skills.length;
      moveSkill(drag.group, drag.index, toG, index);
    } else {
      moveGroup(drag.group, target.group);
    }
    setDrag(null);
    setDropTarget(null);
  }

  function addSkill(groupIdx: number) {
    const group = groups[groupIdx];
    const name = (drafts[group.id] ?? "").trim();
    if (!name) return;
    if (groups.some((g) => g.skills.includes(name))) return;
    onChange(
      groups.map((g, i) =>
        i === groupIdx ? { ...g, skills: [...g.skills, name] } : g,
      ),
    );
    setDrafts((d) => ({ ...d, [group.id]: "" }));
  }

  // Removing a category never deletes its skills — they land in Ungrouped,
  // created at the removed group's slot when none exists.
  function removeGroup(groupIdx: number) {
    const removed = groups[groupIdx];
    const rest = groups.filter((_, i) => i !== groupIdx);
    if (rest.length === 0) {
      onChange([ungroupedGroup()]);
      return;
    }
    const ungroupedIdx = rest.findIndex((g) => g.category === null);
    if (removed.skills.length === 0) {
      onChange(rest);
    } else if (ungroupedIdx >= 0) {
      onChange(
        rest.map((g, i) =>
          i === ungroupedIdx
            ? { ...g, skills: [...g.skills, ...removed.skills] }
            : g,
        ),
      );
    } else {
      onChange(
        insertAt(rest, groupIdx, {
          ...ungroupedGroup(),
          skills: removed.skills,
        }),
      );
    }
  }

  function renameGroup(groupIdx: number, name: string) {
    onChange(
      groups.map((g, i) => (i === groupIdx ? { ...g, category: name } : g)),
    );
  }

  function removeSkill(groupIdx: number, skillIdx: number) {
    onChange(
      groups.map((g, i) =>
        i === groupIdx
          ? { ...g, skills: g.skills.filter((_, j) => j !== skillIdx) }
          : g,
      ),
    );
  }

  function swapGroup(i: number, j: number) {
    const next = groups.map((g) => ({ ...g, skills: [...g.skills] }));
    [next[i], next[j]] = [next[j], next[i]];
    onChange(next);
  }

  function groupDragOver(e: React.DragEvent, gi: number, index: number | null) {
    if (!drag) return;
    e.preventDefault();
    e.stopPropagation();
    setDropTarget({ group: gi, index });
  }

  const singleUngrouped =
    groups.length === 1 && groups[0].category === null;

  return (
    <div className="flex flex-col gap-3">
      {groups.map((group, gi) => (
        <div
          key={group.id}
          ref={(el) => {
            groupEls.current[gi] = el;
          }}
          onDragOver={(e) => {
            // Not over a chip or the header: append skills to this group,
            // or move the dragged group before this one.
            if (drag) groupDragOver(e, gi, null);
          }}
          onDrop={(e) => {
            e.preventDefault();
            e.stopPropagation();
            handleDrop({ group: gi, index: null });
          }}
          className={cn(
            "rounded-lg",
            singleUngrouped
              ? ""
              : "border border-zinc-800 bg-zinc-950/40 p-3",
            dropTarget?.group === gi &&
              dropTarget.index === null &&
              drag?.kind === "skill" &&
              "ring-1 ring-purple-500/60",
          )}
        >
          {!singleUngrouped && (
            <div
              onDragOver={(e) => groupDragOver(e, gi, null)}
              onDrop={(e) => {
                e.preventDefault();
                e.stopPropagation();
                handleDrop({ group: gi, index: null });
              }}
              className={cn(
                "mb-2 flex items-center gap-1",
                dropTarget?.group === gi &&
                  drag?.kind === "group" &&
                  "rounded ring-1 ring-purple-500/60",
              )}
            >
              <button
                type="button"
                draggable
                onDragStart={(e) => {
                  setDrag({ kind: "group", group: gi });
                  const el = groupEls.current[gi];
                  if (el)
                    e.dataTransfer.setDragImage(el, 8, 8);
                  e.dataTransfer.effectAllowed = "move";
                }}
                onDragEnd={() => {
                  setDrag(null);
                  setDropTarget(null);
                }}
                className="cursor-grab text-zinc-500 hover:text-zinc-300"
                aria-label="Drag to Reorder Category"
              >
                <GripVertical className="size-4" />
              </button>
              {group.category === null ? (
                <span className="text-xs font-medium tracking-wide text-zinc-500 uppercase">
                  Ungrouped
                </span>
              ) : (
                <Input
                  value={group.category}
                  onChange={(e) => renameGroup(gi, e.target.value)}
                  placeholder="Category name"
                  aria-label="Category name"
                  className={cn(inputCls, "h-7 flex-1 text-sm")}
                />
              )}
              <button
                type="button"
                disabled={gi === 0}
                onClick={() => swapGroup(gi, gi - 1)}
                className="text-zinc-500 hover:text-zinc-200 disabled:cursor-default disabled:opacity-30 disabled:hover:text-zinc-500"
                aria-label="Move Category Up"
              >
                <ArrowUp className="size-4" />
              </button>
              <button
                type="button"
                disabled={gi === groups.length - 1}
                onClick={() => swapGroup(gi, gi + 1)}
                className="text-zinc-500 hover:text-zinc-200 disabled:cursor-default disabled:opacity-30 disabled:hover:text-zinc-500"
                aria-label="Move Category Down"
              >
                <ArrowDown className="size-4" />
              </button>
              {group.category !== null && (
                <button
                  type="button"
                  onClick={() => removeGroup(gi)}
                  className="text-zinc-500 hover:text-red-400"
                  aria-label={`Remove Category ${group.category}`}
                  title="Remove category — its skills move to Ungrouped"
                >
                  <Trash2 className="size-4" />
                </button>
              )}
            </div>
          )}
          <div className="flex flex-wrap items-center gap-2">
            {group.skills.map((skill, si) => (
              <span
                key={skill}
                draggable
                onDragStart={(e) => {
                  e.stopPropagation();
                  setDrag({ kind: "skill", group: gi, index: si });
                  e.dataTransfer.effectAllowed = "move";
                }}
                onDragEnd={() => {
                  setDrag(null);
                  setDropTarget(null);
                }}
                onDragOver={(e) => groupDragOver(e, gi, si)}
                onDrop={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  handleDrop({ group: gi, index: si });
                }}
                className={cn(
                  chipCls,
                  "cursor-grab",
                  dropTarget?.group === gi &&
                    dropTarget.index === si &&
                    "ring-1 ring-purple-400",
                )}
              >
                {skill}
                <button
                  type="button"
                  onClick={() => removeSkill(gi, si)}
                  className="text-purple-300/60 hover:text-purple-200"
                  aria-label={`Remove ${skill}`}
                >
                  ×
                </button>
              </span>
            ))}
            <Input
              value={drafts[group.id] ?? ""}
              onChange={(e) =>
                setDrafts((d) => ({ ...d, [group.id]: e.target.value }))
              }
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  addSkill(gi);
                }
              }}
              onBlur={() => addSkill(gi)}
              placeholder={
                group.skills.length === 0
                  ? "Add a skill — press Enter"
                  : "+ skill"
              }
              className={cn(inputCls, "h-7 w-36 text-sm")}
            />
          </div>
        </div>
      ))}
      {drag?.kind === "group" && (
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setDropTarget({ group: groups.length, index: null });
          }}
          onDrop={(e) => {
            e.preventDefault();
            handleDrop({ group: groups.length, index: null });
          }}
          className={cn(
            "rounded-lg border border-dashed border-zinc-700 px-3 py-2 text-center text-xs text-zinc-500",
            dropTarget?.group === groups.length &&
              "border-purple-500/60 text-purple-300",
          )}
        >
          Drop here to move to the end
        </div>
      )}
      <div>
        <Button
          type="button"
          variant="outline"
          className="border-zinc-700 text-zinc-300 hover:bg-zinc-800"
          onClick={() =>
            onChange([
              ...groups,
              { id: newGroupId(), category: "", skills: [] },
            ])
          }
        >
          <Plus /> Add Category
        </Button>
      </div>
      {groups.length > 1 && (
        <p className="text-xs text-zinc-500">
          Drag skills between categories, or drag a category&apos;s grip to
          reorder it.
        </p>
      )}
    </div>
  );
}
