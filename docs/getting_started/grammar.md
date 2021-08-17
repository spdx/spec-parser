# Grammar for structured markdown input

## Lexer Regex (In order of priority)
```python
COMMENT: r'(?:(?!\n)\s)*<!?--(?:(?!-->)(.|\n|\s))*-->(?:(?!\n)\s)*\n*'

SUMMARY = r'((?<=\n)|^)\#{2}\s+Summary(?:(?!\n)\s)*(\n+|$)'
DESCRIPTION = r'((?<=\n)|^)\#{2}\s+Description(?:(?!\n)\s)*(\n+|$)'
METADATA = r'((?<=\n)|^)\#{2}\s+Metadata(?:(?!\n)\s)*(\n+|$)'
PROPERTIES = r'((?<=\n)|^)\#{2}\s+Properties(?:(?!\n)\s)*(\n+|$)'
ENTRIES = r'((?<=\n)|^)\#{2}\s+Entries(?:(?!\n)\s)*(\n+|$)'

H6 = r'((?<=\n)|^)\s*\#{6}'
H5 = r'((?<=\n)|^)\s*\#{5}'
H4 = r'((?<=\n)|^)\s*\#{4}'
H3 = r'((?<=\n)|^)\s*\#{3}'
H2 = r'((?<=\n)|^)\s*\#{2}'
H1 = r'((?<=\n)|^)\s*\#{1}'
H_TEXTLINE = r'(?<=\#)[^\n]+(\n+|$)'

ULISTA = r'((?<=\n)|^)[*+-][^\n]+(\n+|$)'
ULISTB = r'((?<=\n)|^)([ ]{2,4}|\t)[*+-][^\n]+(\n+|$)'

TEXTLINE = r'((?<=\n)|^)[^\n]+(\n+|$)'
NEWLINE = r'\n+'

```

## CFL for `Class` Entity

```
document:
    maybe_newlines name summary description metadata properties

name:
    H1 H_TEXTLINE

summary:
    SUMMARY para

description:
    DESCRIPTION para

metadata:
    METADATA metadata_list

metadata_list:
    metadata_list metadata_line
    | empty

metadata_line:
    ULISTA

properties:
    PROPERTIES properties_list

properties_list:
    properties_list single_property
    | empty 

single_property:
    ULISTA avline_list

avline_list:
    avline_list avline
    | empty

avline:
    ULISTB

para:
    para para_line
    | empty

para_line:
    TEXTLINE
    | ULISTA
    | ULISTB

newlines:
    NEWLINE

maybe_newlines:
    newlines
    | empty

empty:

```

## CFL for `Property` Entity

```
document:
    maybe_newlines name summary description metadata

name:
    H1 H_TEXTLINE

summary:
    SUMMARY para

description:
    DESCRIPTION para

metadata:
    METADATA metadata_list

metadata_list:
    metadata_list metadata_line
    | empty

metadata_line:
    ULISTA

para:
    para para_line
    | empty

para_line:
    TEXTLINE
    | ULISTA
    | ULISTB

newlines:
    NEWLINE

maybe_newlines:
    newlines
    | empty

empty:

```


## CFL for `Vocab` Entity

```
document:
    maybe_newlines name summary description metadata entries

name:
    H1 H_TEXTLINE

summary:
    SUMMARY para

description:
    DESCRIPTION para

metadata:
    METADATA metadata_list

metadata_list:
    metadata_list metadata_line
    | empty

metadata_line:
    ULISTA

entries:
    ENTRIES entry_list

entry_list:
    entry_list entry_line
    | empty

entry_line:
    ULISTA

para:
    para para_line
    | empty

para_line:
    TEXTLINE
    | ULISTA
    | ULISTB

newlines:
    NEWLINE

maybe_newlines:
    newlines
    | empty

empty:

```