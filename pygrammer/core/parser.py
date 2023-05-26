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
    'Verbosity',
    'ERROR',
    'WARNING',
    'DEBUG1',
    'SUCCESS',
    'DEBUG2',
    'INFO',
    'DEBUG3',
    'ALL',
    'COUNT_MAP',
    'GrammarNodes',
    'parse',
]


# endregion (exports)
# ---------------------------------------------------------
# region GLOBALS


grammar: 'Source | None' = None

# endregion (globals)
# ---------------------------------------------------------
# region CONSTANTS & ENUMS


RE_SPACE = r'''\s+'''
RE_INLINE_COMM = r''';;.*[\n$]'''
RE_MULTILINE_COMM = r'''(?s);[*].*?[*];'''

RE_SECTION = r"""\.(\w+)(:\s*(\w+))?"""
RE_TOKEN_NAME = r"""[_A-Z][_A-Z0-9]+"""
RE_RULE_NAME = r"""([A-Z][a-zA-Z]*)+"""
RE_TOKEN_VALUE = r"""(x)?`(.+)`(!)?"""
RE_TOKEN_ITEM = r"""(?P<quote>['"])(.*?)(?P=quote)"""
RE_DECORATOR = r"""@(\w+)"""
RE_EXCLUSION = r"""\^(\w+)"""
RE_COLON = r""":"""
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

SECTION_TOKEN = 'token'
SECTION_RULE = 'rules'
SECTION_END = r'\.end'
DECORATOR_SKIP = 'skip'
DECORATOR_SLC = 'slc'
DECORATOR_MLC = 'mlc'

COUNT_MAP = {
    '?': NC_ZERO_OR_ONE,
    '+': NC_ONE_OR_MORE,
    '*': NC_ZERO_OR_MORE,
}


class Verbosity(IntEnum):
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
    input_filename: str
    output_filename: str
    tokens: dict[str, TokenDef] = field(default_factory=dict)
    kinds: dict[str, KindDef] = field(default_factory=dict)
    rules: dict[str, RuleDef] = field(default_factory=dict)
    node_names: list[str] = field(default_factory=list)

    def has_node(self, node: GrammarNodeDefinition) -> bool:
        return node.name in self.node_names

    def add(self, node: GrammarNodeDefinition) -> bool:
        if self.has_node(node):
            return False

        if isinstance(node, TokenDef):
            self.tokens[node.name] = node
            return True

        elif isinstance(node, KindDef):
            self.tokens[node.name] = node
            return True

        elif isinstance(node, RuleDef):
            self.tokens[node.name] = node
            return True

        return False


@dataclass
class Source:
    contents: str
    current: str
    filename: str
    verbosity: Verbosity = ERROR

    @property
    def location(self) -> tuple[str, int, int, str]:
        """Returns a 4-tuple containing the filename, line number, column, and line of code"""
        consumed = len(self.contents) - len(self.current)
        consumed_lines = self.contents[0: consumed].split('\n')
        line_num = len(consumed_lines)
        col_num = len(consumed_lines[-1]) + 1
        remaining_line = self.current.split('\n')[0]
        line = f"  {consumed_lines[-1]}{remaining_line}"

        return self.filename, line_num, col_num, line

    @property
    def index(self) -> int:
        """Gets the current string index of the grammar contents"""
        return len(self.contents) - len(self.current)

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

    def expect_regex(self, regex: str, error_message: str | None = None) -> re.Match:
        """Tries to match regex and returns its match object. Prints an error otherwise."""
        if m := self.match_regex(regex):
            return m
        self.error(error_message or f"Expected '{regex}'")

    def match_regex(self, regex: str, skip: bool = True) -> re.Match | None:
        """Tries to match a regex, consumes it and returns its match object. Returns None otherwise."""
        if m := re.match(regex, self.current):
            val = m[0].replace('\n', '\\n')
            self.current = self.current[len(m[0]):]
            if self.verbosity >= DEBUG3:
                self.info(f"Match success: {repr(regex)}", as_debug=True)
            if skip:
                self.skip()
            return m
        else:
            if self.verbosity >= DEBUG3:
                self.info(f"Match fail: {repr(regex)}", as_debug=True)
        return None

    def is_regex(self, regex: str) -> bool:
        """Returns whether a regex matches."""
        if re.match(regex, self.current):
            return True
        return False

    def error(self, message: str) -> None:
        """Aborts with an error message."""
        file, lin, col, line = self.location

        header = f"{Fore.BLACK}{Back.RED}ERROR: {Style.BRIGHT}{Fore.RED}{Back.BLACK} {message}{Style.RESET_ALL}"
        location = f"{file}:{lin}:{col}{Style.RESET_ALL}"
        pointer = f"  {' ' * (col - 1)}{Fore.RED}^{Style.RESET_ALL}"

        print(f"{header}\n{location}\n{line}\n{pointer}", file=sys.stderr)
        sys.exit(1)

    def warning(self, message: str) -> None:
        """Aborts with an error message."""
        file, lin, col, line = self.location

        header = f"{Fore.BLACK}{Back.YELLOW}WARNING: {Style.BRIGHT}{Fore.YELLOW}{Back.BLACK} {message}{Style.RESET_ALL}"
        location = f"{file}:{lin}:{col}{Style.RESET_ALL}"
        pointer = f"  {' ' * (col - 1)}{Fore.YELLOW}^{Style.RESET_ALL}"

        print(f"{header}\n{location}\n{line}\n{pointer}", file=sys.stderr)

    def info(self, message: str, localized: bool = True, as_debug: bool = False) -> None:
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

    def success(self, message: str, localized: bool = True) -> None:
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


def parse(grammar_source: str, grammar_filename: str, output_parser_filename: str, verbosity: Verbosity = ERROR) -> GrammarNodes:
    """Parses a grammar and produces an parser API module"""
    global grammar

    ptime: float = time.process_time()
    last_grammar: Source = grammar

    grammar = Source(grammar_source, grammar_source, grammar_filename, verbosity)

    if verbosity >= INFO:
        grammar.info(f"Parsing grammar file: '{grammar_filename}'")

    if verbosity >= DEBUG1:
        num_lines = grammar_source.count('\n')
        grammar.info(f"Grammar has {num_lines} lines, {len(grammar_source)} chars", as_debug=True)

    grammar_nodes: GrammarNodes = GrammarNodes(grammar_filename, output_parser_filename)
    parse_grammar(grammar_nodes, verbosity)

    delta: float = time.process_time() - ptime

    if verbosity >= SUCCESS:
        grammar.info(f"Grammar parsing finished.")

    if verbosity >= DEBUG1:
        grammar.info(f"Grammar parsing took {delta:.4f} seconds.", as_debug=True)

    grammar = last_grammar
    return grammar_nodes


def parse_grammar(grammar_nodes: GrammarNodes, verbosity: Verbosity = ERROR):
    """"""
    grammar.skip()
    while True:
        if parse_section(grammar_nodes, verbosity):
            continue

        break


def parse_section(grammar_nodes: GrammarNodes, verbosity: Verbosity = ERROR) -> bool:
    """"""
    m: Match = grammar.expect_regex(RE_SECTION, ERR_SECTION)

    section_name: str = m[1]
    section_spec: str = m[3] if m[3] else m[1]

    grammar.skip()

    if section_name == SECTION_TOKEN:
        if verbosity >= DEBUG1:
            grammar.info(f"Section: {section_name} ({section_spec})", as_debug=True)

        if section_name == section_spec:
            parse_token_definitions(section_name, grammar_nodes, verbosity)
            grammar.expect_regex(SECTION_END, "Expected section end")
        else:
            parse_kind_definition(section_name, section_spec, grammar_nodes, verbosity)
        return True

    if section_name == SECTION_RULE:
        if verbosity >= DEBUG1:
            grammar.info(f"Section: {section_name}", as_debug=True)

        parse_rule_definitions(grammar_nodes, verbosity)
        return True

    return False


def parse_token_definitions(section_name: str, grammar_nodes: GrammarNodes, verbosity: Verbosity = ERROR):
    """"""
    value_match: Match

    while True:
        if name_match := grammar.match_regex(RE_TOKEN_NAME):
            def_name: str = name_match[0]
            value_match = grammar.expect_regex(RE_TOKEN_VALUE, ERR_TOKEN_VALUE)
            def_excludes: list[str] = []
            def_decorators: list[str] = []

            if verbosity >= DEBUG2:
                grammar.info(f"{def_name} = {value_match[0]}", as_debug=True)

            while True:
                if directive_match := grammar.match_regex(RE_DECORATOR):

                    if verbosity >= DEBUG2:
                        grammar.info(f"Directive: {directive_match[0]}", as_debug=True)

                    if directive_match[1] == DECORATOR_SKIP:
                        # skippable
                        def_decorators.append(directive_match[1])
                    elif directive_match[1] == DECORATOR_SLC:
                        # single line comment
                        def_decorators.append(directive_match[1])
                    elif directive_match[1] == DECORATOR_MLC:
                        # multi line comment
                        def_decorators.append(directive_match[1])
                    continue

                if exclusion_match := grammar.match_regex(RE_EXCLUSION):

                    if verbosity >= DEBUG2:
                        grammar.info(f"Directive: {exclusion_match[0]}", as_debug=True)
                    def_excludes.append(exclusion_match[1])
                    continue

                break
            def_expand: bool = value_match[1] is not None
            def_rule: str = value_match[2]
            def_format: bool = value_match[3] is None

            # if def_expand:
                # def_rule = expand_token_value(def_rule)

            token_definition: TokenDef = TokenDef(def_name, def_rule, True, def_format, def_excludes, def_decorators)

            if grammar_nodes.has_node(token_definition):
                grammar.error(ERR_DEFINITION)
            grammar_nodes.add(token_definition)

            if verbosity >= DEBUG1:
                grammar.info(f"Token added: {token_definition.name}", localized=False)


            grammar.skip()
            continue
        break



def parse_kind_definition(section_name: str, section_spec: str, grammar_nodes: GrammarNodes, verbosity: Verbosity = ERROR):
    """"""
    kind_items: list[str] = []

    while True:
        if item_match := grammar.match_regex(RE_TOKEN_ITEM):
            if verbosity >= DEBUG2:
                grammar.info(f"Token kind: {repr(item_match[2])}", localized=False, as_debug=True)
            if item_match[0] in kind_items:
                grammar.error(ERR_TOKEN_ITEM)

            kind_items.append(item_match[0])
            continue

        break
    grammar.expect_regex(SECTION_END, "Expected section end")

    kind_definition: KindDef = KindDef(section_spec, kind_items)

    if grammar_nodes.has_node(kind_definition):
        grammar.error(ERR_DEFINITION)
    grammar_nodes.add(kind_definition)

    if verbosity >= DEBUG1:
        grammar.info(f"Kind added: {kind_definition.name}", localized=False)



def parse_rule_definitions(grammar_nodes: GrammarNodes, verbosity: Verbosity = ERROR):
    """"""
    names: list[str] = []

    while True:
        if rule_match := grammar.match_regex(RE_RULE_NAME):
            if rule_match[0] in names:
                grammar.error(ERR_RULE_NAME)
            names.append(rule_match[0])

            rule_definition: RuleDef = RuleDef(rule_match[0])
            grammar.expect_regex(RE_COLON)

            entry: NodeGroup = rule_definition.add_entry()
            parse_rule_entry(entry, rule_definition.node, verbosity)

            while grammar.match_regex(RE_OR):
                entry = rule_definition.add_entry()
                parse_rule_entry(entry, rule_definition.node, verbosity)

            grammar.expect_regex(RE_SEMICOLON)

            if grammar_nodes.has_node(rule_definition):
                grammar.error(ERR_DEFINITION)
            grammar_nodes.add(rule_definition)

            if verbosity >= DEBUG1:
                grammar.info(f"Rule added: {rule_definition.name}", localized=False)

            continue
        break


def parse_rule_entry(entry: NodeGroup, node: dict[str, Any], verbosity: Verbosity = ERROR):
    """"""
    ref: GrammarNodeReference | NodeGroup
    refs: Sequence[GrammarNodeReference | NodeGroup] = []

    while True:
        if match_item := grammar.match_regex(RE_TOKEN_INSTANCE):
            ref = TokenRef(match_item[1])
            refs.append(ref)
            continue

        if match_item := grammar.match_regex(RE_KIND_INSTANCE):
            cnt = COUNT_MAP.get(match_item[2], NC_ONE)
            ref = KindRef(match_item[1], count=cnt)
            refs.append(ref)
            continue

        if match_item := grammar.match_regex(RE_RULE_INSTANCE):
            cnt = COUNT_MAP.get(match_item[2], NC_ONE)
            ref = RuleRef(match_item[1], count=cnt)
            refs.append(ref)
            continue

        if match_item := grammar.match_regex(RE_OPEN_PAREN):
            group: NodeGroup = NodeGroup(GM_SEQUENTIAL, NC_ONE)

            if verbosity >= DEBUG2:
                grammar.info("Entered inline Group", as_debug=True)

            parse_inline_group(group, RE_CLOSE_PAREN_GROUP)

            if verbosity >= DEBUG2:
                grammar.info(f"Exited inline Group: {group}", as_debug=True)

            refs.append(group)
            continue

        if match_item := grammar.match_regex(RE_OPEN_BRACKET):
            group: NodeGroup = NodeGroup(GM_OPTIONAL, NC_ONE)
            parse_inline_group(group, RE_CLOSE_BRACKET)
            refs.append(group)
            continue
        break

    for i, ref in enumerate(refs):
        entry.add_item(ref, '_')

    if grammar.match_regex(RE_CAPTURE):
        capts: str | list[Any] = parse_entry_capture(refs, node, verbosity=verbosity)
        assign_group_captures(entry, capts, verbosity)


def parse_entry_capture(refs: Sequence[GrammarNodeReference | NodeGroup], node: dict[str, Any], inline: bool = False, verbosity: Verbosity = ERROR) -> str | list[Any]:
    """"""
    captures = []
    closed = False

    while True:
        if capt_match := grammar.match_regex(RE_UNDERSCORE):
            captures.append(RE_UNDERSCORE)
            continue

        if capt_match := grammar.match_regex(RE_OPEN_PAREN):
            sub_capt: str | list[Any] = parse_entry_capture(refs, node, inline=True)
            captures.append(sub_capt)
            continue

        if capt_match := grammar.match_regex(RE_CLOSE_PAREN):
            if not inline:
                grammar.error(f"Unexpected ')'")
            closed = True

        if capt_match := grammar.match_regex(r"(\*)?(\w+)(\.\w+)?"):
            captures.append(capt_match[0])
            capt_sequence = capt_match[1]

            if capt_match[3]:
                capture = f"{capt_match[2]}.{capt_match[3]}"
            else:
                capture = capt_match[2]

            if capt_sequence:
                node[capture] = []
            else:
                node[capture] = None

            continue
        break

    if inline and not closed:
        grammar.error("Expected ')'")

    return captures


def assign_group_captures(group: NodeGroup, captures: str | list[str], verbosity: Verbosity = ERROR):
    """"""
    refs: list[GrammarNodeReference | NodeGroup] = group.refs
    n_capts: int = len(captures)
    n_refs: int = len(refs)

    for i in range(n_refs):
        ref = refs[i]
        if i >= n_capts:
            continue
        cap = captures[i]

        if isinstance(ref, GrammarNodeReference) and isinstance(cap, str) or isinstance(ref, (str, NodeGroup)) and isinstance(cap, list):
            ref.capture = cap

            if isinstance(ref, NodeGroup) and isinstance(cap, list):
                ref.captures = cap
                ref.capture = '_'
                assign_group_captures(ref, cap, verbosity)

        elif isinstance(ref, NodeGroup) and ref.mode is GM_ALTERNATIVE and isinstance(cap, str):
            ref.capture = cap

        else:
            if verbosity >= WARNING:
                grammar.warning(f"Rule entry mismatches items and capture names")

        if verbosity >= DEBUG1:
            grammar.info(f"Node ref: `{ref}`, assigned: `{cap}`", as_debug=True)


def parse_inline_group(group: NodeGroup, re_close_brace: str, verbosity: Verbosity = ERROR):
    """"""
    initial_mode: GroupMode = group.mode
    initial_count: NodeCount = group.count
    can_be_alternative: bool = group.mode is not GM_OPTIONAL
    is_alternative: bool = group.mode is GM_ALTERNATIVE
    expects_pipe: bool = False
    refs: Sequence[GrammarNodeReference | NodeGroup] = []
    ref: GrammarNodeReference | NodeGroup

    while True:

        if match_item := grammar.match_regex(RE_OR):
            if is_alternative:
                if expects_pipe:
                    expects_pipe = False
                    continue
                else:
                    grammar.error(ERR_UNEXPECTED_PIPE)
            elif can_be_alternative:
                if len(refs) == 1:
                    is_alternative = True
                    expects_pipe = False
                    group.mode = GM_ALTERNATIVE
                    continue
                else:
                    grammar.error(ERR_UNEXPECTED_PIPE)
            else:
                grammar.error(ERR_UNEXPECTED_PIPE)

        if match_item := grammar.match_regex(RE_TOKEN_INSTANCE):
            if is_alternative and expects_pipe:
                grammar.error(ERR_EXPECTED_PIPE)

            ref = TokenRef(match_item[1])
            refs.append(ref)
            if is_alternative:
                expects_pipe = True

            continue

        if match_item := grammar.match_regex(RE_KIND_INSTANCE):
            if is_alternative and expects_pipe:
                grammar.error(ERR_EXPECTED_PIPE)

            cnt = COUNT_MAP.get(match_item[2], NC_ONE)
            ref = KindRef(match_item[1], count=cnt)
            refs.append(ref)
            if is_alternative:
                expects_pipe = True

            continue

        if match_item := grammar.match_regex(RE_RULE_INSTANCE):
            if is_alternative and expects_pipe:
                grammar.error(ERR_EXPECTED_PIPE)

            cnt = COUNT_MAP.get(match_item[2], NC_ONE)
            ref = RuleRef(match_item[1], count=cnt)
            refs.append(ref)
            if is_alternative:
                expects_pipe = True

            continue
        if match_item := grammar.match_regex(RE_OPEN_PAREN):
            if is_alternative and expects_pipe:
                grammar.error(ERR_EXPECTED_PIPE)

            inline_group: NodeGroup = NodeGroup(GM_SEQUENTIAL, NC_ONE)
            parse_inline_group(inline_group, RE_CLOSE_PAREN_GROUP)
            refs.append(inline_group)
            if is_alternative:
                expects_pipe = True

            continue

        if match_item := grammar.match_regex(RE_OPEN_BRACKET):
            if is_alternative and expects_pipe:
                grammar.error(ERR_EXPECTED_PIPE)

            inline_group: NodeGroup = NodeGroup(GM_OPTIONAL, NC_ONE)
            parse_inline_group(inline_group, RE_CLOSE_BRACKET)
            refs.append(inline_group)
            if is_alternative:
                expects_pipe = True

            continue
        break

    if close_match := grammar.expect_regex(re_close_brace):
        if initial_mode is not GM_OPTIONAL:
            group.count = COUNT_MAP.get(close_match[1], NC_ONE)

    if ref in refs:
        group.add_item(ref, '_')

# endregion (functions)
