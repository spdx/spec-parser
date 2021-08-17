# Defaults and Error checking in spec-parser

## Defaults in Metadata

Following metadata attributes are added, if not present in original input.

- `id`: [`https://spdx.org/rdf/<namespace>#<name_of_entity>`]
- `Instantiability`: [`Concrete`]
- `Status`: [`Stable`]

## Valid Metadata key

If the metadata key doesn't match the following list, error is reported. 

- `name`
- `SubclassOf`
- `Nature`
- `Range`
- `Instantiability`
- `Status`

## Defaults in Data-Property attributes

Following Data-property attributes are added, if not present in original input.

- `minCount`: [`0`]
- `maxCount`: [`*`]


## Valid Data property attribute key

If the Data-property attribute key doesn't match the following list, error is reported.

- `type`
- `minCount`
- `maxCount`