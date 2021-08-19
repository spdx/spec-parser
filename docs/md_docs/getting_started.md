# Getting Started

## Sections

- [Installation](#installing-dependencies)

- [Usage](#usage) 

- [Internals of spec-parser](./internals.md)

- [Grammar specification of parser](./grammar.md)

- [Information on Defaults Error checking](./error_checks.md)


## Installing dependencies

```
❯ python3 -m pip install -r requirements.txt
```

## Usage

```
❯ python main.py -h
usage: spec-parser [-h] [--gen-md] [--gen-refs] [--gen-rdf] [--use-table] [--out-dir OUT_DIR] spec_dir

SPDX specification parser

positional arguments:
  spec_dir           Directory containing specs

optional arguments:
  -h, --help         show this help message and exit
  --gen-md           Dumps markdown
  --gen-refs         Generate References list for Property
  --gen-rdf          Experimental! Generate RDF in turtle format
  --use-table        Use markdown-table to display properties in `Class` entity
  --out-dir OUT_DIR  Output Directory for generating markdown
```