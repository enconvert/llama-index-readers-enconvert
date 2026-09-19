# EnConvert reader for LlamaIndex

`llama-index-readers-enconvert` turns web pages and whole sites into LlamaIndex `Document`s through
[EnConvert](https://www.enconvert.com). Every perceived page carries a `render_quality` score (0.0-1.0)
in its metadata, so a blocked or empty page comes back flagged rather than trusted.

## Install

```bash
pip install llama-index-readers-enconvert
```

## Use

```python
from llama_index.readers.enconvert import EnConvertReader

reader = EnConvertReader(api_key="sk_...")  # or set $ENCONVERT_API_KEY

# A few URLs into clean-markdown Documents:
docs = reader.load_data(urls=["https://example.com", "https://example.com/pricing"])

# Or a whole site into RAG-ready chunk Documents:
docs = reader.load_data(ingest_url="https://docs.example.com", mode="sitemap", max_pages=100)

from llama_index.core import VectorStoreIndex
index = VectorStoreIndex.from_documents(docs)
```

- **URLs** are perceived into markdown; metadata carries `url` and `render_quality`.
- **`ingest_url`** crawls the site (async; the reader polls to completion), then returns one Document per
  chunk, each carrying the chunk's own metadata (source URL, title, etc.).

Auth: a **private** key (`sk_...`) from your [dashboard](https://www.enconvert.com/dashboard/api-keys).
Public `pk_` keys are rejected. The key is read from `api_key=` or `$ENCONVERT_API_KEY` and is excluded
from the reader's serialized form.

## Licence

[MIT](LICENSE)
