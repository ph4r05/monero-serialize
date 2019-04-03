# Unordered map serialization

Definitions: 

- `/usr/local/include/boost/serialization/unordered_map.hpp`
- `/usr/local/include/boost/serialization/unordered_collections_save_imp.hpp`
- `/usr/local/include/boost/serialization/unordered_collections_load_imp.hpp`

`unordered_set` and `unordered_map` have the same serialization mechanism.

## Schema

Container `value_type` for `unordered_map`:
```cpp
typedef pair<const key_type, mapped_type>              value_type;
```

Container `value_type` for `unordered_set`:
```cpp
typedef _Value                                                     key_type;
typedef key_type                                                   value_type;
```

Serialization mechanism:
```cpp
ar << BOOST_SERIALIZATION_NVP(count);
ar << BOOST_SERIALIZATION_NVP(bucket_count);
ar << BOOST_SERIALIZATION_NVP(item_version);

typename Container::const_iterator it = s.begin();
while(count-- > 0){
    // note borland emits a no-op without the explicit namespace
    boost::serialization::save_construct_data_adl(
        ar, 
        &(*it), 
        boost::serialization::version<
            typename Container::value_type
        >::value
    );
    ar << boost::serialization::make_nvp("item", *it++);
}
```

- The `save_construct_data_adl` saves nothing as default constructor requires no param in this case.
- The `ar << boost::serialization::make_nvp("item", *it++);` saves `pair<const key_type, mapped_type>`.

