# pygrammer Documentation

## 1. Basics

### 1.1 The pygrammer grammar file format

Every grammar file is expect to contain:

- Token definitions
- Zero or more token group definitions
- One or more rule definitions

### 1.2 The grammar file basic layout

Looking at the very basic layout, the grammar is composed of sections:

```
;; This is a single line comment

;* This is
a multiline
comment *;

.token
;; here goes all token definitions
.end

.token: SOME_GROUP
;; here goes a list of token values of kind SOME_GROUP
.end

;; more token groups can be defined here

.rules
;; here goes all rule definitions, at least one is necessary
.end

;; from here there can be anything
```

## 2. Sections

Only 3 types of sections exist:

- `.token` for individual token definitions
- `.token: NAME` for definition of groups of tokens, if necessary
- `.rules` for definition of parsing rules

All must be terminated with `.end`.

### 2.1 The `.token` section

In the `.token` section any number of tokens can be defined. Token definitions take the form:

```
TOKEN_NAME `regular_expression` ( @decorator | ^EXCLUSION )*
```

where:

- `TOKEN_NAME` is the name of the token, strictly in ALL_CAPS;
- `` `regular_expression` `` is the RE string;
- `@decorator` can be any decorator applicable to the token
- `^EXCLUSION` can be any token group name which values this token cannot match

### 2.2 The `.token: NAME` section

The `.token:NAME` section is optional and any number of groups can be defined.
In token groups, the name must be ALL_CAPS. Token groups cannot be given decorators nor exclusions.
Each group item should be on its own line. Token group items take the form:

```
'regular_expression'
```

where:

- `'regular_expression'` is the RE string;

### 2.3 The `.rules` section

In the `.rules` section any number of tokens can be defined, being one the minimun required.
The basic form of a rule is like it follows:

```
RuleName:
    OptionalAttributesOrDirectives
    = ruleDefinition
    | oneOrMoreAlternativeRuleDefinitions
    ;
```

And it can look like:

```
RuleName:
    @{attribute:value, directive}
    = SOME_TOKEN_REFERENCE 'someTokenLiteral' SomeRuleReference   ;; each line is a rule definition
    | OtherRuleReference ( 'literal_inside_group' RuleInsideGroupReference )*
    | [ 'optionalLiteral' OptionalRuleReference ] ANOTHER_TOKEN_REFERENCE
    ;
```

where:

- `RuleName` is the name of the rule, strictly in PascalCase form. Names like `RGBColor` (with acronyms) are not valid.
- `@{...}` a set of directives or attributes to customize the rule behavior or output
- `attribute:value` can be any attribute and value applicable to the rule;
- `directive` can be any directive applicable to the rule;
- `SOME_TOKEN_REFERENCE`, `ANOTHER_TOKEN_REFERENCE` can be the name of any individual or group of tokens defined in their sections;
- `'someTokenLiteral'`, `'literal_inside_group'`  and `'optionalLiteral'` can be any valid regular expression or string;
- `SomeRuleReference`,  `OtherRuleReference` and `OptionalRuleReference` can be the name of any rule defined in the `.rules` section.

#### 2.3.1 Inline Groups in Rule definitions

Rule definitions can have inline groups of references or other groups. There are tree types of groups:

- Optional: `[ item1 item2 .. itemN ]`

    If the first item matches, then the following itens in the group must also match.

- Sequential: `( item1 item2 .. itemN )`

    All itens in the group must match. Sequential groups should be closed with either:
    - `)?` indicating zero or one match of the group,
    - `)+` indicating one or more matches of the group, or
    - `)*` indicating zero or more matches of the group.

- Alternative: `( item1 | item2 | .. | itemN )`

    Must match one of the items in the group. It can also be closed either by `)?`, `)+` or `)*`, like sequential groups.


## 3. Capturing rule matches

For a good grammar to produce a good AST, its rules must define _capture names_. A _capture_ is the name of a branch inside an AST node. If a rule defines no capture names for its items, the resulting node returned from the parse function will contain only the node _kind_ and, in some cases, the location where it occurs in the source. This means the AST will have only the root node.

Also, many rule attributes and directives depend on the definition of capture names.

To define capture names is very easy. Consider the Rule definition below:

```
ConstantDecl:
    = 'constant' WORD ':' TYPENAME [ '=' Expression ] ';'
    ;
```
There is nothing wrong with this `ConstantDecl` rule. A parsing function will be generated for it. If the intention is only syntactical, it will work as intended. For other purposes, like compilation, intepretation, transpilation and many other _*ations_, this won't be enough.

Capture names are defined by adding a sequence of names after the rule definition, followed by an arrow (`=>`). This sequence of names should match the order and organization of the rule items. Take a look at the same rule, below, now with capture names:

```
ConstantDecl:
    @{declare:name}
    = 'constant' WORD ':' TYPENAME [ '=' Expression ] ';'   => _ name.value _ typespec ( _ value ) _
    ;
```

The first thing to notice is that some names are defined as `_`. This means that the matched item can be ignored, no capture is assigned to it and it won't be added to the AST node returned. For syntactical purposes, these are still honored.

The next thing is this dotted name (`name.value`) for the `WORD` token. This is a field lookup, basically: `value` must be on the matched token otherwise it's an error. Now, All token matches have a `value` item, so this is safe. When `WORD` matches, only the `value` item is kept from it and added to the `ConstantDecl` node, named as `name`.

Next, we have `typespec`, which captures a token and will hold the whole TYPENAME node.

After, there is a inline optional group. This one may or may not be present. Either way, we should honor the itens inside of it.

In the definition of capture names, _order_ is required but completion is not. This means that it is OK to define names only up to a certain point and left the rest unnamed.

So, from `constant MAXLINES: int32;`, the resulting node from this rule should look like:

```jsonc
{
    "kind": "CONSTANT_DECL",
    "lc": [1, 1],   // lc means line and column, the location in the source file where it occurs
    "name": "MAXLINES",  // this is what we got from name.value
    "typespec": {
        "kind": "TYPENAME",
        "lc": [1, 20],
        "value": "int32"
    },
    // considering that the optional group didn't matched, value is not present.
}
```

### 3.1 List of matching items

In the example below:

```
Enumerands:
    ='{' EnumerandDecl ( ',' EnumerandDecl )* '}'   => _ *enumerands ( _ *enumerands ) _
    ;
```

The `enumerands` capture is preffixed with a star (`*`). In those cases where a rule item can be matched more than once under the same capture name, the star should prefix the capture. This means that the capture item is a list, and items will be appended to it as they get matched.

The same applies when the rule items themselves are marked with `?`, `+` or `*`.


## 4. Token decorators

These are the currenlty available decorators that can be applied to token definitions:

### 4.1 `@skip`

The `@skip` decorator causes the token to be ignored when it is matched. It does more than that, actually. It causes the token RE value to be added to an special parsing function that is called whenever the skippable tokens can be encountered. This function, surprinsingly, is called `skip()`. It is commom for grammars to ignore white spaces, newlines, comments, so this decorator makes this possible.

### 4.2 `@internal`

The `@internal` decorator causes the token no to be used inside other functions in the parser API. This is to avoid generating code that is not intended to be executed. Tokens with this decorator should be used along with the `@expand` decorator, described below.

### 4.3 `@expand`

The `@expand` decorator exists to avoid unnecessary repetion in token definitions. Sometimes, two or more tokens have portions of their REs that are exaclty equal. The idea behind this decorator is that tokens can reference other tokens by name in their values and then have these names expanded to the respective value.

Let's consider the tokens below:

```
DEC `0-9`           @internal
ALPHA `a-zA-Z`      @internal
ALNUM `ALPHADEC`    @internal @expand
WORD `ALPHAALNUM*`  @expand
```

Of the tokens defined above, only `WORD` will have code generated for it. Three functions will be provided:
- `is_word() -> bool`, to check if the next token is a `WORD`,
- `match_word() -> bool`, to try to match a WORD, and
- `expect_word() -> bool`, to demand a `WORD` token to be matched.

Now, `DEC`, `ALPHA`, `ALNUM` won't have their versions of these functions. On the other hand, they are used in the definition of `WORD`. For the value of `WORD` to be defined correctly, it have to be expanded to the values of `ALPHA` and `ALNUM`, which in turn have also to be expanded.

### 4.4 `@[1-9]`

For token definitions that contains matching groups, this decorator allows the token value to refer to the specified group index. If not applied, the index 0 is used.

## 5. Token exclusions

A valid token exclusion is the name of any token group defined, preffixed by `^`.

## 6. Rule attributes

Rule attributes are `key:value` pairs added to a `@{}` element in a rule definition.

### 6.1 `key`

The `key` directive exists to prevent long branch formations in the AST as the result complex rule nestings in the grammar. Although rule nesting can go deep, it is common that the nodes in it are simple enough that their presence is redundant and they can be removed from the tree without changind its overall meaning. Rules with `key:name` applied are those which nodes can be removed from the AST whenever a specific condition is met: that the only components in the output node are the `kind` and the `key` item named `name`. When this condition is met, the `key` item is returned instead of the node, resulting in a less deep tree.

> NOTE: for the `key` attribute to work, the rule definition must define a capture name for its items.

Consider the piece of grammar below:

```
Operand:
    = ...   ;; hidden for sake of brevity
    ;

SumOperation:
    @{key:left}
    = Operand [ '+' Operand ]     => left ( _ right )
    ;
```

Without the `key` attribute, whenever the parser runs `SumOperation`, it will produce and return:

```jsonc
// this
{
    "kind": "SUM_OPERATION",
    "left": { "kind": "OPERAND", /* ... */ },
    "right": { "kind": "OPERAND", /* ... */ }
}
// or this
{
    "kind": "SUM_OPERATION",
    "left": { "kind": "OPERAND", /* ... */ },
    "right": null
}
```

But with `key:left` applied, the same run will produce and return:

```jsonc
// the node with all its important parts
{
    "kind": "SUM_OPERATION",
    "left": { "kind": "OPERAND", /* ... */ },
    "right": { "kind": "OPERAND", /* ... */ }
}
// or the only part that matters: the 'left' item itself
{
    "kind": "OPERAND",
    /* ... */
}
```

### 6.2 `flip`

As the name may suggest, the `flip:name` existis to invert the positions between _parent_ and _child_ nodes. There are situations where a item matched inside a rule should be the logical parent of the rule itself but it is matched as a child only because it happens to match after (and when) the parent matches.

> NOTE: the `flip` must be applied on the parent that will became the child

Consider the example below:

```
;; BaseOp can be field lookup, array subscription or function call with an UnaryOperand node as its base
BaseOp:
    = '.' WORD            => _ field
    | '[' NUMBER ']'      => _ index _
    | '(' Arguments ')'   => _ args _
    ;

UnaryOperand:
    @{ key: operand, flip: base}
    | Operand [ BaseOp ]       => operand ( base )
    | ...
    ;
```

In this case, whenever `base` matches in `UnaryOperand`, instead of adding `base` to it, the opposit happens. The `BaseOp` item matched as `base` will have the `UnaryOperand` parent node as item named `base` in it. `UnaryOperand` will then return a `BaseOp` with its _parent_ as its _child_.


### 6.3 `scope`

The `scope:name` attribute changes the behavior of the rule so it act as a namespace. The only effect of this attribute is to add and item in its output node named `name`. This means that this attribute does not work on its own, but should be used in conjunction with othe attribute, described below, namely: `declare`. The rule scope is pushed when the rule starts to be parsed and popped at the end, to allow for nested scopes. The objective of scopes is to enable the matching of multiple items that can be identified by a key in which the value is unique inside the active scope.

> NOTE: `scope` attributes should be applied on _parent_ rules.

### 6.4 `declare`

The `declare:name` attribute changes the rule behavior when used along with the `scope` attribute. The rule is _declared_ when a scope is active, it has an item name `name` that must be of value type `str` and this value is not a item in the scope namespace.

Consider the following grammar:

```
FunctionBlock:
    @{scope:names}
    = '{' VariableDecl+ '}'
    ;

VariableDecl:
    @{declare:name}
    = 'let' WORD ':' TYPENAME [ '=' Expression ] ';'   => _ name.value _ typespec ( _ value ) _
    ;
```

`FunctionBlock` defines a scope to _declare_ any matching `VariableDecl` item. Take a look at the capturing name for the `WORD` token: it is `name.value`. This notation is a variant of the `key:name` attribute, with the difference that it is an error when `.value` is not found in the matched item, but is OK when the `key` is not found. It is guarranteed that all matched tokens have a `value` item, so this capture will never fail. Also, `value` is always a string, which can be used as an identifier as its capture value (`name`) suggests.

Inside `FunctionBlock`, the matched item returned by `VariableDecl` (note that it does not have a capture name defined) will be looked up for an item named `name`. If this item exists and is a string value, it will be checked against the items in the scope. If there is already an item with the same name, an error message is printed and the parser is interrupted. Otherwise, this `VariableDecl` item matched is added to the scope under is own name and the parsing continues.

### 6.5 `verbosity`

`verbosity:level` exists for logging and debugging purposes. When the rule runs, the verbosity level specified is pushed at the beginning and popped at the end. This allows to filter which and where log messages are displayed. Verbosity levels are:

- `error`: only error messages are displayed
- `warning`: only error and warning messages are displayed
- `debug1`: only debug1 and the above messages are displayed. Debug1 are less frequent and less detailed.
- `success`: only success and the above messages are displayed.
- `debug2`: only debug2 and the above messages are displayed. Use with care.
- `info`: only info and the above messages are displayed
- `debug3`: only debug3 and the above messages are displayed. Debug3 are very frequent and more detailed. Can cause _log explosion_ in the console.
- `all`: shows all messages. It is quite certain that it _will_ cause _log explosion_.


## 7. Rule directives

Rule directives are `actions` added to a `@{}` element in a rule definition.

### 7.1 `merge`

The `merge` rule exists to allow the definition of rules that have the _same start_ but _different ends_. There are situations where it is difficult to know in advance the exact rule because it can be one of many similar rules. The approach to this problem is to define _child_ rules that branches out from this similarity, and when they get matched inside the parent rule, their items get transferred to the parent, turning it into the item it was trying to detect.
 
Consider this grammar piece:

```
StructMemberBody:
    @{merge}
    = ':' TYPENAME ( PropertyDecl | FieldDecl )     => _ typespec body
    | MethodDecl    => body
    ;

StructMember:
    @{declare:name}
    = WORD StructMemberBody     => name.value body
    ;
```

Imagine that in a rule for a struct member, there can be fields, properties and methods, all starting by the name. There is no way to know whether the member is a field or a property. The answer may be many tokens ahead. In `StructMember`, the `body` item can be any of the three (`PropertyDecl`, `FieldDecl` or `MethodDecl`). Even when is clear that it is not a method, it still unclear whether it is a field or property. In this example, `PropertyDecl`, `FieldDecl` and `MethodDecl` should receive the `merge` directive. Whatever is matched for `body` in `StructMemberBody`, gets merged into it, becoming the item it matched. Then again, when `body` is metched in `StructMember` it gets merged into it. At the end, `StructMember` becomes either a `PropertyDecl`, a `FieldDecl` or a `MethodDecl`.

