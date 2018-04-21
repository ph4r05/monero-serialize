# Monero Python serialization library

[![Build Status](https://travis-ci.org/ph4r05/monero-serialize.svg?branch=master)](https://travis-ci.org/ph4r05/monero-serialize)

The library provides basic serialization logic for the Monero types,
used in transaction processing and transaction signing.

- Mainly supports binary serialization equivalent to Monero `BEGIN_SERIALIZE_OBJECT()`.
This serialization mechanism is used in the blockchain entity serialization.
- Boost portable serialization added.
- Support for `BEGIN_KV_SERIALIZE_MAP` is in progress
  - json works,
  - binary wire format not fully supported yet

The binary wire formats use streaming dumping / parsing for better memory efficiency.

For usage please take a look at tests.

## Example usage:

```python
import binascii
from monero_serialize import xmrserialize as x
from monero_serialize import xmrtypes as xmr

msg = xmr.TxinToKey(amount=123, key_offsets=[1, 2, 3, 2**76], k_image=bytearray(range(32)))

# Serialize
writer = x.MemoryReaderWriter()
await x.dump_message(writer, msg)
print(binascii.hexlify(writer.buffer))

# Deserialize
test_deser = await x.load_message(x.MemoryReaderWriter(writer.buffer), xmr.TxinGen)
```

### Symmetric Boost archive

```
import binascii
from monero_serialize import xmrserialize as x
from monero_serialize import xmrtypes as xmr
from monero_serialize import xmrboost as xmrb

data_hex = b'011673657269616c697a6174696f6e3a3a61726368697665000000000134'
data_bin = base64.b16decode(data_hex, True)
reader = x.MemoryReaderWriter(bytearray(data_bin))
ar = xmrb.Archive(reader, False)

msg = xmr.TxinGen()
await ar.root_message(msg)
self.assertEqual(msg.height, 0x34)
```
