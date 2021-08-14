# Getting Started


## Section

- [Installation](##setting-up)

- [Usage](##usage) 

- [Internals of spec-parser](./internals.md)

- [Grammar specification of parser](./grammar.md)

- [Information on Defaults Error checking](./error_checks.md)


## Setting Up

TODO

## Usage

### For parsing specfication

```
❯ python src/driver [spec-folder]
```

### Detailed information about usage

```
❯ python src/driver.py --help
usage: spec-parser [-h] [--md] [--table] [--refs] [--rdf] [--out OUT] spec_dir

SPDX specification parser

positional arguments:
  spec_dir    Directory containing specs

optional arguments:
  -h, --help  show this help message and exit
  --md        Dumps markdown
  --table     Use tabular format in Class for displaying Properties
  --refs      Generate References list for Property
  --rdf       Experimental! Generate RDF in turtle format
  --out OUT   Output Directory for generating markdown
```