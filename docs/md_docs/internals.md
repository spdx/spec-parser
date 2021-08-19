# Internals

## Workflow

1. Given the `spec` folder, spec-parser traverse this folder and discover all `namespace` folders and extract all the `Classes`, `Properties` and `Vocabularies` inside respective `namespace` folder. [Ref: `spec_parser/spec_parser.py`]
2. Each entity (ie. `Class`, `Property` or `Vocab`) is specified in the structured markdown format, so appropriate LALR(1) parser parse the structured markdown format, and relevant parsing errors are reported. [Ref: `spec_parser/parser.py`]
3. When a specific entity is parsed successfully, all parsed information are passed to create object internally and references information are extracted and applied internally. [Ref: `spec_parser/utils.py`]
4. Once, all the entities are parsed and processed, we generate pretty markdowns and RDF. [Ref: `spec_parser/utils.py`]

## Major Components

### 1. `SpecParser` (path: `spec_parser/spec_parser.py`)

This class is used for traversing the input `spec` folder, and traversing the folder and discovering all the namespaces and all their entities. The primary task of this class is to parse the spec folder. 

### 2. `Spec` (path: `spec_parser/utils.py`)

This class stores all the namespaces (including all entities inside it). This class also maintain Spec level information like references and name of all entities and namespaces. 

### 3. `SpecClass` (path: `spec_parser/utils.py`)

This class stores the parsed information of `Class` entity. This class also consists of method such `_gen_md` and `_gen_rdf`, which generate pretty markdown and populate relevant RDF information respectively. 


### 4. `SpecProperty` (path: `spec_paresr/utils.py`)

This class stores the parsed information of `Property` entity. This class also consists of method such `_gen_md` and `_gen_rdf`, which generate pretty markdown and populate relevant RDF information respectively. 


### 5. `SpecVocab` (path: `spec_parser/utils.py`)

This class stores the parsed information of `Vocab` entity. This class also consists of method such `_gen_md` and `_gen_rdf`, which generate pretty markdown and populate relevant RDF information respectively. 

### 6. `MDLexer` (path: `spec_parser/parser.py`)

This is the common lexer for all the 3 parser. This lexer has dependecy of `sly` (which is a LALR(1) parser generating python package). 

### 7. `MDClass` (path: `spec_parser/parser.py`)

This is the parser for `Class` entity.


### 8. `MDProperty` (path: `spec_parser/parser.py`)

This is the parser for `Property` entity.


### 9. `MDVocab` (path: `spec_parser/parser.py`)

This is the parser for `Vocab` entity.

