# spec-parser

Automagically process the model of the SPDXv3 specification to validate input
and/or generate stuff.

## Functionality

The software always reads and validates the complete model (given as input).

It then optionally generates one or more of the following outputs:

1. JSON dump of the parsed model, to load all data without parsing
2. MkDocs files, to be used by mkdocs to generate a website
3. PlantUML file, to be used by plantuml to generate a diagram
4. RDF files (ontology and context), for any need
5. TeX files, to be used by LaTeX to generate a printable version
6. Web page files, to provide information on the RDF URIs

If no generation is specified in the command line,
the default functionality is to generate everything.

## Usage

```
usage: main.py [-h] [-V] [-d] [-v] [-f] [-n]
               [-o OUTPUT]
               [-j] [-J dir]
               [-m] [-M dir]
               [-p] [-P dir]
               [-r] [-R dir]
               [-t] [-T dir]
               [-w] [-W dir]
               input_dir

Generate documentation from an SPDXv3 model.

positional arguments:
  input_dir             Path to the input 'model' directory.

options:
  -h, --help                                Show this help message and exit
  -d, --debug                               Print debug output
  -f, --force                               Force overwrite of existing output directories.
  -j, --generate-jsondump                   Generate a dump of the model in JSON format.
  -J, --output-jsondump OUTPUT_JSONDUMP     Output directory for JSON dump file.
  -m, --generate-mkdocs                     Generate mkdocs output.
  -M, --output-mkdocs OUTPUT_MKDOCS         Output directory for mkdocs files.
  -n, --no-output                           Perform no output generation, only input validation.
  -o, --output OUTPUT                       Single output directory for all output types.
  -p, --generate-plantuml                   Generate PlantUML output.
  -P, --output-plantuml OUTPUT_PLANTUML     Output directory for PlantUML files.
  -r, --generate-rdf                        Generate RDF output.
  -R, --output-rdf OUTPUT_RDF               Output directory for RDF files.
  -t, --generate-tex                        Generate TeX output.
  -T, --output-tex OUTPUT_TEX               Output directory for TeX files.
  -v, --verbose                             Print verbose output
  -V, --version                             Show program version number and exit
  -w, --generate-webpages                   Generate web pages output.
  -W, --output-webpages OUTPUT_WEBPAGES     Output directory for web pages.

```

### Checking input

If no generation is needed and only input validation is required:

```shell
python3 main.py -n some/where/.../model
```

Note that no dependencies are needed.

## Prerequisites

| **Action** | *Prerequisites* |
|---|---|
| input validation (`-n`/`--no-output`) | None |
| JSON dump generation | [jsonpickle](https://pypi.org/project/jsonpickle/) Python module |
| MkDocs generation | [Jinja2](https://pypi.org/project/Jinja2/) Python module |
| PlantUML generation | None |
| RDF generation | [RDFlib](https://pypi.org/project/rdflib/) Python module |
| TeX generation | [Jinja2](https://pypi.org/project/Jinja2/) Python module and [pandoc](https://pandoc.org/) software |
| Web pages generation | [Jinja2](https://pypi.org/project/Jinja2/) Python module |

The software will check for the presence of prerequisites,
according to the calling arguments,
and exit if they are not present.

## Contributing

Contributions are always welcome!

Feel free to open issues for any behavior that is not
(or even simply does not seem) correct.

However, due to the pressure for releasing SPDXv3,
development is happening in fast mode,
and not always refelcted in this repository.
To save everyone valuable time, if you want to contribute code:
clearly indicate in the corresponding issue
your willingness to work on it,
and _wait_ for the assignment of the issue to you.
