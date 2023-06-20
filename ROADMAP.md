# ROADMAP

## Plans for v1.0.0

### Features

- [ ] More attributes, directives and decorators, wich may or may not come in v1.0:
    - [ ] `forward:key` attribute to propagates the `node[key]` to its components
    - [ ] `kind:NODE_KIND` attribute (re)define de `node['kind']` after parsing a rule
    - [ ] `keepkind` directive prevent `merge` directive from overwriting the node kind
    - [ ] `join` directive to merge in the parent node only the items the parent node does not have
    - [ ] `file`, `filename`, `absdir`, `reldir` directives to add the respective file information to the node
    - [x] `@relfilepath` token decorator to check after matching if the value is a valid relative file path string format
    - [x] `@absfilepath` token decorator to check after matching if the value is a valid absolut file path string format
    - [x] `@reldirpath` token decorator to check after matching if the value is a valid relative directory path string format
    - [x] `@absdirpath` token decorator to check after matching if the value is a valid absolut directory path string format
    - [ ] **CANCELLED**: `@mustexist` token decorator to use along `@relfilepath`, `@absfilepath`, `@reldirpath` and `@absdirpath` to ensure the file or directory exists
    - [x] `@loadandparse` token decorator to take the value as a source file path, load its contents, parse it and return its AST
    - [ ] `.import .. .end` section to add import external functions to be called by the parser (to be used with the `transform:callable` attribute)
    - [ ] `transport:callable` attribute to perfom any desired transformation on the node before returning it from the parsing function
- [ ] **NOW IN v1.0.0** Tokenizer:
    - [x] Generate a stream of tokens that can be used for syntax highlighting
- [ ] Allow the parser to work also on strings.

- [ ] Whatever relevant comes to mind in the process

### Revisions

- [ ] Review the code generation system to reduce the file size
    - [x] `is_*()` functions for rules got way smaller, basically one-liners.
    - [ ] remove code repetitions (WIP).
    - [ ] remove generated code that never gets called.
- [x] Keep `node['some_list'] = []` from getting in the way of `@{key:some_item}` when no item is ever appended.
- [ ] Review the logging system to fix or mitigate the _log explosion_
- [x] Try to eliminate the limitations of the parser regarding complex rules, which cause noticiable bottlenecks
    - [x] `is_*()` functions for rules don't cheat anymore by calling `match_*()` to see if it returns `None`.

### Documentation

- [ ] Publish the documentation on ReadTheDocs

## Plans for v1.1.x

### Revisions

- [ ] Tokenizer:
    - [ ] Ensure the stream can be incrementally generated
