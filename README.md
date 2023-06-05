# pygrammer
A pure Python recursive descent parser generator for non too-technical language grammars

## Table of contents

1. Basic Example
2. How to use pygrammer
3. Features
4. Installation

## 1. Basic Example

Pygrammer defines a somewhat custom EBNF sintax that looks like the code below:

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
*;

.rules

Block:
    = '{' Statement* '}'        ;; The Block rule doesn't required Statement to be defined ahead of it
    ;

Number:
    @{merge}    ;; 'merge' causes the token to be merged into the Number rule
    = INTEGER
    | FLOAT
    ;

Operand:
    = WORD
    | Number
    ;

Operation:
    @{key: left}    ;; 'key' tries to reduce the Operation to its key, avoiding deeply nested AST nodes
    = Operand ( OPERATOR Operand )*     => left ( operator right )  ;; '=>' allows for node capturing, see below to learn more
    ;

IfStatement:
    = 'if' OPERAND Block
    ;

WhileStatement:
    = 'while' OPERAND Block
    ;

PrintStatement:
    = 'print' Operation ';'
    ;

Assignment:
    = WORD '=' Operation ';'
    ;

Statement:
    = IfStatement
    | WhileStatement
    | PrintStatement
    | Assignment
    ;

Script:
    = Statement*
    ;

.end

Past the .end, you can write whatever you want. The parser won't read it.

```
