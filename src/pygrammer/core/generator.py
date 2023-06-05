# -*- encoding: utf8 -*-

# region LICENSE
# ------------------------------------------------------------------------------
# The MIT License
#
#
# Copyright 2023 Jorge A. Gomes
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# ------------------------------------------------------------------------------
# endregion (license)

# region IMPORTS

import sys

from enum import Enum
from typing import Any, Sequence
from contextlib import contextmanager
from .grammar import *
from .parser import *
from .templates import *

# endregion (imports)
# ---------------------------------------------------------
# region EXPORTS


__all__ = [
    'compose',
]


# endregion (exports)
# ---------------------------------------------------------
# region GLOBALS


composer: 'SourceComposer' = None
grammar: 'GrammarNodes' = None
source: 'Source' = None

# endregion (globals)
# ---------------------------------------------------------
# region CONSTANTS & ENUMS


NEWLINE = '\n'
INDENT = '    '

# endregion (constants)
# ---------------------------------------------------------
# region CLASSES


class SourceComposer:
    """Utility class to generate the parser code for the provided grammar"""

    def __init__(self, output_filename: 'str'):
        self.output_filename: 'str' = output_filename
        self.output: 'str' = ''
        self.indent: 'int' = 0

    @property
    def indentation(self) -> 'str':
        """Gets the ammount of space needed in the current indentation level"""
        return INDENT * self.indent

    def write(self):
        """Writes the generated parser code into a file"""
        with open(self.output_filename, 'w', encoding='utf8') as fp:
            fp.write(self.output)

    def empty(self, num: 'int' = 1):
        """Adds one or more newlines to the output"""
        self.output += NEWLINE * num

    def empty_indent(self, num: 'int' = 1, lv: 'int' = 1):
        """Adds one or more newlines to the output, then increases the indentation level"""
        self.output += NEWLINE * num
        self.indent += lv

    def empty_dedent(self, num: 'int' = 1, lv: 'int' = 1):
        """Adds one or more newlines to the output, then decreases the indentation level"""
        self.output += NEWLINE * num
        self.indent = max(0, self.indent - lv)

    def indent_only(self, lv: 'int' = 1):
        """Increases the indentation level"""
        self.indent += lv

    def dedent_only(self, lv: 'int' = 1):
        """Decreases the indentation level"""
        self.indent = max(0, self.indent - lv)

    def empty_reset(self, num: 'int' = 1):
        """Adds one or more newlines, then sets the indentation level to zero"""
        self.output += NEWLINE * num
        self.indent = 0

    def inline(self, code: 'str'):
        """Appends the code string at the end of the output"""
        self.output += code

    def line(self, code: 'str'):
        """Adds a newline, then appends the code string at the end of the output following indentation"""
        if len(self.output) and self.output[-1] == NEWLINE:
            self.output += self.indentation
        else:
            self.output += NEWLINE + self.indentation
        self.output += code

    def line_and_indent(self, code: 'str'):
        """Adds a newline, appends the code string at the end and increases indentation"""
        if len(self.output) and self.output[-1] == NEWLINE:
            self.output += self.indentation
        else:
            self.output += NEWLINE + self.indentation
        self.output += code
        self.indent += 1

    def line_and_dedent(self, code: 'str'):
        """Adds a newline, appends the code string at the end and decreases indentation"""
        self.output += NEWLINE + self.indentation
        self.output += code
        self.indent -= max(0, self.indent - 1)

    def line_and_reset(self, code: 'str'):
        """Adds a newline, appends the code string at the end and zeroes indentation"""
        self.output += NEWLINE + self.indentation
        self.output += code
        self.indent = 0

    def add_and_reset(self, code: 'str'):
        """Appends the code string at the end and zeroes indentation"""
        self.output += code
        self.output += NEWLINE
        self.indent = 0

    def add_and_indent(self, code: 'str'):
        """Appends the code string at the end and increases indentation"""
        self.output += code
        self.output += NEWLINE
        self.indent += 1

    def add_and_dedent(self, code: 'str'):
        """Appends the code string at the end and decreases indentation"""
        self.output += code
        self.output += NEWLINE
        self.indent = max(0, self.indent - 1)

    def indent_and_add(self, code: 'str'):
        """Increases indentation, then appends the code string"""
        self.output += NEWLINE
        self.indent += 1
        self.output += code

    def dedent_and_add(self, code: 'str'):
        """Decreases indentation, then appends the code string"""
        self.indent = max(0, self.indent - 1)
        self.output += NEWLINE + self.indentation
        self.output += code

    def reset_and_add(self, code: 'str'):
        """Zeroes indentation, then appends the code string"""
        self.indent = 0
        self.output += NEWLINE + self.indentation
        self.output += code

    def dashed_line(self, length: 'int' = 40):
        """Adds a commented dashed line of given length (defaulting to 40)"""
        self.comment("-" * length)

    def comment(self, text: 'str', inline: 'bool' = False):
        """Adds a comment"""
        comm = f"# {text}"
        if inline:
            self.inline(f"    {comm}")
        else:
            self.line(comm)

    def docstring(self, text: 'str'):
        """Adds the text wrapped in tripple quotation marks"""
        full = f'"""{text}"""'
        doc = full.split('\n')
        for line in doc:
            self.line(line)

    def multiline_list(self, items: 'list[str]', name: 'str | None', inline: 'bool' = True):
        """Composes a list literal from given items"""
        if name is not None:
            if inline:
                self.add_and_indent(f"{name} = [")
            else:
                self.line_and_indent(f"{name} = [")
        else:
            if inline:
                self.add_and_indent(f"[")
            else:
                self.line_and_indent(f"[")

        for item in items:
            self.line(f"{item},")

        self.dedent_and_add(f"]")

    def multiline_dict(self, items: 'dict[str, str]', name: 'str | None', inline: 'bool' = True):
        """Composes a dict literal from given items"""
        if name is not None:
            if inline:
                self.add_and_indent(f"{name} = {{")
            else:
                self.line_and_indent(f"{name} = {{")
        else:
            if inline:
                self.add_and_indent("{")
            else:
                self.line_and_indent("{")

        for k, v in items.items():
            self.line(f"{k}: {v},")

        self.dedent_and_add("}")

    def template(self, tpl: 'str', *args, **kwargs):
        """Adds the template string to the output, correcting indentation"""
        try:
            formatted = tpl.format(*args, **kwargs) if len(args) > 0 or len(kwargs) > 0 else tpl
            for line in formatted.split(NEWLINE):
                if line == '\n':
                    self.empty(2)
                else:
                    self.line(line)
        except Exception:
            self.comment("Failed to add template (formatting error)")

    def template_exact(self, tpl: 'str', *args, **kwargs):
        """Adds the template string to the output, keeping indentation as is"""
        indent = self.indent
        self.indent = 0
        try:
            formatted = tpl.format(*args, **kwargs) if len(args) > 0 or len(kwargs) > 0 else tpl
            for line in formatted.split(NEWLINE):
                if line == '':
                    self.empty(2)
                self.line(line)
        except Exception:
            self.comment("Failed to add template (formatting error)")
        self.indent = indent

    @contextmanager
    def suite(self, do_indent: 'bool' = True, dedent_only: 'bool' = True, lv: 'int' = 1):
        """Context manager to compose an indented block of code"""
        if do_indent:
            self.empty_indent(lv=lv)
        yield
        if do_indent:
            if dedent_only:
                self.dedent_only(lv=lv)
            else:
                self.empty_dedent(lv=lv)


    @contextmanager
    def if_stmt(self, condition: 'str', inline: 'bool' = False, dedent_only: 'bool' = True):
        """Context manager to compose an if statement"""
        if inline:
            self.add_and_indent(f"if {condition}:")
        else:
            self.line_and_indent(f"if {condition}:")
        yield
        if dedent_only:
            self.dedent_only()
        else:
            self.empty_dedent()


    @contextmanager
    def else_stmt(self, dedent_only: 'bool' = True):
        """Context manager to compose an else statement"""
        self.line_and_indent(f"else:")
        yield
        if dedent_only:
            self.dedent_only()
        else:
            self.empty_dedent()

    @contextmanager
    def while_stmt(self, condition: 'str', inline: 'bool' = False, dedent_only: 'bool' = True):
        """Context manager to compose a while statement"""
        if inline:
            self.add_and_indent(f"while {condition}:")
        else:
            self.line_and_indent(f"while {condition}:")
        yield
        if dedent_only:
            self.dedent_only()
        else:
            self.empty_dedent()

    @contextmanager
    def with_stmt(self, target: 'str', inline: 'bool' = False, dedent_only: 'bool' = True):
        """Context manager to compose a with statement"""
        if inline:
            self.add_and_indent(f"with {target}:")
        else:
            self.line_and_indent(f"with {target}:")
        yield
        if dedent_only:
            self.dedent_only()
        else:
            self.empty_dedent()

    @contextmanager
    def for_stmt(self, item: 'str', container: 'str'):
        """Context manager to compose a for statement"""
        self.add_and_indent(f"for {item} in {container}:")
        yield
        self.empty_dedent()

    @contextmanager
    def func_def(self, name: 'str', params: 'list[str]', docstring: 'str | None',
                 decorators: 'list[str] | None' = None, empty_before: 'int' = 1,
                 empty_after: 'int' = 1):
        """Context manager to compose a function definition"""
        if empty_before > 0:
            self.empty_reset(empty_before)

        if decorators:
            for deco in decorators:
                self.line(f"@{deco}")

        plist = ', '.join(params)
        self.add_and_indent(f"def {name}({plist}):")

        if docstring:
            self.docstring(docstring)
        yield
        if empty_after > 0:
            self.empty_reset(empty_after)

    @contextmanager
    def region(self, label: 'str'):
        """Context manager to compose a code region (code folding and organization)"""
        self.line(f"# region {label.upper()}")
        self.empty(2)
        yield
        self.empty(2)
        self.line(f"# endregion ({label.lower()})")

# endregion (classes)
# ---------------------------------------------------------
# region FUNCTIONS


def snakefy(string: 'str') ->'str':
    """Converts the string from PascalCase or ALL_CAPS to snake_case"""
    lastchar = ''
    result = ''

    for char in string:
        if lastchar:
            if char.isupper():
                if lastchar.isupper() or lastchar.isdigit() or lastchar == '_':
                    result += f'{char.lower()}'
                else:
                    result += f'_{char.lower()}'
            else:
                result += char
        else:
            result += char.lower()
        lastchar = char

    return result


def compose(grammar_nodes: 'GrammarNodes', grammar_source: 'Source'):
    """Composes the parser for the grammar"""
    global composer, grammar, source

    last_composer: 'SourceComposer' = composer
    last_grammar: 'GrammarNodes' = grammar

    grammar = grammar_nodes
    source = grammar_source

    composer = SourceComposer(grammar_nodes.output_filename)

    compose_parser()

    composer.write()

    composer = last_composer
    grammar = last_grammar


def compose_parser():
    """Composes the parser module"""
    with composer.region("header"):
        composer.template_exact(TPL_WARNING)
        composer.template_exact(TPL_LICENSE, year=2023, cr_owner="Jorge A. Gomes")

    composer.dashed_line()

    with composer.region("imports"):
        composer.line("import sys")
        composer.template_exact(TPL_DEPENDENCIES)


    composer.dashed_line()

    with composer.region("exports"):
        composer.empty()

        composer.multiline_list(["'parse'"], '__all__')

    composer.dashed_line()

    with composer.region("globals"):
        composer.template_exact(TPL_GLOBALS)

    composer.dashed_line()

    with composer.region("constants and enums"):
        composer.template_exact(TPL_CONSTANTS)

    composer.dashed_line()

    with composer.region("classes"):
        composer.template_exact(TPL_SOURCE_CLASS_1)

        with composer.suite(lv=3):
            for name, tokendef in grammar.tokens.items():
                if tokendef.has_decorator(DCR_SKIP):
                    with composer.if_stmt(f"m := self.match_regex(r'''{tokendef.value}''', skip=False)"):
                        composer.line("continue")

        composer.template_exact(TPL_SOURCE_CLASS_2)

    with composer.region("functions"):

        with composer.region("utilities"):
            composer.template_exact(TPL_UTILITIES)

        with composer.region("parser API"):

            with composer.func_def('parse', ['source_fname', 'output_ast_fname', 'start_rule'], "Parsers a source file and generates an abstract syntax tree of the source."):
                composer.line("global source")
                composer.line("main_rule = f'match_{snakefy(start_rule)}'")
                composer.line("callback = globals().get(main_rule, lambda: {})")
                composer.line("print(start_rule, main_rule)")
                with composer.with_stmt("open(source_fname, 'r', encoding='utf8') as fp"):
                    composer.line("source_contents = fp.read()")
                composer.line("source = Source(source_contents, source_contents, source_fname)")
                composer.line("source.skip()")
                composer.line("return callback()")

            compose_token_definitions()
            compose_kind_definitions()
            compose_rule_definitions()

        with composer.func_def('main', [], "Parser's CLI entry point.", empty_before=3, empty_after=1):
            composer.template(TPL_MAIN)

    composer.dashed_line()

    with composer.region("entry point"):

        with composer.if_stmt('__name__ == "__main__"'):
            composer.line('sys.exit(main())')

        composer.empty()

# region GRAMMAR NODES

# region DEFINITIONS


def compose_token_definitions():
    """Composes all token definitions"""
    with composer.region("token definitions"):
        for name, tokendef in grammar.tokens.items():
            if tokendef.has_decorator(DCR_INTERNAL) or tokendef.has_decorator(DCR_SKIP):
                continue
            compose_tokendef(name, tokendef)


def compose_kind_definitions():
    """Composes all token group definitions"""
    with composer.region("kind definitions"):
        for name, kinddef in grammar.kinds.items():
            compose_kinddef(name, kinddef)


def compose_rule_definitions():
    """Composes all rule definitions"""
    with composer.region("rule definitions"):
        for name, ruledef in grammar.rules.items():
            compose_ruledef(name, ruledef)


def compose_def_body(suffix: 'str', docstring: 'str', const_name: 'str', regex_str: 'str', match_index: 'int'):
    """Composes the functions for parsing tokens"""
    with composer.func_def(f"is_{suffix}", [], docstring):
        composer.line(f"return source.is_regex(r{regex_str})")

    with composer.func_def(f"match_{suffix}", [], docstring):
        composer.line("location = source.location")
        with composer.if_stmt(f"m := source.match_regex(r{regex_str})"):
            composer.line('''log(False, debug3=f"Matched token with regex {{regex_str}} at line {location[1]}, {location[2]}: '{m[0]}'")''')
            composer.line(f"return {{ 'kind': '{const_name}', 'value': m[{match_index}], 'lc': [ location[1], location[2] ] }}")
        composer.line(f"return None")

    with composer.func_def(f"expect_{suffix}", [], docstring):
        composer.line("location = source.location")
        composer.line(f"m = source.expect_regex(r{regex_str}, '{const_name} expected.')")
        composer.line(f"return {{ 'kind': '{const_name}', 'value': m[{match_index}], 'lc': [ location[1], location[2] ] }}")

    with composer.func_def(f"parse_{suffix}", [], docstring):
        composer.line(f"item = expect_{suffix}()")
        composer.line(f"return item['value']")

# region TOKEN


def compose_tokendef(token_name: 'str', token: 'TokenDef'):
    """Composes the functions for parsing a token definition"""
    suffix: 'str' = snakefy(token_name)
    const_name: 'str' = suffix.upper()
    docstring: 'str' = f'Parses a {token_name} token'
    regex_str: 'str' = f"'''{token.value}'''"

    compose_def_body(suffix, docstring, const_name, regex_str, token.match_index)

# endregion (TOKEN)

# region KIND


def compose_kinddef(kind_name: 'str', kind: 'KindDef'):
    """Composes the functions for parsing a token group definition"""
    suffix: 'str' = snakefy(kind_name)
    const_name: 'str' = suffix.upper()
    docstring: 'str' = f'Parses a {kind_name} kind'
    values = '|'.join(kind.values)
    regex_str = f"'''{values}'''"

    compose_def_body(suffix, docstring, const_name, regex_str, 0)

# endregion (KIND)

# region RULE


def check_entry(entry: 'NodeGroup'):
    if not isinstance(entry.first, RuleRef):
        return

    if ruledef := grammar.get_rule(entry.first.value):
        if not ruledef.is_simple:
            source.index = entry.first.index
            source.error("Rule entry cannot start with complex rule references")


def compose_ruledef(rule_name: 'str', rule: 'RuleDef'):
    """Composes the functions for parsing a rule"""
    suffix: 'str' = snakefy(rule_name)
    docstring: 'str' = f'Parses a {rule_name} rule'
    node_kind: 'str' = suffix.upper()

    with composer.func_def(f"expect_{suffix}", [], docstring):
        composer.line("loc = source.index")
        with composer.if_stmt(f"node := match_{suffix}()"):
            composer.line("return node")
        composer.line(f"source.error(\"{node_kind} node expected.\", at=loc)")

    with composer.func_def(f"match_{suffix}", [], docstring):
        if verbosity := rule.get("verbosity"):
            composer.line(f"push_verb('{verbosity}', True)")
        composer.line(f"log(False, debug1=f'In {rule_name}:')")

        composer.line(f"node = {{ 'kind': '{node_kind}' }}")

        if rule.has("scope"):
            composer.line(f"log(False, debug2=f'Entering {rule_name} scope')")
            composer.line(f"push_scope()")

        for i, entry in enumerate(rule.entries):
            # check_entry(entry)
            compose_group_entry(entry, rule, i == 0)
            with composer.suite():
                composer.line(f"log(False, debug3=f'Matched {rule_name} entry no.{i}')")

        with composer.else_stmt():
            composer.line(f"log(False, debug2=f'No match for {rule_name} rule')")
            composer.line("node = None")

        if scope_val := rule.has("scope"):
            composer.line(f"log(False, debug2=f'Leaving {rule_name} scope')")
            composer.line(f"pop_scope(node, '{scope_val}')")

        if identifier := rule.get("declare"):
            with composer.if_stmt("node"):
                composer.line(f"declare('{identifier}', node, '{node_kind}')")

        if verbosity := rule.get("verbosity"):
            composer.line(f"pop_verb(True)")

        if rule.has_key:
            if rule.has('flip'):
                item = rule.get('flip')
                composer.line(f"return flipped(reduced(node, '{rule.key}'), '{item}', '{rule.key}')")
            else:
                composer.line(f"return reduced(node, '{rule.key}')")
        else:
            composer.line("return node")

    with composer.func_def(f"is_{suffix}", [], docstring):
        composer.line("global scopes_enabled")
        composer.line("reenable_scopes = scopes_enabled is True")
        composer.line("result = False")
        composer.line("scopes_enabled = False")
        if rule.is_simple:
            for i, entry in enumerate(rule.entries):
                check_entry(entry)
                compose_reference(entry.first, 'test', test_chained=i > 0)
                with composer.suite():
                    composer.line(f"log(False, debug3=f'{rule_name} found')")
                    composer.line("result = True")

            with composer.else_stmt():
                composer.line(f"log(False, debug3=f'{rule_name} not found')")
                composer.line("result = False")
        else:
            composer.line(f"index = source.index")
            composer.line(f"result = False")
            composer.line(f"push_verb('error')")
            with composer.if_stmt(f"m := match_{suffix}()"):
                # composer.line(f"log(False, debug3=f'{rule_name} (complex) found')")
                composer.line(f"result = True")
            # composer.line(f"source.warning('{rule_name} is complex and can only be tested by cheating.')")
            composer.line(f"pop_verb()")
            composer.line(f"source.index = index")
        composer.line("scopes_enabled = True if reenable_scopes else False")
        composer.line("return result")

# endregion (RULE)

# region NODE GROUP


def compose_group_entry(group: 'NodeGroup', rule: 'RuleDef', first: 'bool'):
    """Composes the code for a rule alternative"""

    compose_reference(group.first, 'test', test_chained=not first)

    with composer.suite():
        for item in group.refs:
            if isinstance(item, GrammarNodeReference):
                compose_reference(item, 'init', supress_init_one=True)

        for item in group.refs:
            if isinstance(item, GrammarNodeReference):
                compose_reference(item)

            elif isinstance(item, NodeGroup):
                compose_group_inline(item)


def compose_group_inline(group: 'NodeGroup'):
    """Composes the code for a inline group"""
    for item in group.refs:
        if isinstance(item, GrammarNodeReference):
            compose_reference(item, 'init', supress_init_one=True)

    if group.mode is GM_OPTIONAL:
        compose_group_optional(group)

    elif group.mode is GM_ALTERNATIVE:
        compose_group_alternative(group)

    elif group.mode is GM_SEQUENTIAL:
        compose_group_sequential(group)


def compose_group_optional(group: 'NodeGroup'):
    """Composes the code for a optional inline group"""
    composer.comment("Option group below")
    compose_reference(group.first, 'test', test_loop=False)
    with composer.suite():
        for item in group.refs:
            if isinstance(item, GrammarNodeReference):
                compose_reference(item, 'capture', use_capture=group.capture)

            elif isinstance(item, NodeGroup):
                compose_group_inline(item)


def compose_group_alternative(group: 'NodeGroup'):
    """Composes the code for a alternative inline group"""
    composer.comment("Alternative group below")
    dedent_after_loop = False

    if group.count in (NC_ONE_OR_MORE, NC_ZERO_OR_MORE):
        composer.line_and_indent(f"while True:")
        dedent_after_loop = True

    for i, item in enumerate(group.refs):
        if isinstance(item, NodeGroup):
            source.index = item.index
            source.error("Invalid item in alternative group")

        compose_reference(item, 'test', test_chained=i > 0)
        with composer.suite():
            compose_reference(item, 'capture', test_chained=i > 0)
    with composer.else_stmt():
        if group.count is NC_ONE:
            composer.line("source.error('Unexpected token')")
        elif group.count in (NC_ONE_OR_MORE, NC_ZERO_OR_MORE):
            composer.line("break")

    if dedent_after_loop:
        composer.dedent_only()


def compose_group_sequential(group: 'NodeGroup'):
    """Composes the code for a sequential inline group"""
    composer.comment("Sequential group below")
    dedent_after_loop = False

    if group.count in (NC_ONE_OR_MORE, NC_ZERO_OR_MORE):
        compose_reference(group.refs[0], 'test', use_capture='item', test_loop=True)
        composer.indent_only()
        dedent_after_loop = True

    for i, item in enumerate(group.refs):
        if isinstance(item, NodeGroup):
            compose_group_inline(item)

        else:
            compose_reference(item, 'capture', supress_init_one=True)

    if dedent_after_loop:
        composer.dedent_only()


# endregion (node group)

# endregion (definitions)

# region REFERENCES


def compose_reference(ref: 'GrammarNodeReference', action: 'str' = 'capture', **kwargs):
    """Composes parsing operations referenced inside rules"""
    has_cap: 'bool' = ref.capture != '_'
    many: 'bool' = ref.capture.startswith('*') or ref.count in (NC_ONE_OR_MORE, NC_ZERO_OR_MORE)
    opt: 'bool' = ref.count in (NC_ZERO_OR_ONE, NC_ZERO_OR_MORE)
    cap = kwargs.get("use_capture", ref.capture).lstrip('*')
    should_merge_rule: 'bool' = False
    has_lookup: 'bool' = False
    if '.' in cap:
        cap, lookup = cap.split('.', 2)
        has_lookup = True
    initializer: 'str' = '[]' if many else 'None'
    test_chained = kwargs.get('test_chained', False)
    supress_init_one = kwargs.get('supress_init_one', False)

    if action == 'init':
        if has_cap:
            if supress_init_one and not many:
                return
            composer.line(f"node['{cap}'] = {initializer}")

    elif action == 'test':
        if kwargs.get('test_loop', False):
            stmt = 'while'
        else:
            stmt = 'elif' if test_chained else 'if'

        if isinstance(ref, TokenRef):
            val = escape_token(ref.value)
            composer.line(f"{stmt} is_token(r'{val}'):")

        elif isinstance(ref, KindRef):
            composer.line(f"{stmt} is_{snakefy(ref.value)}():")

        elif isinstance(ref, RuleRef):
            rule: 'RuleDef' = grammar.get_rule(ref.value)
            composer.line(f"{stmt} is_{snakefy(ref.value)}():")

    elif action == 'capture':
        if isinstance(ref, TokenRef):
            kind = 'TOKEN'
            val = escape_token(ref.value)
            call = f"match_token(r'{val}')" if opt else f"expect_token(r'{val}')"
            mcall = f"match_token(r'{val}')"

        elif isinstance(ref, KindRef):
            kind = snakefy(ref.value).upper()
            call = f"match_{snakefy(ref.value)}()" if opt else f"expect_{snakefy(ref.value)}()"
            mcall = f"match_{snakefy(ref.value)}()"

        elif isinstance(ref, RuleRef):
            rule: 'RuleDef' = grammar.get_rule(ref.value)
            should_merge_rule = rule.has_directive('merge')
            source.info(f"{rule.name} should merge rule: {should_merge_rule} ({rule.get('update')}={cap})", localized=False, as_debug=should_merge_rule)

            kind = snakefy(ref.value).upper()
            call = f"match_{snakefy(ref.value)}()" if opt else f"expect_{snakefy(ref.value)}()"
            mcall = f"match_{snakefy(ref.value)}()"

        if should_merge_rule:
            if ref.count not in (NC_ONE, NC_ZERO_OR_ONE):
                source.error(f"{ref.value} rule must have at most one ocurrence ({ref.count.name}).")
            composer.line(f"node_update(node, {mcall})")
        else:
            if has_lookup:
                call = f"node_lookup({call}, '{lookup}', '{kind}')"
            capt = f".append({call})" if many else f" = {call}"
            if has_cap:
                if ref.count is NC_ONE:
                    composer.line(f"node['{cap}']{capt}")
                elif ref.count is NC_ONE_OR_MORE:
                    composer.line(f"node['{cap}'].append({call})")
                    composer.line_and_indent(f"while {cap} := {mcall}:")
                    composer.line(f"node['{cap}'].append({cap})")
                    composer.dedent_only()
                elif ref.count is NC_ZERO_OR_MORE:
                    composer.line_and_indent(f"while {cap} := {mcall}:")
                    composer.line(f"node['{cap}'].append({cap})")
                    composer.dedent_only()
                else:
                    composer.line(f"node['{cap}']{capt}")
            else:
                if ref.count is NC_ONE:
                    composer.line(call)
                elif ref.count is NC_ONE_OR_MORE:
                    composer.line_and_indent(f"while {mcall}:")
                    composer.line_and_indent(f"if not {mcall}:")
                    composer.line(f"break")
                    composer.dedent_only(2)
                elif ref.count is ZERO_OR_MORE:
                    composer.line_and_indent(f"while {mcall}:")
                    composer.line_and_indent(f"if not {mcall}:")
                    composer.line(f"break")
                    composer.dedent_only(2)
                else:
                    composer.line(mcall)


def escape_token(tkn: 'str') ->'str':
    """Escapes characters that have meaning in regluar expressions"""
    return {
        r'(': r'\(',
        r'{': r'\{',
        r'[': r'\[',
        r')': r'\)',
        r'}': r'\}',
        r']': r'\]',
        r'\\': r'\\\\',
        r'^': r'\^',
        r'-': r'\-',
        r'*': r'\*',
        r'+': r'\+',
        r'?': r'\?',
        r'"': r'\"',
        r"'": r'\'',
        r".": r'\.',
    }.get(tkn, tkn)

# endregion (references)

# endregion (grammar nodes)

# endregion (functions)
