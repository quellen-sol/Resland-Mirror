"use client";

import { useMemo, useState, useTransition } from "react";
import { Brain, Check, Loader2, PenLine, Plus, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  MAX_FACT_CHARS,
  MAX_MEMORY_FACTS,
  MAX_TOPIC_CHARS,
  SOURCE_LABELS,
  groupFactsByTopic,
  type MemoryFact,
} from "@/lib/memory";
import {
  addMemoryFact,
  deleteMemoryFact,
  updateMemoryFact,
  type FactResult,
} from "./actions";

const fieldClass =
  "border-zinc-700 bg-zinc-950/50 text-zinc-200 placeholder:text-zinc-600 focus-visible:border-brand-500 focus-visible:ring-brand-500/30";

const TOPICS_LIST_ID = "memory-topics";

export default function MemoryBank({
  initial,
  jobTopics,
}: {
  initial: MemoryFact[];
  jobTopics: string[];
}) {
  const [facts, setFacts] = useState(initial);
  const [topic, setTopic] = useState("");
  const [content, setContent] = useState("");
  const [editing, setEditing] = useState<MemoryFact | null>(null);
  const [pending, startTransition] = useTransition();

  const groups = useMemo(() => groupFactsByTopic(facts), [facts]);
  // Suggest the topics the agents file facts under, so typed facts land
  // beside learned ones.
  const topicOptions = useMemo(
    () =>
      [
        ...new Set([
          ...jobTopics,
          ...facts.map((f) => f.topic),
          "Preferences",
          "General",
        ]),
      ].sort((a, b) => a.localeCompare(b)),
    [jobTopics, facts],
  );
  const full = facts.length >= MAX_MEMORY_FACTS;

  function save(
    action: () => Promise<FactResult>,
    onSaved: (fact: MemoryFact) => void,
  ) {
    startTransition(async () => {
      try {
        const res = await action();
        if (!res.ok) {
          toast.error(res.error);
          return;
        }
        onSaved(res.fact);
      } catch {
        toast.error("Couldn't save that fact. Please try again.");
      }
    });
  }

  function add() {
    save(
      () => addMemoryFact(topic, content),
      (fact) => {
        setFacts((prev) => [...prev, fact]);
        // Keep the topic: facts often come in runs about one job.
        setContent("");
      },
    );
  }

  function saveEdit() {
    if (!editing) return;
    const draft = editing;
    save(
      () => updateMemoryFact(draft.id, draft.topic, draft.content),
      (fact) => {
        setFacts((prev) => prev.map((f) => (f.id === fact.id ? fact : f)));
        setEditing(null);
      },
    );
  }

  function remove(id: number) {
    startTransition(async () => {
      try {
        await deleteMemoryFact(id);
        setFacts((prev) => prev.filter((f) => f.id !== id));
        setEditing((e) => (e?.id === id ? null : e));
      } catch {
        toast.error("Couldn't delete that fact. Please try again.");
      }
    });
  }

  return (
    <>
      <datalist id={TOPICS_LIST_ID}>
        {topicOptions.map((t) => (
          <option key={t} value={t} />
        ))}
      </datalist>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Add a fact</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          <Input
            list={TOPICS_LIST_ID}
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            maxLength={MAX_TOPIC_CHARS}
            aria-label="Topic"
            placeholder="Topic: a job like “Engineer at Acme”, a project, or Preferences"
            className={fieldClass}
          />
          <Textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            maxLength={MAX_FACT_CHARS}
            rows={3}
            aria-label="Fact"
            placeholder="One fact, with the numbers. For example: “The order sync service handled about 2M events a day.”"
            className={fieldClass}
          />
          <div className="flex items-center justify-between gap-3">
            <p className="text-xs text-zinc-500">
              {facts.length} of {MAX_MEMORY_FACTS} facts
            </p>
            <Button
              onClick={add}
              disabled={pending || full || !topic.trim() || !content.trim()}
            >
              <Plus /> Add fact
            </Button>
          </div>
        </CardContent>
      </Card>

      {groups.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center gap-3 py-12 text-center">
            <Brain className="size-8 text-zinc-600" />
            <p className="text-sm text-zinc-400">
              Nothing here yet. When you answer questions while tailoring your
              resume or improving bullets, the facts you give show up here.
            </p>
          </CardContent>
        </Card>
      ) : (
        groups.map((group) => (
          <Card key={group.topic}>
            <CardHeader>
              <CardTitle className="text-base">{group.topic}</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="flex flex-col divide-y divide-zinc-800">
                {group.facts.map((fact) =>
                  editing?.id === fact.id ? (
                    <li
                      key={fact.id}
                      className="flex flex-col gap-2 py-3 first:pt-0 last:pb-0"
                    >
                      <Input
                        list={TOPICS_LIST_ID}
                        value={editing.topic}
                        onChange={(e) =>
                          setEditing({ ...editing, topic: e.target.value })
                        }
                        maxLength={MAX_TOPIC_CHARS}
                        aria-label="Topic"
                        className={fieldClass}
                      />
                      <Textarea
                        value={editing.content}
                        onChange={(e) =>
                          setEditing({ ...editing, content: e.target.value })
                        }
                        maxLength={MAX_FACT_CHARS}
                        rows={3}
                        aria-label="Fact"
                        className={fieldClass}
                      />
                      <div className="flex justify-end gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setEditing(null)}
                          className="border-zinc-700 text-zinc-300 hover:bg-zinc-800"
                        >
                          Cancel
                        </Button>
                        <Button size="sm" onClick={saveEdit} disabled={pending}>
                          {pending ? <Loader2 className="animate-spin" /> : <Check />}
                          Save
                        </Button>
                      </div>
                    </li>
                  ) : (
                    <li
                      key={fact.id}
                      className="flex items-start gap-2 py-3 first:pt-0 last:pb-0"
                    >
                      <div className="min-w-0 flex-1">
                        <p className="text-sm whitespace-pre-wrap text-zinc-200">
                          {fact.content}
                        </p>
                        <p className="mt-1 text-xs text-zinc-500">
                          {SOURCE_LABELS[fact.source]}
                        </p>
                      </div>
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        aria-label="Edit fact"
                        title="Edit"
                        onClick={() => setEditing(fact)}
                        className="text-zinc-400"
                      >
                        <PenLine />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        aria-label="Delete fact"
                        title="Delete"
                        onClick={() => remove(fact.id)}
                        disabled={pending}
                        className="text-zinc-400 hover:text-red-300"
                      >
                        <Trash2 />
                      </Button>
                    </li>
                  ),
                )}
              </ul>
            </CardContent>
          </Card>
        ))
      )}
    </>
  );
}
