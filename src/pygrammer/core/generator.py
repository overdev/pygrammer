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
from colorama import Fore, Back, Style
from .grammar import *
from .parser import *
from .templates import *

# endregion (imports)
# ---------------------------------------------------------
# region EXPORTS


__all__ = [
    "compose",
]


# endregion (exports)
# ---------------------------------------------------------
# region GLOBALS


composer: "SourceComposer" = None
grammar: "GrammarNodes" = None
source: "Source" = None

gen_templates: dict[str, str] = {
    're_consts': '',
}

start_rule: str = ''

# endregion (globals)
# ---------------------------------------------------------
# region CONSTANTS & ENUMS


NEWLINE = "\n"
INDENT = "    "

RE_CONSTANTS = 're_consts'

# endregion (constants)
# ---------------------------------------------------------
# region CLASSES


class SourceComposer:
    """Utility class to generate the parser code for the provided grammar"""

    def __init__(self, output_filename: "str"):
        self.output_filename: "str" = output_filename
        self.output: "str" = ""
        self.indent: "int" = 0

    @property
    def indentation(self) -> "str":
        """Gets the ammount of space needed in the current indentation level"""
        return INDENT * self.indent

    def write(self):
        """Writes the generated parser code into a file"""
        with open(self.output_filename, "w", encoding="utf8") as fp:
            fp.write(self.output)

    def empty(self, num: "int" = 1):
        """Adds one or more newlines to the output"""
        self.output += NEWLINE * num

    def empty_indent(self, num: "int" = 1, lv: "int" = 1):
        """Adds one or more newlines to the output, then increases the indentation level"""
        self.output += NEWLINE * num
        self.indent += lv

    def empty_dedent(self, num: "int" = 1, lv: "int" = 1):
        """Adds one or more newlines to the output, then decreases the indentation level"""
        self.output += NEWLINE * num
        self.indent = max(0, self.indent - lv)

    def indent_only(self, lv: "int" = 1):
        """Increases the indentation level"""
        self.indent += lv

    def dedent_only(self, lv: "int" = 1):
        """Decreases the indentation level"""
        self.indent = max(0, self.indent - lv)

    def empty_reset(self, num: "int" = 1):
        """Adds one or more newlines, then sets the indentation level to zero"""
        self.output += NEWLINE * num
        self.indent = 0

    def inline(self, code: "str"):
        """Appends the code string at the end of the output"""
        self.output += code

    def line(self, code: "str"):
        """Adds a newline, then appends the code string at the end of the output following indentation"""
        if len(self.output) and self.output[-1] == NEWLINE:
            self.output += self.indentation
        else:
            self.output += NEWLINE + self.indentation
        self.output += code

    def line_and_indent(self, code: "str"):
        """Adds a newline, appends the code string at the end and increases indentation"""
        if len(self.output) and self.output[-1] == NEWLINE:
            self.output += self.indentation
        else:
            self.output += NEWLINE + self.indentation
        self.output += code
        self.indent += 1

    def line_and_dedent(self, code: "str"):
        """Adds a newline, appends the code string at the end and decreases indentation"""
        self.output += NEWLINE + self.indentation
        self.output += code
        self.indent -= max(0, self.indent - 1)

    def line_and_reset(self, code: "str"):
        """Adds a newline, appends the code string at the end and zeroes indentation"""
        self.output += NEWLINE + self.indentation
        self.output += code
        self.indent = 0

    def add_and_reset(self, code: "str"):
        """Appends the code string at the end and zeroes indentation"""
        self.output += code
        self.output += NEWLINE
        self.indent = 0

    def add_and_indent(self, code: "str"):
        """Appends the code string at the end and increases indentation"""
        self.output += code
        self.output += NEWLINE
        self.indent += 1

    def add_and_dedent(self, code: "str"):
        """Appends the code string at the end and decreases indentation"""
        self.output += code
        self.output += NEWLINE
        self.indent = max(0, self.indent - 1)

    def indent_and_add(self, code: "str"):
        """Increases indentation, then appends the code string"""
        self.output += NEWLINE
        self.indent += 1
        self.output += code

    def dedent_and_add(self, code: "str"):
        """Decreases indentation, then appends the code string"""
        self.indent = max(0, self.indent - 1)
        self.output += NEWLINE + self.indentation
        self.output += code

    def reset_and_add(self, code: "str"):
        """Zeroes indentation, then appends the code string"""
        self.indent = 0
        self.output += NEWLINE + self.indentation
        self.output += code

    def dashed_line(self, length: "int" = 40):
        """Adds a commented dashed line of given length (defaulting to 40)"""
        self.comment("-" * length)

    def comment(self, text: "str", inline: "bool" = False):
        """Adds a comment"""
        comm = f"# {text}"
        if inline:
            self.inline(f"    {comm}")
        else:
            self.line(comm)

    def docstring(self, text: "str"):
        """Adds the text wrapped in tripple quotation marks"""
        full = f'"""{text}"""'
        doc = full.split("\n")
        for line in doc:
            self.line(line)

    def multiline_list(
        self, items: "list[str]", name: "str | None", inline: "bool" = True
    ):
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

    def multiline_dict(
        self, items: "dict[str, str]", name: "str | None", inline: "bool" = True
    ):
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

    def template(self, tpl: "str", *args, **kwargs):
        """Adds the template string to the output, correcting indentation"""
        try:
            formatted = (
                tpl.format(*args, **kwargs) if len(args) > 0 or len(kwargs) > 0 else tpl
            )
            for line in formatted.split(NEWLINE):
                if line == "\n":
                    self.empty(2)
                else:
                    self.line(line)
        except Exception:
            self.comment("Failed to add template (formatting error)")

    def template_exact(self, tpl: "str", *args, **kwargs):
        """Adds the template string to the output, keeping indentation as is"""
        indent = self.indent
        self.indent = 0
        try:
            formatted = (
                tpl.format(*args, **kwargs) if len(args) > 0 or len(kwargs) > 0 else tpl
            )
            for line in formatted.split(NEWLINE):
                if line == "":
                    self.empty(2)
                self.line(line)
        except Exception:
            self.comment("Failed to add template (formatting error)")
        self.indent = indent

    @contextmanager
    def suite(
        self, do_indent: "bool" = True, dedent_only: "bool" = True, lv: "int" = 1
    ):
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
    def if_stmt(
        self, condition: "str", inline: "bool" = False, dedent_only: "bool" = True
    ):
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
    def else_stmt(self, dedent_only: "bool" = True):
        """Context manager to compose an else statement"""
        self.line_and_indent(f"else:")
        yield
        if dedent_only:
            self.dedent_only()
        else:
            self.empty_dedent()

    @contextmanager
    def while_stmt(
        self, condition: "str", inline: "bool" = False, dedent_only: "bool" = True
    ):
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
    def with_stmt(
        self, target: "str", inline: "bool" = False, dedent_only: "bool" = True
    ):
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
    def for_stmt(self, item: "str", container: "str"):
        """Context manager to compose a for statement"""
        self.add_and_indent(f"for {item} in {container}:")
        yield
        self.empty_dedent()

    @contextmanager
    def func_def(
        self,
        name: "str",
        params: "list[str]",
        docstring: "str | None",
        decorators: "list[str] | None" = None,
        empty_before: "int" = 1,
        empty_after: "int" = 1,
    ):
        """Context manager to compose a function definition"""
        if empty_before > 0:
            self.empty_reset(empty_before)

        if decorators:
            for deco in decorators:
                self.line(f"@{deco}")

        plist = ", ".join(params)
        self.add_and_indent(f"def {name}({plist}):")

        if docstring:
            self.docstring(docstring)
        yield
        if empty_after > 0:
            self.empty_reset(empty_after)

    @contextmanager
    def region(self, label: "str"):
        """Context manager to compose a code region (code folding and organization)"""
        self.line(f"# region {label.upper()}")
        self.empty(2)
        yield
        self.empty(2)
        self.line(f"# endregion ({label.lower()})")

    def replace(self, sub: str, rep: str):
        """Replaces a substring sub in the output code with its replacement string rep"""
        self.output = self.output.replace(sub, rep)

# endregion (classes)
# ---------------------------------------------------------
# region FUNCTIONS


def template_append(key: str, code: str):
    global gen_templates

    if key in gen_templates:
        template = f"{gen_templates[key]}{code}"
    else:
        template = code

    gen_templates[key] = template


def snakefy(string: "str") -> "str":
    """Converts the string from PascalCase or ALL_CAPS to snake_case"""
    lastchar = ""
    result = ""

    for char in string:
        if lastchar:
            if char.isupper():
                if lastchar.isupper() or lastchar.isdigit() or lastchar == "_":
                    result += f"{char.lower()}"
                else:
                    result += f"_{char.lower()}"
            else:
                result += char
        else:
            result += char.lower()
        lastchar = char

    return result


def compose(grammar_nodes: "GrammarNodes", grammar_source: "Source"):
    """Composes the parser for the grammar"""
    global composer, grammar, source

    last_composer: "SourceComposer" = composer
    last_grammar: "GrammarNodes" = grammar

    grammar = grammar_nodes
    source = grammar_source

    composer = SourceComposer(grammar_nodes.output_filename)

    compose_parser()

    composer.write()

    composer = last_composer
    grammar = last_grammar


def compose_parser():
    """Composes the parser module"""
    global gen_templates

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

        composer.multiline_list(["'parse'", "'generate_ast'", "'generate_stream'"], "__all__")

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
                        if tokendef.has_decorator(DCR_GRABTOKEN):
                            composer.line("location = source.location")
                            composer.line(f'current_classifiers = unload_classifiers()')
                            composer.line(f"token = {{ 'kind': '{name}', 'value': m[{tokendef.match_index}], 'lc': [ location[1], location[2] ], 'classifier': classify('{snakefy(name)}') }}")
                            composer.line(f'load_classifiers(current_classifiers, True)')
                            composer.line("grab_token(token, location)")
                        composer.line("continue")

        composer.template_exact(TPL_SOURCE_CLASS_2)

    with composer.region("functions"):
        with composer.region("utilities"):
            composer.template_exact(TPL_UTILITIES)

        with composer.region("parser API"):
            composer.template_exact(TPL_API, start_rule=grammar.start_rule.name)

            compose_token_definitions()
            compose_kind_definitions()
            compose_rule_definitions()

        with composer.func_def("main", [], "Parser's CLI entry point.", empty_before=3, empty_after=1):
            composer.template(TPL_MAIN, start_rule=grammar.start_rule.name)

    composer.dashed_line()

    with composer.region("entry point"):
        with composer.if_stmt('__name__ == "__main__"'):
            composer.line("sys.exit(main())")

        composer.empty()

    composer.replace("# **RE** #", gen_templates[RE_CONSTANTS])

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
    global start_rule

    entry_rule: RuleDef = None
    with composer.region("rule definitions"):
        for name, ruledef in grammar.rules.items():
            if ruledef.has_directive("start"):
                entry_rule = ruledef
            compose_ruledef(name, ruledef)

    if entry_rule is None:
        source.error(f"No starting rule: Please, apply the {Fore.MAGENTA}start{Fore.RED} directive to a rule of your choosing.")
    elif source.verbosity >= INFO:
        source.info(f"Starting rule: {Fore.MAGENTA}{entry_rule.name}", localized=False)
    start_rule = entry_rule.name


def compose_def_body(definition: "TokenDef | KindDef", suffix: "str", docstring: "str", const_name: "str", regex_str: "str", match_index: "int", excludes: "list[str] | None"):
    """Composes the functions for parsing tokens"""
    with composer.func_def(f"is_{suffix}", ["value=''"], docstring):
        composer.line("location = source.location")
        with composer.if_stmt(f"match_{suffix}(value, False)"):
            composer.line(f"return True")
        composer.line(f"return False")

    with composer.func_def(f"match_{suffix}", ["value=''", "advance=True", f"token_classifier='{suffix}'"], docstring):
        composer.line("location = source.location")

        with composer.if_stmt(f"m_{suffix} := source.match_regex(RE_{const_name}, False)"):
            if excludes:
                for exclusion in excludes:
                    if kind := grammar.kinds.get(exclusion):
                        value = '|'.join(kind.values)
                        with composer.if_stmt(f"m_{snakefy(exclusion)} := RE_{exclusion}.fullmatch(m_{suffix}[{match_index}])"):
                            with composer.if_stmt(f"not advance"):
                                composer.line(f"return False")
                            composer.line(f"log(True, error='Expected {const_name}, got {exclusion}')")
                    else:
                        source.error(f"{const_name} exclusion '{exclusion}' is not defined")

            if isinstance(definition, TokenDef) and definition.has_any_decorator(DCR_RELFILEPATH, DCR_ABSFILEPATH, DCR_RELDIRPATH, DCR_ABSDIRPATH, DCR_ENSURERELATIVE, DCR_ENSUREABSOLUTE, DCR_LOADANDPARSE):
                composer.line(f"m_path: str = m_{suffix}[{match_index}]")
                composer.line(f"m_path_valid: bool = True")
                composer.line(f"m_path_error: bool = False")
                composer.line(f"m_path_message: str = ''")
                composer.line(f"submodule: 'dict | None' = None")
                path_kind = "'PATH'"

                if definition.has_decorator(DCR_RELFILEPATH):
                    composer.template(TPL_RELFILEPATH)
                    path_kind = "'FILE_PATH_RELATIVE'"

                if definition.has_decorator(DCR_ABSFILEPATH):
                    composer.template(TPL_ABSFILEPATH)
                    path_kind = "'FILE_PATH_ABSOLUTE'"

                if definition.has_decorator(DCR_RELDIRPATH):
                    composer.template(TPL_RELDIRPATH)
                    path_kind = "'DIRECTORY_PATH_RELATIVE'"

                if definition.has_decorator(DCR_ABSDIRPATH):
                    composer.template(TPL_ABSDIRPATH)
                    path_kind = "'DIRECTORY_PATH_ABSOLUTE'"

                if definition.has_decorator(DCR_ENSURERELATIVE):
                    composer.template(TPL_ENSURERELATIVE)
                    path_kind = path_kind.replace('ABSOLUTE', 'RELATIVE')

                if definition.has_decorator(DCR_ENSUREABSOLUTE):
                    composer.template(TPL_ENSUREABSOLUTE)
                    path_kind = path_kind.replace('RELATIVE', 'ABSOLUTE')

                with composer.if_stmt("not m_path_valid"):
                    with composer.if_stmt("advance"):
                        with composer.if_stmt("m_path_error"):
                            composer.line("log(True, error=m_path_message)")
                        with composer.else_stmt():
                            composer.line("log(True, warning=m_path_message)")
                    with composer.else_stmt():
                            composer.line("return False")

                with composer.else_stmt():
                    if definition.has_decorator(DCR_LOADANDPARSE):
                        with composer.if_stmt("advance"):
                            composer.line(f"source.expect_regex(RE_{const_name}, advance)")
                            composer.template(TPL_LOADANDPARSE)
                        composer.line(f"token = {{ 'kind': 'SUBMODULE', 'path': os.path.abspath(os.path.normpath(m_path)), 'valid': m_path_valid, 'exists': os.path.exists(m_path), 'lc': [ location[1], location[2] ], 'classifier': classify(token_classifier) }}")
                        composer.line(f"grab_token(token, location)")
                        composer.line(f"return token")
                    else:
                        with composer.if_stmt("advance"):
                            composer.line(f"source.expect_regex(RE_{const_name}, advance)")
                            composer.line(f"token {{ 'kind': {path_kind}, 'path': os.path.abspath(os.path.normpath(m_path)), 'valid': m_path_valid, 'exists': os.path.exists(m_path), 'lc': [ location[1], location[2] ], 'classifier': classify(token_classifier) }}")
                            composer.line(f"grab_token(token, location)")
                            composer.line(f"return token")
                        with composer.else_stmt():
                            composer.line("return True")
            else:
                with composer.if_stmt(f"value and not re.fullmatch(value, m_{suffix}[{match_index}])"):
                    composer.line(f"return None if advance else False")

                with composer.if_stmt("advance"):
                    composer.line(f"m = source.expect_regex(RE_{const_name}, advance)")
                    composer.line(f"log(False, debug3=f\"\"\"Matched token RE_{const_name} at line {{location[1]}}, {{location[2]}}: '{{m[{match_index}]}}'\"\"\")")
                    composer.line(f"token = {{ 'kind': '{const_name}', 'value': m_{suffix}[{match_index}], 'lc': [ location[1], location[2] ], 'classifier': classify(token_classifier) }}")
                    composer.line(f"grab_token(token, location)")
                    composer.line(f"return token")
                with composer.else_stmt():
                    composer.line(f"return True")

        composer.line(f"return None if advance else False")

    with composer.func_def(f"expect_{suffix}", ["value=''", f"token_classifier='{suffix}'"], docstring):
        composer.line("index = source.index")
        with composer.if_stmt(f"m_{suffix} := match_{suffix}(value, token_classifier=token_classifier)"):
            composer.line(f"return m_{suffix}")
        composer.line(f"source.error('Expected {const_name}', at=index)")

    # with composer.func_def(f"parse_{suffix}", [], docstring):
    #     composer.line(f"item = expect_{suffix}()")
    #     composer.line(f"return item['value']")


# region TOKEN


def compose_tokendef(token_name: "str", token: "TokenDef"):
    """Composes the functions for parsing a token definition"""
    suffix: "str" = snakefy(token_name)
    const_name: "str" = suffix.upper()
    docstring: "str" = f"Parses a {token_name} token"
    regex_str: "str" = f"'''{token.value}'''"

    template_append(RE_CONSTANTS,
        f"# Pattern for the {const_name} token\n"
        f"RE_{const_name}: re.Pattern = re.compile(r{regex_str})\n"
    )

    compose_def_body(token, suffix, docstring, const_name, regex_str, token.match_index, token.exclusions)


# endregion (TOKEN)

# region KIND


def compose_kinddef(kind_name: "str", kind: "KindDef"):
    """Composes the functions for parsing a token group definition"""
    suffix: "str" = snakefy(kind_name)
    const_name: "str" = suffix.upper()
    docstring: "str" = f"Parses a {kind_name} kind"
    values = "|".join(kind.values)
    regex_str = f"'''{values}'''"

    template_append(RE_CONSTANTS,
        f"# Pattern for the {kind_name} token group\n"
        f"RE_{const_name}: re.Pattern = re.compile(r{regex_str})\n"
    )

    compose_def_body(kind, suffix, docstring, const_name, regex_str, 0, None)


# endregion (KIND)

# region RULE


def check_entry(entry: "NodeGroup"):
    if not isinstance(entry.first, RuleRef):
        return

    if ruledef := grammar.get_rule(entry.first.value):
        if not ruledef.is_simple:
            source.index = entry.first.index
            source.error("Rule entry cannot start with complex rule references")

def compose_ruledef_classification(rule_name: "str", rule: "RuleDef", suffix: "str", is_pushing: bool):
    if retroclassifier := rule.get("retroclassify"):
        with composer.if_stmt('not just_checking'):
            composer.line(f"retroclassify('{retroclassifier}')")

    if classifier := rule.get("reclassify"):
        with composer.if_stmt('not just_checking'):
            if is_pushing:
                composer.line(f'current_classifiers = unload_classifiers()')
                composer.line(f'push_classifier("{classifier}")')
            else:
                composer.line(f'load_classifiers(current_classifiers, True)')

    elif classifier := rule.get("classify"):
        with composer.if_stmt('not just_checking'):
            composer.line(f'push_classifier("{classifier}")' if is_pushing else f'pop_classifier()')

    elif rule.has_directive("reclassify"):
        with composer.if_stmt('not just_checking'):
            if is_pushing:
                composer.line(f'current_classifiers = unload_classifiers()')
                composer.line(f'push_classifier("{suffix}")')
            else:
                composer.line(f'load_classifiers(current_classifiers, True)')

    elif rule.has_directive("classify"):
        with composer.if_stmt('not just_checking'):
            composer.line(f'push_classifier("{suffix}")' if is_pushing else f'pop_classifier()')

def compose_ruledef(rule_name: "str", rule: "RuleDef"):
    """Composes the functions for parsing a rule"""
    suffix: "str" = snakefy(rule_name)
    docstring: "str" = f"Parses a {rule_name} rule"
    node_kind: "str" = suffix.upper()

    with composer.func_def(f"is_{suffix}", [], docstring):
        composer.line(f"return match_{suffix}(True)")

    with composer.func_def(f"match_{suffix}", ['just_checking = False'], docstring):
        composer.line("index = source.index")
        if verbosity := rule.get("verbosity"):
            composer.line(f"push_verb('{verbosity}', True)")
        composer.line(f"log(False, debug3=f'Testing {rule_name}:' if just_checking else f'Matching {rule_name}:')")

        composer.line(f"node = {{ 'kind': '{node_kind}' }}")

        compose_ruledef_classification(rule_name, rule, suffix, True)

        if rule.has("scope"):
            composer.line(f"log(False, debug2=f'Entering {rule_name} scope')")
            composer.line(f"push_scope(just_checking, '{suffix.upper()}')")

        for i, entry in enumerate(rule.entries):
            # check_entry(entry)
            compose_group_entry(entry, rule, i == 0)
            with composer.suite():
                composer.line(f"log(False, debug3=f'Matched {rule_name} entry no.{i}')")

        with composer.else_stmt():
            with composer.if_stmt(f"just_checking"):
                composer.line("return False")
            composer.line(f"log(False, debug2=f'No match for {rule_name} rule')")
            composer.line("node = None")

        if scope_val := rule.get("scope"):
            composer.line(f"log(False, debug2=f'Leaving {rule_name} scope')")
            composer.line(f"pop_scope(node, '{scope_val}', just_checking)")

        if name_key := rule.get("lookup"):
            with composer.if_stmt("node"):
                composer.line(f"lookup_name = node.get('{name_key}')")
                composer.line(f"ref = scope_lookup(lookup_name, True)")
                composer.line(f"log(True, debug1=f\"ref lookup for {name_key} is {{ref}}\")")
                composer.line(f"merge(node, ref, keep_kind=True)")
                composer.line(f"print(f\"ref lookup for {name_key} is {{ref}}\")")

        elif name_key := rule.get("find"):
            with composer.if_stmt("node"):
                composer.line(f"lookup_name = node.get('{name_key}')")
                composer.line(f"ref = scope_lookup(lookup_name, False)")
                composer.line(f"log(True, debug1=f\"ref search for {name_key} is {{ref}}\")")
                composer.line(f"merge(node, ref, keep_kind=True)")
                composer.line(f"print(f\"ref search for {name_key} is {{ref}}\")")

        if identifier := rule.get("declare"):
            with composer.if_stmt("node"):
                composer.line(f"declare('{identifier}', node, '{node_kind}')")

        if verbosity := rule.get("verbosity"):
            composer.line(f"pop_verb(True)")

        compose_ruledef_classification(rule_name, rule, suffix, False)

        if rule.has_directive("deflate"):
            composer.line("deflate(node)")
        # else:
            # print("RULE", suffix, "does not have deflate")

        if rule.has_key:
            if rule.has("flip"):
                item = rule.get("flip")
                composer.line(
                    f"return flipped(reduced(node, '{rule.key}'), '{item}', '{rule.key}')"
                )
            else:
                composer.line(f"return reduced(node, '{rule.key}')")
        else:
            composer.line("return node")

    with composer.func_def(f"expect_{suffix}", [], docstring):
        composer.line("loc = source.index")
        with composer.if_stmt(f"node := match_{suffix}()"):
            composer.line("return node")
        composer.line(f'source.error("{node_kind} node expected.", at=loc)')


# endregion (RULE)

# region NODE GROUP


def compose_group_entry(group: "NodeGroup", rule: "RuleDef", first: "bool"):
    """Composes the code for a rule alternative"""
    if group.is_doubtfull:
        source.index = group.index
        source.error("Entry must have at least one non-optional item")

    elif group.is_uncertain:
        compose_group_entry_test(group, not first)

    elif isinstance(group.first, NodeGroup) and group.first.mode is GM_ALTERNATIVE:
        compose_group_alternative_test(group.first, not first)
    else:
        compose_reference(group.first, "test", test_chained=not first)

    with composer.suite():
        with composer.if_stmt(f"just_checking"):
            composer.line("return True")
        # for item in group.refs:
        #     if isinstance(item, GrammarNodeReference):
        #         compose_reference(item, "init", supress_init_one=True)

        for item in group.refs:
            if isinstance(item, GrammarNodeReference):
                compose_reference(item)

            elif isinstance(item, NodeGroup):
                compose_group_inline(item)


def compose_group_entry_test(group: "NodeGroup", chained: "bool", return_test: bool = False):
    calls = []
    for i, item in enumerate(group.first_optionals):
        call = None
        if isinstance(item, NodeGroup):
            if item.is_uncertain or item.is_doubtfull:
                source.index = item.index
                source.error("Level of matching uncertainty is too high")

            else:
                call = compose_group_entry_test(item, i > 0, return_test=True)

        else:
            call = compose_reference(item, "test", return_test=True)

        if call:
            calls.append(call)

    full_test = ' or '.join(calls)

    if return_test:
        return full_test

    stmt = 'elif' if chained else 'if'
    composer.line(f"{stmt} {full_test}:")


def compose_group_inline(group: "NodeGroup"):
    """Composes the code for a inline group"""
    if group.mode is GM_OPTIONAL:
        compose_group_optional(group)

    elif group.mode is GM_ALTERNATIVE:
        compose_group_alternative(group)

    elif group.mode is GM_SEQUENTIAL:
        compose_group_sequential(group)


def compose_group_optional(group: "NodeGroup"):
    """Composes the code for a optional inline group"""
    composer.comment("Option group below")
    compose_group_entry_test(group, False)
    with composer.suite():
        for item in group.refs:
            if isinstance(item, GrammarNodeReference):
                compose_reference(item, "capture")

            elif isinstance(item, NodeGroup):
                compose_group_inline(item)


def compose_group_alternative_test(group: "NodeGroup", chained: "bool", return_test: bool = False):
    calls = []
    for item in group.refs:
        call = None
        if isinstance(item, NodeGroup):
            if item.is_uncertain or item.is_doubtfull:
                source.index = item.index
                source.error("Level of matching uncertainty is too high")
            else:
                call = compose_group_entry_test(item, False, return_test=True)
        else:
            call = compose_reference(item, "test", return_test=True)

        if call:
            calls.append(call)

    full_test = ' or '.join(calls)

    if return_test:
        return full_test

    stmt = 'elif' if chained else 'if'
    composer.line(f"{stmt} {full_test}:")


def compose_group_alternative(group: "NodeGroup"):
    """Composes the code for a alternative inline group"""
    composer.comment("Alternative group below")
    dedent_after_loop = False

    if group.count in (NC_ONE_OR_MORE, NC_ZERO_OR_MORE):
        composer.line_and_indent(f"while True:")
        dedent_after_loop = True

    for i, item in enumerate(group.refs):
        if isinstance(item, NodeGroup):
            compose_group_inline(item)
        else:
            compose_reference(item, "test", test_chained=i > 0)
            with composer.suite():
                compose_reference(item, "capture", test_chained=i > 0)
    if group.count is not NC_ZERO_OR_ONE:
        with composer.else_stmt():
            if group.count is NC_ONE:
                composer.line("source.error('Unexpected token')")
            elif group.count in (NC_ONE_OR_MORE, NC_ZERO_OR_MORE):
                composer.line("break")

    if dedent_after_loop:
        composer.dedent_only()


def compose_group_sequential(group: "NodeGroup"):
    """Composes the code for a sequential inline group"""
    composer.comment("Sequential group below")
    dedent_after_loop = False

    if group.count in (NC_ONE_OR_MORE, NC_ZERO_OR_MORE):
        compose_reference(group.refs[0], "test", use_capture="item", test_loop=True)
        composer.indent_only()
        dedent_after_loop = True

    for i, item in enumerate(group.refs):
        if isinstance(item, NodeGroup):
            compose_group_inline(item)

        else:
            compose_reference(item, "capture", supress_init_one=True)

    if dedent_after_loop:
        composer.dedent_only()


# endregion (node group)

# endregion (definitions)

# region REFERENCES


def compose_reference(ref: "GrammarNodeReference", action: "str" = "capture", **kwargs):
    """Composes parsing operations referenced inside rules"""
    has_cap: "bool" = ref.capture != "_"
    must_append: "bool" = ref.capture.startswith("*")
    is_optional: "bool" = ref.count in (NC_ZERO_OR_ONE, NC_ZERO_OR_MORE)
    cap = kwargs.get("use_capture", ref.capture).lstrip("*")
    should_merge_rule: "bool" = False
    should_join_rule: "bool" = False
    should_update_rule: "bool" = False
    keep_kind: "bool" = False
    has_lookup: "bool" = False

    must_grab = '^' not in cap and cap != '_'
    if not must_grab:
        cap = cap.replace('^', '')

    if "." in cap:
        cap, lookup = cap.split(".", 2)
        has_lookup = True

    cap_is_kind = cap.isupper()
    if cap_is_kind:
        tkind = grammar.kinds.get(cap)
        if not tkind:
            tkind = grammar.tokens.get(cap)
        if not tkind:
            source.index = ref.index
            source.error(f"Token definition assigned for capture not found: '{cap}'")

    cap_class = f'token_classifier="{snakefy(cap)}"' if must_grab or cap_is_kind else f'token_classifier=None'
    test_chained = kwargs.get("test_chained", False)
    supress_init_one = kwargs.get("supress_init_one", False)
    return_test = kwargs.get("return_test", False)

    if action == "init":
        pass

    elif action == "test":
        call = ''
        if kwargs.get("test_loop", False):
            stmt = "while"
        else:
            stmt = "elif" if test_chained else "if"

        if isinstance(ref, TokenRef):
            val = escape_token(ref.value)
            if cap_is_kind:
                call = f"is_{snakefy(cap)}(r'{val}')"
            else:
                call = f"is_token(r'{val}')"

        elif isinstance(ref, KindRef):
            if cap_is_kind:
                source.index = ref.index
                source.error(f"capture name for token reference {ref.value} cannot be ALL_CAPS")
            call = f"is_{snakefy(ref.value)}(value='')"

        elif isinstance(ref, RuleRef):
            if cap_is_kind:
                source.index = ref.index
                source.error(f"capture name for rule reference {ref.value} cannot be ALL_CAPS")
            rule: "RuleDef" = grammar.get_rule(ref.value)
            if rule is None:
                source.index = ref.index
                source.error(f"Rule not found: {ref.value}")
            call = f"is_{snakefy(ref.value)}()"

        if return_test:
            return call
        else:
            composer.line(f"{stmt} {call}:")

    elif action == "capture":
        if isinstance(ref, TokenRef):
            val = escape_token(ref.value)
            if cap_is_kind:
                kind = cap
                cap = snakefy(cap)
                mcall = f"match_{cap}(r'{val}', {cap_class})"
                call = mcall if is_optional else f"expect_{cap}(r'{val}', {cap_class})"
            else:
                kind = "TOKEN"
                mcall = f"match_token(r'{val}', {cap_class})"
                call = mcall if is_optional else f"expect_token(r'{val}', {cap_class})"

        elif isinstance(ref, KindRef):
            if cap_is_kind:
                source.index = ref.index
                source.error(f"capture name for token reference {ref.value} cannot be ALL_CAPS")
            kind = snakefy(ref.value).upper()
            mcall = f"match_{snakefy(ref.value)}({cap_class})"
            call = mcall if is_optional else f"expect_{snakefy(ref.value)}({cap_class})"

        elif isinstance(ref, RuleRef):
            if cap_is_kind:
                source.index = ref.index
                source.error(f"capture name for rule reference {ref.value} cannot be ALL_CAPS")
            rule: "RuleDef" = grammar.get_rule(ref.value)
            if rule is None:
                source.index = ref.index
                source.error(f"Rule not found: {ref.value}")
            keepkind = rule.has_directive("keepkind")
            should_merge_rule = rule.has_directive("merge")
            should_join_rule = rule.has_directive("join") and not should_merge_rule
            should_update_rule = rule.has_directive("update") and not should_merge_rule and not should_join_rule

            kind = snakefy(ref.value).upper()
            mcall = f"match_{snakefy(ref.value)}()"
            call = mcall if is_optional else f"expect_{snakefy(ref.value)}()"

        if should_merge_rule:
            if ref.count not in (NC_ONE, NC_ZERO_OR_ONE):
                source.error(f"{ref.value} rule must have at most one ocurrence ({ref.count.name}).")
            composer.line(f"merge(node, {mcall}, keep_kind={keep_kind})")
        elif should_join_rule:
            if ref.count not in (NC_ONE, NC_ZERO_OR_ONE):
                source.error(f"{ref.value} rule must have at most one ocurrence ({ref.count.name}).")
            composer.line(f"join(node, {mcall})")
        elif should_update_rule:
            if ref.count not in (NC_ONE, NC_ZERO_OR_ONE):
                source.error(f"{ref.value} rule must have at most one ocurrence ({ref.count.name}).")
            composer.line(f"update(node, {mcall}, keep_kind={keep_kind})")
        else:
            if has_lookup:
                call = f"node_lookup({call}, '{lookup}', '{kind}')"
                mcall = f"node_lookup({mcall}, '{lookup}', '{kind}')"

            if must_grab:
                if ref.count is NC_ONE:
                    if must_append:
                        composer.line(f"append(node, '{cap}', {call})")
                    else:
                        composer.line(f"node['{cap}'] = {call}")
                elif ref.count is NC_ONE_OR_MORE:
                    composer.line(f"append(node, '{cap}', {call})")
                    composer.line_and_indent(f"while {cap} := {mcall}:")
                    composer.line(f"append(node, '{cap}', {cap})")
                    composer.dedent_only()
                elif ref.count is NC_ZERO_OR_MORE:
                    composer.line_and_indent(f"while {cap} := {mcall}:")
                    composer.line(f"append(node, '{cap}', {cap})")
                    composer.dedent_only()
                elif ref.count is NC_ZERO_OR_ONE:
                    if must_append:
                        composer.line(f"append(node, '{cap}', {mcall})")
                    else:
                        composer.line(f"node['{cap}'] = {mcall}")

            else:
                if ref.count is NC_ONE:
                    composer.line(call)
                elif ref.count is NC_ONE_OR_MORE:
                    composer.line_and_indent(f"while {mcall}:")
                    composer.line_and_indent(f"if not {mcall}:")
                    composer.line(f"break")
                    composer.dedent_only(2)
                elif ref.count is NC_ZERO_OR_MORE:
                    composer.line_and_indent(f"while {mcall}:")
                    composer.line_and_indent(f"if not {mcall}:")
                    composer.line(f"break")
                    composer.dedent_only(2)
                else:
                    composer.line(mcall)


def escape_token(tkn: "str") -> "str":
    """Escapes characters that have meaning in regluar expressions"""
    return {
        r"(": r"\(",
        r"{": r"\{",
        r"[": r"\[",
        r")": r"\)",
        r"}": r"\}",
        r"]": r"\]",
        r"\\": r"\\\\",
        r"^": r"\^",
        r"-": r"\-",
        r"*": r"\*",
        r"+": r"\+",
        r"?": r"\?",
        r'"': r"\"",
        r"'": r"\'",
        r".": r"\.",
    }.get(tkn, tkn)


# endregion (references)

# endregion (grammar nodes)

# endregion (functions)
