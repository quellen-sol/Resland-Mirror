"""Excalidraw scene -> component graph normalization, validation issues,
rendering, heuristics, and diffs. Element fixtures mirror the fields
Excalidraw 0.18 writes (startBinding/endBinding, containerId, customData).

Run: .venv/bin/python -m unittest backend.shared.tests.test_system_design_diagram -v
"""

import json
import unittest

from shared.system_design import diagram


def shape(el_id, kind=None, frame=None, type="rectangle", deleted=False):
    el = {
        "id": el_id,
        "type": type,
        "isDeleted": deleted,
        "frameId": frame,
        "boundElements": [],
    }
    if kind:
        el["customData"] = {"kind": kind}
    return el


def text(el_id, value, container=None, deleted=False):
    return {
        "id": el_id,
        "type": "text",
        "text": value,
        "originalText": value,
        "containerId": container,
        "isDeleted": deleted,
    }


def arrow(el_id, start=None, end=None, start_head=None, end_head="arrow", type="arrow"):
    def bind(target):
        return {"elementId": target, "focus": 0, "gap": 4} if target else None

    return {
        "id": el_id,
        "type": type,
        "isDeleted": False,
        "startBinding": bind(start),
        "endBinding": bind(end),
        "startArrowhead": start_head,
        "endArrowhead": end_head,
    }


def labelled(el_id, label, kind=None, **kw):
    """A shape plus its bound label, the way Excalidraw stores both."""
    return [shape(el_id, kind=kind, **kw), text(f"{el_id}-t", label, container=el_id)]


def simple_scene():
    return [
        *labelled("c", "Mobile Client", kind="client"),
        *labelled("lb", "Load Balancer", kind="load_balancer"),
        *labelled("svc", "Feed Service"),
        *labelled("db", "Postgres"),
        arrow("a1", "c", "lb"),
        text("a1-t", "HTTPS", container="a1"),
        arrow("a2", "lb", "svc"),
        arrow("a3", "svc", "db"),
    ]


class ParseScene(unittest.TestCase):
    def test_bare_elements_array(self):
        self.assertEqual(diagram.parse_scene(json.dumps([{"id": "x"}])), [{"id": "x"}])

    def test_full_export(self):
        raw = json.dumps({"type": "excalidraw", "elements": [{"id": "x"}]})
        self.assertEqual(diagram.parse_scene(raw), [{"id": "x"}])

    def test_garbage_is_empty(self):
        for raw in (None, "", "not json", "42", '{"elements": 3}', '["a", 1]'):
            with self.subTest(raw=raw):
                self.assertEqual(diagram.parse_scene(raw), [])


class InferKind(unittest.TestCase):
    def test_common_labels(self):
        cases = {
            "Redis Cache": "cache",
            "memcached": "cache",
            "Kafka": "queue",
            "Message Queue": "queue",
            "SQS": "queue",
            "Postgres": "database",
            "User DB": "database",
            "Cassandra cluster": "database",
            "S3 bucket": "blob_store",
            "Object Storage": "blob_store",
            "CDN": "cdn",
            "Load Balancer": "load_balancer",
            "ALB": "load_balancer",
            "API Gateway": "api_gateway",
            "Mobile Client": "client",
            "Browser": "client",
            "Users": "client",
            "Elasticsearch": "search",
            "Fanout Worker": "worker",
            "Feed Service": "service",
            "Album Service": "service",
            "": "other",
        }
        for label, kind in cases.items():
            with self.subTest(label=label):
                self.assertEqual(diagram.infer_kind(label), kind)


class NormalizeScene(unittest.TestCase):
    def test_shapes_become_labelled_nodes_with_refs(self):
        graph = diagram.normalize_scene(simple_scene())
        self.assertEqual([n.id for n in graph.nodes], ["c", "lb", "svc", "db"])
        self.assertEqual([n.ref for n in graph.nodes], ["n1", "n2", "n3", "n4"])
        self.assertEqual(graph.node("svc").label, "Feed Service")

    def test_palette_kind_wins_over_inference(self):
        graph = diagram.normalize_scene(
            [*labelled("x", "Something odd", kind="cache"), *labelled("y", "Redis")]
        )
        self.assertEqual(graph.node("x").kind, "cache")
        self.assertFalse(graph.node("x").kind_inferred)
        self.assertEqual(graph.node("y").kind, "cache")
        self.assertTrue(graph.node("y").kind_inferred)

    def test_unknown_palette_kind_falls_back_to_inference(self):
        graph = diagram.normalize_scene(labelled("x", "Kafka", kind="spaceship"))
        self.assertEqual(graph.node("x").kind, "queue")
        self.assertTrue(graph.node("x").kind_inferred)

    def test_bound_arrows_become_edges_with_labels(self):
        graph = diagram.normalize_scene(simple_scene())
        pairs = [(e.source, e.target, e.label) for e in graph.edges]
        self.assertEqual(
            pairs, [("c", "lb", "HTTPS"), ("lb", "svc", ""), ("svc", "db", "")]
        )
        self.assertEqual(graph.dangling, [])

    def test_arrowhead_only_at_start_flips_direction(self):
        graph = diagram.normalize_scene(
            [
                *labelled("a", "A"),
                *labelled("b", "B"),
                arrow("e", "a", "b", start_head="arrow", end_head=None),
            ]
        )
        self.assertEqual((graph.edges[0].source, graph.edges[0].target), ("b", "a"))
        self.assertFalse(graph.edges[0].bidirectional)

    def test_two_arrowheads_is_bidirectional(self):
        graph = diagram.normalize_scene(
            [
                *labelled("a", "A"),
                *labelled("b", "B"),
                arrow("e", "a", "b", start_head="arrow", end_head="triangle"),
            ]
        )
        self.assertTrue(graph.edges[0].bidirectional)

    def test_half_bound_arrow_is_dangling(self):
        graph = diagram.normalize_scene(
            [*labelled("a", "A"), arrow("e", "a", None), text("e-t", "writes", "e")]
        )
        self.assertEqual(graph.edges, [])
        self.assertEqual(len(graph.dangling), 1)
        self.assertEqual(graph.dangling[0].source, "a")
        self.assertIsNone(graph.dangling[0].target)
        self.assertEqual(graph.dangling[0].label, "writes")

    def test_arrow_bound_to_deleted_shape_is_dangling(self):
        graph = diagram.normalize_scene(
            [*labelled("a", "A"), shape("gone", deleted=True), arrow("e", "a", "gone")]
        )
        self.assertEqual(graph.edges, [])
        self.assertEqual(graph.dangling[0].target, None)

    def test_lines_never_connect(self):
        graph = diagram.normalize_scene(
            [*labelled("a", "A"), *labelled("b", "B"), arrow("l", type="line")]
        )
        self.assertTrue(graph.dangling[0].is_line)

    def test_deleted_elements_are_ignored(self):
        graph = diagram.normalize_scene(
            [
                *labelled("a", "A"),
                shape("b", deleted=True),
                text("t", "old", deleted=True),
            ]
        )
        self.assertEqual([n.id for n in graph.nodes], ["a"])
        self.assertEqual(graph.notes, [])

    def test_free_text_is_a_note_unless_an_arrow_binds_it(self):
        graph = diagram.normalize_scene(
            [
                text("note", "fan-out on write\nfor most users"),
                text("users", "Users"),
                *labelled("api", "API"),
                arrow("e", "users", "api"),
            ]
        )
        self.assertEqual(graph.notes, ["fan-out on write for most users"])
        users = graph.node("users")
        self.assertIsNotNone(users)
        self.assertEqual(users.kind, "client")
        self.assertEqual(len(graph.edges), 1)

    def test_label_with_missing_container_is_a_note(self):
        graph = diagram.normalize_scene([text("t", "orphan label", container="nope")])
        self.assertEqual(graph.notes, ["orphan label"])

    def test_frames_name_their_members(self):
        graph = diagram.normalize_scene(
            [
                {"id": "f", "type": "frame", "name": "Write path", "isDeleted": False},
                *labelled("a", "Ingest", frame="f"),
            ]
        )
        self.assertEqual(graph.node("a").frame, "Write path")
        self.assertIsNone(graph.node("f"))

    def test_non_dict_and_unknown_elements_are_skipped(self):
        graph = diagram.normalize_scene(
            ["junk", {"type": "freedraw", "id": "fd"}, {"type": "image", "id": "im"}]
        )
        self.assertEqual(graph.nodes, [])
        self.assertEqual(graph.edges, [])

    def test_round_trips_through_dict(self):
        graph = diagram.normalize_scene(
            [*simple_scene(), arrow("d", "db", None), text("n", "note")]
        )
        again = diagram.DiagramGraph.from_dict(json.loads(json.dumps(graph.to_dict())))
        self.assertEqual(again, graph)


class Issues(unittest.TestCase):
    def test_clean_design_has_no_issues(self):
        self.assertEqual(diagram.normalize_scene(simple_scene()).issues(), [])

    def test_orphans_dangling_and_lines_are_reported(self):
        graph = diagram.normalize_scene(
            [
                *simple_scene(),
                *labelled("lonely", "Analytics"),
                arrow("half", "svc", None),
                arrow("ln", type="line"),
            ]
        )
        self.assertEqual(graph.orphan_ids(), ["lonely"])
        kinds = sorted((i.kind, i.element_id) for i in graph.issues())
        self.assertEqual(
            kinds,
            [("dangling_arrow", "half"), ("line", "ln"), ("orphan_node", "lonely")],
        )
        messages = " ".join(i.message for i in graph.issues())
        self.assertIn("Analytics", messages)
        self.assertIn("Feed Service", messages)


class Render(unittest.TestCase):
    def test_lists_components_connections_and_notes(self):
        graph = diagram.normalize_scene(
            [*simple_scene(), text("n", "cache later"), arrow("half", "svc", None)]
        )
        out = graph.render()
        self.assertIn('n1 "Mobile Client" [client]', out)
        self.assertIn('n3 "Feed Service" [service, inferred]', out)
        self.assertIn('n1 "Mobile Client" -> n2 "Load Balancer" (HTTPS)', out)
        self.assertIn("cache later", out)
        self.assertIn("not attached", out)

    def test_bidirectional_and_frames(self):
        graph = diagram.normalize_scene(
            [
                {"id": "f", "type": "frame", "name": "Region A", "isDeleted": False},
                *labelled("a", "A", frame="f"),
                *labelled("b", "B"),
                arrow("e", "a", "b", start_head="arrow"),
            ]
        )
        out = graph.render()
        self.assertIn("<->", out)
        self.assertIn('in frame "Region A"', out)

    def test_empty_diagram(self):
        self.assertIn("empty", diagram.DiagramGraph().render().lower())


class AnalyzeDesign(unittest.TestCase):
    def test_empty_diagram(self):
        obs = diagram.analyze_design(diagram.DiagramGraph())
        self.assertEqual(len(obs), 1)
        self.assertIn("no components", obs[0])

    def test_client_straight_to_database(self):
        graph = diagram.normalize_scene(
            [
                *labelled("c", "Browser"),
                *labelled("d", "Postgres"),
                arrow("e", "c", "d"),
            ]
        )
        self.assertTrue(
            any(
                "directly" in o and "Postgres" in o
                for o in diagram.analyze_design(graph)
            )
        )

    def test_no_cache_and_no_load_balancer(self):
        graph = diagram.normalize_scene(
            [
                *labelled("c", "Browser"),
                *labelled("s", "API Server"),
                *labelled("d", "MySQL"),
                arrow("e1", "c", "s"),
                arrow("e2", "s", "d"),
            ]
        )
        obs = " ".join(diagram.analyze_design(graph))
        self.assertIn("cache", obs)
        self.assertIn("load balancer", obs)

    def test_shared_database(self):
        scene = [*labelled("d", "Postgres")]
        for i in range(3):
            scene += [*labelled(f"s{i}", f"Service {i}"), arrow(f"e{i}", f"s{i}", "d")]
        obs = " ".join(diagram.analyze_design(diagram.normalize_scene(scene)))
        self.assertIn("share", obs)

    def test_queue_without_consumer(self):
        graph = diagram.normalize_scene(
            [
                *labelled("s", "Order Service"),
                *labelled("q", "Kafka"),
                arrow("e", "s", "q"),
            ]
        )
        obs = " ".join(diagram.analyze_design(graph))
        self.assertIn("Kafka", obs)
        self.assertIn("consum", obs)

    def test_solid_design_has_no_structural_complaints(self):
        graph = diagram.normalize_scene(
            [
                *simple_scene(),
                *labelled("r", "Redis"),
                arrow("e9", "svc", "r"),
            ]
        )
        self.assertEqual(diagram.analyze_design(graph), [])


class DiffGraphs(unittest.TestCase):
    def test_first_look_has_no_diff(self):
        self.assertEqual(
            diagram.diff_graphs(None, diagram.normalize_scene(simple_scene())), []
        )

    def test_no_changes(self):
        g = diagram.normalize_scene(simple_scene())
        self.assertEqual(diagram.diff_graphs(g, g), [])

    def test_added_removed_renamed(self):
        before = diagram.normalize_scene(simple_scene())
        scene = [el for el in simple_scene() if el["id"] not in ("a3",)]
        for el in scene:
            if el["id"] == "svc-t":
                el["originalText"] = el["text"] = "Timeline Service"
        scene += [*labelled("r", "Redis"), arrow("a9", "svc", "r", start_head="arrow")]
        after = diagram.normalize_scene(scene)
        changes = "\n".join(diagram.diff_graphs(before, after))
        self.assertIn('Added component "Redis"', changes)
        self.assertIn('Renamed "Feed Service" to "Timeline Service"', changes)
        self.assertIn('Removed connection "Timeline Service" -> "Postgres"', changes)
        self.assertIn('Added connection "Timeline Service" <-> "Redis"', changes)

    def test_removed_component_and_relabelled_connection(self):
        before = diagram.normalize_scene(simple_scene())
        scene = [el for el in simple_scene() if el["id"] not in ("db", "db-t", "a3")]
        for el in scene:
            if el["id"] == "a1-t":
                el["originalText"] = el["text"] = "gRPC"
        changes = "\n".join(diagram.diff_graphs(before, diagram.normalize_scene(scene)))
        self.assertIn('Removed component "Postgres"', changes)
        self.assertIn("gRPC", changes)


if __name__ == "__main__":
    unittest.main()
