## Purpose
- To identify the structure of Markdown representation
- To create RegEx and Grammar specification for this structured markdown. 
- To validate and report all possible parsing error (if any) in the inputted markdown file.
- To be used as GitHub action for reporting parsing error (if any) in markdown files.
- [Extended Purpose] To automate the process of maintenance of SPDX specs in all format by only changing Markdown files. 


## Deliverables

#### Community Bonding
- [X] Review the existing discussion and work done around the structure of markdown representation.

#### Mid evaluation Deliverables
- [ ] Proposing and documenting the specification of structured markdown in form of RegEx and CFL.
- [ ] Implementing the parser for models, profiles with error checking and error reporting. 
- [ ] Extending parser to auto generate pretty markdown. 

#### Final Evaluation Deliverables
- [ ] Extending the parser to output relation information in desired format.
- [ ] Documenting and testing the tool with existing markdowns.
- [ ] Improving and packaging tool as a package for better portability.

## Implementation language and tools
- Python 3
- [SLY framework](https://github.com/dabeaz/sly)

CC: @zvr, Matthew Crawford