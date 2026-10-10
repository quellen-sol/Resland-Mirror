"""Tombstone ids for deleted accounts (shared.accounts)."""

import unittest
import uuid

from shared.accounts import TOMBSTONE_PREFIX, is_tombstone_id, new_tombstone_id


class TombstoneIdTest(unittest.TestCase):
    def test_new_id_is_prefixed_uuid(self):
        tomb = new_tombstone_id()
        self.assertTrue(tomb.startswith(TOMBSTONE_PREFIX))
        # The rest is a real uuid4 — random, so it can't encode the person.
        self.assertEqual(uuid.UUID(tomb.removeprefix(TOMBSTONE_PREFIX)).version, 4)

    def test_ids_are_unique(self):
        self.assertNotEqual(new_tombstone_id(), new_tombstone_id())

    def test_recognizes_tombstones(self):
        self.assertTrue(is_tombstone_id(new_tombstone_id()))

    def test_real_auth0_ids_are_not_tombstones(self):
        for sub in ("auth0|abc", "google-oauth2|123", "github|9", "", "deleted"):
            with self.subTest(sub=sub):
                self.assertFalse(is_tombstone_id(sub))


if __name__ == "__main__":
    unittest.main()
