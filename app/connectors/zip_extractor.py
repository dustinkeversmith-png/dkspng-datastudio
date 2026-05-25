"""
ZipExtractor — download a remote ZIP archive and extract the first matching
file inside it to a local cache directory.

Usage
-----
    from app.connectors.zip_extractor import ZipExtractor

    extractor = ZipExtractor(
        url="https://aqs.epa.gov/aqsweb/airdata/daily_aqi_by_county_2023.zip",
        cache_key="epa_air_quality",
        match_suffix=".csv",          # extract the first .csv inside the zip
    )
    local_csv_path = extractor.extract()
"""

from __future__ import annotations

import hashlib
import os
import urllib.request
import zipfile
from pathlib import Path


_DOWNLOAD_DIR = os.path.join(os.getcwd(), "data", "downloads")


class ZipExtractor:
    """Download a ZIP from *url* and extract the first file matching *match_suffix*.

    Parameters
    ----------
    url:
        Remote URL of the ZIP archive.
    cache_key:
        A stable identifier used to name the local cache directory so repeated
        calls skip re-downloading.
    match_suffix:
        Only the first entry inside the ZIP whose name ends with this suffix
        is extracted.  Defaults to ``".csv"``.
    match_name:
        If provided, the extracted file must also contain this substring in
        its name (case-insensitive).
    force:
        If True, re-download and re-extract even if the cache already exists.
    """

    def __init__(
        self,
        url: str,
        cache_key: str,
        match_suffix: str = ".csv",
        match_name: str | None = None,
        force: bool = False,
    ) -> None:
        self.url = url
        self.cache_key = cache_key
        self.match_suffix = match_suffix.lower()
        self.match_name = match_name.lower() if match_name else None
        self.force = force

        # Unique sub-dir per URL so different ZIPs don't collide
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        self._cache_dir = Path(_DOWNLOAD_DIR) / f"{cache_key}_{url_hash}"
        self._zip_path = self._cache_dir / "archive.zip"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def extract(self) -> str:
        """Return the local path to the extracted file, downloading if needed."""
        self._cache_dir.mkdir(parents=True, exist_ok=True)

        if self.force or not self._zip_path.exists():
            self._download()

        return self._extract_matching()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _download(self) -> None:
        print(f"[ZipExtractor] Downloading {self.url} ...")
        req = urllib.request.Request(
            self.url,
            headers={"User-Agent": "RegionalDataStudio/1.0 (ZipExtractor)"},
        )
        with urllib.request.urlopen(req) as resp, open(self._zip_path, "wb") as f:
            f.write(resp.read())
        print(f"[ZipExtractor] Saved to {self._zip_path}")

    def _extract_matching(self) -> str:
        with zipfile.ZipFile(self._zip_path) as zf:
            candidates = [
                n for n in zf.namelist()
                if n.lower().endswith(self.match_suffix)
                and (self.match_name is None or self.match_name in n.lower())
            ]
            if not candidates:
                raise FileNotFoundError(
                    f"No entry ending with '{self.match_suffix}' found in {self._zip_path}. "
                    f"Available entries: {zf.namelist()}"
                )

            chosen = candidates[0]
            dest = self._cache_dir / Path(chosen).name

            if self.force or not dest.exists():
                print(f"[ZipExtractor] Extracting '{chosen}' → {dest}")
                data = zf.read(chosen)
                dest.write_bytes(data)
            else:
                print(f"[ZipExtractor] Using cached extract: {dest}")

        return str(dest)
