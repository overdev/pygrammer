# pygrammer
A pure Python recursive descent parser generator for non too-technical language grammars

## Table of contents

1. Basic Example
2. How to use pygrammer
3. Features
4. Installation

## 1. Basic Example

Pygrammer defines a somewhat custom EBNF syntax that looks like the code below:

```
;; pygrammer grammar example

;* Token section

Tokens can be defined as regular strings or regular expressions, although the generator always takes them as regexes.
A valid token definition requires:
- the definition to be inside the .token and .end markups;
- the name to be ALL_CAPS;
- the value to immediately follows the name

Token value regular expressions should follows the Python's re lib.
Tokens can also be given decorators to indicate how the generator should treat them.
*;
.token

WHITESPACE  `\s+`       @skip                   ;; make witespace characters to be ignored when found

ALPHA       `[a-zA-Z]`  @internal               ;; internal tokens don't have parsing functions
NUM         `[0-9]`     @internal
ALNUM       `ALPHANUM`  @internal   @expand     ;; expand replaces token names in the RE with their values

WORD        `ALPHAALNUM*`   @expand ^KEYWORD    ;; acceptable WORD values must excludes values in the KEYWORD token group
STRING      `(['"])(.*?)(\1)`       @2          ;; marks the token value to be group indicated by the index

INTEGER     `NUM+`      @expand
FLOAT       `NUM+\.NUM` @expand

.end

;* Token group section(s)

Token groups works mostly like individual tokens, except that they can be limited range of values.
Valid token group definitions require:
- a list of one or more values inside the .token: <name> and .end markups;
- the name to be ALL_CAPS;

Token groups cannot have decorators.
*;

.token: KEYWORD
'if'
'else'
'while'
'return'
'continue'
'break'
'print'
'let'
.end

.token: OPERATOR:
'+'
'-'
'*'
'/'
'%'
.end

;* Rules section

Valid rules requires:
- the name to in strict PascalCase, so rule names with abreviations aren't considered valid (e.g. 'RGBColor')

Rules can be given attributes and directives. These, like token decorators, indicate how the generator should treat them.
Rule definition item can have capture names. These names defines what goes inside and what is ignored in the AST node of each rule
*;

.rules

;; The Block rule doesn't required Statement to be defined ahead of it
Block:
    @{scope:localvars}
    = '{' Statement* '}'        =>  _ statements _   ;; '=>' allows for node capturing; '_' are ignored
    ;

Number:
    @{merge}    ;; the 'merge' directive causes the node contents to be merged into the parent node
    = INTEGER
    | FLOAT
    ;

Operand:
    = WORD      => operand
    | Number        => operand
    ;

Operation:
    @{key: left}    ;; the 'key' attribute tries to reduce the Operation node to its key, avoiding long AST branches
    = Operand ( OPERATOR Operand )*     => left ( operator right )  ;; capture names must honor inline groups
    ;

IfStatement:
    = 'if' OPERAND Block    => _ condition block
    ;

WhileStatement:
    = 'while' OPERAND Block     => _ condition block
    ;

PrintStatement:
    = 'print' Operation ';'     => _ expr _
    ;

Assignment:
    = WORD '=' Operation ';'    => lvalue _ rvalue
    ;

VarDeclaration:
    @{declare: name}    ;; this node name and definition will be added to the current scope
    = 'let' WORD '=' Operation ';'    => _ name _ value _
    ;

Statement:
    = IfStatement
    | WhileStatement
    | PrintStatement
    | VarDeclaration
    | Assignment
    ;

Script:
    @{scope:localvars}  ;; scope attribute for declaring global variables
    = Statement*
    ;

.end

Past the .end, you can write whatever you want. The parser won't read it.

```

## 2. How to use pygrammer

It is fairly simple.

First you define the grammar for the language model you want a parser for, line the basic example above.

With pygrammer installed, first open the terminal and run it with command below:

```
$ pygrammer --help
```

This will give you basic information on the arguments you must and can pass to pygrammer. 

Now, with your grammar file _in hand_, run pygrammer with this command:

```
$ pygrammer path\to\my\grammar.txt --out where\i\want\to\save\my_language_parser.py --verbose warning
```

Changing, of cource, the file paths to your test case.

After this, if pygrammer run with any errors or warnings, you should see them in the terminal. Warnings won't stop the generator, only errors do so.

If no errors were encountered, you should see a new file in the location of the `--out` parameter value.

Now you have a parser module that should be able to parse any source following the grammar you defined. This module was generated so that you can use in some project or directly from the terminal.

If you use it as an imported module, you just need to:

```python
from my_parser import parse  # parse() is all that you need to parse any source file
```

To use it in the terminal, you can:

```
$ python3 my_parser.py --help
```
to get commandline information, then:

```
$ python3 my_parser.py path\to\my\source_code.ext --out where\i\want\to\save\my_source_ast.json --start StartingRule
```

Set `--start` to the grammar rule name you want the parser to begin parsing

The output of the parser is an AST, but it is possible that is runs without producing a significant result. In this case, no file is created.

Otherwise, if everything went fine, you should see a new _JSON_ file in the location of the `--out` parameter value.

That's how you use pygrammer.


## 3. Features

If you read the items 1 and 2, you already know it

- Meant to be used as development cli tool
- Generates Python code that you can run, read, undersand and modify to fit your needs
- Gives some little tools that allows customisation of the parser algorithm (decorators, attributes, directives)
- The generated parser produces the AST in _JSON_ format so you can use it with other available tools elsewhere
- Easy to learn and to use. Please, check out the [documentation](https://github.com/overdev/pygrammer/blob/master/DOCUMENTATION.md).


## 4. Installation

As of now, pygrammer is not production-ready (it's planned to be only in v.1.0.0), so you can only install from the [releases tab](https://github.com/overdev/pygrammer/releases) (not available in PyPI yet). Please, feel free to try it and [report any issues](https://github.com/overdev/pygrammer/issues) you may encounter.

Install it with pip:

```
$ pip install <link to the python wheel file>
```
