# Monero Python serialization library

[![Build Status](https://travis-ci.org/ph4r05/monero-serialize.svg?branch=master)](https://travis-ci.org/ph4r05/monero-serialize)

The library provides basic serialization logic for the Monero types,
used in transaction processing and transaction signing.

- Mainly supports binary serialization equivalent to Monero `BEGIN_SERIALIZE_OBJECT()`.
This serialization mechanism is used in the blockchain entity serialization.
- Boost portable serialization added.
- Support for `BEGIN_KV_SERIALIZE_MAP` is mainly supported. JSON and binary wire format.

The binary wire formats use streaming dumping / parsing for better memory efficiency.

For usage please take a look at [tests](https://github.com/ph4r05/monero-serialize/tree/master/monero_serialize/tests).

```
pip install monero-serialize
```

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

### Archive interface

```python
import binascii
from monero_serialize import xmrserialize as x
from monero_serialize import xmrtypes as xmr

msg = xmr.TxinGen(height=42)

# Serialize
writer = x.MemoryReaderWriter()
ar1 = x.Archive(writer, True)
await ar1.message(msg)

# Deserialize
msg2 = xmr.TxinGen()
ar2 = x.Archive(x.MemoryReaderWriter(writer.buffer), False)
await ar2.message(msg2)
```

### Symmetric Boost archive

```python
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


## XMR classes

```python
class Hash(x.BlobType): pass;
class ECKey(x.BlobType): pass;
class ECPoint(x.BlobType): pass;
class SecretKey(ECKey): pass;
class ECPublicKey(ECPoint): pass;
class KeyImage(ECPoint): pass;
class KeyDerivation(ECPoint): pass;
class TxoutToScript(x.MessageType): pass;
class TxoutToKey(x.MessageType): pass;
class TxoutToScriptHash(x.MessageType): pass;
class TxoutTargetV(x.VariantType): pass;
class TxinGen(x.MessageType): pass;
class TxinToKey(x.MessageType): pass;
class TxinToScript(x.MessageType): pass;
class TxinToScriptHash(x.MessageType): pass;
class TxInV(x.VariantType): pass;
class TxOut(x.MessageType): pass;
class TransactionPrefix(x.MessageType): pass;
class TransactionPrefixExtraBlob(TransactionPrefix): pass;

#
# rctTypes.h
#

class Key64(x.ContainerType): pass;
class KeyV(x.ContainerType): pass;
class KeyM(x.ContainerType): pass;
class KeyVFix(x.ContainerType): pass;
class KeyMFix(x.ContainerType): pass;
class CtKey(x.MessageType): pass;
class CtkeyV(x.ContainerType): pass;
class CtkeyM(x.ContainerType): pass;
class MultisigKLRki(x.MessageType): pass;
class MultisigOut(x.MessageType): pass;
class EcdhTuple(x.MessageType): pass;
class BoroSig(x.MessageType): pass;
class MgSig(x.MessageType): pass;
class RangeSig(x.MessageType): pass;
class Bulletproof(x.MessageType): pass;
class EcdhInfo(x.ContainerType): pass;
class RctSigBase(x.MessageType): pass;
class RctSigPrunable(x.MessageType): pass;
class RctSig(RctSigBase): pass;
class Signature(x.MessageType): pass;
class SignatureArray(x.ContainerType): pass;
class Transaction(TransactionPrefix): pass;
class BlockHeader(x.MessageType): pass;
class HashVector(x.ContainerType): pass;
class Block(BlockHeader): pass;
class AccountPublicAddress(x.MessageType): pass;
class SubaddressIndex(x.MessageType): pass;
class MultisigLR(x.MessageType): pass;
class MultisigInfo(x.MessageType): pass;
class MultisigStruct(x.MessageType): pass;
class TxExtraPadding(x.MessageType): pass;
class TxExtraPubKey(x.MessageType): pass;
class TxExtraNonce(x.MessageType): pass;
class TxExtraMergeMiningTag(x.MessageType): pass;
class TxExtraAdditionalPubKeys(x.MessageType): pass;
class TxExtraMysteriousMinergate(x.MessageType): pass;
class TxExtraField(x.VariantType): pass;
class TxExtraFields(x.ContainerType): pass;
class OutputEntry(x.TupleType): pass;
class TxSourceEntry(x.MessageType): pass;
class TxDestinationEntry(x.MessageType): pass;
class TransferDetails(x.MessageType): pass;
class TxConstructionData(x.MessageType): pass;
class PendingTransaction(x.MessageType): pass;
class PendingTransactionVector(x.ContainerType): pass;
class UnsignedTxSet(x.MessageType): pass;
class SignedTxSet(x.MessageType): pass;
class MultisigTxSet(x.MessageType): pass;
```
