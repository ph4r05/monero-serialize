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

# Donations
Thanks for your support!

```
86KCjujm1Hp4dD2uyZdXjHQr5e5aNujG6LcunA8iQYjx4AwRorVLDpHMKKmrKQfAPFC5KCKPpjdax3NEbExBRTnSTS1QXWA
```


# Advanced usage

## Archive interface

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

## Symmetric Boost archive

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
class TxIndex(x.MessageType): pass;
class TransactionMetaData(x.MessageType): pass;

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


# Serialization formats

## Blockchain format

The BC serialization format is scheme-oriented, i.e., you have to provide the scheme according to which 
serialize/deserialize the data. Scheme specifies how are fields composed, whether the size of containers is 
fixed (and then also the size is specified by the scheme) or not.

The format is not versioned, i.e., serialization format does not store explicit version numbers which would affect serialization scheme.

### Uvarint

- Variable length integer encoded by 7-bit chunks, little endian. 
- The MSB indicates whether there are more octets (1) or it is the last one (0).
- 0 - 0x7f encoded in 1 byte, 0x80 - 0x3fff encoded in 2 bytes, ...

Example:
- `0x0f     -> 0f`
- `0x1000   -> 8020`
- `0xffff   -> ffff03`
- `0xffffff -> ffffff07`

### UInt

- Fixed width integer, little endian encoded

Example:

- `0x0f     Width 4 = 0f000000`
- `0x1000   Width 4 = 001000`
- `0xffffff Width 4 = ffffff00`

### Blob

- Binary bytes can have either fixed size or variable size.
- Variable size format: `uvarint(lenght) || data`
- Fixed-size format: `data`
- Typical example of a fixed-width blob is EC point or scalar, which has 32 bytes

### Unicode string

- Format: `uvarint(length) || input.encode("utf8")`

### Container

- Variable size format: `uvarint(length) || *elements`
- Fixed size format: `*elements`
- Elements are serialized according to the scheme of the element. 
- All elements are of the same type which is specified by the schema of the container

### Tuple

- Tuple is heterogenous
- Format: `uvarint(length) || *elements`
- Each element is serialized according to the scheme specified in the tuple

### Variant

- Similar to union from C, stores precisely one data type out of many
- Variants are identified by 1 byte code
- Format: `uint(variant_code) || variant_object`
- Variant object is serialized according to the scheme corresponding for the particular variant

### Message / object

- Collection of heterogenous fields
- Fields are serialized according to the scheme
- Field ordering is fixed by the message scheme
- Field have names, but no name nor number of fields are serialized 
- Messages serialization scheme can vary based on the version number provided from outside



## Boost serialization

- Mainly used by the wallet and for internal purposes.
- Scheme oriented format. Scheme is required to understand the serialized data.
- Versioned serialization format, explicitly storing version numbers to the serialized data.
- Reference: [Boost Serialization](https://www.boost.org/doc/libs/1_61_0/libs/serialization/doc/index.html)
- Archive starts with the header `011673657269616c697a6174696f6e3a3a617263686976650000` which translates to `\x01\x16serialization::archive\x00\x00`. The `[-2]` byte enables tracking (tracking is not supported in this lib), `[-1]` is a version of root element.
- [Basic archive](https://www.boost.org/doc/libs/1_66_0/libs/serialization/src/basic_oarchive.cpp)

### Versioning
- Schemes are versioned based on the C++ type, this python lib identifies the object based on its type and parameters (e.g. container + element type). Once the version for particular type has been stored to the stream, it is not stored again. In C++ this is handled by the type system and compiler. In this library we have to explicitly track whether the type version has been already stored. 
- Elementary types are not versioned (int, uvarint, unicode)
- Versioning can be disabled in the complex types 
- Version is stored as the following tuple: `(uvarint(tracking) || uvarint(version))`
  - tracking relates to the [Boost Object Tracking](https://www.boost.org/doc/libs/1_61_0/libs/serialization/doc/special.html#objecttracking), advanced construct used with pointers (tracking by memory address), alpha version of tracking is supported for reading the archive.
  - tracking in C++ code: `BOOST_CLASS_TRACKING`
  - Versioning in the [Boost docs](https://www.boost.org/doc/libs/1_61_0/libs/serialization/doc/tutorial.html#versioning)
  - If tracking is enabled, the format is: `(uvarint(tracking) || uvarint(version) || uvarint(object_id))`

### Uvarint

- First byte encodes length and sign. Supports byte widths: 0-8. 2 byte positive number: 0x2, 2 byte negative number: 0xfe
- Encoding in 8bit chunks, little endian.
- Uvarint serialization scheme defined by Monero code.

### Unicode 

- Format: `uvarint(length) || input.encode("utf8")`

### Blob

- Format: `uvarint(length) || data`

### Container

- Primitive type containers are not versioned, in general, container is versioned.
- After version follows `uvarint(length)`
- Version of the element follows as `uvarint(element_version)` (exception for case of raw containers = statically allocated like Key64)
- Elements follow. If element is serialized for the first time, same rules apply for the versioning - version is stored.
- Example: `(tr, v), collection_size, element_version, (obj_tr, obj_v), obj1, obj2, ...`

### Tuple

- Versioned
- Stored without size information - obtained from the scheme

### Variant

- Versioned
- Format: `uvarint(variant_code) || field`
- Example: `(tr, v), which, (tr, v), val`

### Message

- Versioned
- Stores field in a defined order, without storing field names or field types. Types are derived from the scheme.
- Fields serialized recursively.

## JSONRPC 

- Monero serialization format, with either binary or JSON form
- Defines serialization types supported by the format, each supported serialization primitive has a tag.
  - signed and unsigned integers of a fixed widths of: 18, 16,32, 64 bits
  - boolean 
  - double
  - string
  - object
  - array

- Root of archive starts with the `0x01011101 || 0x01020101 || 0x1`, i.e, signature A, signature B, format version
- Archive can be parsed as JSON, i.e., without scheme.

### Integers
- Integer to encode is N, then the format encodes `N<<2 | size_flag` as little endian
- Flags 0, 1, 2, 3 correspond to 1, 2, 4, 8 byte integers correspondingly 

### String
- Format: `uvarint(length) || data`

### Array
- Serializes `element_type | SerializeType.ARRAY_FLAG` as integer, where `element_type` is the object tag.
- Serializes length of the container
- Serializes each element recursively

### Section / object
- Correspond to JSON dictionaries with string keys
- Format: `uvarint(length) || serialize_string(section_1) || serialize_storage(value_1)`
- The `serialize_storage` serializes:
  - object tag if object type does not have `ARRAY_FLAG` flag
  - object itself recursively
  
