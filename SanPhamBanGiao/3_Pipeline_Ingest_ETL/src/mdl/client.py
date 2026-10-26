"""Client Python cho Math Data Lake API — dùng bởi Nhóm 2–8.

    from mdl.client import MathLakeClient
    c = MathLakeClient("http://localhost:8000")
    c.record("00f6e184715f8cd8dbe9")
    for r in c.iter_records(source="proofnet", fields="record_id,nl_problem,formal_statement"): ...
    c.export("leandojo", split="test", path="leandojo_test.parquet")
"""
import httpx


class MathLakeClient:
    def __init__(self, base_url="http://localhost:8000", timeout=60.0):
        self.http = httpx.Client(base_url=base_url, timeout=timeout)

    def _get(self, path, **params):
        r = self.http.get(path, params={k: v for k, v in params.items() if v is not None})
        r.raise_for_status()
        return r.json()

    def health(self):
        return self._get("/health")

    def stats(self):
        return self._get("/stats")

    def record(self, record_id):
        return self._get(f"/records/{record_id}")

    def iter_records(self, page_size=500, **filters):
        """Duyệt mọi bản ghi khớp bộ lọc bằng phân trang theo khóa."""
        after = None
        while True:
            page = self._get("/records", limit=page_size, after=after, **filters)
            yield from page["records"]
            after = page["next_after"]
            if not after:
                return

    def theorems_using(self, premise, limit=50):
        return self._get(f"/premises/{premise}/theorems", limit=limit)

    def nl_formal_pairs(self, split=None):
        return self._get("/pairs/nl-formal", split=split)

    def provenance(self, record_id):
        return self._get(f"/provenance/{record_id}")

    def catalog(self):
        return self._get("/catalog")

    def export(self, source, path, split=None, fields=None, fmt="parquet"):
        params = {k: v for k, v in {"source": source, "split": split, "fields": fields, "fmt": fmt}.items() if v}
        with self.http.stream("GET", "/export", params=params) as r:
            r.raise_for_status()
            with open(path, "wb") as f:
                for chunk in r.iter_bytes():
                    f.write(chunk)
        return path
