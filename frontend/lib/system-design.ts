// System design mock interview — shared types, labels, and pure helpers for
// the interview room and the report. Mirrors shared.system_design (Python).

export type Phase =
  | "REQUIREMENTS"
  | "ESTIMATION"
  | "HIGH_LEVEL_DESIGN"
  | "DEEP_DIVE"
  | "FEEDBACK";

export const PHASES: Phase[] = [
  "REQUIREMENTS",
  "ESTIMATION",
  "HIGH_LEVEL_DESIGN",
  "DEEP_DIVE",
  "FEEDBACK",
];

export const PHASE_LABELS: Record<Phase, string> = {
  REQUIREMENTS: "Requirements",
  ESTIMATION: "Estimation",
  HIGH_LEVEL_DESIGN: "High-Level Design",
  DEEP_DIVE: "Deep Dive",
  FEEDBACK: "Feedback",
};

export type Level = "MID" | "SENIOR" | "STAFF";

export const LEVEL_LABELS: Record<Level, string> = {
  MID: "Mid-Level",
  SENIOR: "Senior",
  STAFF: "Staff",
};

export type HireSignal = "STRONG_HIRE" | "HIRE" | "LEAN_NO_HIRE" | "NO_HIRE";

export const HIRE_SIGNAL_LABELS: Record<HireSignal, string> = {
  STRONG_HIRE: "Strong Hire",
  HIRE: "Hire",
  LEAN_NO_HIRE: "Lean No Hire",
  NO_HIRE: "No Hire",
};

export type ComponentKind =
  | "client"
  | "cdn"
  | "load_balancer"
  | "api_gateway"
  | "service"
  | "worker"
  | "cache"
  | "database"
  | "queue"
  | "blob_store"
  | "search"
  | "other";

export interface PaletteItem {
  kind: ComponentKind;
  label: string;
  shape: "rectangle" | "ellipse" | "diamond";
  color: string;
}

// Components the candidate can drop on the canvas. Each carries
// customData.kind so the interviewer knows what a box is, not just its label.
export const COMPONENT_PALETTE: PaletteItem[] = [
  { kind: "client", label: "Client", shape: "rectangle", color: "#a5d8ff" },
  { kind: "cdn", label: "CDN", shape: "rectangle", color: "#d0bfff" },
  { kind: "load_balancer", label: "Load Balancer", shape: "diamond", color: "#ffd8a8" },
  { kind: "api_gateway", label: "API Gateway", shape: "rectangle", color: "#ffd8a8" },
  { kind: "service", label: "Service", shape: "rectangle", color: "#b2f2bb" },
  { kind: "worker", label: "Worker", shape: "rectangle", color: "#b2f2bb" },
  { kind: "cache", label: "Cache", shape: "rectangle", color: "#ffc9c9" },
  { kind: "database", label: "Database", shape: "ellipse", color: "#99e9f2" },
  { kind: "queue", label: "Queue", shape: "rectangle", color: "#fcc2d7" },
  { kind: "blob_store", label: "Blob Storage", shape: "ellipse", color: "#e9ecef" },
  { kind: "search", label: "Search Index", shape: "rectangle", color: "#eebefa" },
];

export interface ProblemSummary {
  id: string;
  title: string;
  difficulty: "EASY" | "MEDIUM" | "HARD";
  tags: string[];
  summary: string;
}

export interface InterviewMessage {
  id: number;
  role: "INTERVIEWER" | "CANDIDATE";
  phase: Phase;
  content: string;
  created_at: string;
}

export interface DimensionResult {
  key: string;
  label: string;
  weight: number;
  score: number;
  evidence: string;
  feedback: string;
}

export interface DiagramComment {
  ref: string;
  element_id: string;
  label: string;
  comment: string;
}

export interface GradeReport {
  letter_grade: string;
  hire_signal: HireSignal;
  weighted_score: number;
  level: Level;
  dimensions: DimensionResult[];
  summary: string;
  strengths: string[];
  improvements: string[];
  study_topics: string[];
  diagram_comments: DiagramComment[];
  phase_durations: Partial<Record<Phase, number>>;
}

export interface RefComponent {
  id: string;
  kind: ComponentKind;
  label: string;
  purpose: string;
}

export interface RefConnection {
  source: string;
  target: string;
  label: string;
}

export interface ReferenceBrief {
  title: string;
  prompt: string;
  clarifications: { topic: string; answer: string }[];
  functional_requirements: string[];
  non_functional_requirements: string[];
  estimation_notes: string[];
  reference_components: RefComponent[];
  reference_connections: RefConnection[];
  deep_dive_topics: string[];
  pitfalls: string[];
}

export type SessionStatusValue =
  | "PROCESSING"
  | "WAITING_FOR_INPUT"
  | "COMPLETED"
  | "FAILED";

export interface SessionStatus {
  session_id: string;
  status: SessionStatusValue;
  phase: Phase;
  source: "BANK" | "JOB";
  level: Level;
  problem_id: string | null;
  company_name: string | null;
  role: string | null;
  title: string | null;
  prompt: string | null;
  notice: string | null;
  phase_started_at: string;
  created_at: string;
  completed_at: string | null;
  server_time: string;
  phase_durations: Partial<Record<Phase, number>>;
  phase_targets: Partial<Record<Phase, number>>;
  messages: InterviewMessage[];
  letter_grade: string | null;
  hire_signal: HireSignal | null;
  result: GradeReport | null;
  reference: ReferenceBrief | null;
}

export interface DiagramIssue {
  kind: "dangling_arrow" | "line" | "orphan_node";
  element_id: string;
  message: string;
}

export interface Workspace {
  diagram: string;
  requirements: string;
  estimates: string;
  issues: DiagramIssue[];
}

export interface LayoutBox {
  id: string;
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface DimensionAverage {
  key: string;
  label: string;
  average: number;
  count: number;
}

// Rubric dimension order (shared.system_design.rubric.DIMENSIONS).
export const RUBRIC_ORDER = [
  "requirements",
  "estimation",
  "high_level_design",
  "deep_dive",
  "communication",
  "time_management",
];

const NODE_WIDTH = 190;
const NODE_HEIGHT = 74;
// Wide enough for a short arrow label between columns.
const COLUMN_GAP = 190;
const ROW_GAP = 46;

/** 0:45 / 6:05 / 1:02:03 — a running clock. */
export function fmtClock(seconds: number): string {
  const total = Math.max(0, Math.floor(seconds));
  const h = Math.floor(total / 3600);
  const m = Math.floor((total % 3600) / 60);
  const s = String(total % 60).padStart(2, "0");
  return h ? `${h}:${String(m).padStart(2, "0")}:${s}` : `${m}:${s}`;
}

export function nextPhase(phase: Phase): Phase | null {
  const i = PHASES.indexOf(phase);
  return i >= 0 && i + 1 < PHASES.length ? PHASES[i + 1] : null;
}

/** The button that moves the candidate on, or null where they can't. */
export function advanceLabel(phase: Phase): string | null {
  if (phase === "HIGH_LEVEL_DESIGN") return "Submit Design";
  if (phase === "REQUIREMENTS" || phase === "ESTIMATION") {
    return `Move to ${PHASE_LABELS[nextPhase(phase)!]}`;
  }
  return null;
}

/** Seconds spent in the current phase, corrected for client clock skew
 *  (offsetMs = server time - client time when the status arrived). */
export function phaseElapsedSeconds(
  phaseStartedAt: string,
  offsetMs: number,
  nowMs: number,
): number {
  return Math.max(0, Math.floor((nowMs + offsetMs - Date.parse(phaseStartedAt)) / 1000));
}

export const GRADE_TONE_CLASSES = {
  great: "text-emerald-300",
  good: "text-sky-300",
  fair: "text-amber-300",
  poor: "text-red-300",
} as const;

export function gradeTone(
  letter: string | null,
): "great" | "good" | "fair" | "poor" {
  switch (letter?.[0]) {
    case "A":
      return "great";
    case "B":
      return "good";
    case "C":
      return "fair";
    default:
      return "poor";
  }
}

/** Left-to-right layered layout for the reference design: each component
 *  sits one column right of the furthest component that points at it. */
export function layoutReferenceDesign(
  components: { id: string }[],
  connections: { source: string; target: string }[],
): LayoutBox[] {
  const ids = components.map((c) => c.id);
  const known = new Set(ids);
  const edges = connections.filter(
    (c) => known.has(c.source) && known.has(c.target) && c.source !== c.target,
  );
  // Longest-path layering, relaxed at most |V| times so cycles terminate.
  const column = new Map(ids.map((id) => [id, 0]));
  for (let pass = 0; pass < ids.length; pass++) {
    let changed = false;
    for (const e of edges) {
      const next = column.get(e.source)! + 1;
      if (next > column.get(e.target)! && next < ids.length) {
        column.set(e.target, next);
        changed = true;
      }
    }
    if (!changed) break;
  }
  const rows = new Map<number, number>();
  return ids.map((id) => {
    const col = column.get(id)!;
    const row = rows.get(col) ?? 0;
    rows.set(col, row + 1);
    return {
      id,
      x: col * (NODE_WIDTH + COLUMN_GAP),
      y: row * (NODE_HEIGHT + ROW_GAP),
      width: NODE_WIDTH,
      height: NODE_HEIGHT,
    };
  });
}

/** An arrow from one laid-out box to another, edge to edge: Excalidraw's
 *  skeleton binds arrows to their boxes but doesn't position them. */
export function arrowGeometry(
  source: LayoutBox,
  target: LayoutBox,
): { x: number; y: number; points: [number, number][] } {
  const midY = (b: LayoutBox) => b.y + b.height / 2;
  const midX = (b: LayoutBox) => b.x + b.width / 2;
  let start: [number, number];
  let end: [number, number];
  if (target.x >= source.x + source.width) {
    start = [source.x + source.width, midY(source)];
    end = [target.x, midY(target)];
  } else if (target.x + target.width <= source.x) {
    start = [source.x, midY(source)];
    end = [target.x + target.width, midY(target)];
  } else if (target.y >= source.y) {
    start = [midX(source), source.y + source.height];
    end = [midX(target), target.y];
  } else {
    start = [midX(source), source.y];
    end = [midX(target), target.y + target.height];
  }
  const dx = end[0] - start[0];
  const dy = end[1] - start[1];
  // An edge that skips a column would cut through the boxes in between —
  // arc it over the top of both ends instead.
  if (Math.abs(dx) > COLUMN_GAP * 1.5) {
    const lift = Math.min(source.y, target.y) - ROW_GAP - start[1];
    return {
      x: start[0],
      y: start[1],
      points: [
        [0, 0],
        [dx / 2, lift],
        [dx, dy],
      ],
    };
  }
  return {
    x: start[0],
    y: start[1],
    points: [
      [0, 0],
      [dx, dy],
    ],
  };
}

/** Average score per rubric dimension across graded interviews, in rubric
 *  order. Interviews without a report are skipped. */
export function dimensionAverages(
  reports: (Pick<GradeReport, "dimensions"> | null)[],
): DimensionAverage[] {
  const totals = new Map<string, { label: string; sum: number; count: number }>();
  for (const report of reports) {
    for (const d of report?.dimensions ?? []) {
      const t = totals.get(d.key) ?? { label: d.label, sum: 0, count: 0 };
      t.sum += d.score;
      t.count += 1;
      totals.set(d.key, t);
    }
  }
  const rank = (key: string) => {
    const i = RUBRIC_ORDER.indexOf(key);
    return i < 0 ? RUBRIC_ORDER.length : i;
  };
  return [...totals.entries()]
    .sort(([a], [b]) => rank(a) - rank(b))
    .map(([key, t]) => ({
      key,
      label: t.label,
      average: Math.round((t.sum / t.count) * 10) / 10,
      count: t.count,
    }));
}

/** The dimension to practice next — lowest average, ties to rubric order. */
export function weakestDimension(
  averages: DimensionAverage[],
): DimensionAverage | null {
  return averages.reduce<DimensionAverage | null>(
    (worst, a) => (!worst || a.average < worst.average ? a : worst),
    null,
  );
}
