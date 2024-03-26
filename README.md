# spec-parser

Automagically process the model of the SPDXv3 specification to validate input or to generate stuff.

## Build / Install

```
python3 -m pip install build
python3 -m build
```

This creates a wheel file in `dist` that can be installed.  Alternatively,
run setup.py to install:

```
python3 ./setup.py install
```

## Usage

```
spec-parser -h 
usage: main.py [-h] [-d] [-f] [-n] [-q] [-v] [-V] input_dir [output_dir]

Generate documentation from an SPDX 3.0 model

positional arguments:
  input_dir       Directory containing the input specification files
  output_dir      Directory to write the output files to

options:
  -h, --help      show this help message and exit
  -d, --debug     Print debug output
  -f, --force     Overwrite existing generated files
  -n, --nooutput  Do not generate anything, only check input
  -q, --quiet     Print no output
  -v, --verbose   Print verbose output
  -V, --version   show program's version number and exit
```

Note that not all flags are functional yet.

### Checking input

```
spec-parser -n some/where/.../model
```

Note that no dependencies are needed.

### Generate output
```
spec-parser some/where/.../model some/where/else/.../output_dir
```


## Current status (mostly complete / in progress)

- [x] parse everything in model
- [x] generate mkdocs input
- [x] generate JSON dump
- [x] generate diagrams
- [x] generate RDF ontology
- [x] generate JSON-LD context


## Contributing

Contributions are always welcome!

Feel free to open issues for any behavior that is (or even simply does not seem) correct.

However, due to the pressure for releasing SPDXv3, development is happening in fast mode, and not always refelcted in this repository.
To save everyone valuable time, if you want to contribute code: clearly indicate in the corresponding issue your willingness to work on it, and _wait_ for the assignment of the issue to you.

