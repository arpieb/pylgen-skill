# PyLGEN — Cython API Reference



<!-- source: docs/api-reference/cython/api-reference-cython-analysis.md -->

# Module `analysis`

## Submodule `analysis.context`

> ### `Context`

Base Context class.

 - `__init__()`

#### Properties

 - `cdef list[SemanticError] _errors`

 - `cdef list[str] _stack`

#### Methods

 - `cpdef void push_trace(str trace)`: appends trace to the stack.
    - Args:
        - `trace (str)`

 - `cpdef void pop_trace()`: removes the last trace.

 - `cpdef void push_new_scope()`: push a new scope into the context. (not implemented, raises `NotImplementedError`).

 - `cpdef void pop_scope()`: pops the current scope. (not implemented, raises `NotImplementedError`).

 - `cpdef void clear_runtime_errors()`: clear all the runtime errors. (not implemented, raises `NotImplementedError`).

 - `cpdef list[RuntimeError] get_runtime_errors()`: returns all detected runtime errors. (not implemented, raises `NotImplementedError`).

 - `cpdef void clear_semantic_errors()`: Clear all the semantic errors.

 - `cpdef void reset()`: reset the context.

 - `cpdef void clear_errors()`: clear all errors.

 - `cpdef void add_semantic_error(error)`: adds a semantic error.
    - Args:
        - `error`: instance of a subclass of `SemanticError`.

 - `cpdef void add_runtime_error(ast, error)`: Adds a new `RuntimeError` from the given ast. (not implemented, raises `NotImplementedError`).
    - Args:
        - `ast`: instance of a subclass of `AST`. 
        - `error`: instance of a subclass of `RuntimeError`.

## Submodule `analysis.lexical`

> ### `LexicalRule`

Abstract class for a lexical validation rule.

 - `__init__(str msg)`: initializes the instance with the message of the error validation.
    - Args:
        - `msg (str)`

#### Properties

 - `cdef str _msg`: the message of the error validation.

#### Methods

 - `cpdef bool _check(str text)`: text validation logic. (not implemented, raises `NotImplementedError`).
    - Args:
        - `text (str)`

 - `cpdef LexicalError check(Token token)` — returns a `LexicalError` if `_check` fails, otherwise returns `None`.
    - Args:
        - `token (Token)`

## Submodule `analysis.visitor`

> ### `ASTVisitor`

Base class of a visitor on the ***Visitor Pattern***.

 - `__init__(type context_type)`
    - Args:
        - `context_type (type)`: the type of the subclass of `Context` for which this visitor is intended. 

#### Properties

 - `cdef type _context_type`

#### Methods

 - `cpdef void _check_context_type(context)`: validates `context`.
    - Args:
        - `context`: the instance to be validated.
    
    - Raises: `TypeError` if `context` is not an instance of `_context_type`.

 - `cpdef void visit(ast, context)`: the logic of visit an AST node. (not implemented, raises `NotImplementedError`).
    - Args:
        - `ast`: (instance of a subclass of `AST`).
        - `context`: instance of `_context_type`.

> ### `ASTChildrenSelector`

Base class for AST children selectors.

 - `__init__(type context_type)`
    - Args:
        - `context_type (type)`: the type of the subclass of `Context` for which this visitor is intended.

#### Properties

 - `cdef type _context_type`

#### Methods

 - `cpdef void _check_context_type(context)`:
    - Args:
        `context`: the instance to be validated.
    
    - Raises: `TypeError` if `context` is not an instance of `_context_type`.

 - `cpdef list[AST] select_children(ast, context)`: returns a list of children in the order they will be visited. (not implemented, raises `NotImplementedError`).
    - Args:
        - `ast`: instance of a subclass of `AST`.
        - `context`: instance of `_context_type`.

> ### `TraversalStrategy`

Base class for traversal strategies for walking over ASTs.

 - `__init__(type context_type)`
    - Args:
        - `context_type (type)`: the type of the subclass of `Context` for which this visitor is intended.
    
    - Raises: `ValueError(f'context_type must be a subclass of {Context}')` if `context_type` is not a subclass of `Context`.

#### Properties

 - `cdef type _context_type`
 - `cdef AST _root`
 - `cdef dict[type,ASTChildrenSelector] _selectors`
 - `cdef ASTChildrenSelector _default_selector`

#### Methods

 - `cpdef void _check_context_type(context)`:
    - Args:
        - `context`: the instance to be validated.
    
    - Raises `TypeError` if `context` is not an instance of `_context_type`.
 
 - `cpdef void init(root)`: initializes the traversal with the root AST.
    - Args:
        - `root`: instance of  subclass of `AST`.

 - `cpdef bint has_next()`: returns `True` if there is a next AST node to visit. (not implemented, raises `NotImplementedError`).

 - `cpdef AST current(context)`: returns the current AST node to visit. (not implemented, raises `NotImplementedError`).
    - Args:
        - `context`: instance of `_context_type`.

 - `cpdef void reset()`: resets the traversal. (not implemented, raises `NotImplementedError`).

 - `cpdef ASTChildrenSelector _get_selector(ast)`: looks up by type; if not found and a default exists, uses it.
    - Args:
        - `ast`: instance of a subclass of `AST`.

 - `cpdef void add_selector(ast_type:type, selector:ASTChildrenSelector)`: sets the selector for the given type `ast_type`.
    - Args:
        - `ast_type`: subclass of `AST`.
        - `selector`: instance of a subclass of `ASTChildrenSelector`.

    - Raises: `TypeError` if the signature of the 2nd parameter of `selector.select_children` is not annotated or does not match `_context_type`.

 - `cpdef void set_default_selector(selector)`: sets the default selector.
    - Args:
        - `selector`: instance of a subclass of `ASTChildrenSelector`.

    - Raises: analogous to `add_selector`.

 - `cdef void add_selector_without_signature_checking(ast_type,selector)`
    - Args:
        - `ast_type`: subclass of `AST`.
        - `selector`: instance of a subclass of `ASTChildrenSelector`.

 - `cdef void set_default_selector_without_signature_checking(selector)`
    - Args:
        - `selector`: instance of a subclass of `ASTChildrenSelector`.

> ### `ASTWalker`

Class for an AST walker.

 - `__init__(context, strategy)`
    - Args:
        - `context`: instance of a subclass of `Context`.
        - `strategy`: instance of a subclass of `TraversalStrategy`.

#### Properties

 - `cdef Context _context`
 - `cdef dict[type,ASTVisitor] _visitors`
 - `cdef TraversalStrategy _strategy`
 - `cdef ASTVisitor _default_visitor`

#### Methods

 - `cpdef void add_visitor(ast_type, visitor)`: sets the visitor for the given type `ast_type`.
    - Args:
        - `ast_type`: subclass of `AST`.
        - `visitor`: instance of a subclass of `ASTVisitor`.
    
    - Raises: `TypeError` if the signature of the 2nd parameter of `visitor.visit` is not annotated or does not match `_context_type`.

 - `cpdef void set_default_visitor(visitor)`: sets the default visitor.
    - Args:
        - `visitor`: instance of a subclass of `ASTVisitor`.
    - Raises: analogous to `add_visitor`.

 - `cpdef void walk(ast)`: initializes the strategy and iterates until `has_next` is false; for each node it finds the visitor and invokes it. Finally calls `reset` on the strategy.
    - Args:
        - `ast`: instance of a subclass of `AST`.

 - `cdef void add_visitor_without_signature_checking(ast_type,visitor)`
    - Args:
        - `ast_type`: subclass of `AST`.
        - `visitor`: instance of a subclass of `ASTVisitor`.

 - `cdef void set_default_visitor_without_signature_checking(visitor)`
    - Args:
        - `visitor`: instance of a subclass of `ASTVisitor`.

> ### Note on Typing and Genericity in the `analysis` Module

At the time the PyLGEN code was written, Cython lacked a **full-fledged generics system** that would have allowed extension classes (`cdef class`) (such as `ASTVisitor`, `ASTChildrenSelector`, `TraversalStrategy`, and `ASTWalker`), to statically infer the concrete types of the `Context` and `AST` subclasses with which they operate. Cython’s "fused types", the closest equivalent to generics, cannot be applied to extension classes. Consequently, it was not possible to create a type-safe generic hierarchy without sacrificing the performance benefits that justify the use of Cython in PyLGEN.

To maintain the advantages of static typing, the arguments were typed using the base classes (`Context` and `AST`), and `_check_context_type` was implemented as a runtime safeguard. While not strictly mandatory, this function verifies that the provided context is of the expected type; its use is a recommended practice for any contributor extending these classes.

It is important to emphasize that this is a **temporary compromise**. Recent versions of Cython (such as 3.3) have introduced support for generics and parameterized container types, and it is expected that support for generic extension classes will continue to mature. Once that happens, `_check_context_type` can be gradually replaced by native generic typing, rendering it obsolete. Until then, it should neither be removed nor dismissed as an unnecessary artifact, as it serves as the guarantee for type safety in the compiled version of PyLGEN.



<!-- source: docs/api-reference/cython/api-reference-cython-automaton.md -->

# Module `automaton`

## Submodule `automaton.automaton`

> ### `State`

State class for building automatons. This class is inmutable.

 - `__init__(id, value, is_accept=False)`
    - Args:
        
        - `id (str)`: identifier; two states with the same `id` are equal.

        - `value (Any)`: value contained in the state.

        - `is_accept (bint)`: whether it is an accepting state.

#### Properties

 - `_id (cdef str)`

 - `_value (cdef object)`

 - `_is_accept (cdef bint)`

 - `_hash (cdef int)`

> ### `Automaton`

Base class for automaton definition.

 - `__init__()`:
    - Raises: `ValueError("Can not instance this class")`

#### Properties

 - `_states_by_id (cdef dict[str,State])`: mapping of states by its ids.

 - `_alphabet (cdef set[str])`

 - `_start_state (cdef State)`: start state of the automaton.
 
 - `_current_state (cdef State)`: current state of the automaton.

 - `_trans_func (cdef Table)`: transitions of the automaton in a tabular form.

 - `_epsilons (cdef dict[str,set[str]])`: epsilons transitions of the automaton.

 - `_closures (cdef dict[str,set[State]])`: cache for the closures computations.

 - `_transitions_added_while_completing (cdef list[tuple[str,str]])`: record of the transitions added in a `make_complete()` call.

 - `_is_complete (cdef bint)`: `True` if the every state has defined a transition.
 
 - `_is_stuck (cdef bint)`: `True` if the automaton tried to advance from an state with a symbol that hasn't a transition defined.

 - `_fault_id (cdef str)`: id of the current fault state if exists.

 - `_preimages (cdef dict[tuple[str,str],set[State]])`: used during minimization process.

#### Methods

 - `cpdef void add_transition(from_state, to_state, symbol)`: adds a transition. (Automatically updates the `states` and `is_complete` properties of the current automaton).

    - Args:
        - `from_state (State)`: origin state.
        - `to_state (State)`: destination state.
        - `symbol (str)`: symbol that triggers the transitions.

    - Raises: `ValueError` if `symbol` is not in the alphabet.
  
  - `cpdef bint has_transition(state, symbol)`: returns `True` if the transition `(state, symbol)` exists.
    - Args:
        - `state (State)`: origin state.
        - `symbol (str)`

 - `cpdef State next(state, symbol)`: returns the destination state for the given transition `(state,symbol)`.
    - Args:
        - `state (State)`: origin state.
        - `symbol (str)`

    - Raises: `KeyError` if there is no transition.

 - `cpdef void reset()`: resets the automaton to its initial state before any internal change that has been done.

 - `cpdef set[State] closure(state)`: returns the set of states corresponding to the epsilon-closure of `state`.
    - Args:
        - `state (State)`

 - `cpdef void make_complete()`: adds all missing transitions to a fault state.

 - `cpdef void restore_to_before_complete()`: removes the fault state and added transitions.

 - `cpdef void extend_alphabet(symbols)`: expands the current alphabet with the new set of symbols.
    - Args:
        - `symbols (Set[str])`

> ### `DFA`

Class for a ***Deterministic Finite Automata***. Inherits from `Automaton` (`DFA(Automaton)`).

 - `__init__(start_id, start_value, alphabet, start_accept=False)`
    - Args:
        - `start_id (str)`: id of the start state.
        - `start_value (object)`: value of the start state.
        - `alphabet (set[str])`: alphabet of the automaton.
        - `start_accept (bint)`: if `True`, the start state is an accepting state.

#### Methods

 - `cdef set[State] _state_preimage_for_symbol(state, symbol)`: computes the preimage of the given state for the given symbol.
    - Args:
        - `state (State)`
        - `symbol (str)`

 - `cdef set[State] _block_preimage_for_symbol(states, symbol)`: computes the preimage of a set of states for the given symbol.
    - Args:
        - `states (set[State])`
        - `symbol (str)`

 - `cdef Table _build_new_transition_function(old_ids_to_new_ids_map)`: creates the transition function in tabular form from the current transition function and a mapping from old ids of states to new ids of states.
    - Args:
        - `old_ids_to_new_ids_map (dict[str,str])`: mapping from old ids of states to new ids of states.

 - `cdef DFA _build_new_dfa(partition)`: build a new `DFA` based in the given partition of states.
    - Args:
        - `partition (list[set[State]])`

 - `cpdef void walk(symbol)`: advances if not stuck; if no transition, marks `_is_stuck` internal flag as `True`.
    - Args:
        - `symbol (str)`

 - `cpdef bint accept(string)`: `True` if the automaton ends in an accepting state after reading the entire string. Calls `reset` at the end.
    - Args:
        - `string (list[str])`

 - `cpdef DFA minimize(initial_partition = [])`: returns the equivalent minimized `DFA` (Hopcroft's algorithm).
    - Args:
        - `initial_partition (list[set[State]])`: initial partition.

> ### `NFA`

Class for our [Hybrid $\epsilon$-DFA](../../formal-foundations/formal-foundations-automata.md#the-hybrid-epsilon-dfa-a-deterministic-core-with-spontaneous-moves). Inherits from `Automaton` (`NFA(Automaton)`).

 - `__init__(start_id, start_value, alphabet, start_accept=False)`
    - Args:
        - `start_id (str)`: id of the start state.
        - `start_value (Any)`: value of the start state.
        - `alphabte (Set[str])`: alphabet of the automaton.
        - `start_accept (bool)`: if `True`, the start state is an accepting state.

#### Methods

 - `cdef State _build_state(states)`: builds a new state with value `states`.
    - Args:
        - `states (set[State])`

 - `cdef State _build_new_state(state,target_table,current_states)`: used during determinzition of the automaton.
    - Args:
        - `state (State)`
        - `target_table (Table)`
        - `current_states (set[State])`

 - `cpdef void add_epsilon_transition(from_state, to_state)`: adds an epsilon-transition.
    - Args:
        - `from_state (State)`: origin state.
        - `to_state (State)`: destination state.

 - `cpdef DFA to_deterministic()`: returns the equivalent `DFA` (subset construction with epsilon-closure).

> ### Module functions

 - `cdef DFA _copy_dfa(dfa)`: copy the dfa.
    - Args:
        - `dfa (DFA)`

 - `cdef NFA _copy_nfa(nfa)`: copy the nfa.
    - Args:
        - `nfa (NFA)`

 - `cdef NFA _automaton_union(automatons)`: returns the `NFA` equivalent to the union between all the automatons provided.
    - Args:
        - `automatons (set[Automaton])`

 - `cdef DFA _dfa_complement(automaton)`: returns the `DFA` of the complement of the given automaton.
    - Args:
        - `automaton (DFA)`

 - `cdef DFA _nfa_complement(automaton)`: returns the `DFA` of the complement of the given automaton.
    - Args:
        - `automaton (NFA)`

 - `cdef DFA _automaton_complement(automaton)`: returns the `DFA` of the complement of the given automaton.
    - Args:
        - `automaton (Automaton)`

 - `cdef DFA _automaton_intersection(automatons)`: returns the `DFA` equivalent to the intersection between all the automatons provided.
    - Args:
        - `automatons (set[Automaton])`

 - `cdef NFA _automaton_concatenation(first, second)`: returns the `NFA` equivalent to the concatenation of `first` followed by `second`.
    - Args:
        - `first (Automaton)`
        - `second (Automaton)`

 - `cdef NFA _automaton_closure(automaton, type_)`
    - Args:
        - `automaton (Automaton)`
        - `type_ (int)`:
            - `0`: returns the `NFA` equivalent to $L^{*}$, where $L$ is the language of `automaton`.
            - `1`: returns the `NFA` equivalent to $L$+, where $L$ is the language of `automaton`.
            - `2`: returns the `NFA` equivalent to $L$?, where $L$ is the language of `automaton`.

 - `cdef NFA _automaton_reverse(automaton)`:returns the `NFA` equivalent to the given automaton with all its transitions inverted.
    - Args:
        - `automaton (Automaton)`

 - `cpdef DFA create_dfa(states, transition_function, start_id, alphabet)`: creates a `DFA` from the given states, alphabet and transitions.
    - Args:
        - `states (Set[State])`: states of the automaton.
        - `transition_function (Table)`: the transition function in a tabular form.
        - `start_id (str)`: id of the start state.
        - `alphabet (Set[str])`: alphabet of the automaton.
    
    - Raises: `ValueError(f'A initial state is needed, not found any state with given id {start_id}')` if none of `states` has the id `start_id`.

 - `cpdef NFA create_nfa(states, transition_function, epsilon_transitions, start_id, alphabet)`: creates an `NFA` from the given states, alphabet, transitions and epsilon transitions.
    - Args:
        - `states (Set[State])`: states of the automaton.
        - `transition_function (Table)`: the transition function in a tabular form.
        - `epsilon_transitions (Dict[str,Set[str]])`: the epsilon transitions.
        - `start_id (str)`: id of the start state.
        - `alphabet (Set[str])`: alphabet of the automaton.

    - Raises: `ValueError(f'A initial state is needed, not found any state with given id {start_id}')` if none of `states` has the id `start_id`.

 - `cpdef DFA get_word_automaton(word)`: returns a `DFA` that accepts only `word`.
    - Args:
        - `word (str)`

 - `cpdef NFA get_words_automaton(words)`: returns an `NFA` that accepts only the given words (union of DFAs).
    - Args:
        - `words (List[str])`

 - `cpdef DFA get_word_automaton_with_value(word, value, only_finals=False)`: analogous to `get_word_automaton`.
    - Args:
        - `word (str)`
        - `value (Any)`: value to assign to states.
        - `only_finals (bool)`: if `True`, `value` is assigned only to accepting states.

 - `cpdef NFA get_words_automaton_with_value(words, value, only_finals=False)`: analogous to `get_words_automaton`.
    - Args:
        - `words (List[str])`
        - `value (Any)`: value to assign to states.
        - `only_finals (bool)`: if `True`, `value` is assigned only to accepting states.



<!-- source: docs/api-reference/cython/api-reference-cython-common.md -->

# Module `common`

## Submodule `common.types`

> ### `Symbol`

Class that represents a grammar symbol.

 - `__init__(str symbol, bint is_terminal = False, bint is_epsilon = False)`
    - Args:
        - `symbol (str)`: the symbol.

        - `is_terminal (bint)`: whether it is a terminal.

        - `is_epsilon (bint)`: whether it is the epsilon symbol. A symbol can only be epsilon if it is a terminal.

    - Raises: `ValueError('A symbol only can be epsilon if its a terminal symbol')`.

#### Properties

 - `_symbol (cdef str)`
 - `_is_terminal (cdef bint)`
 - `_is_epsilon (cdef bint)`
 - `_hash (cdef int)`

> ### `AST`

Abstract Syntax Tree class.

 - `__init__(Symbol symbol, int start_line, int start_column, int end_line, int end_column)`
    - Args:
        - `symbol (Symbol)`: internal symbol of the AST.
        - `start_line (int)`, `start_column (int)`: start position in source.
        - `end_line (int)`, `end_column (int)`: end position in source.

    - Raises: `ValueError` if positions are invalid.

#### Properties

 - `_symbol (cdef Symbol)`.
 - `_start_line (cdef int)`: line of the start position in source.
 - `_start_column (cdef int)`: column of the start position in source.
 - `_end_line (cdef int)`: line of the end position in source.
 - `_end_column (cdef int)`: column of the end position in source.
 - `_is_error (cdef bint)`: `True` if is an `ErrorAST`, `False` otherwise.

#### Methods

 - `cpdef list[AST] children()`: method to be implemented by subclasses (`raise NotImplementedError`). It must return the children of the current AST (by general consensus, in the same order that must be processed normally).

> ### `Error`

Abstract error class.

 - `__init__(object type_, int start_line, int start_column, int end_line, int end_column, str msg)`
    - Args:
        - `type_ (object)`.
        - `start_line (int)`, `start_column (int)`: start position in source.
        - `end_line (int)`, `end_column (int)`: end position in source.
        - `msg (str)`.

    - Raises: `TypeError` if `type_` is not a member of `ErrorType` and is not an `str`, `ValueError` if `type_` is not an `ErrorType`, or `ValueError` if positions are invalid.

#### Properties

 - `_start_line (cdef int)`: line of the start position in source.
 - `_start_column (cdef int)`: column of the start position in source.
 - `_end_line (cdef int)`: line of the end position in source.
 - `_end_column (cdef int)`: column of the end position in source.
 - `_type (cdef object)`: The type of the error.
 - `_msg (cdef str)`: The message of the error.
 - `_hash (cdef int)`.

> ### `Error` subclasses

All this classes inherits from `Error` class.

#### `LexicalError`

 - `__init__(str msg, int start_line, int start_column, int end_line, int end_column)`: sets `type_ = ErrorType.LEXICAL`.

#### `SyntaxError`

 - `__init__(str msg, int start_line, int start_column, int end_line, int end_column)`: sets `type_ = ErrorType.SYNTAX`.

#### `SemanticError`

 - `__init__(str msg, int start_line, int start_column, int end_line, int end_column)`: sets `type_ = ErrorType.SEMANTIC`.

#### `RuntimeError`

 - `__init__(list[str] stack_trace, int start_line, int start_column, int end_line, int end_column, str msg)`: sets `type_ = ErrorType.RUNTIME`.

 - **Property**: `_stack_trace (cdef list[str])`.

> ### `ErrorAST`

Error Syntax Tree Class (inherits from `AST`: `ErrorAST(AST)`).

 - `__init__(Symbol symbol, int start_line, int start_column, int end_line, int end_column, set[SemanticError] errors)`
    - Args:
        - `symbol (Symbol)`: internal symbol of the AST.
        - `start_line (int)`, `start_column (int)`: start position in source.
        - `end_line (int)`, `end_column (int)`: end position in source.
        - `errors (set[SemanticError])`: errors inside the ast.
    
    - Raises: `ValueError` if positions are invalid.
    - Sets `_is_error` internal flag to `True`.

 - **Property**: `_errors (cdef set[SemanticError])`.

> ### `ASTListView`

View over a list of `AST`.

#### Properties
    
 - `_data (cdef list[AST])`
 - `_start (cdef int)`
 - `_end (cdef int)`

#### Methods

 - `cdef inline AST _get(int idx)`:
     - Raises: `IndexError('ASTListView index out of range')` if `idx < 0` or `idx >= _end - _start`.
 
 - `cdef inline int _size()`: returns `self._end - self._start`

> **WARNING**
This class is internally managed by the parser, it is not meant to be used directly by the user.

> ### `Token`

Token class (inherits from `AST`: `Token(AST)`).

 - `__init__(str text, object type_, Symbol symbol, int line, int column)`
    - Raises: `ValueError` if `type_` is not a subclass of `TokenType`.
    - Calls `super().__init__(symbol, line, column, line, column + len(text))`.

#### Properties

 - `_text (cdef str)`: The text of the token.
 - `_type (cdef object)`: The type of the token.

#### Methods

 - `cpdef list[AST] children()`: returns `[]`

## Submodule `common.table`

> ### `Table`

Class used to store the transitions of an automata.

 - `__init__()`: initializes `_table = {}`.

#### Properties

 - `_table (cdef dict)`

#### Methods

 - `cpdef dict to_dict()`: returns copy as a plain dict.
 - `cpdef void from_dict(dict data)`: updates `_table` with `data`.



<!-- source: docs/api-reference/cython/api-reference-cython-grammar.md -->

# Module `grammar`

## Submodule `grammar.grammar`

> ### `SymbolNotPresentInGrammarException`

Exception raised when a symbol is not found in the current grammar (inherits from `Exception`).

 - `__init__(symbol: Symbol, *args)`

#### Properties

 - `_msg (cdef str)`: message of the exception.

> ### `Production`

Class that represents a grammar production.

 - `__init__(head, production)`
    - Args:
        - `head (Symbol)`: left-hand side of the grammar production.
        - `production (List[Symbol])`: right-hand side of the grammar production.
    
    - Raises: `ValueError("head can't be a terminal symbol")` if `head._is_terminal` is `True`.

#### Properties

 - `_id (cdef str)`: the id of the production (`f'{head} -> {" ".join(prod)}'`).
 - `_head (cdef Symbol)`
 - `_production (cdef list[Symbol])`
 - `_hash (cdef int)`: precomputed hash.

> ### `ProductionsSet`

Class that contains the productions for an specific non-terminal.

 - `__init__()`

#### Properties

 - `_productions (cdef dict[str,list[Symbol]])`: mapping of productions.
 - `_last_production_added (cdef list[Symbol])`: the last production added (used internally by `Grammar`).

#### Methods

 - `cdef void _add_production(production)`: adds a new production if not present.
    - Args:
        - `production (list[Symbol])`

> ### `AttributedProductionsSet`

Version of `ProductionsSet` for attributed grammars. Inherits from `ProductionsSet` (`AttributedProductionsSet(ProductionsSet)`).

 - `__init__()`

#### Properties

 - `_last_reductor_added (cdef object)`: the reductor associated to `_last_production_added` (used internally by `AttributedGrammar`).

#### Methods

 - `cdef void _add_attributed_production(self,list[Symbol] production,object reductor)`:adds an attributed production if not present.
    - Args:
        - `production (list[Symbol])`
        - `reductor (object)`: the function that the parser will call when it reduces by this production.

> ### `Grammar`

Base class for a grammar.

 - `__init__(start_symbol, end_symbol = '\x00')`
    - Args:
        - `start_symbol (Symbol)`: the start symbol of the grammar.
        - `end_symbol (str)`: the `EOF` symbol for the parser, internally the grammar stores a terminal symbol with value `end_symbol`.
    
    - Raises: `ValueError("start_symbol can't be terminal")` if `start_symbol._is_terminal` is `True`.

#### Properties

 - `_start_symbol (cdef Symbol)`: start symbol of the grammar.
 - `_end_symbol (cdef Symbol)`: `EOF` symbol of the grammar (used by the parser).
 - `_terminals (cdef set[Symbol])`: the current terminals of the grammar (including the `EOF` symbol created using `end_symbol`).
 - `_non_terminals (cdef set[Symbol])`:the current non-terminals of the grammar.
 - `_follows (cdef dict[Symbol,set[Symbol]])`: used for cache in the `FOLLOW` set computation.
 - `_firsts (cdef dict[Symbol,set[Symbol]])`: used for cache in the `FIRST` set computation.
 - `_productions (cdef dict[Symbol,ProductionsSet])`: mapping of the productions set of each symbol.
 - `_productions_by_symbol (cdef dict[Symbol,set[Production]])`: mapping of the productions of each symbol for direct access.
 - `_firsts_computed (cdef bint)`: flag to invalidate cache for `FIRST` sets already computed.
 - `_follows_computed (cdef bint)`: flag to invalidate cache for `FOLLOW` sets already computed.
 - `_epsilon (cdef Symbol)`: the epsilon symbol of the grammar (if exists).
 - `_symbols (cdef set[Symbol])`: symbols of the grammar.

#### Methods

 - `cdef bint _derives_in_epsilon(symbol)`: returns `True` if `symbol` can produce the epsilon symbol following the productions rules of the grammar.
    - Args:
        - `symbol (Symbol)`

 - `cdef void _make_firsts()`: initializes the cache for the `FIRST` sets computation.

 - `cdef void _make_follows()`: initializes the cache for the `FOLLOW` sets computation.

 - `cdef void _add_production(head,production)`: adds a production if not present in grammar.
    - Args:
        - `head (Symbol)`
        - `production (list[Symbol])`
    
    - Raises:
        - `ValueError("head can't be a terminal symbol")` if `head._is_terminal` is `True`.
        - `ValueError('Only can exists one epsilon symbol')` if there is an epsilon symbol in productions different from the current present in the grammar (if exists).
 
 - `cdef str _id()`: computes the id of the grammar based in the current productions, terminals, non-terminals and any structural information of the grammar itself.

 - `cpdef set[Symbol] first(production)`: returns the `FIRST` set of the given sequence of symbols.
    - Args:
        `production (list[Symbol])`
    
    - Raises: `SymbolNotPresentInGrammarException` if any symbol is not present in the grammar.

 - `cpdef set[Symbol] follow(symbol)`: returns the `FOLLOW` set of the given symbol.
    - Args:
        - `symbol (Symbol)`

    - Raises: `SymbolNotPresentInGrammarException` if any symbol is not present in the grammar.

 - `cpdef dict to_dict()`: returns a plain representation of the grammar in a dictionary.

> ### `AttributedGrammar(Grammar)`

Version of `Grammar` for attributed grammars. Inherits from `Grammar` (`AttributedGrammar(Grammar)`).

 - `__init__(start_symbol, end_symbol='\x00')`: analogous to `Grammar.__init__`.

#### Properties

 - `_reductors_by_production (cdef dict[Production,object])`: mapping of the reductors by the productions that triggers it.

#### Methods

 - `cpdef object get_reductor(production)`: gets the associated reductor the given production.
    - Args:
        - `production (Production)`
    
    - Raises: `KeyError` if there's no exists any reductor associated to the given production.

 - `cdef void _add_attributed_production(head,production,reductor)`: adds a production with its reductor if not present in grammar.
    - Args:
        - `head (Symbol)`
        - `production (list[Symbol])`
        - `reductor (object)`
    
    - Raises:
        - `ValueError("head can't be a terminal symbol")` if `head._is_terminal` is `True`.
        - `ValueError('Only can exists one epsilon symbol')` if there is an epsilon symbol in productions different from the current present in the grammar (if exists).

> ### Module functions

 - `cdef bint _is_left_regular(g)`: returns `True` if the grammar is left-regular.
    - Args:
        `g (Grammar)`

 - `cdef bint _is_right_regular(g)`: returns `True` if the grammar is right-regular.
    - Args:
        `g (Grammar)`

 - `cdef Grammar _augment_grammar(g)`: returns an augmented version of `g`.
    - Args:
        `g (Grammar)`

 - `cdef Grammar _reverse_grammar(g)`: reverses the production bodies of every rule, yielding a grammar that recognizes the reversed language.
    - Args:
        `g (Grammar)`



<!-- source: docs/api-reference/cython/api-reference-cython-lexer.md -->

# Module `lexer`

## Submodule `lexer.base_lexer`

> ### `LexerNotInitializedException`

Exception raised when an attemp is made to obtain the internal `DFA` without initializing the lexer first. Inherits from `Exception` (`LexerNotInitializedException(Exception)`).

> ### `LexerNotTokensProvidedException`

Exception raised when an attemp is made to initialize the lexer without any token automata provided. Inherits from `Exception` (`LexerNotTokensProvidedException(Exception)`).

> ### `BaseLexer`

Base class for a lexer.

 - `__init__(get_symbol_function, ignore_pattern,check_annotation = True)`
    - Args:
        - `get_symbol_function (Callable[[Any, str], Symbol])`: mapping function that maps a tuple `(Any,str)` to a `Symbol`. The mapping function must be annotated with the specific signature `Callable[[Any, str], Symbol]` if `check_annotation` is `True`, where the first argument annotation must be a subclass of `TokenType`. If `check_annotation` is `False`, the annotation checking is not performed.
        - `ignore_pattern (DFA)`: the `DFA` used to skip text patterns.
    
    - Raises: `ValueError` if the signature of `get_symbol_function` is invalid.

> **WARNING**
This class is not meant to be used directly.

#### Properties

 - `_text (cdef str)`: the text to tokenize.

 - `_text_readed (cdef str)`: the text currently readed.

 - `_text_position_pointer (cdef int)`: the position pointer to the character to read in the tokenization process.

 - `_line (cdef int)`: current line in the text.

 - `_column (cdef int)`: current column in the text.

 - `_fault_state (cdef State)`: used internally during the tokenization process.

 - `_automatons (cdef set[Automaton])`: the set of automatons used to build the global `DFA` for tokenization.

 - `_initialized (cdef bint)`: `True` if the lexer has been initialized.

 - `_priorites (cdef dict[int,object])`: used to select the type of token to return when a conflictive state is reached.

 - `_priorities_sorted (cdef list[int])`: used to select the type of token to return when a conflictive state is reached.

 - `_dfa_transition_function (cdef dict[str,str])`: used to accelerate the tokenization process.

 - `_dfa (cdef DFA)`: the internal `DFA` used for tokenization.

 - `_get_symbol_function (cdef object)`: the mapping function.

 - `_types_by_state (cdef dict[str,set[object]])`: used internally to assign the type to each token.

 - `_current_token (cdef Token)`: the current token.

 - `_ignore (cdef DFA)`: the `DFA` used to skip tokens.

 - `_enum_type (cdef object)`: the enumeration of types for the tokens.

#### Methods

 - `cdef Token _get_token(text,line,column)`: used to build `_current_token`.
    - Args:
        - `text (str)`: the text of the token to build.
        - `line (int)`: the current line.
        - `column (int)`: the current column.

 - `cdef void _add_token(priority,type_,automaton)`: adds a new token automaton.
    - Args:
        - `priority (int)`
        - `type_ (object)`: the type of the new token.
        - `automaton (Automaton)`: the automaton to recognize the token.

 - `cdef Symbol _get_symbol(type_,text)`: the internal mapping function.
    - Args:
        - `type_ (Any)`: the type of token.
        - `text (str)`: the text of the token.
    
    - Raise: `ValueError('type_ must be a subclass of TokenType')`

 - `cdef set[object] _get_dfa_state_values(state)`: used to get the internal `DFA` states values.
    - Args:
        - `state (State)`: gets the token types of the given state.

 - `cdef bint _move_next()`: iterates until a new token is readed.

 - `cdef Token _current()`: gets the current token readed.

 - `cdef bint _is_fault_state(state)`: returns `True` if the given state is the fault state of the internal `DFA` used during the tokenization.
    - Args:
        - `state (State)`

 - `cpdef void initialize()`: initializes the lexer.
    - Raises: `LexerNotTokensProvidedException` if there are no automata provided for tokens.

 - `cpdef void load_text(text)`: prepares the lexer for the tokenization.

## Submodule `lexer.lexer`

> ### `Lexer`

Subclass of `BaseLexer`.

 - `__init__(get_symbol_function, ignore_pattern)`
    - Args:
        - `get_symbol_function (Callable[[Any, str], Symbol])`: analogous to `BaseLexer.__init__`.
        - `ignore_pattern (str)`: regex of the tokens to skip in the tokenization.

#### Properties

 - `_rules (cdef dict[object,set[LexicalRule]])`: lexical rules to apply during the tokenization.

 - `_errors (cdef set[LexicalError])`: set of lexical errors detected during the tokenization.

 - `_eof (cdef Token)`: the `EOF` token.

#### Methods

 - `cpdef void clear_errors()`: clears all the lexical errors detected.

 - `cpdef void set_eof_token(symbol, type_)`: sets the `EOF` token to be emmited at the end of the tokenization.
    - Args:
        - `symbol (str)`: the text of the symbol for the `EOF` token. The symbol of `EOF` token is always a terminal.
        - `type_ (Any)`: must be a member of the enum type declared in the annotation for the first argument of `get_symbol_function`.
    
    - Raises: `ValueError` if `type_` does not belong to the enum of the annotation for the first argument of `get_symbol_function`.

 - `cpdef void add_token_regex(priority, type_, re)`: compiles `re`, assigns `type_` to accepting states of the compilation result of `re` and registers the token.
    - Args:
        - `priority (int)`
        - `type_ (Any)`: must be a member of the enum type declared in the annotation for the first argument of `get_symbol_function`.
        - `re (str)`: the regex for the token.

 - `cpdef void add_rule(type_, rule)`: adds a `LexicalRule` to the set associated with `type_`.
    - Args:
        - `type_ (Any)`: must be a member of the enum type declared in the annotation for the first argument of `get_symbol_function`.
        - `rule (LexicalRule)`: the rule to be applied during tokenization.

> ### `IdentedLexer`

Subclass of `Lexer` specialized on languages with identation.

 - `__init__(get_symbol_function, ignore_pattern)`
    - Args:
        - `get_symbol_function (Callable[[Any, str], Symbol])`: analogous to `BaseLexer.__init__`.
        - `ignore_pattern (str)`: regex of the tokens to skip in the tokenization.

#### Properties

 - `_ident_counter (cdef int)`: used to decide when to emit a `INDENT` or a `DEDENT` token.

 - `_last_ident_value (cdef int)`: used to decide when to emit a `INDENT` or a `DEDENT` token.

 - `_ident_type (cdef object)`: the enumeration value associated to the `INDENT` or `DEDENT` token (must be a member of a subclass of `TokenType`).

 - `_indent_symbol (cdef Symbol)`: associated symbol for the `INDENT` token.

 - `_dedent_symbol (cdef Symbol)`: associated symbol for the `DEDENT` token.

 - `_sanitaze_function (cdef object)`: function used for sanitaze the text before the tokenization, if provided, it's automatically called during `load_text(text)`.

#### Methods

- `cpdef void set_ident(ident_type)`: sets the set of tokens associated to identation (`'    ', '\t'`, etc.) 
    - Args:
        - `ident_type (Any)`: must be a member of the enum type declared in the annotation for the first argument of `get_symbol_function`.
    
    - Raises: `ValueError` if not in the enum.

 - `cpdef void set_indent_symbol(symbol)`: sets the symbol for the `INDENT` token.
    - Args:
        - `symbol (Symbol)`

 - `cpdef void set_dedent_symbol(symbol)`: sets the symbol for the `DEDENT` token.
    - Args:
        - `symbol (Symbol)`

 - `cpdef void set_text_sanitize_function(sanitaze_function)`: stores the sanitization function, if provided, is automatically called during `IdentedLexer.load_text(text)`.
    - Args:
        - `sanitaze_function (Callable[[str],str])`.



<!-- source: docs/api-reference/cython/api-reference-cython-parser.md -->

# Module `parser`

## Submodule `parser.bottom_up_parser_actions`

> ### `BottomUpParserAction`

Enumeration with the possible actions of an LR parser. Inherits from `StrEnum` (`BottomUpParserAction(StrEnum)`).

 - `ACCEPT = 'ACCEPT'`

 - `SHIFT = 'SHIFT'`

 - `REDUCE = 'REDUCE'`

## Submodule `parser.lr0_parser`

> ### `LR0Item`

Class that represents an **LR(0) item**.

 - `__init__(head, left, right)`
    - Args:
        - `head (Symbol)`: non-terminal of the production from which this item comes.
        - `left (Sequence[Symbol])`: the symbols before the dot.
        - `right (Sequence[Symbol])`: the symbols after the dot.

#### Properties 

 - `_id (cdef str)`: the id of the item (`f'{head} -> {left} ◦ {right}'`)

 - `_head (cdef Symbol)`

 - `_left (cdef list[Symbol])`: copy of the symbols before the dot.

 - `_right (cdef list[Symbol])`: copy of the symbols before the dot.

 - `_hash (cdef int)`: precomputed hash.

> ### `LR0State`

Class that represents an **LR(0) state**.

 - `__init__(items, index = 0)`:
    - Args:
        - `items (Set[LR0Item])`: items of the state.
        - `index (int)`: used to produce human-readable string representations like `I0`, `I2`, etc.

#### Properties

 - `_id (cdef str)`

 - `index (cdef int)`

 - `_items (cdef set[LR0Item])`

 - `_hash (cdef int)`

## Submodule `parser.lr1_parser`

> ### `LR1Item`

Class that represents an **LR(1) item**. Inherits from `LR0Item` (`LR1Item(LR0Item)`)

 - `__init__(head, left, right, lookahead)`
    - Args:
        - `head (Symbol)`: non-terminal of the production from which this item comes.
        - `left (Sequence[Symbol])`: the symbols before the dot.
        - `right (Sequence[Symbol])`: the symbols after the dot.
        - `lookahead (Symbol)`: the lookahead symbol.

#### Properties

 - `_id (cdef str)`: Differences from `LR0Item` (`f'{self._head} -> {left} ◦ {right} ({lookahead})'`)

 - `_lookahead (cdef Symbol)`: the lookahead symbol.

> ### `LR1State`

Class that represents an **LR(1) state**.

 - `__init__(items, index = 0)`
    - Args:
        - `items (Set[LR1Item])`: items of the state.
        - `index (int)`: used to produce human-readable string representations like `I0`, `I2`, etc.

#### Properties

 - `_id (cdef str)`
 - `_index (cdef int)`
 - `_items (cdef set[LR1Item])`
 - `_hash (cdef int)`

## Submodule `parser.lalr_parser`

> ### `LALRItem`

Class that represents an **LALR(1) item**. Inherits from `LR0Item` (`LALRItem(LR0Item)`).

 - `__init__(head, left, right, lookaheads = set())`
    - Args:
        - `head (Symbol)`: non-terminal of the production from which this item comes.
        - `left (Sequence[Symbol])`: the symbols before the dot.
        - `right (Sequence[Symbol])`: the symbols after the dot.
        - `lookaheads (Set[Symbol])`: the set of lookahead symbols.

#### Properties

 - `_id (cdef str)`: Differences from `LR0Item` (`f'{self._head} -> {left} ◦ {right} {lookaheads}'`)

 - `_lookaheads (cdef set[Symbol])`: the set of lookahead symbols.

> ### `LALRState`

Class that represents an **LR(1) state**.

 - `__init__(items, index = 0)`
    - Args:
        - `items (Set[LALRItem])`: items of the state.
        - `index (int)`: used to produce human-readable string representations like `I0`, `I2`, etc.

#### Properties

 - `_id (cdef str)`
 - `_index (cdef int)`
 - `_items (cdef set[LALRItem])`
 - `_hash (cdef int)`

## Submodule `parser.parser`

> ### `ParsingException`

Exception raised when an attemp is made to obtain the parse tree after when errors where found during the parsing process. Inherits from `Exception` (`ParsingException(Exception)`).

> ### `ParseTreeNode`

Class that represents a node on the resulting parse tree after a token's stream has been parsed.

 - `__init__(symbol, start_line, start_column, end_line, end_column, children=[])`
    - Args:
         - `symbol (Symbol)`: symbol of this node on the parse tree.
         - `start_line (int)`: start line in the source.
         - `start_column (int)`: start column in the source.
         - `end_line (int)`: end line in the source.
         - `end_column (int)`: end column in the source.
         - `children (list[ParseTreeNode])`: children of this node in the parse tree.

#### Properties

- `_symbol (cdef Symbol)`: symbol of this node on the parse tree.
- `_start_line (cdef int)`: start line in the source.
- `_start_column (cdef int)`: start column in the source.
- `_end_line (cdef int)`: end line in the source.
- `_end_column (cdef int)`: end column in the source.
- `_children (cdef list[ParseTreeNode])`: children of this node in the parse tree.

> ### `Parser`

Base class for a parser.

 - `__init__()`
    - Raises: `ValueError('Can not instance this class')`.

#### Properties

 - `_ast (cdef AST)`: the resulting ast when parsing ends succesfully.

 - `_parsed (cdef bint)`: `True` when parsing ends succesfully.

 - `_draw_parse_tree (cdef bint)`: when `True`, the parser builds the parse tree during the parsing.

 - `_parse_tree (cdef ParseTreeNode)`: the resulting parse tree when parsing ends succesfully with `_draw_parse_tree` setted to `True`.

 - `_parse_tree_nodes (cdef list[ParseTreeNode])`: used internally to build the parse tree.

 - `_errors (cdef set[Error])`: the errors collected during the parsing.

 - `_syntax_error (cdef bint)`: `True` if any syntax error.

#### Methods

 - `cdef void _try_parse(token)`: try to parse the given token. Not implemented raises `NotImplementedError`.
    - Args:
        - `token (Token)`.
    
 - `cpdef void reset()`: resets the parser (not implemented, raises `NotImplementedError`).

 - `cpdef void set_draw_parse_tree_flag(flag)`: if `flag` is `True`, tells the parser to build the parse tree.
    - Args:
        - `flag (bool)`

> ### `BottomUpParser`

Class for a classic lr parser. Inherits from `Parser` (`BottomUpParser(Parser)`).

 - `__init__(start_state, goto_table, action_table)`
    - Args:
        - `start_state (str)`: initial state id, e.g. `"I0"`.
        - `goto_table (Dict[Tuple[str, Symbol], str])`: the `GOTO` table.
        - `action_table (Dict[Tuple[str, Symbol], Tuple[str, str | Production]])`: the `ACTION` table.

#### Properties

 - `_reductor_by_production (cdef dict[int,object])`: mapping of the productions to the corresponding reductor.

 - `_goto_table (cdef dict[tuple[str,Symbol],str])`: `GOTO` table.

 - `_action_table (cdef dict[tuple[str,Symbol],tuple[str,object]])`: `ACTION` table.

 - `_goto_table_optimized (cdef dict[long long,int])`: optimized version of the `GOTO` table.

 - `_action_table_optimized (cdef dict[long long,tuple[str,object]])`: optimized version of the `GOTO` table.

 - `_stack (cdef list[Symbol])`: internal symbols stack for the parsing.

 - `_stack_ast (cdef list[AST])`: internal asts stack for the parsing.

 - `_stack_states (cdef list[int])`: iternal states stack for the parsing.

 - `_start_state (cdef str)`: start state for reseting the parser.

 - `_current_syncronization_set (cdef set[Symbol])`: used internally for the **panic-mode** error recovery strategy.

 - `_panic_mode (cdef bint)`: `True` when the parser is recovering from a syntax error.

 - `_view (cdef ASTListView)`: view passed to reductors.

 - `_stack_top (cdef int)`: updated internally to keep updated `_stack`.

 - `_stack_len (cdef int)`: updated internally to keep updated `_stack`.

 - `_stack_ast_top (cdef int)`: updated internally to keep updated `_stack_ast`.

 - `_stack_ast_len (cdef int)`: updated internally to keep updated `_stack_ast`.

 - `_stack_states_top (cdef int)`: updated internally to keep updated `_stack_states`.

 - `_stack_states_len (cdef int)`: updated internally to keep updated `_stack_states`.

#### Methods

 - `cdef void _start_recovery_mode(symbol, start_line, start_column, end_line, end_column)`: starts the error recovery process.
    - Args:
        - `symbol (Symbol)`: symbol that triggered the error.
        - `start_line (int)`: line where the error starts in source.
        - `start_column (int)`: column where the error starts in source.
        - `end_line (int)`: line where the error ends in source.
        - `end_column (int)`: column where the error ends in source.

 - `cdef void _end_recovery_mode(symbol)`: ends the error recovery process.
    - Args:
        - `symbol (Symbol)`: symbol with which the process stop.

 - `cdef void _set_reductor(production,reductor)`: sets the corresponding reductor to the given production.

## Submodule `parser.parser_builder`

> ### Exceptions

Exceptions raised when the parser building fails.

 - `ParserBuildingConflictException`

 - `SLRParserBuildingConflictException`
    - `__init__(state, symbol)`
        - Args:
            - `state (LR0State)`: conflictive state.
            - `symbol (Symbol)`: conflictive symbol.
    
    - Properties:
        - `_state (cdef LR0State)`: conflictive state.
        - `_symbol (cdef Symbol)`: conflictive symbol.

 - `LR1ParserBuildingConflictException`
    - `__init__(state, symbol)`
        - Args:
            - `state (LR1State)`: conflictive state.
            - `symbol (Symbol)`: conflictive symbol.
    
    - Properties:
        - `_state (cdef LR1State)`: conflictive state.
        - `_symbol (cdef Symbol)`: conflictive symbol.

 - `LALRParserBuildingConflictException`
    - `__init__(state, symbol)`
        - Args:
            - `state (LALRState)`: conflictive state.
            - `symbol (Symbol)`: conflictive symbol.
    
    - Properties:
        - `_state (cdef LALRState)`: conflictive state.
        - `_symbol (cdef Symbol)`: conflictive symbol.

 - `SLRShiftReduceConflictException`: Inherits from `SLRParserBuildingConflictException`.
    - `__init__(state, symbol, next_state, production)`:
        - Args:
            - `state (LR0State)`: conflictive state.
            - `symbol (Symbol)`: conflictive symbol.    
            - `state (LR0State)`: possible `SHIFT` state.
            - `production (Production)`: posible `REDUCE` production.
    
    - Properties:
        - `_state (cdef LR0State)`: possible `SHIFT` state.
        - `_production (cdef Production)`: posible `REDUCE` production.

 - `LR1ShiftReduceConflictException`: Inherits from `LR1ParserBuildingConflictException`.
    - `__init__(state, symbol, next_state, production)`:
        - Args:
            - `state (LR1State)`: conflictive state.
            - `symbol (Symbol)`: conflictive symbol.    
            - `state (LR1State)`: possible `SHIFT` state.
            - `production (Production)`: posible `REDUCE` production.
    
    - Properties:
        - `_state (cdef LR1State)`: possible `SHIFT` state.
        - `_production (cdef Production)`: posible `REDUCE` production.

 - `LALRShiftReduceConflictException`: Inherits from `LALRParserBuildingConflictException`.
    - `__init__(state, symbol, next_state, production)`:
        - Args:
            - `state (LALRState)`: conflictive state.
            - `symbol (Symbol)`: conflictive symbol.    
            - `state (LALRState)`: possible `SHIFT` state.
            - `production (Production)`: posible `REDUCE` production.
    
    - Properties:
        - `_state (cdef LALRState)`: possible `SHIFT` state.
        - `_production (cdef Production)`: posible `REDUCE` production.

 - `SLRReduceReduceConflictException`: Inherits from `SLRParserBuildingConflictException`.
    - `__init__(state, symbol, old, new_)`
        - Args:
            - `state (LR0State)`: conflictive state.
            - `symbol (Symbol)`: conflictive symbol.
            - `old (Production)`: conflictive production.
            - `new_ (Production)`: conflictive production.
    
    - Properties:
        - `_old (cdef Production)`: conflictive production.
        - `_new (cdef Production)`: conflictive production.

 - `LR1ReduceReduceConflictException`: Inherits from `LR1ParserBuildingConflictException`.
    - `__init__(state, symbol, old, new_)`
        - Args:
            - `state (LR1State)`: conflictive state.
            - `symbol (Symbol)`: conflictive symbol.
            - `old (Production)`: conflictive production.
            - `new_ (Production)`: conflictive production.
    
    - Properties:
        - `_old (cdef Production)`: conflictive production.
        - `_new (cdef Production)`: conflictive production.

 - `LALRReduceReduceConflictException`: Inherits from `LALRParserBuildingConflictException`.
    - `__init__(state, symbol, old, new_)`
        - Args:
            - `state (LALRState)`: conflictive state.
            - `symbol (Symbol)`: conflictive symbol.
            - `old (Production)`: conflictive production.
            - `new_ (Production)`: conflictive production.
    
    - Properties:
        - `_old (cdef Production)`: conflictive production.
        - `_new (cdef Production)`: conflictive production.

> ### Module functions.

 - **`CLOSURE`** implementation:
    - `cdef set[LR0Item] _closure_lr0(items, g)`
        - Args:
            - `items (set[LR0Item])`
            - `g (Grammar)`

    - `cdef set[LR1Item] _closure_lr1(items, g)`
        - Args:
            - `items (set[LR1Item])`
            - `g (Grammar)`

    - `cdef set[LALRItem] _closure_lalr(items, g)`
        - Args:
            - `items (set[LALRItem])`
            - `g (Grammar)`

 - **`GOTO`** implementation:

    - `cdef set[LR0Item] _goto_lr0(items, x, g)`
        - Args:
            - `items (set[LR0Item])`
            - `x (Symbol)`
            - `g (Grammar)`

    - `cdef set[LR1Item] _goto_lr1(items, x, g)`
        - Args:
            - `items (set[LR1Item])`
            - `x (Symbol)`
            - `g (Grammar)`

    - `cdef set[LALRItem] _goto_lalr(items, x, g)`
        - Args:
            - `items (set[LALRItem])`
            - `x (Symbol)`
            - `g (Grammar)`

 - `cdef set[LR0State] get_canonical_lr0_states(g)`: returns the set of the canonical LR(0) states.
    - Args:
        - `g (Grammar)`

 - `cdef set[LR1State] get_canonical_lr1_states(g)`: returns the set of the canonical LR(1) states.
    - Args:
        - `g (Grammar)`

 - `cdef tuple[set[LALRState],dict[tuple[LR0State,LR0Item],set[Symbol]],dict[tuple[str,LR0Item,Symbol,str,LR0Item],set[Symbol]]] _get_canonical_lalr_states(g,keep_edge_propagation_info=False)`: returns the set of the canonical LALR(1) states and optionally, a record of the symbols propagated for the propagation edges (used in the `visual` module for visual debugging).
    - Args:
        - `g (Grammar)`
        - `keep_edge_propagation_info (bint)`: if `True`, the info is saved and returned.

> **NOTE**
`_get_canonical_lr0_states`, `_get_canonical_lr1_states` and `_get_canonical_lalr_states`, already adds the production `S -> S'` to the grammar, so it is unnecessary to do this manually.

 - `cdef set[LR0Item] _get_kernel_items_lr0(state, g)`: returns the set of the kernel items of the given state.
    - Args:
        - `state (LR0State)`
        - `g (Grammar)`

 - `cdef set[LR1Item] _get_kernel_items_lr1(state, g)`: returns the set of the kernel items of the given state.
    - Args:
        - `state (LR1State)`
        - `g (Grammar)`

 - `cdef set[LALRItem] _get_kernel_items_lalr(state, g)`: returns the set of the kernel items of the given state.
    - Args:
        - `state (LALRState)`
        - `g (Grammar)`

 - `cdef tuple[dict[LR0State,dict[tuple[LR0Item,Symbol],tuple[LR0State,LR0Item]]],set[LR0State]] _build_lookaheads_propagation_edges(g)`: builds the propagation edges for a LALR(1) parser building, returns a tuple `(edges,lr0_states)`.
    - Args:
        - `g (Grammar)`

 - `cdef tuple[dict[tuple[LALRState,Symbol],LALRState],dict[tuple[LALRState,Symbol],tuple]] _get_goto_action_tables_lalr(g)`, `cdef tuple[dict[tuple[LR0State,Symbol],LR0State],dict[tuple[LR0State,Symbol],tuple]] _get_goto_action_tables_slr(g)`, `cdef tuple[dict[tuple[LR1State,Symbol],LR1State],dict[tuple[LR1State,Symbol],tuple]] _get_goto_action_tables_lr1(g)`: builds the `GOTO` / `ACTION` tables.
    - Args:
        `g (Grammar)`

 - `cdef dict[tuple[str,Symbol],str] _plain_goto_table_lalr(table)`: plains a LALR(1) `GOTO` table.
    - Args:
        - `table (dict[tuple[LALRState,Symbol],LALRState])`

 - `cdef dict[tuple[str,Symbol],str] _plain_goto_table_slr(table)`: plains a SLR `GOTO` table.
    - Args:
        - `table (dict[tuple[LR0State,Symbol],LR0State])`

 - `cdef dict[tuple[str,Symbol],str] _plain_goto_table_lr1(table)`: plains a LR(1) `GOTO` table.
    - Args:
        - `table (dict[tuple[LR1State,Symbol],LR1State])`

 - `cdef dict[tuple[str,Symbol],tuple[str,object]] _plain_action_table_lalr(table)`: plains a LALR(1) `ACTION` table.
    - Args:
        - `table (dict[tuple[LALRState,Symbol],tuple])`

 - `cdef dict[tuple[str,Symbol],tuple[str,object]] _plain_action_table_slr(table)`: plains a SLR `ACTION` table.
    - Args:
        - `table (dict[tuple[LR0State,Symbol],tuple])`

 - `cdef dict[tuple[str,Symbol],tuple[str,object]] _plain_action_table_lr1(table)`: plains a LR(1) `ACTION` table.
    - Args:
        - `table (dict[tuple[LR1State,Symbol],tuple])`

 - `cdef BottomUpParser _build_lalr_parser(g)`: builds a LALR(1) parser.
    - Args:
        - `g (Grammar)`

 - `cdef BottomUpParser _build_slr_parser(g)`: builds a SLR parser.
    - Args:
        - `g (Grammar)`

 - `cdef BottomUpParser _build_lr1_parser(g)`: builds a LR(1) parser.
    - Args:
        - `g (Grammar)`

 - `cdef BottomUpParser _build_lalr_parser_from_attributed(g)`: builds a LALR(1) parser from an attributed grammar and sets the corresponding reductors.
    - Args:
        - `g (AttributedGrammar)`

 - `cdef BottomUpParser _build_slr_parser_from_attributed(g)`: builds a SLR parser from an attributed grammar and sets the corresponding reductors.
    - Args:
        - `g (AttributedGrammar)`

 - `cdef BottomUpParser _build_lr1_parser_from_attributed(g)`: builds a LR(1) parser from an attributed grammar and sets the corresponding reductors.
    - Args:
        - `g (AttributedGrammar)`

## Submodule `parser.parser_type`

> ### `ParserType`

Enumeration with the parser types. Inherits from `StrEnum` (`ParserType(StrEnum)`).

 - `LL1 = 'LL1'`: **currently not supported**.

 - `SLR = 'SLR'`

 - `LR1 = 'LR1'`

 - `LALR1 = 'LALR1'`



<!-- source: docs/api-reference/cython/api-reference-cython-regex.md -->

# Module `regex`

## Submodule `regex.engine`

> ### `RegexParsingException`

Exception raised when a regex can't be parsed. Inherits from `Exception` (`RegexParsingException(Exception)`).

#### Properties

 - `_errors (cdef list[RuntimeError])`

> ### Internal Functions

 - `cdef DFA _left_regular_automaton(g)`: returns a `DFA` equivalent to `g` (specific for left-regular grammars).
    - Args:
        - `g (Grammar)`

 - `cdef DFA _right_regular_automaton(g)`: returns a `DFA` equivalent to `g` (specific for right-regular grammars).
    - Args:
        - `g (Grammar)` 

 - `cdef DFA _get_automaton(g)`:  returns the `DFA` equivalent to the language described by `g`.
    - Args:
        - `g (Grammar)`
    
    - Raises: `ValueError('g must be a regular grammar')` if `g` is not a regular grammar.

 - `cdef Grammar _get_grammar(dfa)`: returns the grammar equivalent to `automaton`.
    - Args:
        - `automaton (Automaton)`

 - `cdef str _get_regex(automaton)`: returns an equivalent regex to `automaton`.
    - Args:
        - `automaton (Automaton)`

 - `cdef DFA _parse(re)`: returns the `DFA` equivalent to `re`.
    - Args:
        - `re (str)`
    
    - Raises: `RegexParsingException` if there are runtime errors.

## Submodule `regex.regex_parser`

 - `cdef set[str] get_latin_punctuation()`, `cdef set[str] get_latin_letters()`: gets latin letters and punctuation characters.

 - `cdef BottomUpParser _build_regex_parser()`: returns a parser for regex expressions.

 - `cdef BaseLexer _build_regex_lexer()`: returns a lexer for regex expressions.
