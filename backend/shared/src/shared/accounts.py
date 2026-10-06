"""Conventions for deleted accounts, shared by the API and the dispatcher.

Deleting an account keeps its billing ledger (`balance_purchase`,
`token_usage`) for accounting, re-pointed at a *tombstone* `user` row that
carries no personal data, so the rows no longer lead back to the person.

Tombstone ids look like ``deleted|<uuid4>``: the ``provider|id`` shape of an
Auth0 `sub`, under a provider name no Auth0 connection uses, so a tombstone
can never collide with (or be signed into as) a real account.
"""

import uuid

TOMBSTONE_PREFIX = "deleted|"


def new_tombstone_id() -> str:
    return f"{TOMBSTONE_PREFIX}{uuid.uuid4()}"


def is_tombstone_id(user_id: str) -> bool:
    return user_id.startswith(TOMBSTONE_PREFIX)
