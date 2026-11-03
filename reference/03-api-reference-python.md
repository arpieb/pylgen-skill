# PyLGEN — Python API Reference



<!-- source: docs/api-reference/python/api-reference-python-common.md -->

# Module `common`

## Submodule `common.enums`

> ### `TokenTypeMeta(EnumMeta)`

Metaclass for `TokenType`. In its `__new__`, it injects `INVALID_TOKEN` into subclasses (except `TokenType` itself).

> ### `TokenType(StrEnum, metaclass=TokenTypeMeta)`

Base enumeration for token types. Subclasses automatically receive an `INVALID_TOKEN` member.

> ### `ErrorType(StrEnum)`

Compiler error types.

 - `LEXICAL = 'LEXICAL'`

 - `SYNTAX = 'SYNTAX'`
 
 - `SEMANTIC = 'SEMANTIC'`
 
 - `RUNTIME = 'RUNTIME'`

## Submodule `common.types`

> ### `Symbol`

Class that represents a grammar symbol.

 - `__init__(symbol: str, is_terminal: bool = False, is_epsilon: bool = False)`
    - Args:
        - `symbol (str)`: the symbol.

        - `is_terminal (bool)`: whether it is a terminal.

        - `is_epsilon (bool)`: whether it is the epsilon symbol. A symbol can only be epsilon if it is a terminal.

    - Raises: `ValueError('A symbol only can be epsilon if its a terminal symbol')`.

#### Properties

 - `symbol (str)`
 - `is_terminal (bool)`
 - `is_epsilon (bool)`

#### Methods

 - `__str__`: returns the symbol.
 - `__repr__`: returns the symbol.
 - `__eq__`: equality by `symbol`, `is_terminal` and `is_epsilon` properties.
 - `__hash__`: precomputed hash using **SHA-256**.

> ### `AST`

Abstract Syntax Tree class.

 - `__init__(symbol:Symbol, start_line:int, start_column:int, end_line:int, end_column:int)`
    - Args:
        - `symbol (Symbol)`: internal symbol of the AST.
        - `start_line (int)`, `start_column (int)`: start position in source.
        - `end_line (int)`, `end_column (int)`: end position in source.

    - Raises: `ValueError` if positions are invalid.

#### Properties

 - `symbol (Symbol)`.
 - `start_position (Tuple[int,int])`: The tuple `(start_line,start_column)`.
 - `end_position (Tuple[int,int])`: The tuple `(end_line,end_column)`.
 - `is_error (bool)`: `True` if is an `ErrorAST`, `False` otherwise.
 - `start_position.setter` / `end_position.setter`: validate ranges.

#### Methods

 - `children() -> List[AST]`: method to be implemented by subclasses (`raise NotImplementedError`). It must return the children of the current AST (by general consensus, in the same order that must be processed normally).
 - `__str__`, `__repr__`: returns `symbol._symbol`.

> ### `Error`

Abstract error class.

 - `__init__(type_:ErrorType | str, start_line:int, start_column:int, end_line:int, end_column:int, msg:str)`
    - Args:
        - `type_ (ErrorType | str)`.
        - `start_line (int)`, `start_column (int)`: start position in source.
        - `end_line (int)`, `end_column (int)`: end position in source.
        - `msg (str)`.

    - Raises: `TypeError` if `type_` is not a member of `ErrorType` and is not an `str`, `ValueError` if `type_` is not an `ErrorType`, or `ValueError` if positions are invalid.

#### Properties

 - `start_position (Tuple[int,int])`: The tuple `(start_line,start_column)`.
 - `end_position (Tuple[int,int])`: The tuple `(end_line,end_column)`.
 - `type (ErrorType)`: The type of the error.
 - `message (str)`: The message of the error.

#### Methods

 - `__str__`, `__repr__`: returns `f'{type} ERROR at line {start_line}: {msg}'`
 - `__hash__`: precomputed hash using **SHA-256**.
 - `__eq__`: equality by `type`, `message`, and positional values.

> ### `Error` subclasses

All this classes inherits from `Error` class.

#### `LexicalError`

 - `__init__(msg:str, start_line:int, start_column:int, end_line:int, end_column:int)`: sets `type_ = ErrorType.LEXICAL`.

#### `SyntaxError`

 - `__init__(msg:str, start_line:int, start_column:int, end_line:int, end_column:int)`: sets `type_ = ErrorType.SYNTAX`.

#### `SemanticError`

 - `__init__(msg:str, start_line:int, start_column:int, end_line:int, end_column:int)`: sets `type_ = ErrorType.SEMANTIC`.

#### `RuntimeError`

 - `__init__(stack_trace:List[str], start_line:int, start_column:int, end_line:int, end_column:int, msg:str)`: sets `type_ = ErrorType.RUNTIME`.

 - **Property**: `stack_trace (List[str])`.

> ### `ErrorAST`

Error Syntax Tree Class (inherits from `AST`: `ErrorAST(AST)`).

 - `__init__(symbol:Symbol, start_line:int, start_column:int, end_line:int, end_column:int, errors: Set[SemanticError])`
    - Args:
        - `symbol (Symbol)`: internal symbol of the AST.
        - `start_line (int)`, `start_column (int)`: start position in source.
        - `end_line (int)`, `end_column (int)`: end position in source.
        - `errors (Set[SemanticError])`: errors inside the ast.
    
    - Raises: `ValueError` if positions are invalid.
    - Sets `_is_error` internal flag to `True`.

> ### `ASTListView`

View over a list of `AST`.

#### Methods

 - `__len__`: The size of the view (`len(view)`).
 - `__getitem__`: For indexing (`view[idx]`).
    - Raises: `IndexError('ASTListView index out of range')` if `idx < 0` or `idx >= len(view)`

> ### `Token`

Token class (inherits from `AST`: `Token(AST)`).

 - `__init__(text:str, type_:Any, symbol:Symbol, line:int, column:int)`
    - Raises: `ValueError` if `type_` is not a subclass of `TokenType`.
    - Calls `super().__init__(symbol, line, column, line, column + len(text))`.

#### Properties

 - `text`: The text of the token.
 - `type`: The type of the token.

#### Methods

 - `children() -> List[AST]`: returns `[]`

## Submodule `common.table`

> ### `Table`

Class used to store the transitions of an automata.

 - `__init__()`: initializes `_table = {}`.

#### Properties

 - `entries (List[Tuple[str,str]])`: keys of the internal dict.
 - `values (List[str])`: values of the internal dict.
 - `items (List[Tuple[str,str,str]])`: tuples `(from, symbol, value)`.

#### Methods

 - `to_dict() (Dict[Tuple[str,str], str])`: returns copy as a plain dict.
 - `from_dict(data: Dict[Tuple[str,str], str])`: updates `_table` with `data`.
 - `__getitem__`: to access values via `table['f','s']`.
    - Raises: `ValueError` if the coord is not length 2 or if values are not `str`.
 - `__setitem__`: to set values via `table['f','s'] = 't'`.
    - Raises: `ValueError` if the coord is not length 2 or if values are not `str`.
 - `__delitem__`: to delete values via `del table['f','s']`.
    - Raises: `ValueError` if the coord is not length 2 or if values are not `str`.



<!-- source: docs/api-reference/python/api-reference-python-lexer.md -->

# Module `lexer`

## Submodule `lexer.base_lexer`

> ### `LexerNotInitializedException`

Exception raised when an attemp is made to obtain the internal `DFA` without initializing the lexer first. Inherits from `Exception` (`LexerNotInitializedException(Exception)`).

> ### `LexerNotTokensProvidedException`

Exception raised when an attemp is made to initialize the lexer without any token automata provided. Inherits from `Exception` (`LexerNotTokensProvidedException(Exception)`).

> ### `BaseLexer`

Base class for a lexer.

 - `__init__(get_symbol_function, ignore_pattern)`
    - Args:
        - `get_symbol_function (Callable[[Any, str], Symbol])`: mapping function that maps a tuple `(Any,str)` to a `Symbol`. The mapping function must be annotated with the specific signature `Callable[[Any, str], Symbol]`, where the first argument annotation must be a subclass of `TokenType`.
        - `ignore_pattern (DFA)`: the `DFA` used to skip text patterns.
    
    - Raises: `ValueError` if the signature of `get_symbol_function` is invalid.

> **WARNING**
This class is not meant to be used directly.

#### Properties

 - `dfa (DFA)`: returns the internal `DFA` used for tokenization.
    - Raises: `LexerNotInitializedException` if not initialized.

 - `tokens (Iterable[Token])`: initializes (if needed) and iterates over all tokens skipping ignored tokens.

#### Methods

 - `initialize()`: initializes the lexer.
    - Raises: `LexerNotTokensProvidedException` if there are no automata provided for tokens.

 - `load_text(text)`: prepares the lexer for tokenization.

## Submodule `lexer.lexer`

> ### `Lexer`

Subclass of `BaseLexer`.

 - `__init__(get_symbol_function, ignore_pattern)`
    - Args:
        - `get_symbol_function (Callable[[Any, str], Symbol])`: analogous to `BaseLexer.__init__`.
        - `ignore_pattern (str)`: regex of the tokens to skip in the tokenization.

#### Properties

 - `errors (Set[LexicalError])`: a copy of the lexical errors detected during the tokenization.
 
 - `tokens (Iterable[Token])`: analogous to `BaseLexer.tokens`, besides normal tokens, emits the EOF token (if provided) at the end.

#### Methods

 - `clear_errors()`: clears all the lexical errors detected.

 - `set_eof_token(symbol, type_)`: sets the `EOF` token to be emmited at the end of the tokenization.
    - Args:
        - `symbol (str)`: the text of the symbol for the `EOF` token. The symbol of `EOF` token is always a terminal.
        - `type_ (Any)`: must be a member of the enum type declared in the annotation for the first argument of `get_symbol_function`.
    
    - Raises: `ValueError` if `type_` does not belong to the enum of the annotation for the first argument of `get_symbol_function`.

 - `add_token_regex(priority, type_, re)`: compiles `re`, assigns `type_` to accepting states of the compilation result of `re` and registers the token.
    - Args:
        - `priority (int)`
        - `type_ (Any)`: must be a member of the enum type declared in the annotation for the first argument of `get_symbol_function`.
        - `re (str)`: the regex for the token.

 - `add_rule(type_, rule)`: adds a `LexicalRule` to the set associated with `type_`.
    - Args:
        - `type_ (Any)`: must be a member of the enum type declared in the annotation for the first argument of `get_symbol_function`.
        - `rule (LexicalRule)`: the rule to be applied during tokenization.

> ### `IdentedLexer`

Subclass of `Lexer` specialized on languages with identation.

 - `__init__(get_symbol_function, ignore_pattern)`
    - Args:
        - `get_symbol_function (Callable[[Any, str], Symbol])`: analogous to `BaseLexer.__init__`.
        - `ignore_pattern (str)`: regex of the tokens to skip in the tokenization.

#### Methods

- `set_ident(ident_type)`: sets the set of tokens associated to identation (`'    ', '\t'`, etc.) 
    - Args:
        - `ident_type (Any)`: must be a member of the enum type declared in the annotation for the first argument of `get_symbol_function`.
    
    - Raises: `ValueError` if not in the enum.

 - `set_indent_symbol(symbol)`: sets the symbol for the `INDENT` token.
    - Args:
        - `symbol (Symbol)`

 - `set_dedent_symbol(symbol)`: sets the symbol for the `DEDENT` token.
    - Args:
        - `symbol (Symbol)`

 - `set_text_sanitize_function(sanitaze_function)`: stores the sanitization function, if provided, is automatically called during `IdentedLexer.load_text(text)`.
    - Args:
        - `sanitaze_function (Callable[[str],str])`.



<!-- source: docs/api-reference/python/api-reference-python-grammar.md -->

# Module `grammar`

## Submodule `grammar.grammar`

> ### `SymbolNotPresentInGrammarException`

Exception raised when a symbol is not found in the current grammar (inherits from `Exception`).

 - `__init__(symbol: Symbol, *args)`

> ### `Production`

Class that represents a grammar production.

 - `__init__(head, production)`
    - Args:
        - `head (Symbol)`: left-hand side of the grammar production.
        - `production (List[Symbol])`: right-hand side of the grammar production.
    
    - Raises: `ValueError("head can't be a terminal symbol")` if `head.is_terminal` is `True`.

#### Properties

 - `id (str)`: the id of the production (`f'{head} -> {" ".join(prod)}'`).
 - `head (Symbol)`
 - `production (List[Symbol])`

#### Methods

 - `__str__`: returns `id`.
 - `__repr__`: returns `id`.
 - `__eq__`: equality by `head` and `production`.
 - `__hash__`: returns the precomputed hash.

> ### `ProductionsSet`

Class that contains the productions for an specific non-terminal.

 - `__init__()`

#### Properties

 - `productions (List[List[Symbol]])`: copy of each production.

#### Methods

 - `__iadd__(production)`: adds a production if not present using the operator `+=`.
    - Args:
        - `production (Tuple[Symbol,...])`

> ### `AttributedProductionsSet`

Version of `ProductionsSet` for attributed grammars. Inherits from `ProductionsSet` (`AttributedProductionsSet(ProductionsSet)`).

 - `__init__()`

#### Methods

 - `__iadd__(self, production_redutor_pair)`: adds an attributed production if not present using the operator `+=`.
    - Args:
        - `production_reductor_pair (Tuple[Tuple[Symbol, ...],Callable[[ASTListView],AST]])`: a pair `(production,reductor)`. `reductor` is the function that the parser will call when it reduces by this production.
    
    - Raises: `ValueError` if the `reductor`'s signature is not `(ASTListView) -> AST`.

> ### `Grammar`

Base class for a grammar.

 - `__init__(start_symbol, end_symbol = '\x00')`
    - Args:
        - `start_symbol (Symbol)`: the start symbol of the grammar.
        - `end_symbol (str)`: the `EOF` symbol for the parser, internally the grammar stores a terminal symbol with value `end_symbol`.
    
    - Raises: `ValueError("start_symbol can't be terminal")` if `start_symbol.is_terminal` is `True`.

#### Properties

 - `id (str)`: based in the current productions, terminals, non-terminals and any structural information of the grammar itself.
 - `productions (Set[Production])`: the current productions of the grammar.
 - `terminals (Set[Symbol])`: the current terminals of the grammar (including the `EOF` symbol created using `end_symbol`).
 - `non_terminals (Set[Symbol])`: the current non-terminals of the grammar.
 - `symbols (Set[Symbol])`: the current symbols present in the grammar (including the `EOF` symbol created using `end_symbol`).
 - `start_symbol (Symbol)`: the start symbol.
 - `end_symbol (Symbol)`: the `EOF` symbol.

#### Static Methods

 - `IsLeftRegular(g)`: returns `True` if the grammar is left-regular.
    - Args:
        `g (Grammar)`

 - `IsRightRegular(g)`: returns `True` if the grammar is right-regular.
    - Args:
        `g (Grammar)`

 - `IsRegular(g)`: returns `True` if the grammar is either left‑ or right‑regular.
    - Args:
        `g (Grammar)`

 - `AugmentGrammar(g)`: returns an augmented version of `g`.
    - Args:
        `g (Grammar)`

 - `Reverse(g)`: reverses the production bodies of every rule, yielding a grammar that recognizes the reversed language.
    - Args:
        `g (Grammar)`

#### Methods

 - `first(production)`: returns the `FIRST` set of the given sequence of symbols.
    - Args:
        `production (List[Symbol])`
    
    - Raises: `SymbolNotPresentInGrammarException` if any symbol is not present in the grammar.

 - `follow(symbol)`: returns the `FOLLOW` set of the given symbol.
    - Args:
        - `symbol (Symbol)`

    - Raises: `SymbolNotPresentInGrammarException` if any symbol is not present in the grammar.

 - `to_dict()`: returns a plain representation of the grammar in a dictionary.

 - `__getitem__(head)`: returns the `ProductionsSet` associated to the non-terminal `head`, via `[`...`]` syntax (eg., `G[nt]`).
    - Args:
        `head (Symbol)`

    - Raises: `ValueError("head can't be a terminal symbol")` if `head.is_terminal` is `True`.
 
 - `__setitem__(head, productions)`: sets the `ProductionsSet` for the non-terminal `head` via `[`...`]` syntax.
    - Args:
        - `head (Symbol)`
        - `productions (ProductionsSet)`
    
    - Raises:
        - `ValueError("head can't be a terminal symbol")` if `head.is_terminal` is `True`.
        - `ValueError('Only can exists one epsilon symbol')` if there is an epsilon symbol in productions different from the current present in the grammar (if exists).

> **TIP**
This method, in combination with `ProductionsSet.__iadd__`, is what allows to use the syntax `G[S] += A,a` to add productions to a grammar.

> ### `AttributedGrammar(Grammar)`

Version of `Grammar` for attributed grammars. Inherits from `Grammar` (`AttributedGrammar(Grammar)`).

 - `__init__(start_symbol, end_symbol='\x00')`: analogous to `Grammar.__init__`.

#### Methods

 - `get_reductor(production)`: gets the associated reductor the given production.
    - Args:
        - `production (Production)`
    
    - Raises: `KeyError` if there's no exists any reductor associated to the given production.

 - `__getitem__(head)`: returns the `AttributedProductionsSet` associated to the non-terminal `head`, via `[`...`]` syntax (eg., `G[nt]`).
    - Args:
        `head (Symbol)`

    - Raises: `ValueError("head can't be a terminal symbol")` if `head.is_terminal` is `True`.
 
 - `__setitem__(head, productions)`: sets the `AttributedProductionsSet` for the non-terminal `head` via `[`...`]` syntax.
    - Args:
        - `head (Symbol)`
        - `productions (ProductionsSet)`
    
    - Raises:
        - `ValueError("head can't be a terminal symbol")` if `head.is_terminal` is `True`.
        - `ValueError('Only can exists one epsilon symbol')` if there is an epsilon symbol in productions different from the current present in the grammar (if exists).

> **TIP**
This method, in combination with `AttributedProductionsSet.__iadd__`, is what allows to use the syntax `G[S] += (A,a),reductor` to add productions to a grammar.



<!-- source: docs/api-reference/python/api-reference-python-parser.md -->

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

 - `id (str)`: the id of the item (`f'{head} -> {left} ◦ {right}'`)

 - `head (Symbol)`

 - `left (Sequence[Symbol])`: copy of the symbols before the dot.

 - `right (Sequence[Symbol])`: copy of the symbols before the dot.

#### Methods

 - `__str__`: returns `id`.

 - `__repr__`: returns `id`.

 - `__eq__`: equality based on `head`, `left` and `right` properties.

 - `__hash__`: precomputed hash.

> ### `LR0State`

Class that represents an **LR(0) state**.

 - `__init__(items, index = 0)`:
    - Args:
        - `items (Set[LR0Item])`: items of the state.
        - `index (int)`: used to produce human-readable string representations like `I0`, `I2`, etc.

#### Properties

 - `id (str)`
 - `index (int)`
 - `items (Set[LR0Item])`

#### Methods

 - `__eq__`: by id.
 - `__hash__`: precomputed hash.

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

 - `id (str)`: Differences from `LR0Item` (`f'{self._head} -> {left} ◦ {right} ({lookahead})'`)

 - `lookahead (Symbol)`: the lookahead symbol.

#### Methods

 - `__eq__`: Differences from `LR0Item`, also compares `lookahead`.

> ### `LR1State`

Class that represents an **LR(1) state**.

 - `__init__(items, index = 0)`
    - Args:
        - `items (Set[LR1Item])`: items of the state.
        - `index (int)`: used to produce human-readable string representations like `I0`, `I2`, etc.

#### Properties

 - `id (str)`
 - `index (int)`
 - `items (Set[LR1Item])`

#### Methods

 - `__eq__`: by id.
 - `__hash__`: precomputed hash.

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

 - `id (str)`: Differences from `LR0Item` (`f'{self._head} -> {left} ◦ {right} {lookaheads}'`)

 - `lookaheads (Set[Symbol])`: the set of lookahead symbols.

#### Methods

 - `__eq__`: also compares `lookaheads`.

> ### `LALRState`

Class that represents an **LR(1) state**.

 - `__init__(items, index = 0)`
    - Args:
        - `items (Set[LALRItem])`: items of the state.
        - `index (int)`: used to produce human-readable string representations like `I0`, `I2`, etc.

#### Properties

 - `id (str)`
 - `index (int)`
 - `items (Set[LALRItem])`

#### Methods

 - `__eq__`: by id.
 - `__hash__`: precomputed hash.

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
         - `children (List[ParseTreeNode])`: children of this node in the parse tree.

#### Properties

 - `symbol (Symbol)`: symbol of this node on the parse tree.

 - `start_position (Tuple[int,int])`: tuple `(start_line, start_column)`, the start position in the source.

 - `end_position (Tuple[int,int])`: tuple `(end_line,end_column)`, the end position in the source.

 - `children (List[ParseTreeNode])`: children of this node in the parse tree.

> ### `Parser`

Base class for a parser.

 - `__init__()`
    - Raises: `ValueError('Can not instance this class')`.

#### Properties

 - `parse_tree (ParseTreeNode)`: root of the parse tree, if succesfully builded
    - Raises: `ParsingException` if any syntax error.

 - `syntax_errors (bool)`: `True` if any syntax error.

 - `errors List[Error]`: all errors detected.

#### Methods

 - `parse(tokens)`: returns the root of the resulting ast if succesfully parsed, otherwise `None`.
    - Args:
        - `tokens (Iterable[Token])`: token's stream.

 - `reset()`: resets the parser (not implemented, raises `NotImplementedError`).

 - `set_draw_parse_tree_flag(flag)`: if `flag` is `True`, tells the parser to build the parse tree.
    - Args:
        - `flag (bool)`

> ### `BottomUpParser`

Class for a classic lr parser. Inherits from `Parser` (`BottomUpParser(Parser)`).

 - `__init__(start_state, goto_table, action_table)`
    - Args:
        - `start_state (str)`: initial state id, e.g. `"I0"`.
        - `goto_table (Dict[Tuple[str, Symbol], str])`: the `GOTO` table.
        - `action_table (Dict[Tuple[str, Symbol], Tuple[str, str | Production]])`: the `ACTION` table.

#### Methods

 - `__setitem__(production, reductor)`: sets the reductor for the given production
    - Raises: `ValueError` if the reductor's signature is not `(ASTListView) -> AST`.

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
        - `state (LR0State)`: conflictive state.
        - `symbol (Symbol)`: conflictive symbol.

 - `LR1ParserBuildingConflictException`
    - `__init__(state, symbol)`
        - Args:
            - `state (LR1State)`: conflictive state.
            - `symbol (Symbol)`: conflictive symbol.
    
    - Properties:
        - `state (LR1State)`: conflictive state.
        - `symbol (Symbol)`: conflictive symbol.

 - `LALRParserBuildingConflictException`
    - `__init__(state, symbol)`
        - Args:
            - `state (LALRState)`: conflictive state.
            - `symbol (Symbol)`: conflictive symbol.
    
    - Properties:
        - `state (LALRState)`: conflictive state.
        - `symbol (Symbol)`: conflictive symbol.

 - `SLRShiftReduceConflictException`: Inherits from `SLRParserBuildingConflictException`.
    - `__init__(state, symbol, next_state, production)`:
        - Args:
            - `state (LR0State)`: conflictive state.
            - `symbol (Symbol)`: conflictive symbol.    
            - `state (LR0State)`: possible `SHIFT` state.
            - `production (Production)`: posible `REDUCE` production.
    
    - Properties:
        - `state (LR0State)`: possible `SHIFT` state.
        - `production (Production)`: posible `REDUCE` production.

 - `LR1ShiftReduceConflictException`: Inherits from `LR1ParserBuildingConflictException`.
    - `__init__(state, symbol, next_state, production)`:
        - Args:
            - `state (LR1State)`: conflictive state.
            - `symbol (Symbol)`: conflictive symbol.    
            - `state (LR1State)`: possible `SHIFT` state.
            - `production (Production)`: posible `REDUCE` production.
    
    - Properties:
        - `state (LR1State)`: possible `SHIFT` state.
        - `production (Production)`: posible `REDUCE` production.

 - `LALRShiftReduceConflictException`: Inherits from `LALRParserBuildingConflictException`.
    - `__init__(state, symbol, next_state, production)`:
        - Args:
            - `state (LALRState)`: conflictive state.
            - `symbol (Symbol)`: conflictive symbol.    
            - `state (LALRState)`: possible `SHIFT` state.
            - `production (Production)`: posible `REDUCE` production.
    
    - Properties:
        - `state (LALRState)`: possible `SHIFT` state.
        - `production (Production)`: posible `REDUCE` production.

 - `SLRReduceReduceConflictException`: Inherits from `SLRParserBuildingConflictException`.
    - `__init__(state, symbol, old, new_)`
        - Args:
            - `state (LR0State)`: conflictive state.
            - `symbol (Symbol)`: conflictive symbol.
            - `old (Production)`: conflictive production.
            - `new_ (Production)`: conflictive production.
    
    - Properties:
        - `old (Production)`: conflictive production.
        - `new_ (Production)`: conflictive production.

 - `LR1ReduceReduceConflictException`: Inherits from `LR1ParserBuildingConflictException`.
    - `__init__(state, symbol, old, new_)`
        - Args:
            - `state (LR1State)`: conflictive state.
            - `symbol (Symbol)`: conflictive symbol.
            - `old (Production)`: conflictive production.
            - `new_ (Production)`: conflictive production.
    
    - Properties:
        - `old (Production)`: conflictive production.
        - `new_ (Production)`: conflictive production.

 - `LALRReduceReduceConflictException`: Inherits from `LALRParserBuildingConflictException`.
    - `__init__(state, symbol, old, new_)`
        - Args:
            - `state (LALRState)`: conflictive state.
            - `symbol (Symbol)`: conflictive symbol.
            - `old (Production)`: conflictive production.
            - `new_ (Production)`: conflictive production.
    
    - Properties:
        - `old (Production)`: conflictive production.
        - `new_ (Production)`: conflictive production.

> ### `ParserBuilder`

Static class that contains all the methods necessary for parser building.

 - `clear_cache()`: clears the internal cache.

 - **`CLOSURE`** implementation:
    - `closure_lr0(items, g) -> Set[LR0Item]`
        - Args:
            - `items (Set[LR0Item])`
            - `g (Grammar)`

    - `closure_lr1(items, g) -> Set[LR1Item]`
        - Args:
            - `items (Set[LR1Item])`
            - `g (Grammar)`

    - `closure_lalr(items, g) -> Set[LALRItem]`
        - Args:
            - `items (Set[LALRItem])`
            - `g (Grammar)`

 - **`GOTO`** implementation:

    - `goto_lr0(items, x, g) -> Set[LR0Item]`
        - Args:
            - `items (Set[LR0Item])`
            - `x (Symbol)`
            - `g (Grammar)`

    - `goto_lr1(items, x, g) -> Set[LR1Item]`
        - Args:
            - `items (Set[LR1Item])`
            - `x (Symbol)`
            - `g (Grammar)`

    - `goto_lalr(items, x, g) -> Set[LALRItem]`
        - Args:
            - `items (Set[LALRItem])`
            - `x (Symbol)`
            - `g (Grammar)`

 - `get_canonical_lr0_states(g)`: returns the set of the canonical LR(0) states.
    - Args:
        - `g (Grammar)`

 - `get_canonical_lr1_states(g)`: returns the set of the canonical LR(1) states.
    - Args:
        - `g (Grammar)`

 - `get_canonical_lalr_states(g)`: returns the set of the canonical LALR(1) states.
    - Args:
        - `g (Grammar)`

> **NOTE**
`get_canonical_lr0_states`, `get_canonical_lr1_states` and `get_canonical_lalr_states`, already adds the production `S -> S'` to the grammar, so it is unnecessary to do this manually.

 - `get_kernel_items_lr0(state, g)`: returns the set of the kernel items of the given state.
    - Args:
        - `state (LR0State)`
        - `g (Grammar)`

 - `get_kernel_items_lr1(state, g)`: returns the set of the kernel items of the given state.
    - Args:
        - `state (LR1State)`
        - `g (Grammar)`

 - `get_kernel_items_lalr(state, g)`: returns the set of the kernel items of the given state.
    - Args:
        - `state (LALRState)`
        - `g (Grammar)`

 - `build_lookaheads_propagation_edges(g)`: builds the propagation edges for a LALR(1) parser building, returns a tuple `(edges,lr0_states)`.
    - Args:
        - `g (Grammar)`

 - `get_goto_action_tables_slr(g)`, `get_goto_action_tables_lr1(g)`, `get_goto_action_tables_lalr(g)`: builds the `GOTO` / `ACTION` tables.
    - Args:
        `g (Grammar)`

 - `build_parser(g, type_)`: builds a parser.
    - Args:
        - `g (Grammar)`
        - `type_ (ParserType)`

 - `build_parser_from_attributed(g, type_)`: builds a parser from an attributed grammar.
    - Args:
        - `g (AttributedGrammar)`
        - `type_ (ParserType)`

 - `get_propagated_lookaheads(g)`: returns the propagation edges for LALR(1) parser building after and before they are filled, in a tuple `(final_lookaheads, propagated_lookaheads)`. Used internally for the module `visual` for visual debuging.
    - Args:
        - `g (Grammar)`

## Submodule `parser.parser_type`

> ### `ParserType`

Enumeration with the parser types. Inherits from `StrEnum` (`ParserType(StrEnum)`).

 - `LL1 = 'LL1'`: **currently not supported**.

 - `SLR = 'SLR'`

 - `LR1 = 'LR1'`

 - `LALR1 = 'LALR1'`



<!-- source: docs/api-reference/python/api-reference-python-analysis.md -->

# Module `analysis`

## Submodule `analysis.context`

> ### `Context`

Base Context class.

 - `__init__()`

#### Properties

 - `errors -> List[SemanticError | RuntimeError]`: copy of semantic errors + runtime errors.

 - `stack_trace -> List[str]`: copy of the stack.

#### Methods

 - `push_trace(trace)`: appends trace to the stack.
    - Args:
        - `trace (str)`

 - `pop_trace()`: removes the last trace.

 - `push_new_scope()`: push a new scope into the context. (not implemented, raises `NotImplementedError`).

 - `pop_scope()`: pops the current scope. (not implemented, raises `NotImplementedError`).

 - `clear_runtime_errors()`: clear all the runtime errors. (not implemented, raises `NotImplementedError`).

 - `get_runtime_errors() -> List[RuntimeError]`: returns all detected runtime errors. (not implemented, raises `NotImplementedError`).

 - `clear_semantic_errors()`: Clear all the semantic errors.

 - `reset()`: reset the context.

 - `clear_errors()`: clear all errors.

 - `add_semantic_error(error)`: adds a semantic error.
    - Args:
        - `error`: instance of a subclass of `SemanticError`.

 - `add_runtime_error(ast, error)`: Adds a new `RuntimeError` from the given ast. (not implemented, raises `NotImplementedError`).
    - Args:
        - `ast`: instance of a subclass of `AST`. 
        - `error`: instance of a subclass of `RuntimeError`.

## Submodule `analysis.lexical`

> ### `LexicalRule`

Abstract class for a lexical validation rule.

 - `__init__(msg: str)`: initializes the instance with the message of the error validation.
    - Args:
        - `msg (str)`

#### Methods

 - `_check(text: str) -> bool`: text validation logic. (not implemented, raises `NotImplementedError`).
    - Args:
        - `text (str)`

 - `check(token: Token) -> LexicalError` — returns a `LexicalError` if `_check` fails, otherwise returns `None`.
    - Args:
        - `token (Token)`

## Submodule `analysis.visitor`

> ### `ASTVisitor`

Base class of a visitor on the ***Visitor Pattern***.

 - `__init__(context_type: type)`
    - Args:
        - `context_type (type)`: the type of the subclass of `Context` for which this visitor is intended.

#### Methods

 - `_check_context_type(context)`: validates `context`.
    - Args:
        - `context`: the instance to be validated.
    
    - Raises: `TypeError` if `context` is not an instance of `context_type`.

 - `visit(ast, context)`: the logic of visit an AST node. (not implemented, raises `NotImplementedError`).
    - Args:
        - `ast`: (instance of a subclass of `AST`).
        - `context`: instance of `context_type`.

> ### `ASTChildrenSelector`

Base class for AST children selectors.

 - `__init__(context_type: type)`
    - Args:
        - `context_type (type)`: the type of the subclass of `Context` for which this visitor is intended.

#### Methods

 - `_check_context_type(context)`:
    - Args:
        `context`: the instance to be validated.
    
    - Raises: `TypeError` if `context` is not an instance of `context_type`.

 - `select_children(ast, context) -> List[AST]`: returns a list of children in the order they will be visited. (not implemented, raises `NotImplementedError`).
    - Args:
        - `ast`: instance of a subclass of `AST`.
        - `context`: instance of `context_type`.

> ### `TraversalStrategy`

Base class for traversal strategies for walking over ASTs.

 - `__init__(context_type: type)`
    - Args:
        - `context_type (type)`: the type of the subclass of `Context` for which this visitor is intended.
    
    - Raises: `ValueError(f'context_type must be a subclass of {Context}')` if `context_type` is not a subclass of `Context`.

#### Methods

 - `_check_context_type(context)`:
    - Args:
        - `context`: the instance to be validated.
    
    - Raises `TypeError` if `context` is not an instance of `context_type`.
 
 - `init(root)`: initializes the traversal with the root AST.
    - Args:
        - `root`: instance of  subclass of `AST`.

 - `has_next() -> bool`: returns `True` if there is a next AST node to visit. (not implemented, raises `NotImplementedError`).

 - `current(context) -> AST`: returns the current AST node to visit. (not implemented, raises `NotImplementedError`).
    - Args:
        - `context`: instance of `context_type`.

 - `reset()`: resets the traversal. (not implemented, raises `NotImplementedError`).

 - `_get_selector(ast) -> ASTChildrenSelector`: looks up by type; if not found and a default exists, uses it.
    - Args:
        - `ast`: instance of a subclass of `AST`.

 - `add_selector(ast_type:type, selector:ASTChildrenSelector)`: sets the selector for the given type `ast_type`.
    - Args:
        - `ast_type`: subclass of `AST`.
        - `selector`: instance of a subclass of `ASTChildrenSelector`.

    - Raises: `TypeError` if the signature of the 2nd parameter of `selector.select_children` is not annotated or does not match `context_type`.

 - `set_default_selector(selector)`: sets the default selector.
    - Args:
        - `selector`: instance of a subclass of `ASTChildrenSelector`.

    - Raises: analogous to `add_selector`.

> ### `ASTWalker`

Class for an AST walker.

 - `__init__(context, strategy)`
    - Args:
        - `context`: instance of a subclass of `Context`.
        - `strategy`: instance of a subclass of `TraversalStrategy`.

#### Methods

 - `add_visitor(ast_type, visitor)`: sets the visitor for the given type `ast_type`.
    - Args:
        - `ast_type`: subclass of `AST`.
        - `visitor`: instance of a subclass of `ASTVisitor`.
    
    - Raises: `TypeError` if the signature of the 2nd parameter of `visitor.visit` is not annotated or does not match `context_type`.

 - `set_default_visitor(visitor)`: sets the default visitor.
    - Args:
        - `visitor`: instance of a subclass of `ASTVisitor`.
    - Raises: analogous to `add_visitor`.

 - `walk(ast)`: initializes the strategy and iterates until `has_next` is false; for each node it finds the visitor and invokes it. Finally calls `reset` on the strategy.
    - Args:
        - `ast`: instance of a subclass of `AST`.



<!-- source: docs/api-reference/python/api-reference-python-regex.md -->

# Module `regex`

## Submodule `regex.engine`

> ### `RegexParsingException`

Exception raised when a regex can't be parsed. Inherits from `Exception` (`RegexParsingException(Exception)`).

#### Properties

 - `errors (List[RuntimeError])`

> ### `RegexEngine`

Static class.

#### Methods

 - `Parse(re)`: returns the `DFA` equivalent to `re`.
    - Args:
        - `re (str)`
    
    - Raises: `RegexParsingException` if there are runtime errors.

 - `GetAutomaton(g)`: returns the `DFA` equivalent to the language described by `g`.
    - Args:
        - `g (Grammar)`
    
    - Raises: `ValueError('g must be a regular grammar')` if `g` is not a regular grammar.

 - `GetGrammar(automaton)`: returns the grammar equivalent to `automaton`.
    - Args:
        - `automaton (Automaton)`

 - `GetRegex(automaton)`: returns an equivalent regex to `automaton`.
    - Args:
        - `automaton (Automaton)`

 - `BuildRegexParser()`: returns a parser for regex expressions.

 - `BuildRegexLexer()`: returns a lexer for regex expressions.



<!-- source: docs/api-reference/python/api-reference-python-automaton.md -->

# Module `automaton`

## Submodule `automaton.automaton`

> ### `State`

State class for building automatons. This class is inmutable.

 - `__init__(id, value,is_accept=False)`
    - Args:
        
        - `id (str)`: identifier; two states with the same `id` are equal.

        - `value (Any)`: value contained in the state.

        - `is_accept (bool)`: whether it is an accepting state.

#### Properties

 - `id (str)`

 - `value (Any)`

 - `is_accept (bool)`

#### Methods

 - `__str__`: returns `str(value)`.

 - `__repr__`: returns `str(value)`.

 - `__eq__`: equality by `id`.

 - `__hash__`: returns the precomputed hash.

> ### `Automaton`

Base class for automaton definition.

 - `__init__()`:
    - Raises: `ValueError("Can not instance this class")`

#### Properties

 - `id (str)`: deterministic hash of start state, states, transitions and epsilon-transitions.

 - `alphabet (Set[str])`: copy of the alphabet.

 - `start_state (State)`: copy of the start state (deep copy if value is a set).

 - `current_state (State)`: copy of the current state.

 - `states (Set[State])`: copy of states.

 - `finals (Set[State])`: accepting states.

 - `is_complete (bool)`: `True` if every state has defined a transition, `False` otherwise.

 - `transition_function (Dict[Tuple[str,str], str])`: a plain representation of the automaton transition function.

 - `epsilon_transitions (Dict[str, Set[str]])`: a plain representation of the automaton epsilon transitions.

 - `is_empty (bool)`: `True` if the language is empty.

 - `is_finite (bool)`: `True` if the language is finite.

#### Static Methods

 - `Union(automatons)`: returns the `NFA` equivalent to the union between all the automatons provided.
    - Args:
        - `automatons (Set[Automaton])`

 - `Complement(automaton)`: returns the `DFA` of the complement of the given automaton.
    - Args:
        - `automaton (Automaton)`

 - `Intersection(automatons)`: returns the `DFA` equivalent to the intersection between all the automatons provided.
    - Args:
        - `automatons (Set[Automaton])`

 - `Concat(first, second)`: returns the `NFA` equivalent to the concatenation of `first` followed by `second`.
    - Args:
        - `first (Automaton)`
        - `second (Automaton)`

 - `KleeneStar(automaton)`: returns the `NFA` equivalent to $L^{*}$, where $L$ is the language of `automaton`.
    - Args:
        - `automaton (Automaton)`

 - `PositiveClosure(automaton)`: returns the `NFA` equivalent to $L$+, where $L$ is the language of `automaton`.
    - Args:
        - `automaton (Automaton)`

 - `Optional(automaton)`: returns the `NFA` equivalent to $L$?, where $L$ is the language of `automaton`.
    - Args:
        - `automaton (Automaton)`

 - `Reverse(automaton)`: returns the `NFA` equivalent to the given automaton with all its transitions inverted.
    - Args:
        - `automaton (Automaton)`

#### Methods

 - `add_transition(from_state, to_state, symbol)`: adds a transition. (Automatically updates the `states` and `is_complete` properties of the current automaton).

    - Args:
        - `from_state (State)`: origin state.
        - `to_state (State)`: destination state.
        - `symbol (str)`: symbol that triggers the transitions.

    - Raises: `ValueError` if `symbol` is not in the alphabet.
  
  - `has_transition(state, symbol)`: returns `True` if the transition `(state, symbol)` exists.
    - Args:
        - `state (State)`: origin state.
        - `symbol (str)`

 - `next(state, symbol)`: returns the destination state for the given transition `(state,symbol)`.
    - Args:
        - `state (State)`: origin state.
        - `symbol (str)`

    - Raises: `KeyError` if there is no transition.

 - `reset()`: resets the automaton to its initial state before any internal change that has been done.

 - `closure(state)`: returns the set of states corresponding to the epsilon-closure of `state`.
    - Args:
        - `state (State)`

 - `make_complete()`: adds all missing transitions to a fault state.

 - `restore_to_before_complete()`: removes the fault state and added transitions.

 - `extend_alphabet(symbols)`: expands the current alphabet with the new set of symbols.
    - Args:
        - `symbols (Set[str])`

#### Operators

 - `__or__`(`|`): union, `aut1 | aut2` is equivalent to `Automaton.Union({aut1,aut2})`.
 - `__and__`(`&`): intersection, `aut1 & aut2` is equivalent to `Automaton.Intersection({aut1,aut2})`.
 - `__add__`(`+`): concatenation, `aut1 + aut2` is equivalent to `Automaton.Concat(aut1,aut2)`.

> ### `DFA`

Class for a ***Deterministic Finite Automata***. Inherits from `Automaton` (`DFA(Automaton)`).

 - `__init__(start_id, start_value, alphabet, start_accept=False)`
    - Args:
        - `start_id (str)`: id of the start state.
        - `start_value (Any)`: value of the start state.
        - `alphabet (Set[str])`: alphabet of the automaton.
        - `start_accept (bool)`: if `True`, the start state is an accepting state.

#### Methods

 - `walk(symbol)`: advances if not stuck; if no transition, marks `_is_stuck` internal flag as `True`.
    - Args:
        - `symbol (str)`

 - `accept(string)`: `True` if the automaton ends in an accepting state after reading the entire string. Calls `reset` at the end.
    - Args:
        - `string (List[str])`

 - `minimize(initial_partition = [])`: returns the equivalent minimized `DFA` (Hopcroft's algorithm).
    - Args:
        - `initial_partition (List[Set[State]])`: initial partition.

#### Operators

 - `__iadd__(transition)`: adds a transition via the `+=` operator.
    - Args:
        - `transition (Tuple[State,str,State])`: has the form `(from_state,symbol,to_state)`, where `from_state` is the origin state, `to_state` is the destination state, and `symbol` is the trigger of the transition.

> ### `NFA`

Class for our [Hybrid $\epsilon$-DFA](../../formal-foundations/formal-foundations-automata.md#the-hybrid-epsilon-dfa-a-deterministic-core-with-spontaneous-moves). Inherits from `Automaton` (`NFA(Automaton)`).

 - `__init__(start_id, start_value, alphabet, start_accept=False)`
    - Args:
        - `start_id (str)`: id of the start state.
        - `start_value (Any)`: value of the start state.
        - `alphabte (Set[str])`: alphabet of the automaton.
        - `start_accept (bool)`: if `True`, the start state is an accepting state.

#### Methods

 - `add_epsilon_transition(from_state, to_state)`: adds an epsilon-transition. (Automatically updates the `states` property of the current automaton).
    - Args:
        - `from_state (State)`: origin state.
        - `to_state (State)`: destination state.

 - `to_deterministic()`: returns the equivalent `DFA` (subset construction with epsilon-closure).

#### Operators

 - `__iadd__(transition)`: adds a transition via the `+=` operator.
    - Args:
        - `transition (Tuple[State,str,State])`: has the form `(from_state,symbol,to_state)`, where `from_state` is the origin state, `to_state` is the destination state, and `symbol` is the trigger of the transition.

> ### Module functions

 - `create_dfa(states, transition_function, start_id, alphabet)`: creates a `DFA` from the given states, alphabet and transitions.
    - Args:
        - `states (Set[State])`: states of the automaton.
        - `transition_function (Table)`: the transition function in a tabular form.
        - `start_id (str)`: id of the start state.
        - `alphabet (Set[str])`: alphabet of the automaton.
    
    - Raises: `ValueError(f'A initial state is needed, not found any state with given id {start_id}')` if none of `states` has the id `start_id`.

 - `create_nfa(states, transition_function, epsilon_transitions, start_id, alphabet)`: creates an `NFA` from the given states, alphabet, transitions and epsilon transitions.
    - Args:
        - `states (Set[State])`: states of the automaton.
        - `transition_function (Table)`: the transition function in a tabular form.
        - `epsilon_transitions (Dict[str,Set[str]])`: the epsilon transitions.
        - `start_id (str)`: id of the start state.
        - `alphabet (Set[str])`: alphabet of the automaton.

    - Raises: `ValueError(f'A initial state is needed, not found any state with given id {start_id}')` if none of `states` has the id `start_id`.

 - `get_word_automaton(word)`: returns a `DFA` that accepts only `word`.
    - Args:
        - `word (str)`

 - `get_words_automaton(words)`: returns an `NFA` that accepts only the given words (union of DFAs).
    - Args:
        - `words (List[str])`

 - `get_word_automaton_with_value(word, value, only_finals=False)`: analogous to `get_word_automaton`.
    - Args:
        - `word (str)`
        - `value (Any)`: value to assign to states.
        - `only_finals (bool)`: if `True`, `value` is assigned only to accepting states.

 - `get_words_automaton_with_value(words, value, only_finals=False)`: analogous to `get_words_automaton`.
    - Args:
        - `words (List[str])`
        - `value (Any)`: value to assign to states.
        - `only_finals (bool)`: if `True`, `value` is assigned only to accepting states.



<!-- source: docs/api-reference/python/api-reference-python-visual.md -->

# Module `visual`

## Main Submodule (`__init__.py`)

> ### Public Functions

 - `draw_automaton(automaton, **kwargs)`: creates an interactive graph in a html file.
    - Args:
        - `automaton (Automaton)`
        - `**kwargs`
            - `filename (str)`: name of the html file that will be generated.
            - `show (bool)`: if `True`, the generated file is opened in the browser.
            - `cache (bool)`: if `True`, the external links in the file are embeded.
            - `physics (bool)`: `pyvis` option (controls physics).
            - `select_menu (bool)`: `pyvis` option (enables the select menu).
            - `filter_menu (bool)`: `pyvis` option (enables the filter menu).
            - `nodes (bool)`: `pyvis` option (enables nodes options menu).
            - `edges (bool)`: `pyvis` option (enables edges options menu).
            - `as_tree (bool)`: `pyvis` option (sets a tree layout).

    - Raises: `ValueError` for each kwarg with incorrect type or if `cache=True` without `CACHE_FILE`.

 - `draw_lexer(lexer, **kwargs)`: delegates to `draw_automaton(lexer.dfa, ...)`, `**kwargs` argument is analogous to `draw_automaton`.

 - `draw_ast(ast, **kwargs)`: creates an interactive graph in a html file,`**kwargs` argument is analogous to `draw_automaton`.
    - Args:
        - `ast (AST)`
    
    - Raises: `ValueError` for each kwarg with incorrect type or if `cache=True` without `CACHE_FILE`.

 - `draw_parse_tree(tree, **kwargs)`: creates an interactive graph in a html file,`**kwargs` argument is analogous to `draw_automaton`.
    - Args:
        `tree (ParseTreeNode)`

    - Raises: `ValueError` for each kwarg with incorrect type or if `cache=True` without `CACHE_FILE`.

 - `show_propagation_edges_table(g, **kwargs)`: creates an interactive graph in a html file, with the info of the propagation edges for a LALR(1) parser building.
    - Args:
        - `g (Grammar)`
        - `**kwargs`:
            - `filename (str)`
            - `show (bool)`
            - `cache (bool)`
    
    - Raises: `ValueError` for each kwarg with incorrect type or if `cache=True` without `CACHE_FILE`.

 - `lr_inspect_grammar(g, type_=ParserType.LALR1, **kwargs)`: creates an interactive graph in a html file, exploring the grammar. Returns `True` if any conflict is found.
    - Args:
        - `g (Grammar)`
        - `**kwargs`:
            - `filename (str)`
            - `show (bool)`
            - `cache (bool)`
            - `report (bool)`: when `True`, generates a html file with the info.

    - Raises: `ValueError` for each kwarg with incorrect type or if `cache=True` without `CACHE_FILE`, or `show=True` and `report=False`.

 - `set_cache_file(filename)`: Sets the global cache file.
    - Args:
        - `filename (str)`

    - Raises: `ValueError` if `filename` is empty.

> **WARNING**
if `filename` exists, it will be overwritten.

## Submodule `visual.table`

> ### HTML templates (compressed with **`LZMA`**) used to generate reports:

 - `propagation_edges_template`
 - `propagation_edges_row_template`
 - `state_details_template`
 - `goto_action_tables_template`

> ### Functions

 - `build_propagation_edges_table(g)`: builds the html table of lookahead propagation edges.
    - Args:
        - `g (Grammar)`

 - `build_action_goto_html_tables(g, type_)`: returns a tuple `(HTML content,flag)`. Delegates on `build_action_goto_lalr_tables`, `build_action_goto_slr_tables` and `build_action_goto_lr1_tables`, depending on `type_`.
    - Args:
        - `g (Grammar)`
        - `type_ (ParserType)`
    - Raises: `NotImplementedError` for unsupported types.
