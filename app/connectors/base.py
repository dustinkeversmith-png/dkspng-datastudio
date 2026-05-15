import os
import urllib.request
import hashlib
from abc import ABC, abstractmethod
import pandas as pd
from app.schemas import SourceDefinition


class Connector(ABC):
    def __init__(self, source: SourceDefinition):
        self.source = source

    def _get_local_download_path(self) -> str:
        url_hash = hashlib.md5(self.source.source_url.encode("utf-8")).hexdigest()[:8]
        filename = f"{self.source.source_key}_{url_hash}"
        # append extension if any
        if "." in self.source.source_url.split("/")[-1]:
            ext = self.source.source_url.split("/")[-1].split(".")[-1]
            # sanitize ext
            ext = "".join(c for c in ext if c.isalnum())
            if ext:
                filename = f"{filename}.{ext}"

        download_dir = os.path.join(os.getcwd(), "data", "downloads")
        os.makedirs(download_dir, exist_ok=True)
        return os.path.join(download_dir, filename)

    def _ensure_downloaded(self) -> str:
        if not self.source.requires_download:
            return self.source.source_url

        local_path = self._get_local_download_path()
        if not os.path.exists(local_path):
            print(f"Downloading dataset '{self.source.source_key}' from {self.source.source_url} ...")
            try:
                # Add a simple user agent for sites that require it
                req = urllib.request.Request(
                    self.source.source_url, 
                    headers={'User-Agent': 'Mozilla/5.0'}
                )
                with urllib.request.urlopen(req) as response, open(local_path, 'wb') as out_file:
                    data = response.read()
                    out_file.write(data)
                print(f"Download complete: {local_path}")
            except Exception as e:
                print(f"Failed to download {self.source.source_url}: {e}")
                raise e
        else:
            print(f"Using previously downloaded file for '{self.source.source_key}': {local_path}")
        
        return local_path

    @abstractmethod
    def fetch(self) -> pd.DataFrame:
        raise NotImplementedError
