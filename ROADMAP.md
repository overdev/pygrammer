# ROADMAP

## Plans for v1.0.0

### Features

- [ ] More attributes, directives and decorators, wich may or may not come in v1.0:
    - [ ] `forward:key` attribute to propagates the `node[key]` to its components
    - [ ] `kind:NODE_KIND` attribute (re)define de `node['kind']` after parsing a rule
    - [ ] `keepkind` directive prevent `merge` directive from overwriting the node kind
    - [ ] `join` directive to merge in the parent node only the items the parent node does not have
    - [ ] `file`, `filename`, `absdir`, `reldir` directives to add the respective file information to the node
    - [ ] `@relfilepath` token decorator to check after matching if the value is a valid relative file path string format
    - [ ] `@absfilepath` token decorator to check after matching if the value is a valid absolut file path string format
    - [ ] `@reldirpath` token decorator to check after matching if the value is a valid relative directory path string format
    - [ ] `@absdirpath` token decorator to check after matching if the value is a valid absolut directory path string format
    - [ ] `@mustexist` token decorator to use along `@relfilepath`, `@absfilepath`, `@reldirpath` and `@absdirpath` to ensure the file or directory exists
    - [ ] `@loadandparse` token decorator to take the value as a source file path, load its contents, parse it and return its AST
    - [ ] Whatever relevant comes to mind in the process

### Revisions

- [ ] Review the code generation system to reduce the file size
    - [x] `is_*()` functions for rules got way smaller, basically one-liners.
- [ ] keep `node['some_list'] = []` from getting in the way of `@{key:some_item}` when no item is ever appended.
- [ ] Review the logging system to fix the _log explosion_
- [ ] Try to eliminate the limitations of the parser regarding complex rules, which cause noticiable bottlenecks
    - [x] `is_*()` functions for rules don't cheat anymore by calling `match_*()` to see if it returns `None`.

### Documentation

- [ ] Publish the documentation on ReadTheDocs