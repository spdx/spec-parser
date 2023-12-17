# spec-parser

Automagically process the specification

## Sections

- [Installation](#installing-dependencies)

- [Usage](#usage) 

- [Internals of spec-parser](./docs/md_docs/internals.md)

- [Grammar specification of parser](./docs/md_docs/grammar.md)

- [Information on Defaults Error checking](./docs/md_docs/error_checks.md)


## Installing dependencies

```
❯ python3 setup.py install
```

or:

```
❯ pip install git+https://github.com/spdx/spec-parser
```

## Usage

```
❯ spec-parser -h
usage: spec-parser [-h] [--gen-md] [--gen-refs] [--gen-rdf] [--use-table] [--out-dir OUT_DIR] spec_dir

SPDX specification parser

positional arguments:
  spec_dir           Directory containing specs

optional arguments:
  -h, --help         show this help message and exit
  --gen-md           Dumps markdown
  --gen-refs         Generate References list for Property
  --gen-rdf          Experimental! Generate RDF in turtle and json-ld format, along with the json-ld context
  --use-table        Use markdown-table to display properties in `Class` entity
  --out-dir OUT_DIR  Output Directory for generating markdown
```

## Current Roadmap

- [X] Validating and reporting all possible parsing error (in any) the incoming markdown files.
- [X] Auto generating Pretty markdowns.
- [X] Adding defaults and Generating cross-references.
- [X] Generating RDF in Turtle format.
- [ ] Adding Restrictions in RDF.