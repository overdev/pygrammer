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
import re
import time

from re import Match
from typing import Any, Sequence
from dataclasses import dataclass, field
from colorama import Fore, Back, Style
from enum import IntEnum, auto
from .grammar import *

# endregion (imports)
# ---------------------------------------------------------
# region EXPORTS


__all__ = [
    "DECORATORS",
    "DCR_WHITESPACE",
    "DCR_LINECOMMENT",
    "DCR_BLOCKCOMMENT",
    "DCR_SKIP",
    "DCR_FORCE_GENERATOR",
    "DCR_EXPAND",
    "DCR_GRABTOKEN",
    "DCR_INTERNAL",
    'DCR_RELFILEPATH',
    'DCR_ABSFILEPATH',
    'DCR_RELDIRPATH',
    'DCR_ABSDIRPATH',
    'DCR_ENSURERELATIVE',
    'DCR_ENSUREABSOLUTE',
    'DCR_LOADANDPARSE',
    "Verbosity",
    "ERROR",
    "WARNING",
    "DEBUG1",
    "SUCCESS",
    "DEBUG2",
    "INFO",
    "DEBUG3",
    "ALL",
    "COUNT_MAP",
    "GrammarNodes",
    "Source",
    "parse",
]


# endregion (exports)
# ---------------------------------------------------------
# region GLOBALS


grammar: "Source | None" = None

# endregion (globals)
# ---------------------------------------------------------
# region CONSTANTS & ENUMS


RE_SPACE = r"""\s+"""
RE_INLINE_COMM = r""";;.*[\n$]"""
RE_MULTILINE_COMM = r"""(?s);[*].*?[*];"""

RE_SECTION = r"""\.(\w+)(:\s*(\w+))?"""
RE_TOKEN_NAME = r"""[_A-Z][_A-Z0-9]+"""
RE_RULE_NAME = r"""([A-Z][a-zA-Z]*)+"""
RE_RULE_ATTRIB = r"""@"""
RE_TOKEN_VALUE = r"""`(.+?)`"""
RE_TOKEN_ITEM = r"""(?P<quote>[`'"])(.*?)(?P=quote)"""
RE_IMPORTS_SECTION = r"(?s)(.*?)\n\.end"
RE_DECORATOR = r"""@(\w+|[0-9])"""
RE_EXCLUSION = r"""\^(\w+)"""
RE_COLON = r""":"""
RE_ASSIGN = r"""="""
RE_OR = r"""\|"""
RE_SEMICOLON = r""";"""
RE_OPEN_PAREN = r"""\("""
RE_OPEN_BRACKET = r"""\["""
RE_CLOSE_PAREN = r"""\)"""
RE_CLOSE_PAREN_GROUP = r"""\)([?+*])?"""
RE_CLOSE_BRACKET = r"""\]"""
RE_UNDERSCORE = r"""_"""
RE_CAPTURE = r"""=>"""
RE_TOKEN_INSTANCE = r"""(?P<quote>['"])(.*?)(?P=quote)"""
RE_KIND_INSTANCE = r"""([_A-Z][_A-Z0-9]+)([?+*])?"""
RE_RULE_INSTANCE = r"""(([A-Z][a-zA-Z]*)+)([?+*])?"""

ERR_SECTION = "Section expected"
ERR_TOKEN_VALUE = "Expected token regular expression"
ERR_TOKEN_ITEM = "Token item already defined above"
ERR_RULE_NAME = "Rule already defined above"
ERR_DEFINITION = "Grammar item already defined"
ERR_UNEXPECTED_PIPE = "Unexpected '|'"
ERR_EXPECTED_PIPE = "Expected '|'"
ERR_ATTRIB_KEY = "Expected rule attribute key"
ERR_ATTRIB_VALUE = "Expected rule attribute value"

SECTION_TOKEN = "token"
SECTION_RULE = "rules"
SECTION_IMPORT = "imports"
SECTION_COLLECTION = "collection"
SECTION_END = r"\.end"

DCR_WHITESPACE = "whitespace"
DCR_LINECOMMENT = "linecomment"
DCR_BLOCKCOMMENT = "blockcomment"
DCR_SKIP = "skip"
DCR_FORCE_GENERATOR = "forcegenerator"
DCR_EXPAND = "expand"
DCR_INTERNAL = "internal"
DCR_GETTER = "getter"
DCR_GRABTOKEN = "grabtoken"
DCR_RELFILEPATH = "relfilepath"
DCR_ABSFILEPATH = "absfilepath"
DCR_RELDIRPATH = "reldirpath"
DCR_ABSDIRPATH = "absdirpath"
DCR_ENSURERELATIVE = "ensurerelative"
DCR_ENSUREABSOLUTE = "ensureabsolute"
DCR_LOADANDPARSE = "loadandparse"

DECORATORS = [
    DCR_WHITESPACE,
    DCR_LINECOMMENT,
    DCR_BLOCKCOMMENT,
    DCR_SKIP,
    DCR_FORCE_GENERATOR,
    DCR_EXPAND,
    DCR_INTERNAL,
    DCR_GETTER,
    DCR_GRABTOKEN,
    DCR_RELFILEPATH,
    DCR_ABSFILEPATH,
    DCR_RELDIRPATH,
    DCR_ABSDIRPATH,
    DCR_ENSURERELATIVE,
    DCR_ENSUREABSOLUTE,
    DCR_LOADANDPARSE,
]

COUNT_MAP = {
    "?": NC_ZERO_OR_ONE,
    "+": NC_ONE_OR_MORE,
    "*": NC_ZERO_OR_MORE,
}


class Verbosity(IntEnum):
    """Represents the levels of information printed out by the parser"""

    ERROR = 0
    WARNING = auto()
    DEBUG1 = auto()
    SUCCESS = auto()
    DEBUG2 = auto()
    INFO = auto()
    DEBUG3 = auto()
    ALL = auto()


ERROR = Verbosity.ERROR
WARNING = Verbosity.WARNING
DEBUG1 = Verbosity.DEBUG1
SUCCESS = Verbosity.SUCCESS
DEBUG2 = Verbosity.DEBUG2
INFO = Verbosity.INFO
DEBUG3 = Verbosity.DEBUG3
ALL = Verbosity.ALL

# endregion (constants)
# ---------------------------------------------------------
# region CLASSES


@dataclass
class GrammarNodes:
    """Represents the collection of tokens and rule definitions"""

    input_filename: str
    output_filename: str
    tokens: "dict[str, TokenDef]" = field(default_factory=dict)
    kinds: "dict[str, KindDef]" = field(default_factory=dict)
    collections: "dict[str, CollectionDef]" = field(default_factory=dict)
    rules: "dict[str, RuleDef]" = field(default_factory=dict)
    node_names: "list[str]" = field(default_factory=list)
    start_rule: 'RuleDef | None' = None
    import_code: "str | None" = None

    def has_node(self, node: "GrammarNodeDefinition") -> "bool":
        """Returns whether the specified node is in the collection"""
        return node.name in self.node_names

    def add(self, node: "GrammarNodeDefinition") -> "bool":
        """Adds the specified node to in the collection if it is not already added"""
        if self.has_node(node):
            return False

        if isinstance(node, TokenDef):
            self.tokens[node.name] = node
            return True

        elif isinstance(node, KindDef):
            self.kinds[node.name] = node
            return True

        elif isinstance(node, CollectionDef):
            self.collections[node.name] = node
            return True

        elif isinstance(node, RuleDef):
            self.rules[node.name] = node
            return True

        return False

    def get_rule(self, name: "str") -> "RuleDef | None":
        """Returns the rule definition with given name, or None otherwise"""
        return self.rules.get(name)

    def expand_tokens(self):
        """Perform the expansion of token definition values marked with the `@expand` decorator"""
        for token in self.tokens.values():
            if not token.has_decorator(DCR_EXPAND):
                continue

            for name in self.tokens:
                if name in token.value:
                    token.value = token.value.replace(name, self.tokens[name].value)


@dataclass
class Source:
    """Represents the contents of a source/text file"""

    contents: str
    current: str
    filename: str
    verbosity: "Verbosity" = ERROR

    @property
    def location(self) -> "tuple[str, int, int, str]":
        """Returns a 4-tuple containing the filename, line number, column, and line of code"""
        consumed = len(self.contents) - len(self.current)
        consumed_lines = self.contents[0:consumed].split("\n")
        line_num = len(consumed_lines)
        col_num = len(consumed_lines[-1]) + 1
        remaining_line = self.current.split("\n")[0]
        line = f"  {consumed_lines[-1]}{remaining_line}"

        return self.filename, line_num, col_num, line

    @property
    def index(self) -> "int":
        """Gets or sets the current string index of the grammar contents"""
        return len(self.contents) - len(self.current)

    @index.setter
    def index(self, value: "int") -> "None":
        ind = max(0, min(value, len(self.contents) - 1))
        self.current = self.contents[ind:]

    def skip(self):
        """Skip over whitespace and comments"""
        while True:
            if m := self.match_regex(RE_SPACE, skip=False):
                continue
            if m := self.match_regex(RE_INLINE_COMM, skip=False):
                continue
            if m := self.match_regex(RE_MULTILINE_COMM, skip=False):
                continue
            break

    def expect_regex(
        self, regex: "str", error_message: "str | None" = None
    ) -> "re.Match":
        """Tries to match regex and returns its match object. Prints an error otherwise."""
        if m := self.match_regex(regex):
            return m
        self.error(error_message or f"Expected '{regex}'")

    def match_regex(self, regex: "str", skip: "bool" = True) -> "re.Match | None":
        """Tries to match a regex, consumes it and returns its match object. Returns None otherwise."""
        if m := re.match(regex, self.current):
            val = m[0].replace("\n", "\\n")
            self.current = self.current[len(m[0]) :]
            if self.verbosity >= DEBUG3:
                self.info(f"Match success: {repr(regex)}", as_debug=True)
            if skip:
                self.skip()
            return m
        else:
            if self.verbosity >= DEBUG3:
                self.info(f"Match fail: {repr(regex)}", as_debug=True)
        return None

    def is_regex(self, regex: "str") -> "bool":
        """Returns whether a regex matches."""
        if re.match(regex, self.current):
            return True
        return False

    def error(self, message: "str", at_index: "int | None" = None) -> "None":
        """Aborts with an error message."""
        if at_index is not None:
            self.index = at_index

        file, lin, col, line = self.location

        header = f"{Fore.BLACK}{Back.RED}ERROR: {Style.BRIGHT}{Fore.RED}{Back.BLACK} {message}{Style.RESET_ALL}"
        location = f"{file}:{lin}:{col}{Style.RESET_ALL}"
        pointer = f"  {' ' * (col - 1)}{Fore.RED}^{Style.RESET_ALL}"

        print(f"{header}\n{location}\n{line}\n{pointer}", file=sys.stderr)
        sys.exit(1)

    def warning(self, message: "str") -> "None":
        """Aborts with an error message."""
        file, lin, col, line = self.location

        header = f"{Fore.BLACK}{Back.YELLOW}WARNING: {Style.BRIGHT}{Fore.YELLOW}{Back.BLACK} {message}{Style.RESET_ALL}"
        location = f"{file}:{lin}:{col}{Style.RESET_ALL}"
        pointer = f"  {' ' * (col - 1)}{Fore.YELLOW}^{Style.RESET_ALL}"

        print(f"{header}\n{location}\n{line}\n{pointer}", file=sys.stderr)

    def info(
        self, message: "str", localized: "bool" = True, as_debug: "bool" = False
    ) -> "None":
        """Prints an information message."""
        file, lin, col, line = self.location

        if as_debug:
            header = f"{Fore.BLACK}{Back.WHITE}DEBUG: {Style.BRIGHT}{Fore.WHITE}{Back.BLACK} {message}{Style.RESET_ALL}"
        else:
            header = f"{Fore.BLACK}{Back.CYAN}INFO: {Style.BRIGHT}{Fore.CYAN}{Back.BLACK} {message}{Style.RESET_ALL}"
        location = f"{file}:{lin}:{col}{Style.RESET_ALL}"
        pointer = f"  {' ' * (col - 1)}{Fore.CYAN}^{Style.RESET_ALL}"

        if localized:
            print(f"{header}\n{location}\n{line}\n{pointer}", file=sys.stderr)
        else:
            print(header, file=sys.stdout)

    def success(self, message: "str", localized: "bool" = True) -> "None":
        """Prints an success message."""
        file, lin, col, line = self.location

        header = f"{Fore.BLACK}{Back.GREEN}SUCCESS: {Style.BRIGHT}{Fore.GREEN}{Back.BLACK} {message}{Style.RESET_ALL}"
        location = f"{file}:{lin}:{col}{Style.RESET_ALL}"
        pointer = f"  {' ' * (col - 1)}{Fore.GREEN}^{Style.RESET_ALL}"

        if localized:
            print(f"{header}\n{location}\n{line}\n{pointer}", file=sys.stderr)
        else:
            print(header, file=sys.stdout)


# endregion (classes)
# ---------------------------------------------------------
# region FUNCTIONS


def parse(grammar_source: "str", grammar_filename: "str", output_parser_filename: "str", verbosity: "Verbosity" = ERROR) -> "tuple[GrammarNodes, Source]":
    """Parses a grammar and produces an parser API module"""
    global grammar

    ptime: "float" = time.process_time()
    last_grammar: "Source" = grammar

    grammar = Source(grammar_source, grammar_source, grammar_filename, verbosity)

    if verbosity >= INFO:
        grammar.info(f"Parsing grammar file: '{grammar_filename}'")

    if verbosity >= DEBUG1:
        num_lines = grammar_source.count("\n")
        grammar.info(f"Grammar has {num_lines} lines, {len(grammar_source)} chars", as_debug=True)

    grammar_nodes: "GrammarNodes" = GrammarNodes(grammar_filename, output_parser_filename)
    parse_grammar(grammar_nodes, verbosity)
    grammar_nodes.expand_tokens()

    delta: "float" = time.process_time() - ptime

    if verbosity >= DEBUG1:
        grammar.info(f"Grammar parsing took {delta:.4f} seconds.", localized=False, as_debug=True)

    if verbosity >= SUCCESS:
        grammar.success(f"Grammar parsing finished.", localized=False)

    src = grammar
    grammar = last_grammar

    return grammar_nodes, src


def parse_grammar(grammar_nodes: "GrammarNodes", verbosity: "Verbosity" = ERROR):
    """Parses the grammar sections"""
    grammar.skip()
    while True:
        if parse_section(grammar_nodes, verbosity):
            continue

        break


def parse_section(grammar_nodes: "GrammarNodes", verbosity: "Verbosity" = ERROR) -> "bool":
    """Parses a grammar section"""
    index = grammar.index
    m: "Match" = grammar.expect_regex(RE_SECTION, ERR_SECTION)

    section_name: "str" = m[1]
    section_spec: "str" = m[3] if m[3] else m[1]

    grammar.skip()

    if section_name == SECTION_TOKEN:
        if verbosity >= DEBUG1:
            grammar.info(f"Section: {section_name} ({section_spec})", localized=False, as_debug=True)

        if section_name == section_spec:
            parse_token_definitions(section_name, grammar_nodes, verbosity)
            grammar.expect_regex(SECTION_END, "Expected section end")
        else:
            parse_kind_definition(section_name, section_spec, grammar_nodes, verbosity)
        return True

    if section_name == SECTION_COLLECTION:
        if verbosity >= DEBUG1:
            grammar.info(f"Section: {section_name} ({section_spec})", localized=False, as_debug=True)

        add_collection_definition(section_name, section_spec, grammar_nodes, index, verbosity)
        return True

    if section_name == SECTION_IMPORT:
        if grammar_nodes.import_code:
            grammar.error("Section .import can occur at most once.")
        import_match = grammar.expect_regex(RE_IMPORTS_SECTION)
        grammar_nodes.import_code = import_match[1]

        return True

    if section_name == SECTION_RULE:
        if verbosity >= DEBUG1:
            grammar.info(f"Section: {section_name}", localized=False, as_debug=True)

        parse_rule_definitions(grammar_nodes, verbosity)
        return True

    return False


def parse_decorators(exclusions: "list[str]", annotations: "list[str]", match_index: "list[str]", verbosity: "Verbosity" = ERROR):
    """Parses token definition decorators"""

    has_match_index: "bool" = False
    while True:
        if directive_match := grammar.match_regex(RE_DECORATOR):
            if directive_match[1] in DECORATORS:
                annotations.append(directive_match[1])
                if verbosity >= DEBUG2:
                    grammar.info(f"Directive (annotation): {directive_match[0]}", localized=False, as_debug=True)

            elif re.fullmatch(r"[0-9]", directive_match[1]):
                if has_match_index:
                    grammar.error("Multiple match group indices")
                else:
                    has_match_index = True
                match_index[0] = int(directive_match[1], 10)
                if verbosity >= DEBUG2:
                    grammar.info(f"Directive (regex match group index): {directive_match[0]}", localized=False, as_debug=True)

            else:
                if verbosity >= WARNING:
                    grammar.warning(f"Unknown decorator {directive_match[1]} (will be ignored)")
            continue

        if exclusion_match := grammar.match_regex(RE_EXCLUSION):
            if verbosity >= DEBUG2:
                grammar.info(f"Directive (value exclusion): {exclusion_match[0]}", localized=False, as_debug=True)
            exclusions.append(exclusion_match[1])
            continue

        break


def parse_token_definitions(section_name: "str", grammar_nodes: "GrammarNodes", verbosity: "Verbosity" = ERROR):
    """Parses the `.token` section"""
    value_match: Match

    while True:
        if name_match := grammar.match_regex(RE_TOKEN_NAME):
            def_name: "str" = name_match[0]
            value_match = grammar.expect_regex(RE_TOKEN_VALUE, ERR_TOKEN_VALUE)

            if verbosity >= DEBUG2:
                grammar.info(
                    f"{def_name} = {value_match[0]}", localized=False, as_debug=True
                )

            def_excludes: "list[str]" = []
            def_decorators: "list[str]" = []
            def_match_index: "list[str]" = [0]

            parse_decorators(def_excludes, def_decorators, def_match_index, verbosity)
            def_rule: "str" = value_match[1]

            token_definition: "TokenDef" = TokenDef(
                def_name,
                def_rule,
                True,
                def_excludes,
                def_decorators,
                def_match_index[0],
            )

            if grammar_nodes.has_node(token_definition):
                grammar.error(ERR_DEFINITION)
            grammar_nodes.add(token_definition)

            if verbosity >= DEBUG1:
                grammar.info(f"Token added: {token_definition.name}", localized=False)

            grammar.skip()
            continue
        break


def parse_kind_definition(section_name: "str", section_spec: "str", grammar_nodes: "GrammarNodes", verbosity: "Verbosity" = ERROR):
    """Parses a token group section"""
    kind_items: "list[str]" = []

    while True:
        if item_match := grammar.match_regex(RE_TOKEN_ITEM):
            item_value = item_match[2]

            if verbosity >= DEBUG2:
                grammar.info(f"Token kind: {repr(item_value)}", localized=False, as_debug=True)

            if item_value in kind_items:
                grammar.error(ERR_TOKEN_ITEM)

            kind_items.append(item_value)
            continue
        break

    grammar.expect_regex(SECTION_END, "Expected section end")

    kind_definition: "KindDef" = KindDef(section_spec, kind_items)

    if grammar_nodes.has_node(kind_definition):
        grammar.error(ERR_DEFINITION)
    grammar_nodes.add(kind_definition)

    if verbosity >= DEBUG1:
        grammar.info(f"Kind added: {kind_definition.name}", localized=False)


def add_collection_definition(section_name: "str", section_spec: "str", grammar_nodes: "GrammarNodes", index: int, verbosity: "Verbosity" = ERROR):
    collection_definition: "CollectionDef" = CollectionDef(section_spec, index)

    if grammar_nodes.has_node(collection_definition):
        grammar.error(ERR_DEFINITION)
    grammar_nodes.add(collection_definition)

    if verbosity >= DEBUG1:
        grammar.info(f"Collection added: {collection_definition.name}", localized=False)


def parse_rule_attribute_or_directive(rule: "RuleDef", verbosity: "Verbosity" = ERROR):
    """Parses a single rule attribute or directive"""
    re_word: "str" = r"\w+"
    re_value: "str" = r"\w+(\.\w+)*"
    match_key = grammar.expect_regex(re_word, ERR_ATTRIB_KEY)

    if grammar.match_regex(r":"):
        match_value = grammar.expect_regex(re_value, ERR_ATTRIB_VALUE)

        if not rule.add_attribute(match_key[0], match_value[0]):
            grammar.warning(f"Rule {rule.name} already has {match_key[0]} attribute")
        elif verbosity >= INFO:
            grammar.info(f"Rule attribute added: {match_key[0]}", localized=False)

    else:
        if not rule.add_directive(match_key[0]):
            grammar.warning(f"Rule {rule.name} already has {match_key[0]} directive")
        elif verbosity >= INFO:
            grammar.info(f"Rule directive added: {match_key[0]}", localized=False)

def parse_rule_attributes(rule: "RuleDef", verbosity: "Verbosity" = ERROR):
    """Parses a set of rule attributes or directives"""

    if grammar.match_regex(RE_RULE_ATTRIB):
        grammar.expect_regex(r"\{")
        parse_rule_attribute_or_directive(rule, verbosity)

        while grammar.match_regex(r","):
            parse_rule_attribute_or_directive(rule, verbosity)

        grammar.expect_regex(r"\}")


def parse_rule_definitions(grammar_nodes: "GrammarNodes", verbosity: "Verbosity" = ERROR):
    """Parses the .rules section"""
    names: "list[str]" = []
    can_be_nested: "bool" = True

    while True:
        if rule_match := grammar.match_regex(RE_RULE_NAME):
            if rule_match[0] in names:
                grammar.error(ERR_RULE_NAME)
            names.append(rule_match[0])

            rule_definition: "RuleDef" = RuleDef(rule_match[0], grammar.index)
            grammar.expect_regex(RE_COLON)

            attr_index = grammar.index
            parse_rule_attributes(rule_definition, verbosity)
            if rule_definition.has_directive("start"):
                if grammar_nodes.start_rule is not None:
                    grammar.index = attr_index
                    grammer.error("Multiple starting rules selected.")
                grammar_nodes.start_rule = rule_definition
            grammar.expect_regex(RE_ASSIGN)

            index = grammar.index
            entry: "NodeGroup" = rule_definition.add_entry("node")
            entry.index = index
            starts_with_rule: "bool" = parse_rule_entry(grammar_nodes, rule_definition, entry, rule_definition.node, verbosity)

            if starts_with_rule:
                can_be_nested = False

            while grammar.match_regex(RE_OR):
                index = grammar.index
                entry = rule_definition.add_entry("node")
                entry.index = index
                starts_with_rule = parse_rule_entry(grammar_nodes, rule_definition, entry, rule_definition.node, verbosity)

                if starts_with_rule:
                    can_be_nested = False

            grammar.expect_regex(RE_SEMICOLON)

            if grammar_nodes.has_node(rule_definition):
                grammar.error(ERR_DEFINITION)
            grammar_nodes.add(rule_definition)

            if verbosity >= DEBUG1:
                rule_style: "str" = "simple" if rule_definition.is_simple else "complex"
                grammar.info(f"Rule added: {rule_definition.name} ({rule_style})", localized=False)

            continue
        break


def parse_noskip(grammar_nodes: "GrammarNodes", ref_name: "str", previous_ref: "GrammarNodeReference"):
    if token_def := grammar_nodes.tokens.get(ref_name):
        if token_def.has_decorator(DCR_SKIP):
            if previous_ref is not None:
                previous_ref.do_not_skip(ref_name)
            token_def.add_decorator(DCR_FORCE_GENERATOR)


def parse_rule_entry(grammar_nodes: "GrammarNodes", rule: "RuleDef", entry: "NodeGroup", node: dict[str, Any], verbosity: "Verbosity" = ERROR) -> "bool":
    """Parses the rule definition(s)"""
    ref: GrammarNodeReference | NodeGroup
    refs: "Sequence[GrammarNodeReference | NodeGroup]" = []
    index: "int" = grammar.index
    starts_with_rule: "bool" = False
    previous_ref: GrammarNodeReference | None = None

    while True:
        index = grammar.index

        if match_item := grammar.match_regex(RE_TOKEN_INSTANCE):
            ref = TokenRef(match_item[2], source_index=index)
            refs.append(ref)
            previous_ref = ref
            continue

        if match_item := grammar.match_regex(RE_KIND_INSTANCE):
            cnt = COUNT_MAP.get(match_item[2], NC_ONE)
            ref = KindRef(match_item[1], count=cnt, source_index=index)
            refs.append(ref)
            parse_noskip(grammar_nodes, match_item[1], previous_ref)
            previous_ref = ref
            continue

        if match_item := grammar.match_regex(RE_RULE_INSTANCE):
            cnt = COUNT_MAP.get(match_item[3], NC_ONE)
            ref = RuleRef(match_item[1], count=cnt, source_index=index)
            if len(refs) == 0:
                starts_with_rule = True
            refs.append(ref)
            previous_ref = ref
            continue

        if match_item := grammar.match_regex(RE_OPEN_PAREN):
            inline_group: "NodeGroup" = NodeGroup(GM_SEQUENTIAL, NC_ONE)

            if verbosity >= DEBUG2:
                grammar.info("Entered inline Group", localized=False, as_debug=True)

            previous_ref = parse_inline_group(inline_group, RE_CLOSE_PAREN_GROUP, previous_ref)

            if inline_group.mode is GM_SEQUENTIAL and inline_group.count is NC_ONE:
                grammar.warning("Redundant grouping")

            if verbosity >= DEBUG2:
                grammar.info(f"Exited inline Group: {inline_group}", localized=False, as_debug=True)

            refs.append(inline_group)
            continue

        if match_item := grammar.match_regex(RE_OPEN_BRACKET):
            inline_group: "NodeGroup" = NodeGroup(GM_OPTIONAL, NC_ONE)

            if verbosity >= DEBUG2:
                grammar.info("Entered inline optional Group", localized=False, as_debug=True)

            previous_ref = parse_inline_group(inline_group, RE_CLOSE_BRACKET, previous_ref)

            if verbosity >= DEBUG2:
                grammar.info("Exited inline optional Group", localized=False, as_debug=True)

            refs.append(inline_group)
            continue
        break

    for i, ref in enumerate(refs):
        entry.add_item(ref, "_")

    if grammar.match_regex(RE_CAPTURE):
        capts: "str | list[Any]" = parse_entry_capture(refs, node, verbosity=verbosity, rule=rule)
        assign_group_captures(entry, capts, verbosity)

    return starts_with_rule


def parse_entry_capture(refs: "Sequence[GrammarNodeReference | NodeGroup]", node: dict[str, Any], inline: "bool" = False, verbosity: "Verbosity" = ERROR, rule: RuleDef=None) -> "str | list[Any]":
    """Parses the capture names for rule definition(s)"""
    captures = []
    closed = False

    while True:
        if capt_match := grammar.match_regex(RE_UNDERSCORE):
            captures.append(RE_UNDERSCORE)
            continue

        if capt_match := grammar.match_regex(RE_OPEN_PAREN):
            sub_capt: "str | list[Any]" = parse_entry_capture(refs, node, inline=True)
            captures.append(sub_capt)
            continue

        if capt_match := grammar.match_regex(RE_CLOSE_PAREN):
            if not inline:
                grammar.error(f"Unexpected ')'")
            closed = True
            break

        if capt_match := grammar.match_regex(r"(\*)?(\^)?(\w+)(\.\w+)?"):
            captures.append(capt_match[0])
            capt_sequence = capt_match[1]

            if capt_match[4]:
                capture = f"{capt_match[3]}.{capt_match[4]}"
            else:
                capture = capt_match[3]

            if capt_sequence:
                node[capture] = []
            else:
                node[capture] = None

            continue
        break

    if inline and not closed:
        grammar.error("Expected ')'")

    return captures


def assign_group_captures(group: "NodeGroup", captures: "str | list[str]", verbosity: "Verbosity" = ERROR):
    """Assign the capture names to respective node references"""
    refs: "list[GrammarNodeReference | NodeGroup]" = group.refs
    n_capts: "int" = len(captures)
    n_refs: "int" = len(refs)

    for i in range(n_refs):
        ref = refs[i]
        if i >= n_capts:
            continue
        cap = captures[i]

        if (isinstance(ref, GrammarNodeReference) and isinstance(cap, str) or isinstance(ref, (str, NodeGroup)) and isinstance(cap, list)):
            ref.capture = cap

            if isinstance(ref, NodeGroup) and isinstance(cap, list):
                ref.captures = cap
                ref.capture = "_"
                assign_group_captures(ref, cap, verbosity)

        elif (isinstance(ref, NodeGroup) and ref.mode is GM_ALTERNATIVE and isinstance(cap, str)):
            for subref in ref.refs:
                subref.capture = cap

            ref.capture = cap

        else:
            if verbosity >= WARNING:
                grammar.warning(f"Rule entry mismatches items and capture names")

        if verbosity >= DEBUG1:
            grammar.info(f"Node ref: `{ref}`, assigned: `{cap}`", localized=False, as_debug=True)


def parse_inline_group(group: "NodeGroup", re_close_brace: "str", previous_ref: "GrammarNodeReference", verbosity: "Verbosity" = ERROR) -> 'GrammarNodeReference | None':
    """Parses an inline group of node references"""
    initial_mode: "GroupMode" = group.mode
    initial_count: "NodeCount" = group.count
    can_be_alternative: "bool" = group.mode is not GM_OPTIONAL
    is_alternative: "bool" = group.mode is GM_ALTERNATIVE
    expects_pipe: "bool" = False
    has_rule: "bool" = False
    refs: "Sequence[GrammarNodeReference | NodeGroup]" = []
    ref: "GrammarNodeReference | NodeGroup" = previous_ref
    first_ref = previous_ref

    while True:
        index = grammar.index
        if match_item := grammar.match_regex(RE_OR):
            if is_alternative:
                if expects_pipe:
                    expects_pipe = False
                    continue
                else:
                    grammar.error(ERR_UNEXPECTED_PIPE, index)

            elif can_be_alternative:
                if len(refs) == 1:
                    is_alternative = True
                    previous_ref = first_ref
                    expects_pipe = False
                    group.mode = GM_ALTERNATIVE
                    continue
                else:
                    grammar.error(ERR_UNEXPECTED_PIPE, index)
            else:
                grammar.error(ERR_UNEXPECTED_PIPE, index)

        if match_item := grammar.match_regex(RE_TOKEN_INSTANCE):
            if is_alternative and expects_pipe:
                grammar.error(ERR_EXPECTED_PIPE, index)

            ref = TokenRef(match_item[2])
            refs.append(ref)
            if is_alternative:
                expects_pipe = True
            previous_ref = ref

            continue

        if match_item := grammar.match_regex(RE_KIND_INSTANCE):
            if is_alternative and expects_pipe:
                grammar.error(ERR_EXPECTED_PIPE, index)

            cnt = COUNT_MAP.get(match_item[2], NC_ONE)
            ref = KindRef(match_item[1], count=cnt)
            refs.append(ref)
            if is_alternative:
                expects_pipe = True
            else:
                parse_noskip(grammar_nodes, match_item[1], previous_ref)
                previous_ref = ref

            continue

        if match_item := grammar.match_regex(RE_RULE_INSTANCE):
            if is_alternative:
                if expects_pipe:
                    grammar.error(ERR_EXPECTED_PIPE, index)

            cnt = COUNT_MAP.get(match_item[2], NC_ONE)
            ref = RuleRef(match_item[1], count=cnt)
            refs.append(ref)
            has_rule = True
            if is_alternative:
                expects_pipe = True
            else:
                previous_ref = ref
            continue

        if match_item := grammar.match_regex(RE_OPEN_PAREN):
            if is_alternative and expects_pipe:
                grammar.error(ERR_EXPECTED_PIPE, index)

            inline_group: "NodeGroup" = NodeGroup(GM_SEQUENTIAL, NC_ONE)
            ref = parse_inline_group(inline_group, RE_CLOSE_PAREN_GROUP, previous_ref)

            if inline_group.mode is GM_SEQUENTIAL and inline_group.count is NC_ONE:
                grammar.warning("Redundant grouping")

            refs.append(inline_group)
            if is_alternative:
                expects_pipe = True
            else:
                previous_ref = ref

            continue

        if match_item := grammar.match_regex(RE_OPEN_BRACKET):
            if is_alternative and expects_pipe:
                grammar.error(ERR_EXPECTED_PIPE, index)

            inline_group: "NodeGroup" = NodeGroup(GM_OPTIONAL, NC_ONE)
            ref = parse_inline_group(inline_group, RE_CLOSE_BRACKET, previous_ref)
            refs.append(inline_group)
            if is_alternative:
                expects_pipe = True
            else:
                previous_ref = ref

            continue
        break

    if close_match := grammar.expect_regex(re_close_brace, "Closing brace expected"):
        if initial_mode is not GM_OPTIONAL:
            group.count = COUNT_MAP.get(close_match[1], NC_ONE)

    for ref in refs:
        group.add_item(ref, "_")

    return previous_ref

# endregion (functions)
