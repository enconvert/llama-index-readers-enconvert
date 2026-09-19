"""EnConvert reader for LlamaIndex."""

from __future__ import annotations

import json
import os
import time
from typing import List, Optional

import requests
from enconvert import Enconvert
from llama_index.core.bridge.pydantic import Field
from llama_index.core.readers.base import BasePydanticReader
from llama_index.core.schema import Document


class EnConvertReader(BasePydanticReader):
    """Read web pages or a whole site into LlamaIndex Documents via EnConvert.

    - ``load_data(urls=[...])`` perceives each URL into a clean-markdown Document
      carrying a ``render_quality`` score (0.0-1.0) in its metadata.
    - ``load_data(ingest_url="https://site.com")`` crawls the site into
      RAG-ready chunk Documents (one Document per chunk).
    """

    is_remote: bool = True
    base_url: str = "https://api.enconvert.com"
    # Excluded from serialization so the secret never lands in persisted index metadata.
    api_key: str = Field(
        default_factory=lambda: os.environ.get("ENCONVERT_API_KEY", ""),
        exclude=True,
        description="Private EnConvert key (sk_...). Defaults to $ENCONVERT_API_KEY.",
    )

    @classmethod
    def class_name(cls) -> str:
        return "EnConvertReader"

    def _client(self) -> Enconvert:
        if not self.api_key:
            raise ValueError(
                "EnConvert api_key is missing. Pass api_key= or set $ENCONVERT_API_KEY "
                "(a private key starting with sk_)."
            )
        return Enconvert(api_key=self.api_key, base_url=self.base_url)

    def load_data(
        self,
        urls: Optional[List[str]] = None,
        *,
        ingest_url: Optional[str] = None,
        mode: str = "sitemap",
        max_pages: int = 50,
        poll_interval: float = 5.0,
    ) -> List[Document]:
        client = self._client()
        if urls:
            return [_perceive_doc(client, u) for u in urls]
        if ingest_url:
            return _ingest_docs(client, ingest_url, mode, max_pages, poll_interval)
        raise ValueError("Provide urls=[...] or ingest_url=...")


def _perceive_doc(client: Enconvert, url: str) -> Document:
    op = client.v2.perceive_direct(url, outputs=["markdown"])
    return Document(
        text=op.content.decode("utf-8", "replace"),
        metadata={"url": url, "render_quality": op.render_quality},
    )


def _ingest_docs(
    client: Enconvert,
    url: str,
    mode: str,
    max_pages: int,
    poll_interval: float,
) -> List[Document]:
    job = client.v2.ingest(mode=mode, url=url, max_pages=max_pages)
    while True:
        status = client.v2.get_ingest_job(job.job_id)
        if status.status in ("completed", "failed", "cancelled"):
            break
        time.sleep(poll_interval)
    if status.status != "completed":
        raise RuntimeError(f"EnConvert ingest job {job.job_id} ended: {status.status}")
    resp = requests.get(status.output_url, timeout=120)
    resp.raise_for_status()
    return _chunks_to_documents(resp.text)


def _chunks_to_documents(jsonl_text: str) -> List[Document]:
    """Map an EnConvert ingest JSONL (one chunk per line) to Documents.

    Schema-agnostic: the chunk text comes from ``content`` (or ``text``); every
    other field becomes Document metadata.
    """
    docs: List[Document] = []
    for line in jsonl_text.splitlines():
        line = line.strip()
        if not line:
            continue
        chunk = json.loads(line)
        text = chunk.pop("content", None) or chunk.pop("text", "")
        docs.append(Document(text=text, metadata=chunk))
    return docs


if __name__ == "__main__":
    sample = (
        '{"content": "hello", "source_url": "https://x.com", "chunk_index": 0}\n'
        "\n"
        '{"text": "world", "title": "W"}'
    )
    out = _chunks_to_documents(sample)
    assert len(out) == 2, out
    assert out[0].text == "hello" and out[0].metadata["source_url"] == "https://x.com"
    assert out[1].text == "world" and out[1].metadata["title"] == "W"
    print("ok")
