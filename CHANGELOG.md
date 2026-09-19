# Changelog

## [0.1.0] - 2026-08-27

### Added

- Initial release. `EnConvertReader` loads web pages (`urls=`) into clean-markdown Documents with a
  `render_quality` score, or ingests a whole site (`ingest_url=`) into RAG-ready chunk Documents.
- The API key is read from `api_key=` or `$ENCONVERT_API_KEY` and excluded from serialization.
