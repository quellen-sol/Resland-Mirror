"""Test helpers — a scripted fake psycopg AsyncConnection and AMQP client,
plus in-memory S3 and Auth0 Management fakes for the account flows.

`_Pg` answers `cursor()` calls from a queue of canned result sets, records
every query, and counts commits; services under test see real async
context managers, real row objects, and real call order.
"""

import io
import queue
import unittest.mock

from botocore.exceptions import ClientError


class _Result:
    def __init__(self, rows=(), fetchone=None, rowcount=1):
        self._rows = list(rows)
        self._one = fetchone
        self.rowcount = rowcount

    async def fetchone(self):
        if self._one is not None:
            return self._one
        return self._rows.pop(0) if self._rows else None

    async def fetchall(self):
        rows, self._rows = self._rows, []
        return rows


class _Cursor:
    def __init__(self, conn):
        self._conn = conn

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def execute(self, query, params=None):
        self._conn.queries.append((query, params))
        try:
            return self._conn.results.get_nowait()
        except queue.Empty:
            return _Result()


class _Pg:
    """results: FIFO of _Result / row-list / single-row consumed per execute."""

    def __init__(self, results=()):
        self.results = queue.Queue()
        for item in results:
            if isinstance(item, _Result):
                self.results.put(item)
            else:
                self.results.put(_Result(item))
        self.queries = []
        self.commits = 0

    def cursor(self, **_kw):
        return _Cursor(self)

    def transaction(self):
        cm = unittest.mock.MagicMock()
        cm.__aenter__ = unittest.mock.AsyncMock(return_value=self)
        cm.__aexit__ = unittest.mock.AsyncMock(return_value=False)
        return cm

    async def commit(self):
        self.commits += 1

    async def close(self):
        pass


class _Publisher:
    def __init__(self, order=None):
        self.published = []
        self._order = order

    async def publish(self, message):
        self.published.append(message)
        if self._order is not None:
            self._order.append("publish")


class _Amqp:
    def __init__(self, order=None):
        self.publisher = _Publisher(order)
        self.calls = []

    async def get_publisher(self, exchange, routing_key):
        self.calls.append((exchange, routing_key))
        return self.publisher


def pg_results(*items):
    """Shorthand: each item is a row-list, a single row (fetchone target),
    or a pre-built _Result."""
    return _Pg(items)


def one(row):
    """Wrap a single row so fetchone returns it even inside a list arg."""
    return _Result(fetchone=row)


class FakeS3:
    """In-memory boto3 S3 client: list_objects_v2 (paginated), delete_objects,
    get_object, plus the upload/head/presign calls the export paths make.
    Records list/delete calls so tests can prove what was touched."""

    def __init__(self, objects=None, page_size=1000):
        self.objects = dict(objects or {})
        self.page_size = page_size
        self.list_calls = []
        self.delete_calls = []
        self.fail_list = None
        self.fail_get = None
        self.fail_delete_keys = set()

    def list_objects_v2(self, Bucket, Prefix, ContinuationToken=None, MaxKeys=1000):
        self.list_calls.append((Bucket, Prefix, ContinuationToken))
        if self.fail_list:
            raise self.fail_list
        keys = sorted(k for k in self.objects if k.startswith(Prefix))
        start = int(ContinuationToken or 0)
        page = keys[start : start + min(MaxKeys, self.page_size)]
        truncated = start + len(page) < len(keys)
        resp = {"KeyCount": len(page), "IsTruncated": truncated}
        if page:
            resp["Contents"] = [{"Key": k, "Size": len(self.objects[k])} for k in page]
        if truncated:
            resp["NextContinuationToken"] = str(start + len(page))
        return resp

    def delete_objects(self, Bucket, Delete):
        keys = [o["Key"] for o in Delete["Objects"]]
        assert 0 < len(keys) <= 1000, "S3 caps DeleteObjects at 1,000 keys"
        self.delete_calls.append(keys)
        deleted, errors = [], []
        for key in keys:
            if key in self.fail_delete_keys:
                errors.append({"Key": key, "Code": "AccessDenied", "Message": "no"})
            else:
                self.objects.pop(key, None)
                deleted.append({"Key": key})
        resp = {"Deleted": deleted}
        if errors:
            resp["Errors"] = errors
        return resp

    def get_object(self, Bucket, Key):
        if self.fail_get:
            raise self.fail_get
        if Key not in self.objects:
            raise ClientError(
                {"Error": {"Code": "NoSuchKey", "Message": "gone"}}, "GetObject"
            )
        return {"Body": io.BytesIO(self.objects[Key])}

    def upload_fileobj(self, fileobj, bucket, key):
        self.objects[key] = fileobj.read()

    def head_object(self, Bucket, Key):
        if Key not in self.objects:
            raise ClientError({"Error": {"Code": "404"}}, "HeadObject")
        return {}

    def generate_presigned_url(self, *_args, **_kwargs):
        return "https://s3.test/presigned"


class FakeAuth0:
    """Stands in for api.account.auth0_mgmt.Auth0Management."""

    def __init__(self, configured=True, profile=None):
        self.configured = configured
        self.profile = profile
        self.deleted = []
        self.fail_delete = None
        self.fail_get = None
        # An Auth0NotReady to raise from ensure_scopes (bad secret, scope).
        self.not_ready = None
        self.scope_checks = []

    async def ensure_scopes(self, *scopes):
        from api.account.auth0_mgmt import Auth0NotReady

        self.scope_checks.append(scopes)
        if not self.configured:
            raise Auth0NotReady("not configured")
        if self.not_ready:
            raise self.not_ready

    async def get_user(self, user_id):
        if self.fail_get:
            raise self.fail_get
        return self.profile

    async def delete_user(self, user_id):
        if self.fail_delete:
            raise self.fail_delete
        self.deleted.append(user_id)
