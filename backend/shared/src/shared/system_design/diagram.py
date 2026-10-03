"""Excalidraw scene -> component graph.

The candidate draws on an embedded Excalidraw canvas. Its scene JSON already
records connectivity: an arrow's startBinding/endBinding name the shapes it
is attached to, and a label is a text element whose containerId is its shape
or arrow. Components dropped from our palette carry customData.kind.

The interviewer and grader read the normalized graph, never pixels. Arrows
that aren't attached at both ends and boxes with no connections are reported
as issues so the candidate can fix them before submitting the design.
"""

import json
import re
from dataclasses import asdict, dataclass, field

COMPONENT_KINDS = (
    "client",
    "cdn",
    "load_balancer",
    "api_gateway",
    "service",
    "worker",
    "cache",
    "database",
    "queue",
    "blob_store",
    "search",
    "other",
)

# Shapes that become components. Free-standing text becomes one too, but only
# when an arrow is attached to it — otherwise it's a note.
SHAPE_TYPES = ("rectangle", "ellipse", "diamond")
FRAME_TYPES = ("frame", "magicframe")

# Label keywords per kind, checked in order: infrastructure first, then
# services, then clients — "User Service" is a service, "Users" a client.
_KIND_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = tuple(
    (kind, re.compile(pattern, re.IGNORECASE))
    for kind, pattern in (
        ("cdn", r"\b(cdn|cloudfront|akamai|fastly|edge cache)\b"),
        (
            "load_balancer",
            r"\b(load[ -]?balancers?|lb|alb|elb|nlb|nginx|haproxy|envoy)\b",
        ),
        ("api_gateway", r"\b(api[ -]?gateway|gateway|kong|apigee)\b"),
        ("cache", r"\b(redis|memcached?|elasticache|caches?|caching)\b"),
        (
            "queue",
            (
                r"\b(kafka|sqs|sns|rabbitmq|rabbit|kinesis|pub/?sub|nats|queues?|"
                r"event bus|message bus|broker)\b"
            ),
        ),
        (
            "blob_store",
            (
                r"\b(s3|gcs|blob|blobs|object (store|storage)|buckets?|file store|"
                r"hdfs)\b"
            ),
        ),
        ("search", r"\b(elasticsearch|opensearch|solr|search|index)\b"),
        (
            "database",
            (
                r"(db\b|\b(database|postgres|postgresql|mysql|sql|cassandra|dynamo|"
                r"mongo|cockroach|spanner|aurora|rds|bigtable|hbase|scylla|"
                r"warehouse|datastore|data store|kv store|key-value store)\b)"
            ),
        ),
        ("worker", r"\b(workers?|consumers?|cron|batch jobs?|job runners?)\b"),
        ("service", r"\b(service|services|server|servers|api|backend|app server)\b"),
        (
            "client",
            (
                r"\b(clients?|browsers?|mobile|ios|android|users|end users?|"
                r"web ?app|frontend|desktop app)\b"
            ),
        ),
    )
)

_STORAGE_KINDS = ("database", "cache", "queue", "blob_store", "search")


@dataclass
class DiagramNode:
    id: str
    # Short stable handle (n1, n2, ...) the LLMs use to refer to components.
    ref: str
    label: str
    kind: str
    # False when the kind came from the palette's customData.
    kind_inferred: bool = True
    frame: str | None = None


@dataclass
class DiagramEdge:
    id: str
    source: str
    target: str
    label: str = ""
    bidirectional: bool = False


@dataclass
class DanglingArrow:
    id: str
    label: str = ""
    source: str | None = None
    target: str | None = None
    # Lines can't attach to shapes at all — only the arrow tool binds.
    is_line: bool = False


@dataclass
class DiagramIssue:
    kind: str  # "dangling_arrow" | "line" | "orphan_node"
    element_id: str
    message: str


@dataclass
class DiagramGraph:
    nodes: list[DiagramNode] = field(default_factory=list)
    edges: list[DiagramEdge] = field(default_factory=list)
    dangling: list[DanglingArrow] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def node(self, node_id: str) -> DiagramNode | None:
        return next((n for n in self.nodes if n.id == node_id), None)

    def orphan_ids(self) -> list[str]:
        """Components no connection touches, in node order."""
        touched = {e.source for e in self.edges} | {e.target for e in self.edges}
        return [n.id for n in self.nodes if n.id not in touched]

    def name(self, node_id: str | None) -> str:
        """Quoted label for messages; "an unlabeled <kind>" when a box has no
        text, "nothing" for a missing end."""
        node = self.node(node_id) if node_id else None
        if node is None:
            return "nothing"
        return f'"{node.label}"' if node.label else f"an unlabeled {node.kind}"

    def issues(self) -> list[DiagramIssue]:
        """Problems the candidate should fix before submitting the design."""
        out: list[DiagramIssue] = []
        for d in self.dangling:
            if d.is_line:
                out.append(
                    DiagramIssue(
                        "line",
                        d.id,
                        "A line can't connect components — redraw it with "
                        "the arrow tool, attached to a box at each end.",
                    )
                )
                continue
            label = f' "{d.label}"' if d.label else ""
            out.append(
                DiagramIssue(
                    "dangling_arrow",
                    d.id,
                    f"An arrow{label} from {self.name(d.source)} to "
                    f"{self.name(d.target)} isn't attached at both ends — drag "
                    "each end onto a component until it snaps.",
                )
            )
        for node_id in self.orphan_ids():
            out.append(
                DiagramIssue(
                    "orphan_node",
                    node_id,
                    f"{self.name(node_id)} isn't connected to anything.",
                )
            )
        return out

    def render(self) -> str:
        """Compact plain-text listing for the interviewer and grader."""
        if not self.nodes and not self.notes and not self.dangling:
            return "The diagram is empty."

        def ref(node_id: str | None) -> str:
            node = self.node(node_id) if node_id else None
            if node is None:
                return "(nothing)"
            return f'{node.ref} "{node.label}"'

        lines = [f"Components ({len(self.nodes)}):"]
        for n in self.nodes:
            kind = f"{n.kind}, inferred" if n.kind_inferred else n.kind
            frame = f' in frame "{n.frame}"' if n.frame else ""
            lines.append(f'- {n.ref} "{n.label}" [{kind}]{frame}')
        lines.append(f"Connections ({len(self.edges)}):")
        for e in self.edges:
            arrow = "<->" if e.bidirectional else "->"
            label = f" ({e.label})" if e.label else ""
            lines.append(f"- {ref(e.source)} {arrow} {ref(e.target)}{label}")
        if self.dangling:
            lines.append("Arrows not attached at both ends:")
            for d in self.dangling:
                if d.is_line:
                    lines.append("- a plain line (lines can't connect anything)")
                else:
                    label = f" ({d.label})" if d.label else ""
                    lines.append(f"- from {ref(d.source)} to {ref(d.target)}{label}")
        orphans = self.orphan_ids()
        if orphans:
            lines.append(
                "Components with no connections: "
                + ", ".join(ref(node_id) for node_id in orphans)
            )
        if self.notes:
            lines.append("Free-floating notes:")
            lines.extend(f'- "{note}"' for note in self.notes)
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "DiagramGraph":
        return cls(
            nodes=[DiagramNode(**n) for n in data.get("nodes") or []],
            edges=[DiagramEdge(**e) for e in data.get("edges") or []],
            dangling=[DanglingArrow(**d) for d in data.get("dangling") or []],
            notes=list(data.get("notes") or []),
        )


def parse_scene(raw: str | None) -> list[dict]:
    """Elements from a stored scene: a bare elements array or a full
    Excalidraw export ({"elements": [...]}). Anything unreadable is empty."""
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except ValueError:
        return []
    if isinstance(data, dict):
        data = data.get("elements")
    if not isinstance(data, list):
        return []
    return [el for el in data if isinstance(el, dict)]


def infer_kind(label: str) -> str:
    """Best-guess component kind from a free-form label ("Redis" -> cache)."""
    for kind, pattern in _KIND_PATTERNS:
        if pattern.search(label):
            return kind
    return "other"


def _clean_text(el: dict) -> str:
    raw = el.get("originalText") or el.get("text") or ""
    return " ".join(str(raw).split())


def _bound_id(binding) -> str | None:
    if isinstance(binding, dict):
        target = binding.get("elementId")
        if isinstance(target, str) and target:
            return target
    return None


def normalize_scene(elements: list[dict]) -> DiagramGraph:
    live = [
        el
        for el in elements
        if isinstance(el, dict)
        and isinstance(el.get("id"), str)
        and not el.get("isDeleted")
    ]
    by_id = {el["id"]: el for el in live}

    # Bound text labels its container (a shape or an arrow).
    labels: dict[str, list[str]] = {}
    notes_text: list[tuple[str, str]] = []
    for el in live:
        if el.get("type") != "text":
            continue
        text = _clean_text(el)
        container = el.get("containerId")
        if isinstance(container, str) and container in by_id:
            if text:
                labels.setdefault(container, []).append(text)
        elif text:
            notes_text.append((el["id"], text))

    arrows = [el for el in live if el.get("type") == "arrow"]
    arrow_targets = {
        target
        for el in arrows
        for target in (
            _bound_id(el.get("startBinding")),
            _bound_id(el.get("endBinding")),
        )
        if target
    }

    frames = {
        el["id"]: (el.get("name") or "Frame")
        for el in live
        if el.get("type") in FRAME_TYPES
    }

    graph = DiagramGraph()
    for el in live:
        el_type = el.get("type")
        if el_type in SHAPE_TYPES:
            label = " ".join(labels.get(el["id"], []))
        elif (
            el_type == "text"
            and el["id"] in arrow_targets
            and not el.get("containerId")
        ):
            # Free text an arrow is attached to stands in for a component.
            label = _clean_text(el)
        else:
            continue
        custom = el.get("customData")
        palette_kind = custom.get("kind") if isinstance(custom, dict) else None
        if palette_kind in COMPONENT_KINDS:
            kind, inferred = palette_kind, False
        else:
            kind, inferred = infer_kind(label), True
        frame_id = el.get("frameId")
        graph.nodes.append(
            DiagramNode(
                id=el["id"],
                ref=f"n{len(graph.nodes) + 1}",
                label=label,
                kind=kind,
                kind_inferred=inferred,
                frame=frames.get(frame_id) if isinstance(frame_id, str) else None,
            )
        )

    node_ids = {n.id for n in graph.nodes}
    graph.notes = [text for el_id, text in notes_text if el_id not in node_ids]

    for el in live:
        el_type = el.get("type")
        if el_type == "line":
            graph.dangling.append(DanglingArrow(id=el["id"], is_line=True))
            continue
        if el_type != "arrow":
            continue
        start = _bound_id(el.get("startBinding"))
        end = _bound_id(el.get("endBinding"))
        start = start if start in node_ids else None
        end = end if end in node_ids else None
        label = " ".join(labels.get(el["id"], []))
        if not start or not end:
            graph.dangling.append(
                DanglingArrow(id=el["id"], label=label, source=start, target=end)
            )
            continue
        head_start = bool(el.get("startArrowhead"))
        head_end = bool(el.get("endArrowhead"))
        if head_start and not head_end:
            start, end = end, start
        graph.edges.append(
            DiagramEdge(
                id=el["id"],
                source=start,
                target=end,
                label=label,
                bidirectional=head_start and head_end,
            )
        )
    return graph


def analyze_design(graph: DiagramGraph) -> list[str]:
    """Heuristic observations for the interviewer to verify and probe — not
    verdicts. Empty when nothing stands out."""
    if not graph.nodes:
        return ["The diagram has no components yet."]

    kinds = {n.id: n.kind for n in graph.nodes}
    present = set(kinds.values())
    out: list[str] = []

    def neighbors(node_id: str) -> list[str]:
        found = []
        for e in graph.edges:
            if e.source == node_id:
                found.append(e.target)
            elif e.bidirectional and e.target == node_id:
                found.append(e.source)
        return found

    clients = [n for n in graph.nodes if n.kind == "client"]
    for client in clients:
        for other in neighbors(client.id):
            if kinds.get(other) in _STORAGE_KINDS:
                out.append(
                    f"{graph.name(client.id)} talks directly to "
                    f"{graph.name(other)} ({kinds[other].replace('_', ' ')})."
                )
            elif kinds.get(other) in ("service", "worker") and not (
                present & {"load_balancer", "api_gateway"}
            ):
                out.append(
                    f"Clients reach {graph.name(other)} directly — no load "
                    "balancer or gateway in front of it."
                )

    if "cache" not in present and present & {"database", "service"}:
        out.append("No cache anywhere in the design.")

    for db in (n for n in graph.nodes if n.kind == "database"):
        users = {
            e.source if e.target == db.id else e.target
            for e in graph.edges
            if db.id in (e.source, e.target)
        }
        users = {u for u in users if kinds.get(u) in ("service", "worker")}
        if len(users) >= 3:
            out.append(
                f"{len(users)} components share one database {graph.name(db.id)} "
                "— a possible bottleneck or single point of failure."
            )

    for q in (n for n in graph.nodes if n.kind == "queue"):
        consumed = any(
            (e.source == q.id)
            or (e.bidirectional and q.id in (e.source, e.target))
            or (e.target == q.id and kinds.get(e.source) == "worker")
            for e in graph.edges
        )
        if not consumed:
            out.append(f"Nothing consumes from {graph.name(q.id)}.")

    # Same observation once is enough.
    return list(dict.fromkeys(out))


def _edge_key(e: DiagramEdge) -> tuple[str, str, bool]:
    if e.bidirectional:
        a, b = sorted((e.source, e.target))
        return (a, b, True)
    return (e.source, e.target, False)


def diff_graphs(before: DiagramGraph | None, after: DiagramGraph) -> list[str]:
    """Human-readable changes between two versions of the diagram."""
    if before is None:
        return []

    def name(node_id: str) -> str:
        node = after.node(node_id) or before.node(node_id)
        return f'"{node.label}"' if node and node.label else "an unlabeled box"

    def describe(e: DiagramEdge) -> str:
        arrow = "<->" if e.bidirectional else "->"
        return f"{name(e.source)} {arrow} {name(e.target)}"

    out: list[str] = []
    old_nodes = {n.id: n for n in before.nodes}
    new_nodes = {n.id: n for n in after.nodes}
    for node_id, node in new_nodes.items():
        prev = old_nodes.get(node_id)
        if prev is None:
            out.append(f"Added component {name(node_id)} [{node.kind}]")
        elif prev.label != node.label:
            out.append(f'Renamed "{prev.label}" to "{node.label}"')
    for node_id, node in old_nodes.items():
        if node_id not in new_nodes:
            label = f'"{node.label}"' if node.label else "an unlabeled box"
            out.append(f"Removed component {label}")

    old_edges = {_edge_key(e): e for e in before.edges}
    new_edges = {_edge_key(e): e for e in after.edges}
    for key, edge in new_edges.items():
        prev = old_edges.get(key)
        if prev is None:
            label = f" ({edge.label})" if edge.label else ""
            out.append(f"Added connection {describe(edge)}{label}")
        elif prev.label != edge.label:
            out.append(
                f'Relabeled connection {describe(edge)}: "{prev.label}" to '
                f'"{edge.label}"'
            )
    for key, edge in old_edges.items():
        if key not in new_edges:
            out.append(f"Removed connection {describe(edge)}")
    return out
