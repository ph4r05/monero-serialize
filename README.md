# Monero Python serialization library

The library provides basic serialization logic for the Monero types,
used in transaction processing and transaction signing.

- Mainly supports binary serialization equivalent to Monero `BEGIN_SERIALIZE_OBJECT()`.
- Support for `BEGIN_KV_SERIALIZE_MAP` is in progress
  - json works,
  - binary wire format not fully supported yet

The binary wire formats use streaming dumping / parsing for better memory effectivity.

