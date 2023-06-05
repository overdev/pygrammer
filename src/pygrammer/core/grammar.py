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

from typing import Sequence
from enum import IntEnum, auto

# endregion (imports)
# ---------------------------------------------------------
# region EXPORTS


__all__ = [
    'GroupMode',
    'GM_SEQUENTIAL',
    'GM_ALTERNATIVE',
    'GM_OPTIONAL',
    'NodeCount',
    'NC_ZERO_OR_ONE',
    'NC_ZERO_OR_MORE',
    'NC_ONE',
    'NC_ONE_OR_MORE',
    'GrammarNode',
    'GrammarNodeDefinition',
    'TokenDef',
    'KindDef',
    'RuleDef',
    'NodeGroup',
    'GrammarNodeReference',
    'TokenRef',
    'KindRef',
    'RuleRef',
]


# endregion (exports)
# ---------------------------------------------------------
# region CONSTANTS & ENUMS


class GroupMode(IntEnum):
    SEQUENTIAL = auto()
    ALTERNATIVE = auto()
    OPTIONAL = auto()


GM_SEQUENTIAL = GroupMode.SEQUENTIAL
GM_ALTERNATIVE = GroupMode.ALTERNATIVE
GM_OPTIONAL = GroupMode.OPTIONAL


class NodeCount(IntEnum):
    ZERO_OR_ONE = auto()
    ZERO_OR_MORE = auto()
    ONE = auto()
    ONE_OR_MORE = auto()


NC_ZERO_OR_ONE = NodeCount.ZERO_OR_ONE
NC_ZERO_OR_MORE = NodeCount.ZERO_OR_MORE
NC_ONE = NodeCount.ONE
NC_ONE_OR_MORE = NodeCount.ONE_OR_MORE


# endregion (constants)
# ---------------------------------------------------------
# region CLASSES


class GrammarNode:
    """Base for terminals and rules"""

    def __str__(self) -> str:
        return self.__class__.__name__

# region DEFINITIONS


class GrammarNodeDefinition(GrammarNode):

    def __init__(self, name: str):
        super().__init__()
        self._index: int = 0
        self.name: str = name


class TokenDef(GrammarNodeDefinition):

    def __init__(self, name: str, value: str, is_regex: bool = True, excludes: list[str] | None = None,
                 decorators: list[str] | None = None, match_group_index: int = 0):
        super().__init__(name)
        self.value: str = value
        self._is_regex: bool = is_regex
        self._excludes: list[str] | None = excludes
        self._decorators: list[str] | None = decorators
        self._match_index: int = match_group_index

    @property
    def is_regex(self) -> bool:
        return self._is_regex

    @property
    def match_index(self) -> int:
        return self._match_index

    def has_decorator(self, decorator: str) -> bool:
        return decorator in self._decorators

    def excludes_kind(self, token_kind: str) -> bool:
        return token_kind in self._excludes

    def exclusions(self, token_kind: str) -> list[str]:
        return self._excludes


class KindDef(GrammarNodeDefinition):

    def __init__(self, name: str, values: str):
        super().__init__(name)
        self.values: list[str] = values
        self._is_regex: bool = True
        self._is_group: bool = len(values) > 1

    @property
    def is_regex(self) -> bool:
        return self._is_regex

    @property
    def is_group(self) -> bool:
        return self._is_group


class RuleDef(GrammarNodeDefinition):

    def __init__(self, name: str, source_index: int):
        super().__init__(name)
        self.entries: Sequence[NodeGroup] = []
        self.node: dict[str, Any] = { 'node_kind': name.upper() }
        self.attributes: dict[str, str] = {}
        self.directives: list[str] = []
        # self.is_simple: bool = True
        self._index = source_index

    @property
    def index(self) -> int:
        return self._index

    @property
    def is_alternative(self) -> bool:
        return len(self.entries) > 1

    @property
    def has_scope(self) -> bool:
        return 'scope' in self.attributes

    @property
    def has_key(self) -> bool:
        return 'key' in self.attributes

    @property
    def key(self) -> str | None:
        return self.attributes.get('key')

    @property
    def scope(self) -> str | None:
        return self.attributes.get('scope')

    @property
    def is_simple(self):
        if self.is_alternative:
            return isinstance(self.entries[0].first, (TokenRef, KindRef))
        else:
            for entry in self.entries:
                if isinstance(entry.first, RuleRef):
                    return False
        return True

    def add_entry(self, name: str | None = None) -> 'NodeGroup':
        new_entry = NodeGroup(GM_SEQUENTIAL, NC_ONE, self)
        if name:
            new_entry.capture = name
        self.entries.append(new_entry)
        return new_entry

    def has(self, attr: str) -> bool:
        return attr in self.attributes

    def has_directive(self, directive: str) -> bool:
        return directive in self.directives

    def get(self, attr: str, default=None) -> bool:
        return self.attributes.get(attr, default)

    def add_attribute(self, attrib_key: str, value: str) -> bool:
        if attrib_key not in self.attributes:
            self.attributes[attrib_key] = value
            return True
        return False

    def add_directive(self, directive: str) -> bool:
        if directive not in self.attributes:
            self.directives.append(directive)
            return True
        return False


class NodeGroup:

    def __init__(self, mode: GroupMode, count: NodeCount, parent: 'RuleDef | None' = None):
        self._parent: RuleDef | None = parent
        self.mode: GroupMode = mode
        self.count: NodeCount = count
        self.refs: Sequence[GrammarNodeReference | NodeGroup] = []
        self.captures: Sequence[str] = []
        self.capture: str = '_'
        self.index = 0

    def __str__(self) -> str:
        return f"Group: (refs: {len(self.refs)}, mode: {self.mode.name}, count: {self.count.name}, entry: {self.parent is not None})"

    def __len__(self) -> int:
        return len(self.refs)

    def __getitem__(self, key: int) -> 'tuple[GrammarNodeReference | NodeGroup, str | Sequence[str]]':
        if not isinstance(key, int):
            raise KeyError(f"key: {key}")

        if key < len(self.refs):
            ref = self.refs[key]
            cap = '_'
            if key < len(self.captures):
                cap = self.captures[key]
            return ref, cap

        raise IndexError("Index out of bounds")

    @property
    def first(self) -> 'GrammarNode | NodeGroup':
        return self.refs[0]

    @property
    def has_capture(self) -> bool:
        return self.capture != '_'

    @property
    def parent(self) -> 'RuleDef | None':
        return self._parent

    def add_item(self, item: 'GrammarNodeReference', capture: 'str | Sequence[str] | None' = None):
        self.refs.append(item)
        self.captures.append('_' if not capture else capture)


# endregion (DEFINITIONS)

# region REFERENCES


class GrammarNodeReference(GrammarNode):

    def __init__(self, value: str, count: NodeCount = NC_ONE):
        super().__init__()
        self.value: str = value
        self.count: NodeCount = count
        self.capture: str = '_'

    def __str__(self) -> str:
        return f"{super().__str__()}: (value: {repr(self.value)}, count: {self.count.name}, capture: {repr(self.capture)})"

    @property
    def has_capture(self) -> bool:
        return self.capture != '_'


class TokenRef(GrammarNodeReference):

    def __init__(self, value: str, count: NodeCount = NC_ONE):
        super().__init__(value, count)


class KindRef(GrammarNodeReference):

    def __init__(self, kind_name: str, count: NodeCount = NC_ONE):
        super().__init__(kind_name, count)


class RuleRef(GrammarNodeReference):

    def __init__(self, rule_name: str, count: NodeCount = NC_ONE, source_index: int = 0):
        super().__init__(rule_name, count)
        self._index = source_index

    @property
    def index(self) -> int:
        return self._index


# endregion (REFERENCES)

# endregion (classes)
# ---------------------------------------------------------
# region FUNCTIONS

# endregion (functions)
