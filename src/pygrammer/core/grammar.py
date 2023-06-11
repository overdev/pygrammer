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
    """GroupMode defines how items in an inline group should be treated"""
    SEQUENTIAL = auto()
    ALTERNATIVE = auto()
    OPTIONAL = auto()


GM_SEQUENTIAL = GroupMode.SEQUENTIAL
GM_ALTERNATIVE = GroupMode.ALTERNATIVE
GM_OPTIONAL = GroupMode.OPTIONAL


class NodeCount(IntEnum):
    """NodeCount defined the possible number of ocorrences of an item (token or rule) or group"""
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
    """Base for tokens and rules"""

    def __str__(self) ->'str':
        return self.__class__.__name__

# region DEFINITIONS


class GrammarNodeDefinition(GrammarNode):
    """Base for token and rule definitions"""

    def __init__(self, name: 'str'):
        super().__init__()
        self._index: 'int' = 0
        self.name: 'str' = name


class TokenDef(GrammarNodeDefinition):
    """Represents a token definition"""

    def __init__(self, name: 'str', value: 'str', is_regex: 'bool' = True, excludes: 'list[str] | None' = None,
                 decorators: 'list[str] | None' = None, match_group_index: 'int' = 0):
        super().__init__(name)
        self.value: 'str' = value
        self._is_regex: 'bool' = is_regex
        self._excludes: 'list[str] | None' = excludes
        self._decorators: 'list[str] | None' = decorators
        self._match_index: 'int' = match_group_index

    @property
    def is_regex(self) -> 'bool':
        "Gets the token regular expression"
        return self._is_regex

    @property
    def match_index(self) ->'int':
        """Gets the token's regular expression matching group index"""
        return self._match_index

    @property
    def exclusions(self) ->'list[str]':
        """Gets the token grops this definition excludes"""
        return self._excludes

    def has_decorator(self, decorator: 'str') ->'bool':
        """Returns whether the token definition has the specified decorator"""
        return decorator in self._decorators

    def excludes_kind(self, token_kind: 'str') ->'bool':
        """Returns whether the token definition excludes the specified token group"""
        return token_kind in self._excludes


class KindDef(GrammarNodeDefinition):
    """Represents a Token Group definition"""

    def __init__(self, name: 'str', values: 'str'):
        super().__init__(name)
        self.values: 'list[str]' = values
        self._is_regex: 'bool' = True
        self._is_group: 'bool' = len(values) > 1

    @property
    def is_regex(self) ->'bool':
        """Gets whether the group values are regular expressions (defaults to True)"""
        return self._is_regex

    @property
    def is_group(self) ->'bool':
        """Gets whether the token group has more than one value"""
        return self._is_group


class RuleDef(GrammarNodeDefinition):
    """Represents a Rule definition"""

    def __init__(self, name: 'str', source_index: 'int'):
        super().__init__(name)
        self.entries: 'Sequence[NodeGroup]' = []
        self.node: 'dict[str, Any]' = { 'node_kind': name.upper() }
        self.attributes: 'dict[str, str]' = {}
        self.directives: 'list[str]' = []
        # self.is_simple: 'bool' = True
        self._index = source_index

    @property
    def index(self) ->'int':
        """Gets the character index in the grammar file where the rule occurs"""
        return self._index

    @property
    def is_alternative(self) ->'bool':
        """Gets whether the rule has more than one definition"""
        return len(self.entries) > 1

    @property
    def has_scope(self) ->'bool':
        """Gets whether the rule has the `scope` attribute"""
        return 'scope' in self.attributes

    @property
    def has_key(self) ->'bool':
        """Gets whether the rule has the `key` attribute"""
        return 'key' in self.attributes

    @property
    def key(self) ->'str | None':
        """Gets the rule `key` attribute value"""
        return self.attributes.get('key')

    @property
    def scope(self) ->'str | None':
        """Gets the rule `scope` attribute value"""
        return self.attributes.get('scope')

    @property
    def is_simple(self):
        """Returns whether the rule has one (simple) or more (complex) definitions"""
        if self.is_alternative:
            return isinstance(self.entries[0].first, (TokenRef, KindRef))
        else:
            for entry in self.entries:
                if isinstance(entry.first, RuleRef):
                    return False
        return True

    def add_entry(self, name: 'str | None' = None) -> 'NodeGroup':
        """Adds an entry (alternative definition) to the rule"""
        new_entry = NodeGroup(GM_SEQUENTIAL, NC_ONE, self)
        if name:
            new_entry.capture = name
        self.entries.append(new_entry)
        return new_entry

    def has(self, attr: 'str') ->'bool':
        """Returns whether the rule has the specified attribute `attr`"""
        return attr in self.attributes

    def has_directive(self, directive: 'str') ->'bool':
        """Returns whether the rule has the specified directive"""
        return directive in self.directives

    def get(self, attr: 'str', default=None) ->'bool':
        """Returns the specified directive value, or None otherwise"""
        return self.attributes.get(attr, default)

    def add_attribute(self, attrib_key: 'str', value: 'str') ->'bool':
        """Adds an attribute to the rule"""
        if attrib_key not in self.attributes:
            self.attributes[attrib_key] = value
            return True
        return False

    def add_directive(self, directive: 'str') ->'bool':
        """Adds an directive to the rule"""
        if directive not in self.attributes:
            self.directives.append(directive)
            return True
        return False


class NodeGroup:
    """Represents a group of grammar node references or inline groups"""

    def __init__(self, mode: 'GroupMode', count: 'NodeCount', parent: 'RuleDef | None' = None):
        self._parent: 'RuleDef | None' = parent
        self.mode: 'GroupMode' = mode
        self.count: 'NodeCount' = count
        self.refs: 'Sequence[GrammarNodeReference | NodeGroup]' = []
        self.captures: 'Sequence[str]' = []
        self.capture: 'str' = '_'
        self.index = 0

    def __str__(self) ->'str':
        return f"Group: (refs: {len(self.refs)}, mode: {self.mode.name}, count: {self.count.name}, entry: {self.parent is not None})"

    def __len__(self) ->'int':
        return len(self.refs)

    def __getitem__(self, key: 'int') -> 'tuple[GrammarNodeReference | NodeGroup, str | Sequence[str]]':
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
        """Gets the first item in the group"""
        return self.refs[0]

    @property
    def is_uncertain(self) -> bool:
        """Gets whether the group starting item is optional"""
        ref = self.first
        return ref.count in (NC_ZERO_OR_ONE, NC_ZERO_OR_MORE) or isinstance(ref, NodeGroup) and ref.mode is GM_OPTIONAL

    @property
    def is_doubtfull(self) -> bool:
        """Gets whether all items in the group are optional"""
        refs = []
        for ref in enumerate(self.refs):
            if ref.count in (NC_ZERO_OR_ONE, NC_ZERO_OR_MORE) or isinstance(ref, NodeGroup) and ref.mode is GM_OPTIONAL:
                refs.append(True)
            else:
                refs.append(False)
                break

        return False not in refs

    @property
    def first_optionals(self) -> "Sequence[GrammarNodeReference | NodeGroup]":
        """Gets all starting items that are optional to the group"""
        refs = []
        i: 'int' = -1
        for i, ref in enumerate(self.refs):
            if ref.count in (NC_ZERO_OR_ONE, NC_ZERO_OR_MORE) or isinstance(ref, NodeGroup) and ref.mode is GM_OPTIONAL:
                refs.append(ref)
            else:
                refs.append(ref)
                break
        return refs

    @property
    def has_capture(self) ->'bool':
        """Gets whether this group has defined a capture name"""
        return self.capture != '_'

    @property
    def parent(self) -> 'RuleDef | None':
        """Gets the rule that owns the group, or None otherwise"""
        return self._parent

    def add_item(self, item: 'GrammarNodeReference', capture: 'str | Sequence[str] | None' = None):
        """Adds a node reference to this group, along with its capture name(s)"""
        self.refs.append(item)
        self.captures.append('_' if not capture else capture)

# endregion (definitions)

# region REFERENCES


class GrammarNodeReference(GrammarNode):
    """Represents a reference to a Token or Rule definition"""

    def __init__(self, value: 'str', count: 'NodeCount' = NC_ONE):
        super().__init__()
        self.value: 'str' = value
        self.count: 'NodeCount' = count
        self.capture: 'str' = '_'

    def __str__(self) ->'str':
        return f"{super().__str__()}: (value: {repr(self.value)}, count: {self.count.name}, capture: {repr(self.capture)})"

    @property
    def has_capture(self) ->'bool':
        """Gets whether this node has defined a capture name"""
        return self.capture != '_'


class TokenRef(GrammarNodeReference):
    """Represents a reference to a Token definition"""

    def __init__(self, value: 'str', count: 'NodeCount' = NC_ONE):
        super().__init__(value, count)


class KindRef(GrammarNodeReference):
    """Represents a reference to a Token Group definition"""

    def __init__(self, kind_name: 'str', count: 'NodeCount' = NC_ONE):
        super().__init__(kind_name, count)


class RuleRef(GrammarNodeReference):
    """Represents a reference to a Rule definition"""

    def __init__(self, rule_name: 'str', count: 'NodeCount' = NC_ONE, source_index: 'int' = 0):
        super().__init__(rule_name, count)
        self._index = source_index

    @property
    def index(self) ->'int':
        """Gets the character index in the grammar where this reference occurs"""
        return self._index

# endregion (references)

# endregion (classes)
