# Tutorial — VecLang (Cython-accelerated language)



<!-- source: docs/tutorials/complete-languages/veclang/veclang-intro.md -->

# From Prototype to Production (The power of **Cython**)

**VecLang** is the final tutorial in this section. By now, you've built a complete interpreter for a small arithmetic language, a configuration DSL, and a subset of Python. Each one taught you something new about the pipeline. But there's one question you haven't answered yet: ***how fast is your interpreter?*** And more importantly, ***how fast could it be*** if you needed to handle real-world workloads?

This tutorial is about that question. It's where **PyLGEN's dual nature** shines: you start in pure Python, **prototyping quickly** and **debugging easily**. Then, when performance becomes critical, you **compile your code with Cython** and turn your interpreter into a **high-performance engine**, with only a few changes to the source.

You'll meet VecLang, a feature-rich language with vectors, complex numbers, functions, and slicing. You'll see how to build it step by step, and how to compile it to native code. By the end, you'll know not just how to build a language, but how to make it fast.

> **NOTE: The price to pay**
Although Cython's syntax requires type declarations and additional `.pxd` files, the core logic (the Visitor pattern and the AST structure) remains identical to that of the pure Python tutorial. The verbosity is the price to pay for native performance.

In this section, we'll take a realistic, feature-rich language called **VecLang**, run it through a massive benchmark, and compare PyLGEN against a popular alternative ([***Lark***](https://lark-parser.readthedocs.io/en/stable/)). You'll see exactly how much speed you can gain, and learn how to compile your own projects to production.

We'll follow the same step-by-step approach as the previous tutorials: explore each file, explain every decision, and see the code in action.

Let's dive into VecLang and see how to compile it with **Cython**.



<!-- source: docs/tutorials/complete-languages/veclang/getting-to-know-veclang.md -->

# Getting to know VecLang (A Test Language)

To stress-test an interpreter, you need a language that exercises all stages of the pipeline: lexing, parsing, semantic analysis, and evaluation. **VecLang** is exactly that, a small but expressive DSL that supports:

 - Complex numbers (`complex(2,3)` and `1 + 2j`).
 - Function definitions and calls.
 - Arithmetic with `+`,`-`,`*`,`/`,`**`,`%`.
 - Vector literals (`[1,4.5,var]`) and range generation (`[4:10]`).
 - Indexing (`vec[2]`) and multi-level slicing (`[0:30][5:25][10:15]`).
 - Built-in functions: `sum`, `mean`, `dot`, `print`.

**VecLang** is expressive enough to write non-trivial programs, yet simple enough to implement in a few hundred lines. It's the perfect testbed for benchmarking because it forces the interpreter to exercise **every stage** of the pipeline: lexing, parsing, semantic validation, and evaluation.

## Why VecLang is a Good Benchmark Language

Before diving into the code, let's examine why VecLang is an excellent choice for measuring performance:

 - **Diverse Syntax**: It includes many token types (numbers, operators, keywords, identifiers,symbols like `[` and `]`, etc.).
 - **Rich Grammar**: Operator precedence, function definitions, vector literals, and slicing require a non-trivial LALR(1) grammar with many productions. This tests the parser's efficiency.
 - **Multiple AST Node Types**: The parser builds many different AST classes (binary ops, function calls, vector literals, indexing, slicing, etc.). This forces the reducer functions to work with diverse structures.
 - **Semantic Checks**: function argument count, and variable declaration validation stress the visitor pattern.
 - **Heavy Evaluation**: Vectors and operations on them (element-wise arithmetic, dot product, mean) involve loops and array operations, which are computationally intensive and test the evaluator.
 - **Realistic code size**: The benchmark file (**~2 million lines**) simulates a production-scale input, revealing performance bottlenecks that only appear under load.
 - **Complete pipeline**: Unlike parser-only tools, VecLang includes the entire interpreter cycle, making it a realistic measure of end-to-end performance.

Example code in VecLang:
```txt
// testing complex numbers creation
complex_number = complex(2,3)
complex_number_b = 1 + 3j

// testing function declarations
f(x:complex,y:float) = x / (y - 5)

// testing functions call
var_a = f(complex_number,10)

// more functions declarations
g(x:int,y:int) = x ** y / 10 - 100

// more functions calls
var_b = g(20,4)

// arithmetic operations
var_c = (var_a + var_b) / (var_a - var_b)

// combining calls and operations
var_d = g(50,4) % 7

// testing vectors
vector_1 = [1,4.5,complex_number,var_b]
vector_2 = vector_1 / 5

// testing range
vector_3 = [4:10]

// testing indexing
var_e = vector_1[1]
var_f = vector_2[2]
var_g = vector_3[3]

var_slice = vector_3[1:3]
var_slice_1 = var_slice[0:1]

// testing multiple slicing
var_slice_2 = [0:30][5:25][10:15]

// testing built-in functions
print(var_slice_2)
print(vector_1)
print(vector_2)
print(vector_3)

var_sum = sum(vector_1)
var_mean = mean(vector_3)
var_dot = dot(vector_1,vector_2)

print(var_sum)
print(var_mean)
print(var_dot)
```

With these points in mind, let's start building VecLang from scratch.



<!-- source: docs/tutorials/complete-languages/veclang/veclang-step-1.md -->

# Step 1: Project Structure and Lexer

Create a new project folder `veclang/` with the following files:

    veclang/
        asts.pxd
        asts.pyx
        errors.pxd
        errors.pyx
        lexer.pxd
        lexer.pyi
        lexer.pyx
        parser.pxd
        parser.pyi
        parser.pyx
        setup.py
        tokens_enum.py
        visitors.pxd
        visitors.pyi
        visitors.pyx

We'll write each file step by step.

> **NOTE: Source code**

The source code of the test language **VecLang** can be found on the [github repository](https://github.com/YonyUk/pylgen/tree/master/examples/veclang)

[download source code<br>(veclang)](https://download-directory.github.io/?url=https://github.com/YonyUk/pylgen/tree/master/examples/veclang){ .md-button .md-button--primary style="text-align: center;" }

## 1.1 Token Types (`tokens_enum.py`)

We define our token types using PyLGEN's `TokenType` base class:

File: `tokens_enum.py`
```python
from pylgen.common.enums import TokenType

class TokenTypeEnum(TokenType):

    INTEGER = 'INTEGER'
    FLOAT = 'FLOAT'
    SYMBOL = 'SYMBOL'
    OPERATOR = 'OPERATOR'
    KEYWORD = 'KEYWORD'
    VARIABLE = 'VARIABLE'
    JUMPLINE = 'JUMPLINE'
    COMMENT = 'COMMENT'
    EOF = 'EOF'
```

## 1.2 The Lexer (`lexer.pxd`,`lexer.pyx`,`lexer.pyi`)

Now we build the lexer. It's similar to the arithmetic example, but we add more token patterns.

> **TIP: Good practices**
This structure is typical for projects that leverage **Cython** to compile the interpreter into a high-performance extension:

- **`.pxd` files**: contain **C-level** declarations that expose functions and variables to other Cython modules.
- **`.pyx` files**: hold the actual implementation (the code that gets compiled).
- **`.pyi` files**: provide Python type stubs for static type checkers (e.g., mypy) and better IDE support.

Separating interface from implementation like this keeps the codebase modular and makes compilation faster, both critical when scaling to production workloads. 

> ### Declaration (`lexer.pxd`)

This file tells Cython what functions are available to other modules.

File: `lexer.pxd`
```cython
from pylgen.lexer.lexer cimport Lexer
from pylgen.common.types cimport Symbol

cpdef Lexer build_lexer()

cdef Symbol get_symbol_function(object t,str tx)
```

> ### Implementation (`lexer.pyx`)

Here we define the actual logic. One key design choice for performance is to **predefine every grammar symbol** as a `cdef` variable, rather than creating them on the fly. This eliminates object allocation overhead in the tokenization hot path, a crucial optimization when processing millions of lines.

File: `lexer.pyx`
```cython
from pylgen.lexer.lexer cimport Lexer
from pylgen.common.types cimport Symbol
from .tokens_enum import TokenTypeEnum

cdef Symbol new_line = Symbol('new_line',True) # type:ignore
cdef Symbol int_number = Symbol('integer',True) # type:ignore
cdef Symbol float_number = Symbol('float',True) # type:ignore
cdef Symbol variable = Symbol('variable',True) # type:ignore
cdef Symbol plus = Symbol('+',True) # type:ignore
cdef Symbol minus = Symbol('-',True) # type:ignore
cdef Symbol mod = Symbol('%',True) # type:ignore
cdef Symbol div = Symbol('/',True) # type:ignore
cdef Symbol mul = Symbol('*',True) # type:ignore
cdef Symbol exp = Symbol('**',True) # type:ignore
cdef Symbol eq = Symbol('=',True) # type:ignore
cdef Symbol lp = Symbol('(',True) # type:ignore
cdef Symbol rp = Symbol(')',True) # type:ignore
cdef Symbol lc = Symbol('[',True) # type:ignore
cdef Symbol rc = Symbol(']',True) # type:ignore
cdef Symbol com = Symbol(',',True) # type:ignore
cdef Symbol double_dot = Symbol(':',True) # type:ignore
cdef Symbol sum_keyword = Symbol('sum_keyword',True) # type:ignore
cdef Symbol mean_keyword = Symbol('mean_keyword',True) # type:ignore
cdef Symbol dot_keyword = Symbol('dot_keyword',True) # type:ignore
cdef Symbol print_keyword = Symbol('print_keyword',True) # type:ignore
cdef Symbol type_int = Symbol('int_keyword',True) # type:ignore
cdef Symbol type_float = Symbol('float_keyword',True) # type:ignore
cdef Symbol type_complex = Symbol('complex_keyword',True) # type:ignore
cdef Symbol type_vector = Symbol('vector_keyword',True) # type:ignore
cdef Symbol invalid = Symbol('INVALID TOKEN',True) # type:ignore

cdef Symbol comment = Symbol('COMMENT',True) # type:ignore

cdef dict[str,Symbol] _symbols = {
    '[':lc,
    ']':rc,
    '(':lp,
    ')':rp,
    ',':com,
    ':':double_dot
}

cdef dict[str,Symbol] _operators = {
    '+':plus,
    '-':minus,
    '*':mul,
    '**':exp,
    '/':div,
    '%':mod,
    '=':eq
}

cdef dict[str,Symbol] _keywords = {
    'sum':sum_keyword,
    'mean':mean_keyword,
    'dot':dot_keyword,
    'print':print_keyword,
    'int':type_int,
    'float':type_float,
    'complex':type_complex,
    'vector':type_vector
}

cdef Symbol get_symbol_function(object t,str tx):
    if t == TokenTypeEnum.INTEGER:
        return int_number
    if t == TokenTypeEnum.FLOAT:
        return float_number
    if t == TokenTypeEnum.JUMPLINE:
        return new_line
    if t == TokenTypeEnum.VARIABLE:
        return variable
    if t == TokenTypeEnum.OPERATOR:
        return _operators[tx]
    if t == TokenTypeEnum.SYMBOL:
        return _symbols[tx]
    if t == TokenTypeEnum.KEYWORD:
        return _keywords[tx]
    if t == TokenTypeEnum.COMMENT:
        return comment
    if t == TokenTypeEnum.INVALID_TOKEN:
        return invalid
    raise NotImplementedError()

cpdef Lexer build_lexer():
    lexer = Lexer(get_symbol_function,'\t| |//.*\n',False) # type:ignore
    lexer._enum_type = TokenTypeEnum
    lexer.set_eof_token('\x00',TokenTypeEnum.EOF)
    lexer.add_token_regex(0,TokenTypeEnum.INTEGER,r'\d+')
    lexer.add_token_regex(1,TokenTypeEnum.FLOAT,r'\d*\.\d+|\d+e(\+|\-)\d+')
    lexer.add_token_regex(2,TokenTypeEnum.JUMPLINE,'\n')
    lexer.add_token_regex(3,TokenTypeEnum.KEYWORD,'sum|mean|dot|print|int|float|complex|vector')
    lexer.add_token_regex(4,TokenTypeEnum.VARIABLE,r'[a-zA-Z_]\w*')
    lexer.add_token_regex(5,TokenTypeEnum.OPERATOR,r'\+|\-|/|\*\*?|%|=')
    lexer.add_token_regex(6,TokenTypeEnum.SYMBOL,r'\[|\]|:|\(|\)|\,')
    lexer.add_token_regex(7,TokenTypeEnum.COMMENT,'//.*\n')
    return lexer
```

> **WARNING**
In the previous tutorials, during the lexer definition, the mapping function was written in Python. This allowed the lexer to infer the type of the enum used for tokens from its typing. However, in this case, the mapping function is written in Cython, so the enum type cannot be inferred. This is the reason for the line `lexer._enum_type = TokenTypeEnum`.

> **TIP: The `COMMENT` safety net**
You'll notice in the next section that the `comment` symbol is defined but never appears in the grammar. This is intentional. We already strip comments using the skip pattern `'\t| |//.*\n'`. However, if that pattern ever fails (e.g., due to a mistake or an edge case), the lexer will produce a **`COMMENT`** token. Since this symbol is absent from the grammar, the parser will raise a clear error immediately, alerting us to the issue before it silently corrupts the AST. It's a proactive debugging aid.

> ### Stubs for static typing (`lexer.pyi`)

This file provides type hints for Python consumers of the module.

File: `lexer.pyi`
```python
from pylgen.lexer.lexer import Lexer

def build_lexer() -> Lexer: ...
```



<!-- source: docs/tutorials/complete-languages/veclang/veclang-step-2.md -->

# Step 2: Building the Parser and AST

VecLang's grammar is richer than the arithmetic language we saw earlier: it includes vectors, ranges, slicing, indexing, function definitions, and complex numbers. Our parser must handle all these features efficiently, which is why we'll use **Cython** to compile the parser and its reductors into fast, native code.

## Grammar Symbols: Terminals and Non-terminals

In the Cython‑based implementation, all symbols are defined as `cdef Symbol` variables, both in the declaration file (`asts.pxd`) and the implementation file (`asts.pyx`). This ensures they are available at compile time and reduces overhead.

These are the symbols that map directly to token types. They were already defined in the lexer, but we need to declare them as `cdef` so the parser can recognise them.

> **IMPORTANT**
The symbols returned by the mapping function must perfectly match those used in the grammar, and follow the same token-symbol correspondence.

File: `asts.pxd`
```cython
from pylgen.common.types cimport AST,Symbol,ASTListView,Token,ErrorAST

# NON-TERMINALS
cdef Symbol VecLangProgram
cdef Symbol VecLangInstruction
cdef Symbol VecLangInstructionsSequence
cdef Symbol ArithmeticExpressionLevel1
cdef Symbol ArithmeticExpressionLevel2
cdef Symbol ArithmeticExpressionLevel3
cdef Symbol ArithmeticExpressionLevel4
cdef Symbol Number
cdef Symbol ComplexNumber
cdef Symbol NumberExpression
cdef Symbol VariableExpression
cdef Symbol VoidInstruction
cdef Symbol Components
cdef Symbol Vector
cdef Symbol Range
cdef Symbol Indexing
cdef Symbol Slicing
cdef Symbol FunctionCall
cdef Symbol FunctionArgs
cdef Symbol FunctionDecl
cdef Symbol FunctionDeclArgs
cdef Symbol Type

# TERMINALS
cdef Symbol new_line
cdef Symbol int_number
cdef Symbol float_number
cdef Symbol variable
cdef Symbol plus
cdef Symbol minus
cdef Symbol mod
cdef Symbol div
cdef Symbol mul
cdef Symbol exp
cdef Symbol eq
cdef Symbol lp
cdef Symbol rp
cdef Symbol lc
cdef Symbol rc
cdef Symbol com
cdef Symbol double_dot
cdef Symbol sum_keyword
cdef Symbol mean_keyword
cdef Symbol dot_keyword
cdef Symbol print_keyword
cdef Symbol type_int
cdef Symbol type_float
cdef Symbol type_complex
cdef Symbol type_vector
```

## Designing the Abstract Syntax Tree (AST)

In VecLang, we have many node types. To keep the code maintainable, we use a class hierarchy:

 - A base `AST` class (provided by PyLGEN) provides common attributes like `_start_line`, `_start_column`, `_end_line`, `_end_column` and a `children()` method.

 - `BinaryAST` is an abstract base for all binary operations (addition, subtraction, multiplication, division, modulo, exponentiation, and assignment). It stores `left` and `right` children.

 - Specific binary operation classes (`PlusAST`, `MinusAST`, etc.) inherit from `BinaryAST` and simply forward the operator symbol.

 - Other nodes are domain‑specific: `NumberAST` (for integers, floats, and complex numbers), `VariableExpressionAST`, `VectorAST`, `RangeAST`, `IndexingAST`, `SlicingAST`, `FunctionCallAST`, `FunctionDeclAST`, `FunctionDeclArgsAST`, `TypeAST`, and several for sequences and instructions.

All AST classes are defined as `cdef class` in `asts.pxd` to allow fast attribute access in Cython, and implemented in `asts.pyx`.

### Specialised Nodes

For brevity, we'll highlight a few others:

 - `VectorAST`: holds a `VectorComponentsAST` that contains a list of component ASTs.

 - `RangeAST`: stores `min` and `max` integers (used in vector literals like `[4:10]` and in slicing).

 - `SlicingAST`: combines a target (a variable or vector) with a `RangeAST`.

 - `FunctionCallAST`: stores the function name and a `FunctionArgsAST` (a list of argument ASTs).

 - `FunctionDeclAST`: stores the function name, its arguments (with types), and the body AST.

 - `TypeAST`: holds a type name (int, float, complex, vector).

### Reductors

Reducer functions are also defined and implemented here, so they can be used from other files. We'll explain them later; for now, let's just leave them there.

### Recap

Finally, this is how the files look:

File `asts.pxd`
```cython
from pylgen.common.types cimport AST,Symbol,ASTListView,Token,ErrorAST

# NON-TERMINALS
cdef Symbol VecLangProgram
cdef Symbol VecLangInstruction
cdef Symbol VecLangInstructionsSequence
cdef Symbol ArithmeticExpressionLevel1
cdef Symbol ArithmeticExpressionLevel2
cdef Symbol ArithmeticExpressionLevel3
cdef Symbol ArithmeticExpressionLevel4
cdef Symbol Number
cdef Symbol ComplexNumber
cdef Symbol NumberExpression
cdef Symbol VariableExpression
cdef Symbol VoidInstruction
cdef Symbol Components
cdef Symbol Vector
cdef Symbol Range
cdef Symbol Indexing
cdef Symbol Slicing
cdef Symbol FunctionCall
cdef Symbol FunctionArgs
cdef Symbol FunctionDecl
cdef Symbol FunctionDeclArgs
cdef Symbol Type

# TERMINALS
cdef Symbol new_line
cdef Symbol int_number
cdef Symbol float_number
cdef Symbol variable
cdef Symbol plus
cdef Symbol minus
cdef Symbol mod
cdef Symbol div
cdef Symbol mul
cdef Symbol exp
cdef Symbol eq
cdef Symbol lp
cdef Symbol rp
cdef Symbol lc
cdef Symbol rc
cdef Symbol com
cdef Symbol double_dot
cdef Symbol sum_keyword
cdef Symbol mean_keyword
cdef Symbol dot_keyword
cdef Symbol print_keyword
cdef Symbol type_int
cdef Symbol type_float
cdef Symbol type_complex
cdef Symbol type_vector

cdef class TypeAST(AST):
    cdef str _type
    cdef list[AST] _childs

cdef class FunctionDeclArgsAST(AST):
    cdef dict[VariableExpressionAST,str] _args
    cdef list[AST] _childs

cdef class FunctionDeclAST(AST):
    cdef AST _body
    cdef FunctionDeclArgsAST _args
    cdef str _name
    cdef list[AST] _childs

cdef class FunctionArgsAST(AST):
    cdef list[AST] _args

cdef class FunctionCallAST(AST):
    cdef FunctionArgsAST _args
    cdef str _function_name
    cdef list[AST] _childs

cdef class SlicingAST(AST):
    cdef AST _target
    cdef RangeAST _range
    cdef list[AST] _childs

cdef class IndexingAST(AST):
    cdef AST _target
    cdef int _index
    cdef list[AST] _childs

cdef class RangeAST(AST):
    cdef int _min
    cdef int _max
    cdef list[AST] _childs

cdef class VectorAST(AST):
    cdef VectorComponentsAST _components
    cdef list[AST] _childs

cdef class VectorComponentsAST(AST):
    cdef list[AST] _components

cdef class VoidInstructionAST(AST):
    cdef list[AST] _childs

cdef class VariableExpressionAST(AST):
    cdef str _name
    cdef int _index
    cdef list[AST] _childs

cdef class VecLangInstructionsSequenceAST(AST):
    cdef list[AST] _instructions

cdef class NumberAST(AST):
    cdef type _type # type:ignore
    cdef str _value
    cdef list[AST] _childs

cdef class BinaryAST(AST):
    cdef AST _left
    cdef AST _right
    cdef list[AST] _childs

cdef class PlusAST(BinaryAST):
    pass

cdef class MinusAST(BinaryAST):
    pass

cdef class MulAST(BinaryAST):
    pass

cdef class DivAST(BinaryAST):
    pass

cdef class DivisionByZeroErrorAST(ErrorAST):
    cdef AST _left
    cdef AST _right

cdef class ModuleErrorAST(ErrorAST):
    cdef AST _left
    cdef AST _right

cdef class ValueTooLargeForIntegerErrorAST(ErrorAST):
    cdef str _text

cdef class RangeErrorAST(ErrorAST):
    pass

cdef class ComplexNumberErrorAST(ErrorAST):
    cdef NumberAST _coef
    cdef Token _variable

cdef class ModAST(BinaryAST):
    pass

cdef class ExpAST(BinaryAST):
    pass

cdef class AssignmentAST(BinaryAST):
    pass

cdef AST single_reductor(ASTListView asts)

cdef AST plus_reductor(ASTListView asts)

cdef AST minus_reductor(ASTListView asts)

cdef AST mul_reductor(ASTListView asts)

cdef AST div_reductor(ASTListView asts)

cdef AST mod_reductor(ASTListView asts)

cdef AST exp_reductor(ASTListView asts)

cdef AST assignment_reductor(ASTListView asts)

cdef AST extractor_reductor(ASTListView asts)

cdef AST instructions_sequence_reductor(ASTListView asts)

cdef AST number_reductor(ASTListView asts)

cdef AST void_reductor(ASTListView asts)

cdef AST variable_reductor(ASTListView asts)

cdef AST complex_number_reductor(ASTListView asts)

cdef AST complex_number_reductor_1(ASTListView asts)

cdef AST vector_reductor(ASTListView asts)

cdef AST vector_components_reductor(ASTListView asts)

cdef AST range_reductor(ASTListView asts)

cdef AST range_reductor_1(ASTListView asts)

cdef AST range_reductor_2(ASTListView asts)

cdef AST range_reductor_3(ASTListView asts)

cdef AST indexing_reductor(ASTListView asts)

cdef AST slicing_reductor(ASTListView asts)

cdef AST function_call_reductor(ASTListView asts)

cdef AST function_args_reductor(ASTListView asts)

cdef AST built_in_function_call_reductor(ASTListView asts)

cdef AST function_declare_reductor(ASTListView asts)

cdef AST function_declare_args_reductor(ASTListView asts)

cdef AST type_reductor(ASTListView asts)
```

File: `asts.pyx`
```cython
from pylgen.common.types cimport AST,Symbol,Token,ASTListView,ErrorAST,Error,SemanticError

from .tokens_enum import TokenTypeEnum

import numpy as np # type:ignore

# NON-TERMINALS
cdef Symbol VecLangProgram = Symbol('VecLangProgram') # type:ignore
cdef Symbol VecLangInstruction = Symbol('VecLangInstruction') # type:ignore
cdef Symbol VecLangInstructionsSequence = Symbol('VecLangInstructionSequence') # type:ignore
cdef Symbol ArithmeticExpressionLevel1 = Symbol('ArithmeticExpressionLevel1') # type:ignore
cdef Symbol ArithmeticExpressionLevel2 = Symbol('ArithmeticExpressionLevel2') # type:ignore
cdef Symbol ArithmeticExpressionLevel3 = Symbol('ArithmeticExpressionLevel3') # type:ignore
cdef Symbol ArithmeticExpressionLevel4 = Symbol('ArithmeticExpressionLevel4') # type:ignore
cdef Symbol Number = Symbol('Number') # type:ignore
cdef Symbol ComplexNumber = Symbol('ComplexNumber') # type:ignore
cdef Symbol NumberExpression = Symbol('NumberExpression') # type:ignore
cdef Symbol VariableExpression = Symbol('VariableExpression') # type:ignore
cdef Symbol VoidInstruction = Symbol('VoidInstruction') # type:ignore
cdef Symbol Components = Symbol('Components') # type:ignore
cdef Symbol Vector = Symbol('Vector') # type:ignore
cdef Symbol Range = Symbol('Range') # type:ignore
cdef Symbol Indexing = Symbol('Indexing') # type:ignore
cdef Symbol Slicing = Symbol('Slicing') # type:ignore
cdef Symbol FunctionCall = Symbol('FunctionCall') # type:ignore
cdef Symbol FunctionArgs = Symbol('FunctionArgs') # type:ignore
cdef Symbol FunctionDecl = Symbol('FunctionDecl') # type:ignore
cdef Symbol FunctionDeclArgs = Symbol('FunctionDeclArgs') # type:ignore
cdef Symbol Type = Symbol('Type') # type:ignore

# TERMINALS
cdef Symbol new_line = Symbol('new_line',True) # type:ignore
cdef Symbol int_number = Symbol('integer',True) # type:ignore
cdef Symbol float_number = Symbol('float',True) # type:ignore
cdef Symbol variable = Symbol('variable',True) # type:ignore
cdef Symbol plus = Symbol('+',True) # type:ignore
cdef Symbol minus = Symbol('-',True) # type:ignore
cdef Symbol mod = Symbol('%',True) # type:ignore
cdef Symbol div = Symbol('/',True) # type:ignore
cdef Symbol mul = Symbol('*',True) # type:ignore
cdef Symbol exp = Symbol('**',True) # type:ignore
cdef Symbol eq = Symbol('=',True) # type:ignore
cdef Symbol lp = Symbol('(',True) # type:ignore
cdef Symbol rp = Symbol(')',True) # type:ignore
cdef Symbol lc = Symbol('[',True) # type:ignore
cdef Symbol rc = Symbol(']',True) # type:ignore
cdef Symbol com = Symbol(',',True) # type:ignore
cdef Symbol double_dot = Symbol(':',True) # type:ignore
cdef Symbol sum_keyword = Symbol('sum_keyword',True) # type:ignore
cdef Symbol mean_keyword = Symbol('mean_keyword',True) # type:ignore
cdef Symbol dot_keyword = Symbol('dot_keyword',True) # type:ignore
cdef Symbol print_keyword = Symbol('print_keyword',True) # type:ignore
cdef Symbol type_int = Symbol('int_keyword',True) # type:ignore
cdef Symbol type_float = Symbol('float_keyword',True) # type:ignore
cdef Symbol type_complex = Symbol('complex_keyword',True) # type:ignore
cdef Symbol type_vector = Symbol('vector_keyword',True) # type:ignore

cdef Symbol div_error = Symbol('Division Error')
cdef Symbol mod_error = Symbol('Module Error')
cdef Symbol int_too_large_error = Symbol('Integer Too Large Error')
cdef Symbol range_error = Symbol('Range Error')
cdef Symbol complex_error = Symbol('Complex Error')

cdef class TypeAST(AST):

    def __init__(self, str type_name, int line, int column):
        super().__init__(Type, line, column,line,column + len(type_name)) # type:ignore
        self._type = type_name
        self._childs = []
    
    @property
    def type_name(self) -> str:
        return self._type
    
    cpdef list[AST] children(self):
        return self._childs

cdef class FunctionDeclArgsAST(AST):

    def __init__(self, dict[VariableExpressionAST,str] args, int start_line, int start_column, int end_line, int end_column):
        super().__init__(FunctionDeclArgs, start_line,start_column,end_line,end_column)
        self._args = args
        self._childs = list(args.keys())
    
    @property
    def type_vars(self) -> dict[VariableExpressionAST,str]:
        return self._args.copy()
    
    cpdef list[AST] children(self):
        return self._childs

cdef class FunctionDeclAST(AST):

    def __init__(self, str func_name, FunctionDeclArgsAST args, AST body,int line, int column):
        super().__init__(FunctionDecl, line, column,body._end_line,body._end_column) # type:ignore
        self._name = func_name
        self._args = args
        self._body = body
        self._childs = [args,body]
    
    @property
    def func_name(self) -> str:
        return self._name
    
    @property
    def args(self) -> FunctionDeclArgsAST:
        return self._args
    
    @property
    def body(self) -> AST:
        return self._body
    
    cpdef list[AST] children(self):
        return self._childs

cdef class FunctionCallAST(AST):

    def __init__(self, str function_name, FunctionArgsAST args, int start_line, int start_column, int end_line, int end_column):
        super().__init__(FunctionCall, start_line, start_column, end_line, end_column) # type:ignore
        self._function_name = function_name
        self._args = args
        self._childs = [args]
    
    @property
    def function_name(self) -> str:
        return self._function_name
    
    @property
    def args(self) -> FunctionArgsAST:
        return self._args
    
    cpdef list[AST] children(self):
        return self._childs

cdef class FunctionArgsAST(AST):

    def __init__(self, list[AST] args, int start_line, int start_column, int end_line, int end_column):
        super().__init__(FunctionArgs, start_line, start_column, end_line, end_column) # type:ignore
        self._args = args.copy()
    
    @property
    def args(self) -> list[AST]:
        return self._args.copy()
    
    cpdef list[AST] children(self):
        return self._args

cdef class SlicingAST(AST):

    def __init__(self, AST target, RangeAST range_, int start_line, int start_column, int end_line, int end_column):
        super().__init__(Slicing, start_line, start_column, end_line, end_column) # type:ignore
        self._target = target
        self._range = range_
        self._childs = [target,range_]
    
    @property
    def range(self) -> RangeAST:
        return self._range
    
    @property
    def target(self) -> AST:
        return self._target

    cpdef list[AST] children(self):
        return self._childs

cdef class IndexingAST(AST):

    def __init__(self, AST target, int index, int start_line, int start_column, int end_line, int end_column):
        super().__init__(Indexing, start_line, start_column, end_line, end_column) # type:ignore
        self._target = target
        self._index = index
        self._childs = [target]
    
    @property
    def target(self) -> AST:
        return self._target
    
    @property
    def index(self) -> int:
        return self._index
    
    cpdef list[AST] children(self):
        return self._childs

cdef class RangeAST(AST):

    def __init__(self, int min_,int max_, int start_line, int start_column, int end_line, int end_column):
        super().__init__(Range, start_line, start_column, end_line, end_column) # type:ignore
        self._max = max_
        self._min = min_
        self._childs = []
    
    @property
    def min(self) -> int:
        return self._min
    
    @property
    def max(self) -> int:
        return self._max
    
    cpdef list[AST] children(self):
        return self._childs

cdef class VectorAST(AST):

    def __init__(self, VectorComponentsAST components):
        super().__init__(Vector, components._start_line, components._start_column, components._end_line, components._end_column) # type:ignore
        self._components = components
        self._childs = [components]

    @property
    def length(self) -> int:
        return len(self._components._components)
    
    cpdef list[AST] children(self):
        return self._childs

cdef class VectorComponentsAST(AST):

    def __init__(self, list[AST] components, int start_line, int start_column, int end_line, int end_column):
        super().__init__(Components, start_line, start_column, end_line, end_column) # type:ignore
        self._components = components
    
    cpdef list[AST] children(self):
        return self._components

cdef class VoidInstructionAST(AST):

    def __init__(self, int start_line, int start_column, int end_line, int end_column):
        super().__init__(VoidInstruction, start_line, start_column, end_line, end_column) # type:ignore
        self._childs = []

    cpdef list[AST] children(self):
        return self._childs

cdef class VariableExpressionAST(AST):
    
    def __init__(self, str name, int line, int column):
        super().__init__(VariableExpression, line, column,line,column + len(name)) # type:ignore
        self._name = name
        self._index = -1
        self._childs = []
    
    @property
    def name(self) -> str:
        return self._name
    
    cpdef list[AST] children(self):
        return self._childs

cdef class VecLangInstructionsSequenceAST(AST):

    def __init__(self, list[AST] instructions, int start_line, int start_column, int end_line, int end_column):
        super().__init__(VecLangInstructionsSequence, start_line, start_column, end_line, end_column) # type:ignore
        self._instructions = instructions
    
    cpdef list[AST] children(self):
        return self._instructions

cdef class NumberAST(AST):

    def __init__(self, str value, type _type, int line, int column):
        super().__init__(NumberExpression, line, column,line, column + len(value)) # type:ignore
        self._value = value
        self._type = _type
        self._childs = []
    
    @property
    def value(self) -> str:
        return self._value
    
    @property
    def type(self) -> type:
        return self._type
    
    cpdef list[AST] children(self):
        return self._childs

cdef class BinaryAST(AST):

    def __init__(self, Symbol symbol, AST left, AST right):
        super().__init__(symbol, left._start_line, left._start_column, right._end_line, right._end_column) # type:ignore
        self._left = left
        self._right = right
        self._childs = [left,right]
    
    @property
    def left(self) -> AST:
        return self._left
    
    @property
    def right(self) -> AST:
        return self._right
    
    cpdef list[AST] children(self):
        return self._childs

cdef class PlusAST(BinaryAST):

    def __init__(self, AST left, AST right):
        super().__init__(plus, left, right)

cdef class MinusAST(BinaryAST):

    def __init__(self, AST left, AST right):
        super().__init__(minus, left, right)

cdef class ModAST(BinaryAST):

    def __init__(self, AST left, AST right):
        super().__init__(mod, left, right)

cdef class MulAST(BinaryAST):

    def __init__(self, AST left, AST right):
        super().__init__(mul, left, right)

cdef class DivAST(BinaryAST):

    def __init__(self, AST left, AST right):
        super().__init__(div, left, right)

cdef class DivisionByZeroErrorAST(ErrorAST):
    
    def __init__(self, AST left,AST right):
        cdef SemanticError error = SemanticError('division by zero not allowed',left._start_line,left._start_column, right._end_line, right._end_column)
        super().__init__(div_error,left._start_line,left._start_column,right._end_line,right._end_column,{error})
        self._left = left
        self._right = right
    
    cpdef list[AST] children(self):
        return [self._left,self._right]

cdef class ModuleErrorAST(ErrorAST):

    def __init__(self, AST left, AST right,set[SemanticError] errors) -> None:
        super().__init__(mod_error,left._start_line,left._start_column,right._end_line,right._end_column,errors)
        self._left = left
        self._right = right
    
    cpdef list[AST] children(self):
        return [self._left,self._right]

cdef class ValueTooLargeForIntegerErrorAST(ErrorAST):

    def __init__(self, int line, int column,str text) -> None:
        cdef SemanticError error = SemanticError('Integer too large for 64 bits',line,column,line,column + len(text))
        super().__init__(int_too_large_error,line,column,line,column + len(text),{error})
        self._text = text
    
    @property
    def text(self) -> str:
        return self._text

    cpdef list[AST] children(self):
        return []

cdef class RangeErrorAST(ErrorAST):

    def __init__(self, int start_line, int start_column, int end_line, int end_column, set[SemanticError] errors) -> None:
        super().__init__(range_error,start_line,start_column,end_line,end_column,errors)
    
    cpdef list[AST] children(self):
        return []

cdef class ComplexNumberErrorAST(ErrorAST):

    def __init__(self, int start_line, int start_column, int end_line, int end_column,NumberAST coef, Token token) -> None:
        cdef SemanticError error = SemanticError(f'Unexpected expression "{coef._value}{token._text}", maybe you meant "{coef._value}j"?',start_line,start_column,end_line,end_column)
        super().__init__(complex_error,start_line,start_column,end_line,end_column,{error})
        self._coef = coef
        self._variable = token
    
    cpdef list[AST] children(self):
        return [self._coef,self._variable]

cdef class ExpAST(BinaryAST):

    def __init__(self, AST left, AST right):
        super().__init__(exp, left, right)

cdef class AssignmentAST(BinaryAST):

    def __init__(self, AST left, AST right):
        super().__init__(eq, left, right)

cdef inline AST single_reductor(ASTListView asts):
    return asts._get(0)

cdef inline AST plus_reductor(ASTListView asts):
    return PlusAST(asts._get(0),asts._get(2))

cdef inline AST minus_reductor(ASTListView asts):
    return MinusAST(asts._get(0),asts._get(2))

cdef inline AST mul_reductor(ASTListView asts):
    return MulAST(asts._get(0),asts._get(2))

cdef inline AST div_reductor(ASTListView asts):
    cdef NumberAST right
    if asts._get(2)._symbol._hash == NumberExpression._hash:
        right = asts._get(2)
        if right._type(right._value) == 0:
            return DivisionByZeroErrorAST(asts._get(0),right)
    return DivAST(asts._get(0),asts._get(2))

cdef inline AST mod_reductor(ASTListView asts):
    cdef NumberAST right,left
    cdef set[SemanticError] errors = set()

    if asts._get(2)._symbol._hash == NumberExpression._hash:
        right = asts._get(2)
        if right._type(right._value) == 0:
            errors.add(SemanticError("module by zero not allowed",asts._get(0)._start_line,asts._get(0)._start_column,right._end_line,right._end_column))
        if right._type == np.complex128:
            errors.add(SemanticError("module with complex numbers not allowed",asts._get(0)._start_line,asts._get(0)._start_column,right._end_line,right._end_column))
        if right._type != np.int64:
            errors.add(SemanticError("module by a non-integer not allowed",asts._get(0)._start_line,asts._get(0)._start_column,right._end_line,right._end_column))
    if asts._get(0)._symbol._hash == NumberExpression._hash:
        left = asts._get(0)
        if left._type == np.complex128:
            errors.add(SemanticError("module with complex numbers not allowed",left._start_line,left._start_column,asts._get(2)._end_line,asts._get(2)._end_column))
    if errors:
        return ModuleErrorAST(asts._get(0),asts._get(2),errors)
    return ModAST(asts._get(0),asts._get(2))

cdef inline AST exp_reductor(ASTListView asts):
    return ExpAST(asts._get(0),asts._get(2))

cdef inline AST assignment_reductor(ASTListView asts):
    return AssignmentAST(asts._get(0),asts._get(2))

cdef inline AST extractor_reductor(ASTListView asts):
    asts._get(1)._start_line = asts._get(0)._start_line
    asts._get(1)._start_column = asts._get(0)._start_column
    asts._get(1)._end_line = asts._get(2)._end_line
    asts._get(1)._end_column = asts._get(2)._end_column
    return asts._get(1)

cdef inline AST instructions_sequence_reductor(ASTListView asts):
    cdef VecLangInstructionsSequenceAST pre
    cdef AST instruction
    if asts._size() == 1:
        instruction = asts._get(0)
        return VecLangInstructionsSequenceAST([instruction],instruction._start_line,instruction._start_column,instruction._end_line,instruction._end_column) # type:ignore
    elif asts._size() == 2:
        return asts._get(0)
    else:
        pre = asts._get(0) # type:ignore
        instruction = asts._get(2)
        pre._instructions.append(instruction)
        pre._end_line = instruction._end_line
        pre._end_column = instruction._end_column
        return pre

cdef inline AST void_reductor(ASTListView asts):
    cdef AST ast = asts._get(0)
    return VoidInstructionAST(ast._start_line,ast._start_column,ast._end_line,ast._end_column)

cdef inline AST number_reductor(ASTListView asts):
    cdef Token operator,number
    cdef NumberAST ast
    
    if asts._size() == 1:
        number = asts._get(0) # type:ignore
        if number._type == TokenTypeEnum.INTEGER:
            if int(number._text).bit_length() >= 64:
                return ValueTooLargeForIntegerErrorAST(number._start_line,number._start_column,number._text)
            ast = NumberAST(number._text,np.int64,number._start_line,number._start_column)
        elif number._type == TokenTypeEnum.FLOAT:
            ast = NumberAST(number._text,np.float64,number._start_line,number._start_column)
    else:
        operator = asts._get(0) # type:ignore
        number = asts._get(1) # type:ignore
        if number._type == TokenTypeEnum.INTEGER:
            ast = NumberAST(f'{operator._text}{number._text}',np.int64,number._start_line,number._start_column)
        elif number._type == TokenTypeEnum.FLOAT:
            ast = NumberAST(f'{operator._text}{number._text}',np.float64,number._start_line,number._start_column)
    return ast

cdef inline AST variable_reductor(ASTListView asts):
    cdef Token token = asts._get(0) # type:ignore
    return VariableExpressionAST(token._text,token._start_line,token._start_column)

cdef inline AST complex_number_reductor(ASTListView asts):
    cdef Token token = asts._get(0) # type:ignore
    cdef NumberAST real,img
    cdef complex _value

    real = asts._get(2) # type:ignore
    img = asts._get(4) # type:ignore

    _value = np.complex128(real._type(real._value),img._type(img._value))

    return NumberAST(str(_value),np.complex128,token._start_line,token._start_column)

cdef inline AST complex_number_reductor_1(ASTListView asts):
    cdef Token token = asts._get(1)
    cdef NumberAST img = asts._get(0)
    cdef Error error
    cdef complex _value = np.complex128(0,img._type(img._value))

    if token._text != 'j':
        return ComplexNumberErrorAST(img._start_line,img._start_column,img._end_line,img._end_column,img,token)
    
    return NumberAST(str(_value),np.complex128,img._start_line,img._start_column)

cdef inline AST vector_reductor(ASTListView asts):
    cdef VectorComponentsAST components = asts._get(1) # type:ignore
    return VectorAST(components)

cdef inline AST vector_components_reductor(ASTListView asts):
    cdef VectorComponentsAST components
    cdef AST ast

    if asts._size() == 1:
        ast = asts._get(0)
        components = VectorComponentsAST([ast],ast._start_line,ast._start_column,ast._end_line,ast._end_column)
    else:
        components = asts._get(0) # type:ignore
        ast = asts._get(2)
        components._components.append(ast)
        components._end_line = ast._end_line
        components._end_column = ast._end_column
    return components

cdef inline AST range_reductor(ASTListView asts):
    cdef Token min_,max_,double_dots
    cdef set[SemanticError] errors = set()

    min_ = asts._get(0) # type:ignore
    max_ = asts._get(2) # type:ignore
    double_dots = asts._get(1)

    if int(min_._text).bit_length() >= 32:
        errors.add(SemanticError('Integer too large for 32 bits',min_._start_line,min_._start_column,min_._end_line,min_._end_column))
    
    if int(max_._text).bit_length() >= 32:
        errors.add(SemanticError('Integer too large for 32 bits',max_._start_line,max_._start_column,max_._end_line,max_._end_column))

    if int(min_._text) > int(max_._text):
        errors.add(SemanticError('minimum value must be less or equal to maximum value',min_._start_line_line,min_._start_column,max_._end_line,max_._end_column))

    if errors:
        return RangeErrorAST(min_._start_line,min_._start_column,max_._end_line,max_._end_column,errors)
    return RangeAST(int(min_._text),int(max_._text),min_._start_line,min_._start_column,max_._end_line,max_._end_column)

cdef inline AST range_reductor_1(ASTListView asts):
    cdef Token min_,max_,_minus,double_dots
    cdef set[SemanticError] errors = set()

    _minus = asts._get(0) # type:ignore
    min_ = asts._get(1) # type:ignore
    max_ = asts._get(3) # type:ignore
    double_dots = asts._get(2)

    if int(f'{_minus._text}{min_._text}').bit_length() >= 32:
        errors.add(SemanticError('Integer too large for 32 bits',_minus._start_line,_minus._start_column,min_._end_line,min_._end_column))
    
    if int(max_._text).bit_length() >= 32:
        errors.add(SemanticError('Integer too large for 32 bits',max_._start_line,max_._start_column,max_._end_line,max_._end_column))

    if int(f'{_minus._text}{min_._text}') > int(max_._text):
        errors.add(SemanticError('minimum value must be less or equal to maximum value',_minus._start_line_line,_minus._start_column,max_._end_line,max_._end_column))

    if errors:
        return RangeErrorAST(_minus._start_line,_minus._start_column,max_._end_line,max_._end_column,errors)
    return RangeAST(int(f'{_minus._text}{min_._text}'),int(max_._text),_minus._start_line,_minus._start_column,max_._end_line,max_._end_column)

cdef inline AST range_reductor_2(ASTListView asts):
    cdef Token min_,max_,_minus,double_dots
    cdef set[SemanticError] errors = set()

    min_ = asts._get(0) # type:ignore
    double_dots = asts._get(1)
    _minus = asts._get(2) # type:ignore
    max_ = asts._get(3) # type:ignore

    if int(min_._text).bit_length() >= 32:
        errors.add(SemanticError('Integer too large for 32 bits',min_._start_line,min_._start_column,min_._end_line,min_._end_column))
    
    if int(f'{_minus._text}{max_._text}').bit_length() >= 32:
        errors.add(SemanticError('Integer too large for 32 bits',_minus._start_line,_minus._start_column,max_._end_line,max_._end_column))

    if int(min_._text) > int(f'{_minus._text}{max_._text}'):
        errors.add(SemanticError('minimum value must be less or equal to maximum value',min_._start_line,min_._start_column,max_._end_line,max_._end_column))

    if errors:
        return RangeErrorAST(min_._start_line,min_._start_column,max_._end_line,max_._end_column,errors)
    return RangeAST(int(min_._text),int(f'{_minus._text}{max_._text}'),min_._start_line,min_._start_column,max_._end_line,max_._end_column)

cdef inline AST range_reductor_3(ASTListView asts):
    cdef Token min_,max_,_minus1,_minus2,double_dots
    cdef set[SemanticError] errors = set()

    _minus1 = asts._get(0) # type:ignore
    min_ = asts._get(1) # type:ignore
    double_dots = asts._get(2)
    _minus2 = asts._get(3) # type:ignore
    max_ = asts._get(4) # type:ignore

    if int(f'{_minus1._text}{min_._text}').bit_length() >= 32:
        errors.add(SemanticError('Integer too large for 32 bits',_minus1._start_line,_minus1._start_column,min_._end_line,min_._end_column))
    
    if int(f'{_minus2._text}{max_._text}').bit_length() >= 32:
        errors.add(SemanticError('Integer too large for 32 bits',_minus2._start_line,_minus2._start_column,max_._end_line,max_._end_column))

    if int(f'{_minus1._text}{min_._text}') > int(f'{_minus2._text}{max_._text}'):
        errors.add(SemanticError('minimum value must be less or equal to maximum value',_minus1._start_line,_minus1._start_column,max_._end_line,max_._end_column))

    if errors:
        return RangeErrorAST(_minus1._start_line,_minus1._start_column,max_._end_line,max_._end_column,errors)

    return RangeAST(int(f'{_minus1._text}{min_._text}'),int(f'{_minus2._text}{max_._text}'),_minus1._start_line,_minus1._start_column,max_._end_line,max_._end_column)

cdef inline AST indexing_reductor(ASTListView asts):
    cdef Token index = asts._get(2) # type:ignore
    cdef AST target = asts._get(0)
    return IndexingAST(target,int(index._text),target._start_line,target._start_column,asts._get(3)._end_line,asts._get(3)._end_column)

cdef inline AST slicing_reductor(ASTListView asts):
    cdef AST target = asts._get(0)
    cdef RangeAST _range = asts._get(2) # type:ignore

    return SlicingAST(target,_range,target._start_line,target._start_column,asts._get(3)._end_line,asts._get(3)._end_column)

cdef inline AST function_call_reductor(ASTListView asts):
    cdef VariableExpressionAST function_name = asts._get(0) # type:ignore
    cdef FunctionArgsAST args = asts._get(2) # type:ignore
    return FunctionCallAST(function_name._name,args,function_name._start_line,function_name._start_column,asts._get(3)._end_line,asts._get(3)._end_column)

cdef inline AST built_in_function_call_reductor(ASTListView asts):
    cdef Token keyword = asts._get(0) # type:ignore
    cdef FunctionArgsAST args = asts._get(2) # type:ignore
    return FunctionCallAST(keyword._text,args,keyword._start_line,keyword._start_column,asts._get(3)._end_line,asts._get(3)._end_column)

cdef inline AST function_args_reductor(ASTListView asts):
    cdef FunctionArgsAST args
    cdef AST arg

    if asts._size() == 1:
        arg = asts._get(0)
        args = FunctionArgsAST([arg],arg._start_line,arg._start_column,arg._end_line,arg._end_column)
    else:
        args = asts._get(0) # type:ignore
        arg = asts._get(2)
        args._args.append(arg)
        args._end_line = arg._end_line
        args._end_column = arg._end_column
    
    return args

cdef inline AST function_declare_reductor(ASTListView asts):
    cdef VariableExpressionAST var = asts._get(0) # type:ignore
    cdef FunctionDeclArgsAST args = asts._get(2) # type:ignore
    cdef AST body = asts._get(5)

    return FunctionDeclAST(var._name,args,body,var._start_line,var._start_column)

cdef inline AST function_declare_args_reductor(ASTListView asts):
    cdef FunctionDeclArgsAST args
    cdef VariableExpressionAST var
    cdef TypeAST type_
    
    if asts._size() == 3:
        var = asts._get(0) # type:ignore
        type_ = asts._get(2) # type:ignore
        args = FunctionDeclArgsAST({var:type_._type},var._start_line,var._start_column,type_._end_line,type_._end_column)
    else:
        args = asts._get(0) # type:ignore
        var = asts._get(2) # type:ignore
        type_ = asts._get(4) # type:ignore
        args._args[var] = type_._type
        args._childs.append(var)
        args._end_line = type_._end_line
        args._end_column = type_._end_column
    
    return args

cdef inline AST type_reductor(ASTListView asts):
    cdef Token token = asts._get(0) # type:ignore
    return TypeAST(token._text,token._start_line,token._start_column)
```

We'll add productions grouped by language feature.

> ### 1. Program and Instructions Sequence

A VecLang program is a sequence of instructions separated by newlines.

```cython
VecLangGrammar._add_attributed_production(VecLangProgram,[VecLangInstructionsSequence],single_reductor)

VecLangGrammar._add_attributed_production(VecLangInstructionsSequence,[VecLangInstructionsSequence,new_line,VecLangInstruction],instructions_sequence_reductor)
VecLangGrammar._add_attributed_production(VecLangInstructionsSequence,[VecLangInstructionsSequence,new_line],instructions_sequence_reductor)
VecLangGrammar._add_attributed_production(VecLangInstructionsSequence,[VecLangInstruction],instructions_sequence_reductor)
```

 - `single_reductor` simply returns the only child.

 - `instructions_sequence_reductor` builds a VecLangInstructionsSequenceAST that accumulates instructions.

> ### 2. Arithmetic Expressions

Arithmetic is organised into four precedence levels, from lowest to highest:

 - **Level 1**: addition and subtraction (`+`, `-`).

 - **Level 2**: multiplication, division, modulo (`*`, `/`, `%`).

 - **Level 3**: exponentiation (`**`).

 - **Level 4**: atoms (numbers, variables, vectors, indexing, function calls, parentheses).

```cython
VecLangGrammar._add_attributed_production(ArithmeticExpressionLevel1,[ArithmeticExpressionLevel1,plus,ArithmeticExpressionLevel2],plus_reductor)
VecLangGrammar._add_attributed_production(ArithmeticExpressionLevel1,[ArithmeticExpressionLevel1,minus,ArithmeticExpressionLevel2],minus_reductor)
VecLangGrammar._add_attributed_production(ArithmeticExpressionLevel1,[ArithmeticExpressionLevel2],single_reductor)

VecLangGrammar._add_attributed_production(ArithmeticExpressionLevel2,[ArithmeticExpressionLevel2,mul,ArithmeticExpressionLevel3],mul_reductor)
VecLangGrammar._add_attributed_production(ArithmeticExpressionLevel2,[ArithmeticExpressionLevel2,div,ArithmeticExpressionLevel3],div_reductor)
VecLangGrammar._add_attributed_production(ArithmeticExpressionLevel2,[ArithmeticExpressionLevel2,mod,ArithmeticExpressionLevel3],mod_reductor)
VecLangGrammar._add_attributed_production(ArithmeticExpressionLevel2,[ArithmeticExpressionLevel3],single_reductor)

VecLangGrammar._add_attributed_production(ArithmeticExpressionLevel3,[ArithmeticExpressionLevel3,exp,ArithmeticExpressionLevel4],exp_reductor)
VecLangGrammar._add_attributed_production(ArithmeticExpressionLevel3,[ArithmeticExpressionLevel4],single_reductor)

VecLangGrammar._add_attributed_production(ArithmeticExpressionLevel4,[NumberExpression],single_reductor)
VecLangGrammar._add_attributed_production(ArithmeticExpressionLevel4,[VariableExpression],single_reductor)
VecLangGrammar._add_attributed_production(ArithmeticExpressionLevel4,[Vector],single_reductor)
VecLangGrammar._add_attributed_production(ArithmeticExpressionLevel4,[Indexing],single_reductor)
VecLangGrammar._add_attributed_production(ArithmeticExpressionLevel4,[FunctionCall],single_reductor)
VecLangGrammar._add_attributed_production(ArithmeticExpressionLevel4,[lp,ArithmeticExpressionLevel1,rp],extractor_reductor)

```

 - Each binary operator has its own reductor (`plus_reductor`, `minus_reductor`, etc.) for maximum performance.

 - `extractor_reductor` extracts the inner expression from parentheses, discarding the parentheses symbols.

> ### 3. Numbers and ComplexNumbers

Numbers can be integers, floats, or complex numbers (like `complex(2, 3)` or `3j`). They may also have an explicit sign.

```cython
VecLangGrammar._add_attributed_production(NumberExpression,[Number],single_reductor)
VecLangGrammar._add_attributed_production(NumberExpression,[ComplexNumber],single_reductor)

VecLangGrammar._add_attributed_production(Number,[int_number],number_reductor)
VecLangGrammar._add_attributed_production(Number,[float_number],number_reductor)
VecLangGrammar._add_attributed_production(Number,[plus,int_number],number_reductor)
VecLangGrammar._add_attributed_production(Number,[minus,int_number],number_reductor)
VecLangGrammar._add_attributed_production(Number,[plus,float_number],number_reductor)
VecLangGrammar._add_attributed_production(Number,[minus,float_number],number_reductor)

VecLangGrammar._add_attributed_production(ComplexNumber,[type_complex,lp,Number,com,Number,rp],complex_number_reductor)
VecLangGrammar._add_attributed_production(ComplexNumber,[Number,variable],complex_number_reductor_1)
```

 - `number_reductor` creates a `NumberAST` and determines the type based on the token type.

 - `complex_number_reductor` builds a complex number from two `NumberAST`s.

 - `complex_number_reductor_1` builds a complex number from a number and a variable.

> ### 4. Vectors and Ranges

VecLang supports vector literals like `[1,2,3,4]` and range-based vectors like `[4:10]`.

```cython
VecLangGrammar._add_attributed_production(Vector,[lc,Components,rc],vector_reductor)
VecLangGrammar._add_attributed_production(Vector,[lc,Range,rc],extractor_reductor)
VecLangGrammar._add_attributed_production(Vector,[Slicing],single_reductor)
```

> **NOTE: Slices are vectors too**

Components are sequences of arithmetic expressions separated by commas:

```cython
VecLangGrammar._add_attributed_production(Components,[ArithmeticExpressionLevel1],vector_components_reductor)
VecLangGrammar._add_attributed_production(Components,[Components,com,ArithmeticExpressionLevel1],vector_components_reductor)
```

And ranges can have negative bounds:

```cython
VecLangGrammar._add_attributed_production(Range,[int_number,double_dot,int_number],range_reductor)
VecLangGrammar._add_attributed_production(Range,[minus,int_number,double_dot,int_number],range_reductor_1)
VecLangGrammar._add_attributed_production(Range,[int_number,double_dot,minus,int_number],range_reductor_2)
VecLangGrammar._add_attributed_production(Range,[minus,int_number,double_dot,minus,int_number],range_reductor_3)

```

The different reductors handle the presence of minus signs for negative bounds.

> ### 5. Indexing and Slicing

Indexing: `vec[2]` or `var[5]`. Slicing: `var[0:5]` or `vec[3:7]`.

```cython
VecLangGrammar._add_attributed_production(Indexing,[VariableExpression,lc,int_number,rc],indexing_reductor)
VecLangGrammar._add_attributed_production(Indexing,[Vector,lc,int_number,rc],indexing_reductor)

VecLangGrammar._add_attributed_production(Slicing,[VariableExpression,lc,Range,rc],slicing_reductor)
VecLangGrammar._add_attributed_production(Slicing,[Vector,lc,Range,rc],slicing_reductor)
```

 - `indexing_reductor` builds an `IndexingAST` with the target and the integer index.

 - `slicing_reductor` builds a `SlicingAST` with the target and a `RangeAST`.

> ### 6. Function Calls and Built-in Functions

User‑defined functions and built‑ins (`sum`, `mean`, `dot`, `print`) share the same call syntax.

```cython
VecLangGrammar._add_attributed_production(FunctionCall,[VariableExpression,lp,FunctionArgs,rp],function_call_reductor)
VecLangGrammar._add_attributed_production(FunctionCall,[sum_keyword,lp,FunctionArgs,rp],built_in_function_call_reductor)
VecLangGrammar._add_attributed_production(FunctionCall,[mean_keyword,lp,FunctionArgs,rp],built_in_function_call_reductor)
VecLangGrammar._add_attributed_production(FunctionCall,[dot_keyword,lp,FunctionArgs,rp],built_in_function_call_reductor)
```

> **NOTE**
`print` function is not an arithmetic expression, so we don't write its production here, but in the top of grammar hierarchy, as a `VecLangInstruction`.

```cython
VecLangGrammar._add_attributed_production(VecLangInstruction,[print_keyword,lp,FunctionArgs,rp],built_in_function_call_reductor)
```

Arguments are lists of expressions:

```cython
VecLangGrammar._add_attributed_production(FunctionArgs,[ArithmeticExpressionLevel1],function_args_reductor)
VecLangGrammar._add_attributed_production(FunctionArgs,[FunctionArgs,com,ArithmeticExpressionLevel1],function_args_reductor)
```

 - `function_call_reductor` uses the name from a `VariableExpressionAST`.

 - `built_in_function_call_reductor` uses the token text (e.g., "sum").

> ### 7. Function Declarations

VecLang allows defining functions with typed arguments:

```txt
f(x: int, y: float) = x + y
```

```cython
VecLangGrammar._add_attributed_production(FunctionDecl,[VariableExpression,lp,FunctionDeclArgs,rp,eq,ArithmeticExpressionLevel1],function_declare_reductor)
```

And the arguments are declared with types:

```cython
VecLangGrammar._add_attributed_production(FunctionDeclArgs,[VariableExpression,double_dot,Type],function_declare_args_reductor)
VecLangGrammar._add_attributed_production(FunctionDeclArgs,[FunctionDeclArgs,com,VariableExpression,double_dot,Type],function_declare_args_reductor)

VecLangGrammar._add_attributed_production(Type,[type_complex],type_reductor)
VecLangGrammar._add_attributed_production(Type,[type_float],type_reductor)
VecLangGrammar._add_attributed_production(Type,[type_int],type_reductor)
VecLangGrammar._add_attributed_production(Type,[type_vector],type_reductor)
```

 - `function_declare_args_reductor` builds a `FunctionDeclArgsAST` that maps variable names to their types.

 - `type_reductor` creates a `TypeAST`.

> ### 8. Instructions

An instruction can be an expression, a function declaration, an assignment, or a `print` statement.

```cython
VecLangGrammar._add_attributed_production(VecLangInstruction,[ArithmeticExpressionLevel1],single_reductor)
VecLangGrammar._add_attributed_production(VecLangInstruction,[FunctionDecl],single_reductor)
VecLangGrammar._add_attributed_production(VecLangInstruction,[VariableExpression,eq,ArithmeticExpressionLevel1],assignment_reductor)
VecLangGrammar._add_attributed_production(VecLangInstruction,[print_keyword,lp,FunctionArgs,rp],built_in_function_call_reductor)

# ...

VecLangGrammar._add_attributed_production(VariableExpression,[variable],variable_reductor)
```

 - Assignment uses `assignment_reductor` which creates an `AssignmentAST`.

 - Print is treated as a built‑in function call.

## Connecting the Dots: Reductors

Because performance matters, we define each reductor as a `cdef` function (or `cdef` with a return type) to avoid Python call overhead. They are implemented in `asts.pyx`.

> ### Single and Extractor Reductors

These are trivial:
```cython
cdef inline AST single_reductor(ASTListView asts):
    return asts._get(0)

cdef inline AST extractor_reductor(ASTListView asts):
    asts._get(1)._start_line = asts._get(0)._start_line
    asts._get(1)._start_column = asts._get(0)._start_column
    asts._get(1)._end_line = asts._get(2)._end_line
    asts._get(1)._end_column = asts._get(2)._end_column
    return asts._get(1)
```

> **NOTE: Updating the limits of the current ast**

Here we've updated the coordinates of the current ast to match with its real coordinates

> ### Binary Operation Reductors

We have separate reductors for each operator. For example:

```cython
cdef inline AST plus_reductor(ASTListView asts):
    return PlusAST(asts._get(0),asts._get(2))
```

Similarly for `minus_reductor`, `mul_reductor`, etc. This avoids a conditional chain and is faster in Cython.

> ### Assignment Reductor

```cython
cdef inline AST assignment_reductor(ASTListView asts):
    return AssignmentAST(asts._get(0),asts._get(2))
```

> ### Number and Complex Number Reductors

number_reductor creates a `NumberAST` with the appropriate type.

```cython
cdef inline AST number_reductor(ASTListView asts):
    cdef Token operator,number
    cdef NumberAST ast
    
    if asts._size() == 1:
        number = asts._get(0) # type:ignore
        if number._type == TokenTypeEnum.INTEGER:
            if int(number._text).bit_length() >= 64:
                return ValueTooLargeForIntegerErrorAST(number._start_line,number._start_column,number._text)
            ast = NumberAST(number._text,np.int64,number._start_line,number._start_column)
        elif number._type == TokenTypeEnum.FLOAT:
            ast = NumberAST(number._text,np.float64,number._start_line,number._start_column)
    else:
        operator = asts._get(0) # type:ignore
        number = asts._get(1) # type:ignore
        if number._type == TokenTypeEnum.INTEGER:
            ast = NumberAST(f'{operator._text}{number._text}',np.int64,number._start_line,number._start_column)
        elif number._type == TokenTypeEnum.FLOAT:
            ast = NumberAST(f'{operator._text}{number._text}',np.float64,number._start_line,number._start_column)
    return ast
```

`complex_number_reductor` extracts the real and imaginary parts from two `NumberAST`s and creates a complex number; while `complex_numbre_reductor_1` takes only the imaginary part, from the format `nj` where n is a number.

```cython
cdef inline AST complex_number_reductor(ASTListView asts):
    cdef Token token = asts._get(0) # type:ignore
    cdef NumberAST real,img
    cdef complex _value

    real = asts._get(2) # type:ignore
    img = asts._get(4) # type:ignore

    _value = np.complex128(real._type(real._value),img._type(img._value))

    return NumberAST(str(_value),np.complex128,token._start_line,token._start_column)

cdef inline AST complex_number_reductor_1(ASTListView asts):
    cdef Token token = asts._get(1)
    cdef NumberAST img = asts._get(0)
    cdef Error error
    cdef complex _value = np.complex128(0,img._type(img._value))

    if token._text != 'j':
        return ComplexNumberErrorAST(img._start_line,img._start_column,img._end_line,img._end_column,img,token)
    
    return NumberAST(str(_value),np.complex128,img._start_line,img._start_column)
```

> ### Vector and Components

`vector_reductor` builds a `VectorAST` from a `ComponentsAST`. The components are built by `vector_components_reductor`, which accumulates elements into a list.

> ### Range Reductors

There are four variants to handle signs. Each creates a `RangeAST`.

> ### Indexing and Slicing

`indexing_reductor` extracts the integer index and builds an `IndexingAST`. `slicing_reductor` builds a `SlicingAST` with the target and the `RangeAST`.

> ### Function Call Reductors

`function_call_reductor` gets the function name from a `VariableExpressionAST` and the arguments from a `FunctionArgsAST`.

`built_in_function_call_reductor` uses the token text (e.g., "sum") to name the function.

> ### Function Declaration and Arguments

`function_declare_reductor` creates a `FunctionDeclAST`. `function_declare_args_reductor` builds a dictionary mapping variable names to types.

> ### Type Reductor

`type_reductor` creates a `TypeAST` from the keyword token.

## Putting It All Together

Finally, after adding all productions, we build the LALR(1) parser using PyLGEN's `_build_lalr_parser_from_attributed`:

```cython
return _build_lalr_parser_from_attributed(VecLangGrammar)
```

This function compiles the grammar into a table‑driven parser that can be used to parse any VecLang program.

File: `parser.pxd`

```cython
from pylgen.parser.parser cimport BottomUpParser

cpdef BottomUpParser build_parser()
```

File: `parser.pyx`
```cython
from pylgen.grammar.grammar cimport AttributedGrammar
from pylgen.parser.parser_builder cimport _build_lalr_parser_from_attributed
from pylgen.parser.parser cimport BottomUpParser
from pylgen.common.types cimport AST,ASTListView

from .asts cimport (
    VecLangProgram,
    VecLangInstruction,
    VecLangInstructionsSequence,
    ArithmeticExpressionLevel1,
    ArithmeticExpressionLevel2,
    ArithmeticExpressionLevel3,
    ArithmeticExpressionLevel4,
    Number,
    ComplexNumber,
    NumberExpression,
    VariableExpression,
    Components,
    Vector,
    Range,
    Indexing,
    Slicing,
    FunctionArgs,
    FunctionCall,
    FunctionDecl,
    FunctionDeclArgs,
    Type,
    int_number,
    float_number,
    variable,
    lp,
    rp,
    new_line,
    plus,
    minus,
    mod,
    mul,
    div,
    exp,
    eq,
    lc,
    rc,
    com,
    double_dot,
    sum_keyword,
    mean_keyword,
    dot_keyword,
    print_keyword,
    type_complex,
    type_float,
    type_int,
    type_vector,
    single_reductor,
    instructions_sequence_reductor,
    plus_reductor,
    minus_reductor,
    mul_reductor,
    div_reductor,
    mod_reductor,
    exp_reductor,
    assignment_reductor,
    extractor_reductor,
    number_reductor,
    variable_reductor,
    complex_number_reductor,
    complex_number_reductor_1,
    vector_reductor,
    vector_components_reductor,
    range_reductor,
    range_reductor_1,
    range_reductor_2,
    range_reductor_3,
    indexing_reductor,
    slicing_reductor,
    function_call_reductor,
    function_args_reductor,
    built_in_function_call_reductor,
    function_declare_args_reductor,
    function_declare_reductor,
    type_reductor
)

cpdef BottomUpParser build_parser():
    cdef AttributedGrammar VecLangGrammar = AttributedGrammar(VecLangProgram) # type:ignore

    VecLangGrammar._add_attributed_production(VecLangProgram,[VecLangInstructionsSequence],single_reductor)

    VecLangGrammar._add_attributed_production(VecLangInstructionsSequence,[VecLangInstructionsSequence,new_line,VecLangInstruction],instructions_sequence_reductor)
    VecLangGrammar._add_attributed_production(VecLangInstructionsSequence,[VecLangInstructionsSequence,new_line],instructions_sequence_reductor)
    VecLangGrammar._add_attributed_production(VecLangInstructionsSequence,[VecLangInstruction],instructions_sequence_reductor)

    VecLangGrammar._add_attributed_production(VecLangInstruction,[ArithmeticExpressionLevel1],single_reductor)
    VecLangGrammar._add_attributed_production(VecLangInstruction,[FunctionDecl],single_reductor)
    VecLangGrammar._add_attributed_production(VecLangInstruction,[VariableExpression,eq,ArithmeticExpressionLevel1],assignment_reductor)
    VecLangGrammar._add_attributed_production(VecLangInstruction,[print_keyword,lp,FunctionArgs,rp],built_in_function_call_reductor)

    VecLangGrammar._add_attributed_production(ArithmeticExpressionLevel1,[ArithmeticExpressionLevel1,plus,ArithmeticExpressionLevel2],plus_reductor)
    VecLangGrammar._add_attributed_production(ArithmeticExpressionLevel1,[ArithmeticExpressionLevel1,minus,ArithmeticExpressionLevel2],minus_reductor)
    VecLangGrammar._add_attributed_production(ArithmeticExpressionLevel1,[ArithmeticExpressionLevel2],single_reductor)

    VecLangGrammar._add_attributed_production(ArithmeticExpressionLevel2,[ArithmeticExpressionLevel2,mul,ArithmeticExpressionLevel3],mul_reductor)
    VecLangGrammar._add_attributed_production(ArithmeticExpressionLevel2,[ArithmeticExpressionLevel2,div,ArithmeticExpressionLevel3],div_reductor)
    VecLangGrammar._add_attributed_production(ArithmeticExpressionLevel2,[ArithmeticExpressionLevel2,mod,ArithmeticExpressionLevel3],mod_reductor)
    VecLangGrammar._add_attributed_production(ArithmeticExpressionLevel2,[ArithmeticExpressionLevel3],single_reductor)

    VecLangGrammar._add_attributed_production(ArithmeticExpressionLevel3,[ArithmeticExpressionLevel3,exp,ArithmeticExpressionLevel4],exp_reductor)
    VecLangGrammar._add_attributed_production(ArithmeticExpressionLevel3,[ArithmeticExpressionLevel4],single_reductor)

    VecLangGrammar._add_attributed_production(ArithmeticExpressionLevel4,[NumberExpression],single_reductor)
    VecLangGrammar._add_attributed_production(ArithmeticExpressionLevel4,[VariableExpression],single_reductor)
    VecLangGrammar._add_attributed_production(ArithmeticExpressionLevel4,[Vector],single_reductor)
    VecLangGrammar._add_attributed_production(ArithmeticExpressionLevel4,[Indexing],single_reductor)
    VecLangGrammar._add_attributed_production(ArithmeticExpressionLevel4,[FunctionCall],single_reductor)
    VecLangGrammar._add_attributed_production(ArithmeticExpressionLevel4,[lp,ArithmeticExpressionLevel1,rp],extractor_reductor)

    VecLangGrammar._add_attributed_production(NumberExpression,[Number],single_reductor)
    VecLangGrammar._add_attributed_production(NumberExpression,[ComplexNumber],single_reductor)

    VecLangGrammar._add_attributed_production(Number,[int_number],number_reductor)
    VecLangGrammar._add_attributed_production(Number,[float_number],number_reductor)
    VecLangGrammar._add_attributed_production(Number,[plus,int_number],number_reductor)
    VecLangGrammar._add_attributed_production(Number,[minus,int_number],number_reductor)
    VecLangGrammar._add_attributed_production(Number,[plus,float_number],number_reductor)
    VecLangGrammar._add_attributed_production(Number,[minus,float_number],number_reductor)

    VecLangGrammar._add_attributed_production(ComplexNumber,[type_complex,lp,Number,com,Number,rp],complex_number_reductor)
    VecLangGrammar._add_attributed_production(ComplexNumber,[Number,variable],complex_number_reductor_1)

    VecLangGrammar._add_attributed_production(VariableExpression,[variable],variable_reductor)

    VecLangGrammar._add_attributed_production(Vector,[lc,Components,rc],vector_reductor)
    VecLangGrammar._add_attributed_production(Vector,[lc,Range,rc],extractor_reductor)
    VecLangGrammar._add_attributed_production(Vector,[Slicing],single_reductor)

    VecLangGrammar._add_attributed_production(Components,[ArithmeticExpressionLevel1],vector_components_reductor)
    VecLangGrammar._add_attributed_production(Components,[Components,com,ArithmeticExpressionLevel1],vector_components_reductor)

    VecLangGrammar._add_attributed_production(Range,[int_number,double_dot,int_number],range_reductor)
    VecLangGrammar._add_attributed_production(Range,[minus,int_number,double_dot,int_number],range_reductor_1)
    VecLangGrammar._add_attributed_production(Range,[int_number,double_dot,minus,int_number],range_reductor_2)
    VecLangGrammar._add_attributed_production(Range,[minus,int_number,double_dot,minus,int_number],range_reductor_3)

    VecLangGrammar._add_attributed_production(Indexing,[VariableExpression,lc,int_number,rc],indexing_reductor)
    VecLangGrammar._add_attributed_production(Indexing,[Vector,lc,int_number,rc],indexing_reductor)

    VecLangGrammar._add_attributed_production(Slicing,[VariableExpression,lc,Range,rc],slicing_reductor)
    VecLangGrammar._add_attributed_production(Slicing,[Vector,lc,Range,rc],slicing_reductor)

    VecLangGrammar._add_attributed_production(FunctionCall,[VariableExpression,lp,FunctionArgs,rp],function_call_reductor)
    VecLangGrammar._add_attributed_production(FunctionCall,[sum_keyword,lp,FunctionArgs,rp],built_in_function_call_reductor)
    VecLangGrammar._add_attributed_production(FunctionCall,[mean_keyword,lp,FunctionArgs,rp],built_in_function_call_reductor)
    VecLangGrammar._add_attributed_production(FunctionCall,[dot_keyword,lp,FunctionArgs,rp],built_in_function_call_reductor)

    VecLangGrammar._add_attributed_production(FunctionArgs,[ArithmeticExpressionLevel1],function_args_reductor)
    VecLangGrammar._add_attributed_production(FunctionArgs,[FunctionArgs,com,ArithmeticExpressionLevel1],function_args_reductor)

    VecLangGrammar._add_attributed_production(FunctionDecl,[VariableExpression,lp,FunctionDeclArgs,rp,eq,ArithmeticExpressionLevel1],function_declare_reductor)

    VecLangGrammar._add_attributed_production(FunctionDeclArgs,[VariableExpression,double_dot,Type],function_declare_args_reductor)
    VecLangGrammar._add_attributed_production(FunctionDeclArgs,[FunctionDeclArgs,com,VariableExpression,double_dot,Type],function_declare_args_reductor)

    VecLangGrammar._add_attributed_production(Type,[type_complex],type_reductor)
    VecLangGrammar._add_attributed_production(Type,[type_float],type_reductor)
    VecLangGrammar._add_attributed_production(Type,[type_int],type_reductor)
    VecLangGrammar._add_attributed_production(Type,[type_vector],type_reductor)

    return _build_lalr_parser_from_attributed(VecLangGrammar)
```

File: `parser.pyi`
```cython
from pylgen.parser.parser import BottomUpParser

def build_parser() -> BottomUpParser: ...
```

## Performance-Driven Changes

If you compare this VecLang implementation with the pure-Python arithmetic interpreter from earlier tutorial, you'll notice several differences. At first glance, the code looks more verbose and less "Pythonic". But every change has a purpose: **raw speed**. Let's break down the key transformations and why they matter.

> ### 1. Predefined Symbols Instead of Runtime Creation

Python version
```python
def get_symbol_function(t:TokenTypeEnum,tx:str) -> Symbol:
    if t == TokenTypeEnum.NUMBER:
        return number
    if t == TokenTypeEnum.SYMBOL:
        return Symbol(tx,True)
    # ...
```

Cython version
```cython
cdef Symbol plus = Symbol('+',True)
cdef Symbol minus = Symbol('-',True)
# ....

cdef Symbol get_symbol_function(object t, str tx):
    # ...
    if t == TokenTypeEnum.OPERATOR:
        return _operators[tx]
    # ...
```

**Why it's faster**: Object allocation is expensive, especially in the hot path of tokenisation. By pre-creating every possible symbol as a `cdef` variable, we eliminate millions of allocations when processing large files.

> ### 2. Separate Reductors per Operator Instead of a Single Conditional

Python version
```python
def binary_reductor(asts:ASTListView) -> AST:
    ast_type = None
    if asts[1].symbol == plus:
        ast_type = PlusAST
    # ...
```

Cython version
```cython
cdef inline AST plus_reductor(ASTListView asts):
    return PlusAST(asts._get(0),asts._get(2))

cdef inline AST minus_reductor(ASTListView asts):
    return MinusAST(asts._get(0),asts._get(2))

# ...
```

**Why it's faster**: Function call overhead is reduced, but more importantly, we avoid a runtime conditional chain that must be evaluated for every binary operation. In Cython, `cdef` functions are called with near-C speed, and the parser directly invokes the specific reductor for each production, so no dispatching logic is needed.

> ### 3. C-Level Access to AST Attributes

Python version
```python
class BinaryAST(AST):

    def __init__(self, left:AST,right:AST,symbol: Symbol):
        (sl,sc),(el,ec) = left.start_position,right.end_position
        super().__init__(symbol, sl,sc,el,ec)
        self._left:AST = left
        self._right:AST = right
```

Cython version
```cython
cdef class BinaryAST(AST):
    cdef AST _left
    cdef AST _right
    cdef list[AST] _childs
```

**Why it's faster**: Declaring attributes as `cdef` makes them **direct C struct members**, bypassing Python's attribute dictionary lookup (`__dict__`). Accessing `ast._left` in a reductor becomes a simple memory offset, not a hash table lookup. This is particularly beneficial inside tight loops.

> ### 4. Strong Static Typing for Local Variables

Python version: no type annotations (or optional ones that are ignored at runtime).

Cython version:
```cython
cdef Token operator,number
cdef NumberAST ast
```

**Why it's faster**: Cython can generate C code that uses native C types (or fast Python object pointers) without boxing/unboxing. This reduces the overhead of dynamic type checking and allows optimisations.

> ### 5. Compilation to Native Code

The most obvious difference: all `.pyx` files are compiled to a C extension module. This means:

 - The parser, and reductors run as native machine code.
 - The Python interpreter is bypassed for the hot loops.
 - Memory management  can be more aggressive.

In contrast, the pure-Python version is interpreted line by line by the CPython bytecode evaluator.

> ### Does Every Change Improve Performance? (A Balanced View)

Yes, the overwhelming majority of these changes are **directly motivated by performance**. However, there are a few trade-offs:

 - **Readability**: The code is more verbose and less approachable for beginers. But for a production-grade interpreter that must handle millions of lines, readability takes a back seat to speed.
 - **Flexibility**: In Python, you can easily swap reductors or modify symbol mappings at runtime. In Cython, many of these structures are fixed at compile time, making the interpreter less dynamic. This is acceptable because VecLang's grammar is fixed.
 - **Compilation overhead**: You need a C compiler and Cython installed, and compilation takes extra time. This is a one-time cost for each deployment.

There is one change that is **not** primarily for speed: the use of **NumPy types** (`np.int64`,`np.float64`,`np.complex128`). While **NumPy** itself is highly optimised in C, the main reason we use it is to represent numbers in a way that enables efficent vectorised operations during evaluation (which is a separated stage). This is more about **correctness** and **feature richness** than about parsing performance.

> ### Conclusion

The transition from Python to Cython in VecLang is not cosmetic, it's a series of deliberate, performance-first decisions. We've traded some syntactic sugar for raw speed, and the results will speak for themselves. The approach is not necessary for every project, but when your interpreter must handle production-scale workloads, these are exactly the kinds of optimizations that make the difference between a toy and a tool.



<!-- source: docs/tutorials/complete-languages/veclang/veclang-step-3.md -->

# Step 3: Semantic Analysis and Evaluation

VecLang is far richer than a simple arithmetic language: it supports vectors, slicing, indexing, complex numbers, user-defined functions, and built-ins. This complexity demands a robust semantic framework. We'll build on the same **Visitor** and **Strategy** patterns we used before, but this time we'll leverage Cython to achieve near-native performance.

## Custom Runtime Errors (`errors.pxd`,`errors.pyx`)

VecLang defines a hierarchy of runtime errors, all inheriting from PyLGEN's `RuntimeError`. Each error carries a stack trace, line, column, and a descriptive message.

File: `errors.pxd`(declarations)
```cython
from pylgen.common.types cimport RuntimeError

cdef class DivisionByZeroError(RuntimeError):
    pass

cdef class ModuleByZeroError(RuntimeError):
    pass

cdef class UnSupportedOperationError(RuntimeError):
    pass

cdef class UnSupportedOperationForTypeError(UnSupportedOperationError):
    pass

cdef class UnSupportedOperationForTypesError(UnSupportedOperationError):
    pass

cdef class InvalidOperationError(RuntimeError):
    pass

cdef class BadRangeError(InvalidOperationError):
    pass

cdef class IndexOutOfRangeError(RuntimeError):
    pass
```

File: `errors.pyx`(implementations)
```cython
from pylgen.common.types cimport RuntimeError

cdef class DivisionByZeroError(RuntimeError):

    def __init__(self, list[str] stack_trace, int start_line, int start_column, int end_line, int end_column) -> None:
        super().__init__(stack_trace, start_line, start_column, end_line, end_column, 'Division by zero not allowed')

cdef class ModuleByZeroError(RuntimeError):
    def __init__(self, list[str] stack_trace, int start_line, int start_column, int end_line, int end_column) -> None:
        super().__init__(stack_trace, start_line, start_column, end_line, end_column, 'Module by zero not allowed')

cdef class UnSupportedOperationError(RuntimeError):

    def __init__(self, list[str] stack_trace, int start_line, int start_column, int end_line, int end_column, str msg) -> None:
        super().__init__(stack_trace, start_line, start_column, end_line, end_column, msg)

cdef class UnSupportedOperationForTypeError(UnSupportedOperationError):

    def __init__(self, list[str] stack_trace, int start_line, int start_column, int end_line, int end_column,str operation ,type _type) -> None:
        super().__init__(stack_trace, start_line, start_column, end_line, end_column, f'operation "{operation}" not supported for type {_type}')

cdef class UnSupportedOperationForTypesError(UnSupportedOperationError):
    
    def __init__(self, list[str] stack_trace, int start_line, int start_column, int end_line, int end_column,str operation ,type _type1,type _type2) -> None:
        super().__init__(stack_trace, start_line, start_column, end_line, end_column, f'operation ({_type1} "{operation}" {_type2}) not supported')

cdef class InvalidOperationError(RuntimeError):

    def __init__(self, list[str] stack_trace, int start_line, int start_column, int end_line, int end_column, str msg) -> None:
        super().__init__(stack_trace, start_line, start_column, end_line, end_column, msg)

cdef class BadRangeError(InvalidOperationError):

    def __init__(self, list[str] stack_trace, int start_line, int start_column, int end_line, int end_column) -> None:
        super().__init__(stack_trace, start_line, start_column, end_line, end_column, f'The args[1] < args[0] is not allowed')

cdef class IndexOutOfRangeError(RuntimeError):
    
    def __init__(self, list[str] stack_trace, int start_line, int start_column, int end_line, int end_column,int index, int size) -> None:
        super().__init__(stack_trace, start_line, start_column, end_line, end_column, f'Index {index} out of range (0-{size - 1})')
```

By keeping them as `cdef` classes, we avoid Python attribute lookups and make error creation cheap, important when processing millions of lines.

## The VecLangContext (Managing State)

The `VecLangContext` class (defined in `visitors.pyx`) is the central repository for all runtime state. It extends PyLGEN's `Context` and adds:

 - **Variables**: stored in parallel lists (`_var_values`,`_var_types`,`_var_flags`) and indexed by a dictionary `_vars_index` that maps variable names to integer indices. This is much faster than using a dictionary for values because we can access lists by index.
 - **Scopes**: a stack of scopes (`_scopes`). Each scope is a tuple of (`values`,`types`,`flags`,`index_map`,`eval_stack`). When we enter a function, we push a new scope; when we exit, we pop it.
 - **Functions**: a dictionary `_functions` mapping function names to a tuple of (`body_ast`,`list[(parameter_name,type_str)]`).
 - **Evaluation stack**: `_eval_stack` holds intermediate values during post-order traversal.
 - **Runtime errors**: a dictionary `_runtime_errors` mapping AST nodes to the error that occurred at that node (to avoid duplicate reports).
 - **Built-in functions**: a set `_built_in_functions` for `sum`,`mean`,`dot`, and `print`.

All attributes are declared as `cdef` to enable C-level access.

```cython
cdef class VecLangContext(Context):

    cdef set[str] _built_in_functions
    cdef dict[str,tuple[AST,list[tuple[str,str]]]] _functions
    cdef list[object] _var_values
    cdef list[type] _var_types
    cdef list[bint] _var_flags
    cdef dict[AST,RuntimeError] _runtime_errors
    cdef dict[str,int] _vars_index
    cdef list[object] _eval_stack
    cdef list[tuple[list[object],list[type],list[bint],dict[str,int],list[object]]] _scopes

    cdef tuple[bint,object] look_for_var(self,str var_name)
    cdef void assign_var(self,str var_name,object value)

    cpdef void reset(self)

    cpdef void hard_reset(self)
```

The context provides methods to look up variables (`look_for_var`), assign variables (`assign_var`), push/pop scopes, and manage errors. All methods are `cdef` for speed. This design is a direct performance upgrade over the pure-Python version.

## The Visitor Pattern in Cython

We use PyLGEN's visitor framework, but with a Cython twist: all visitors classes are `cdef` and their `visit` methods are `cpdef`. This allows them to be called from Cython code without Python function call overhead.

| **Pass** | **Visitors involved** | **Objective** |
| :--- | :--- | :--- |
| **Function Collection** | `FunctionDeclASTCollectorVisitor` | Register all user-defined functions in the context. |
| **Semantic Error Collection** | `FunctionCallASTErrorCollector`, `VectorComponentsASTErrorCollector`, `BinaryASTErrorCollectorVisitor`, etc. | Validate types, variables existence, infinite loops, valid ranges and division by zero in compilation time. |
| **Evaluation** | `PlusASTEvaluatorVisitor`, `RangeASTEvaluatorVisitor`, `FunctionCallASTEvaluatorVisitor`, etc. | Execute the code, operate with NumPy and manage the evaluation stack (`_eval_stack`). |

## Function Collector

Before the **semantic error collector** pass, we need to collect all functions defined by the user. This task is done by the `FunctionDeclASTCollectorVisitor` visitor. It scans the AST for function definitions and stores them in the context. This must happen before any function call checks. This visitor is registered in the `functions_collector` walker.

```cython
functions_collector.add_visitor_without_signature_checking(FunctionDeclAST,FunctionDeclASTCollectorVisitor())
```

## Semantic Error Collectors

After user-defined functions collection and before evaluation, we run a **semantic error collection** pass. These visitors detect issues that can be caught statically:

 - `FunctionCall ASTErrorCollectorVisitor`: verifies that called functions exist, that the argument count matches the signature, that arguments are declared variables (if they are variable references), and detects infinite recursion (calls that loop back to the same function).
 - `VectorComponentASTErrorCollector`: ensures that any variable used inside a vector literal has been declared.
 - `SlicingASTErrorCollectorVisitor`: validates that slicing indices are within bounds of the target (if the target is a literal vector or range).
 - `IndexingASTErrorCollectorVisitor`: similar for indexing.
 - `BinaryASTErrorCollectorVisitor`: checks that variables used in binary operations are declared.
 - `VariableIndexerVisitor`: when an assignment is encountered, it assigns an index to the variable in the context, preparing for fast lookup during evaluation.

All these visitors are registered in the `error_collector_walker`.

## Evaluator Visitors

The evaluator visitors perform the actual computation. They assume that all semantic checks have passed and that the context is properly initialised.

 - `NumberASTEvaluatorVisitor`: converts a `NumberAST` to a **NumPy** scalar (`np.int64`,`np.float64`, or `np.complex128`) and pushes it onto the evaluation stack.
 - `BinaryASTEvaluatorVisitor` (base class): fetches left and right values from the stack (or from variables), checks for errors, and stores them int `_left_value`, `_right_value`. Specific subclasses (`PlusASTEvaluatorVisitor`, `MinusASTEvaluatorVisitor`, `MulASTEvaluatorVisitor`,  `DivASTEvaluatorVisitor`, `ModASTEvaluatorVisitor`, `ExpASTEvaluatorVisitor`) perform the operation and push the result.
 - `AssignmentASTEvaluatorVisitor`: evaluates the right-hand side, then assigns the value to the variable using `context.assign_var`.
 - `VectorComponentsASTEvaluatorVisitor`: evaluates each component of a vector, collects them into a NumPy array, and pushes the array.
 - `RangeASTEvaluatorVisitor`: creates a NumPy array using `np.arange` and pushes it.
 - `SlicingASTEvaluatorVisitor`: applies a slice to a vector/range and pushes the result.
 - `IndexingASTEvaluatorVisitor`: extracts a single element from a vector/range.
 - `FunctionCallASTEvaluatorVisitor`: handles both built-in functions (`print`,`sum`,`dot`,`mean`) and user-defined functions. For built-ins, it directly computes the result. For user-defined functions, it pushes a new scope, evaluates the function body, and pops the scope, leaving the return value on the stack.

All these evaluator visitors are registered in the `evaluator_walker`.

> **NOTE**
All these AST node visitors are `cdef` and use typed local variables to avoid Python overhead. They also leverage NumPy's vectorised operations for speed.

## Traversal Strategies

We use two custom traversal strategies, both implementing post-order (children before parent) to ensure that values are available when a node is evaluated.

 - `PostOrderTraversalStrategy`: a standard post-order walk used for function collection and error collection. It uses a stack of `(node,processed)` flags.
 - `PostOrderTraversalEvaluatorStrategy`: similar, but it stops the traversal as soon as any runtime error is added to the context. This prevents cascading errors and saves time.

Both strategies are implemented in Cython with `cdef` methods and use efficient list operations. This strategy works with a **selector** to decide which children to visit. We use `DefaultChildrenSelector` for most nodes, but for `FunctionDeclAST` we use a custom selector that returns no children during function collection (so that function bodies are not checked until the semantic error collection).

## Building the Walkers

The `build_walkers()` function (in `visitors.pyx`) orchestrates everything. It creates a single `VecLangContext` and three `ASTWalker` instances:

 - `functions_collector`: uses `PostOrderTraversalStrategy` and the `FunctionDeclASTCollectorVisitor` to register all function definitions.
 - `error_collector_walker`: uses the same strategy but with all error-collector visitors. This pass performs static checks.
 - `evaluator_walker`: uses `PostOrderTraversalEvaluatorStrategy` and all evaluator visitors. This pass computes results.

All walkers share the same context, so variables and functions persist across passes.

```cython
cpdef tuple[VecLangContext,ASTWalker,ASTWalker,ASTWalker] build_walkers():
    cdef VecLangContext context = VecLangContext()
    cdef TraversalStrategy strategy = PostOrderTraversalStrategy()
    cdef TraversalStrategy eval_strategy = PostOrderTraversalEvaluatorStrategy()
    cdef ASTWalker error_collector_walker = ASTWalker(context,strategy) # type:ignore
    cdef ASTWalker functions_collector = ASTWalker(context,strategy) # type:ignore
    cdef ASTWalker evaluator_walker = ASTWalker(context,eval_strategy) # type:ignore
    # ...

    return context,error_collector_walker,functions_collector,evaluator_walker
```

## Getting the Final Value

After evaluation, we need to extract the result. The helper `get_ast_value(ast,context)`:

 - If the AST is a `VecLangInstructionSequenceAST`, it returns the value of the last instruction.
 - If it's a `VariableExpressionAST`, it looks up the variable in the context.
 - Otherwise, it returns `None` (or you could extend it).

This function is used byt the REPL to display the result.

> ### Recap

File: `visitors.pxd`
```cython
from pylgen.analysis.visitor cimport ASTChildrenSelector,ASTVisitor,ASTWalker,TraversalStrategy
from pylgen.analysis.context cimport Context
from pylgen.common.types cimport AST

from .asts cimport (
    FunctionArgsAST,
    FunctionDeclAST,
    FunctionCallAST
)

cdef class VecLangContext(Context):

    cdef set[str] _built_in_functions
    cdef dict[str,tuple[AST,list[tuple[str,str]]]] _functions
    cdef list[object] _var_values
    cdef list[type] _var_types
    cdef list[bint] _var_flags
    cdef dict[AST,RuntimeError] _runtime_errors
    cdef dict[str,int] _vars_index
    cdef list[object] _eval_stack
    cdef list[tuple[list[object],list[type],list[bint],dict[str,int],list[object]]] _scopes

    cdef tuple[bint,object] look_for_var(self,str var_name)
    cdef void assign_var(self,str var_name,object value)

    cpdef void reset(self)

    cpdef void hard_reset(self)

cdef class PostOrderTraversalStrategy(TraversalStrategy):

    cdef list[tuple[AST,bint]] _stack

    cdef void set_function_scope(self,FunctionDeclAST func_ast, VecLangContext context)

cdef class PostOrderTraversalEvaluatorStrategy(TraversalStrategy):

    cdef list[tuple[AST,bint]] _stack

cdef class DefaultChildrenSelector(ASTChildrenSelector):
    pass

##########################################################################
#                        FUNCTION-COLLECTORS
##########################################################################
cdef class FunctionDeclASTCollectorVisitor(ASTVisitor):
    pass

##########################################################################
#                        ERROR-COLLECTORS
##########################################################################
cdef class FunctionCallASTErrorCollectorVisitor(ASTVisitor):
    
    cdef dict[str,object] _checkers

    cdef void _sum_checker(self,VecLangContext context,FunctionArgsAST args)

    cdef void _dot_checker(self,VecLangContext context, FunctionArgsAST args)

    cdef void _mean_checker(self,VecLangContext context,FunctionArgsAST args)

    cdef void _print_checker(self, VecLangContext context, FunctionArgsAST args)

    cdef void _check_call_loop(self,VecLangContext context, FunctionCallAST call)

cdef class VectorComponentsASTErrorCollector(ASTVisitor):
    pass

cdef class SlicingASTErrorCollectorVisitor(ASTVisitor):
    pass

cdef class IndexingASTErrorCollectorVisitor(ASTVisitor):
    pass

cdef class BinaryASTErrorCollectorVisitor(ASTVisitor):
    pass

##########################################################################
#                                 VARIABLE INDEXING VISITOR
##########################################################################

cdef class VariableIndexerVisitor(ASTVisitor):
    pass

##########################################################################
#                            EVALUATORS
##########################################################################

cdef class BinaryASTEvaluatorVisitor(ASTVisitor):
    
    cdef type _left_type # type:ignore
    cdef type _right_type # type:ignore
    cdef object _left_value
    cdef object _right_value
    cdef bint _runtime_error

cdef class PlusASTEvaluatorVisitor(BinaryASTEvaluatorVisitor):
    pass

cdef class MinusASTEvaluatorVisitor(BinaryASTEvaluatorVisitor):
    pass

cdef class MulASTEvaluatorVisitor(BinaryASTEvaluatorVisitor):
    pass

cdef class ExpASTEvaluatorVisitor(BinaryASTEvaluatorVisitor):
    pass

cdef class DivASTEvaluatorVisitor(BinaryASTEvaluatorVisitor):
    pass

cdef class ModASTEvaluatorVisitor(BinaryASTEvaluatorVisitor):
    pass

cdef class AssignmentASTEvaluatorVisitor(BinaryASTEvaluatorVisitor):
    pass

cdef class FunctionCallASTEvaluatorVisitor(ASTVisitor):
    
    cdef dict[str,object] _evaluators

    cdef ASTWalker _evaluator

    cdef void _print(self,VecLangContext context,FunctionArgsAST args)

    cdef void _sum(self,VecLangContext context, FunctionArgsAST args)

    cdef void _dot(self,VecLangContext context, FunctionArgsAST args)

    cdef void _mean(self,VecLangContext context, FunctionArgsAST args)

cdef class VectorComponentsASTEvaluatorVisitor(ASTVisitor):
    pass

cdef class VectorASTEvaluatorVisitor(ASTVisitor):
    pass

cdef class RangeASTEvaluatorVisitor(ASTVisitor):
    pass

cdef class SlicingASTEvaluatorVisitor(ASTVisitor):
    pass

cdef class IndexingASTEvaluatorVisitor(ASTVisitor):
    pass

cdef class NumberASTEvaluetorVisitor(ASTVisitor):
    pass

cpdef tuple[VecLangContext,ASTWalker,ASTWalker,ASTWalker] build_walkers()

cpdef object get_ast_value(AST ast,VecLangContext context)
```

File: `visitors.pyx`
```cython
from pylgen.analysis.visitor cimport ASTChildrenSelector,ASTVisitor,ASTWalker,TraversalStrategy
from pylgen.analysis.context cimport Context
from pylgen.common.types cimport AST,RuntimeError,SemanticError

import numpy as np # type:ignore

from .asts cimport (
    FunctionCallAST,
    SlicingAST,
    RangeAST,
    VectorAST,
    VectorComponentsAST,
    IndexingAST,
    BinaryAST,
    VariableExpressionAST,
    AssignmentAST,
    PlusAST,
    MinusAST,
    MulAST,
    DivAST,
    ModAST,
    ExpAST,
    NumberAST,
    VecLangInstructionsSequenceAST,
    FunctionArgsAST,
    FunctionDeclAST,
    FunctionDeclArgsAST,
    TypeAST,
    VariableExpression,
    FunctionDecl,
    FunctionCall,
    Vector,
    Range,
    Slicing,
    Number,
    NumberExpression,
    eq
)

from .errors cimport(
    DivisionByZeroError,
    UnSupportedOperationForTypesError,
    ModuleByZeroError,
    BadRangeError,
    InvalidOperationError,
    IndexOutOfRangeError
)

cdef class VecLangContext(Context):

    def __init__(self) -> None:
        super().__init__()
        self._built_in_functions = { 
            'sum',
            'dot',
            'mean',
            'print',
        }
        self._functions = {}
        self._var_flags = []
        self._var_values = []
        self._scopes = []
        self._eval_stack = []
        self._runtime_errors = {}
        self._vars_index = {}
        self._var_types = []
    
    cpdef void reset(self):
        super(VecLangContext,self).reset()
        self._var_flags.clear()
        self._var_values.clear()
        self._scopes.clear()
        self._eval_stack.clear()
        self._vars_index.clear()
        self._var_types.clear()
    
    cpdef void hard_reset(self):
        self.reset()
        self._functions.clear()

    cdef tuple[bint,object] look_for_var(self,str var_name):
        cdef int idx
        cdef int length = len(self._scopes)
        cdef tuple[list[object],list[type],list[bint],dict[str,int],list[object]] scope
        cdef list[object] values
        cdef dict[str,int] idxs

        if var_name in self._vars_index:
            return True, self._var_values[self._vars_index[var_name]]

        for idx in range(length - 1, -1, -1):
            scope = self._scopes[idx]
            values,_,_,idxs,_ = scope
            if var_name in idxs:
                return True, values[idxs[var_name]]
        
        return False,None
    
    cdef void assign_var(self,str var_name,object value):
        cdef int idx,tidx
        cdef int length = len(self._scopes)
        cdef tuple[list[object],list[type],list[bint],dict[str,int],list[object]] scope
        cdef list[object] values
        cdef list[type] types
        cdef list[bint] flags
        cdef dict[str,int] idxs
        cdef list[object] stack

        if var_name in self._vars_index:
            idx = self._vars_index[var_name]
            self._var_flags[idx] = True # type:ignore
            self._var_types[idx] = type(value)
            self._var_values[idx] = value
        else:
            for idx in range(length - 1, -1, -1):
                scope = self._scopes[idx]
                values,types,flags,idxs,stack = scope
                if var_name in idxs:
                    tidx = idxs[var_name]
                    values[tidx] = value
                    flags[tidx] = True # type:ignore
                    types[tidx] = type(value)
                    scope = (values,types,flags,idxs,stack)
                    self._scopes[idx] = scope
                    break

    cpdef list[RuntimeError] get_runtime_errors(self):
        return list(self._runtime_errors.values()) # type:ignore
    
    cpdef void clear_runtime_errors(self):
        self._runtime_errors.clear()

    cpdef void push_new_scope(self):
        cdef tuple[list[object],list[type],list[bint],dict[str,int],list[object]] new_scope
        new_scope = (self._var_values,self._var_types,self._var_flags,self._vars_index,self._eval_stack)
        self._scopes.append(new_scope)
        self._var_values = []
        self._var_types = []
        self._var_flags = []
        self._vars_index = {}
    
    cpdef void pop_scope(self):
        cdef tuple[dict[str,AST],list[object],list[type],list[bint],dict[str,int],list[object]] new_scope
        new_scope = self._scopes.pop()
        self._var_values,self._var_types,self._var_flags,self._vars_index,self._eval_stack = new_scope
        
    cpdef void add_runtime_error(self, AST ast,RuntimeError error):
        if not ast in self._runtime_errors:
            self._runtime_errors[ast] = error # type:ignore

cdef class PostOrderTraversalStrategy(TraversalStrategy):

    def __init__(self) -> None:
        super().__init__(VecLangContext)
        self._stack = []
    
    cdef void set_function_scope(self,FunctionDeclAST func_ast, VecLangContext context):
        cdef tuple[AST,list[tuple[str,str]]] func_scope
        cdef str var_name,var_type
        cdef int var_index

        if func_ast._name in context._functions:
            func_scope = context._functions[func_ast._name]
            
            for var_name,var_type in func_scope[1]: # type:ignore
                var_index = len(context._vars_index)
                context._vars_index[var_name] = var_index
                context._var_flags.append(False) # type:ignore
                context._var_values.append(None)
                if var_type == 'int':
                    context._var_types.append(np.int64)
                elif var_type == 'float':
                    context._var_types.append(np.float64)
                elif var_type == 'complex':
                    context._var_types.append(np.complex128)
                else:
                    context._var_types.append(np.ndarray)
    
    cpdef void init(self,AST root):
        super(PostOrderTraversalStrategy,self).init(root)
        self._stack.append((root,False))
    
    cpdef bint has_next(self):
        return len(self._stack) > 0 # type:ignore

    cpdef AST current(self,Context context):

        cdef AST node
        cdef bint processed
        cdef ASTChildrenSelector selector
        cdef list[AST] children
        cdef int idx

        while self._stack:
            node,processed = self._stack.pop()
            if processed:
                if node._symbol == FunctionDecl:
                    context.pop_scope()
                return node

            if node._symbol == FunctionDecl:
                context.push_new_scope()
                self.set_function_scope(node,context) # type:ignore

            self._stack.append((node,True))
            selector = self._get_selector(node) # type:ignore
            children = selector.select_children(node,context)
            for idx in range(len(children) - 1,-1,-1):
                self._stack.append((children[idx],False))
        return None # type:ignore
    
    cpdef void reset(self):
        self._stack.clear()

cdef class PostOrderTraversalEvaluatorStrategy(TraversalStrategy):

    def __init__(self) -> None:
        super().__init__(VecLangContext)
        self._stack = []

    cpdef void init(self,AST root):
        super(PostOrderTraversalEvaluatorStrategy,self).init(root)
        self._stack.append((root,False))
    
    cpdef bint has_next(self):
        return len(self._stack) > 0 # type:ignore

    cpdef AST current(self,Context context):

        cdef AST node
        cdef bint processed
        cdef ASTChildrenSelector selector
        cdef list[AST] children
        cdef int idx

        while self._stack:
            if (<VecLangContext>context)._runtime_errors:
                self._stack.clear()
                break
            node,processed = self._stack.pop()
            if processed:
                return node

            self._stack.append((node,True))
            selector = self._get_selector(node) # type:ignore
            children = selector.select_children(node,context)
            for idx in range(len(children) - 1,-1,-1):
                self._stack.append((children[idx],False))
        return None # type:ignore
    
    cpdef void reset(self):
        self._stack.clear()

cdef class DefaultChildrenSelector(ASTChildrenSelector):
    
    def __init__(self) -> None:
        super().__init__(VecLangContext)
    
    cpdef list[AST] select_children(self,AST ast,Context context):
        self._check_context_type(context)
        return ast.children()

cdef class FunctionDeclASTChildrenSelector(ASTChildrenSelector):

    def __init__(self) -> None:
        super().__init__(VecLangContext)
    
    cpdef list[AST] select_children(self, AST ast, Context context):
        self._check_context_type(context)
        return []

cdef class FunctionDeclASTCollectorVisitor(ASTVisitor):

    def __init__(self) -> None:
        super().__init__(VecLangContext)
    
    cpdef void visit(self,AST ast, Context context):
        cdef FunctionDeclAST func = ast # type:ignore
        cdef FunctionDeclArgsAST args = func._args
        cdef VariableExpressionAST var
        cdef str var_type
        cdef tuple[AST,list[tuple[str,str]]] function_base_context
        cdef list[tuple[str,str]] arg_vars = []

        for var,var_type in args._args.items():
            arg_vars.append((var._name,var_type))

        self._check_context_type(context)
        function_base_context = (func._body,arg_vars)
        (<VecLangContext>context)._functions[func._name] = (func._body,arg_vars)

cdef class FunctionCallASTErrorCollectorVisitor(ASTVisitor):
    
    def __init__(self) -> None:
        super().__init__(VecLangContext)
        self._checkers = {
            'sum':self._sum_checker,
            'dot':self._dot_checker,
            'mean':self._mean_checker,
            'print':self._print_checker
        }
    
    cdef void _print_checker(self, VecLangContext context, FunctionArgsAST args):
        cdef SemanticError error
        cdef AST arg
        cdef VariableExpressionAST var

        if len(args._args) != 1:
            error = SemanticError(f'Wrong number of args: got {len(args._args)}, expected 1',args._start_line,args._start_column,args._end_line,args._end_column) # type:ignore
            context.add_semantic_error(error)
        
        if len(args._args) < 1:
            return # type:ignore

        arg = args._args[0]

        if arg._symbol == VariableExpression:
            var = arg # type:ignore
            if not (<VecLangContext>context).look_for_var(var._name)[0]:
                error = SemanticError(f'Undeclared variable "{var._name}"',var._start_line,var._start_column,var._end_line,var._end_column) # type:ignore
                context.add_semantic_error(error)

    cdef void _mean_checker(self,VecLangContext context, FunctionArgsAST args):
        cdef SemanticError error
        cdef AST arg
        cdef VariableExpressionAST var

        if len(args._args) != 1:
            error = SemanticError(f'Wrong number of args: got {len(args._args)}, expected 1',args._start_line,args._start_column,args._end_line,args._end_column) # type:ignore
            context.add_semantic_error(error)
        
        if len(args._args) < 1:
            return # type:ignore

        arg = args._args[0]

        if arg._symbol == VariableExpression:
            var = arg # type:ignore
            if not (<VecLangContext>context).look_for_var(var._name)[0]:
                error = SemanticError(f'Undeclared variable "{var._name}"',var._start_line,var._start_column,var._end_line,var._end_column) # type:ignore
                context.add_semantic_error(error)
    
    cdef void _dot_checker(self,VecLangContext context, FunctionArgsAST args):
        cdef SemanticError error
        cdef AST arg
        cdef VariableExpressionAST var

        if len(args._args) != 2:
            error = SemanticError(f'Wrong number of args: got {len(args._args)}, expected 2',args._start_line,args._start_column,args._end_line,args._end_column) # type:ignore
            context.add_semantic_error(error)

        if len(args._args) < 1:
            return # type:ignore

        arg = args._args[0]

        if arg._symbol == VariableExpression:
            var = arg # type:ignore
            if not (<VecLangContext>context).look_for_var(var._name)[0]:
                error = SemanticError(f'Undeclared variable "{var._name}"',var._start_line,var._start_column,var._end_line,var._end_column) # type:ignore
                context.add_semantic_error(error)

        if len(args._args) < 2:
            return # type:ignore

        arg = args._args[1]

        if arg._symbol == VariableExpression:
            var = arg # type:ignore
            if not (<VecLangContext>context).look_for_var(var._name)[0]:
                error = SemanticError(f'Undeclared variable "{var._name}"',var._start_line,var._start_column,var._end_line,var._end_column) # type:ignore
                context.add_semantic_error(error)

    cdef void _sum_checker(self,VecLangContext context, FunctionArgsAST args):
        cdef SemanticError error
        cdef AST arg
        cdef VariableExpressionAST var

        if len(args._args) != 1:
            error = SemanticError(f'Wrong number of args: got {len(args._args)}, expected 1',args._start_line,args._start_column) # type:ignore
            context.add_semantic_error(error)

        arg = args._args[0]

        if arg._symbol == VariableExpression:
            var = arg # type:ignore
            if not (<VecLangContext>context).look_for_var(var._name)[0]:
                error = SemanticError(f'Undeclared variable "{var._name}"',var._start_line,var._start_column,var._end_line,var._end_column) # type:ignore
                context.add_semantic_error(error)

    cdef void _check_call_loop(self,VecLangContext context, FunctionCallAST call):
        cdef AST func_body
        cdef tuple[AST,list[tuple[str,str]]] func_data
        cdef list[AST] asts,seens
        cdef AST child,current
        cdef SemanticError error
        cdef FunctionCallAST func_call

        func_data = (<VecLangContext>context)._functions[call._function_name]
        func_body,_ = func_data

        asts = [func_body]
        seens = []

        while asts:

            current = asts.pop()
            seens.append(current)

            for child in current.children():
                if child._symbol == FunctionCall:
                    func_call = <FunctionCallAST>child # type:ignore
                    if func_call._function_name == call._function_name:
                        error = SemanticError(f'Infinite loop call detected for function {call._function_name}',child._start_line,child._start_column,child._end_line,child._end_column) # type:ignore
                        if not error in context._errors:
                            context.add_semantic_error(error)

                    func_data = (<VecLangContext>context)._functions[func_call._function_name]
                    func_body,_ = func_data
                    
                    if not func_body in seens:
                        asts.append(func_body)

                if not child in seens:
                    asts.append(child)

    cpdef void visit(self, AST ast,Context context):
        cdef SemanticError error
        cdef FunctionCallAST func = ast # type:ignore
        cdef tuple[AST,list[tuple[str,str]]] func_data
        cdef FunctionArgsAST args
        cdef list[tuple[str,str]] func_signature
        cdef AST func_body
        cdef VariableExpressionAST var_arg
        cdef AST arg
        cdef int idx,sig_args_len,args_len

        self._check_context_type(context)
        if not (func._function_name in (<VecLangContext>context)._functions or func._function_name in (<VecLangContext>context)._built_in_functions):
            error = SemanticError(f'function {func._function_name} doesn\'t exists',func._start_line,func._start_column,func._end_line,func._end_column) # type:ignore
            context.add_semantic_error(error)
        
        if func._function_name in self._checkers:
            self._checkers[func._function_name](context,func._args) # type:ignore
        elif func._function_name == 'print':
            pass
        else:

            if not func._function_name in (<VecLangContext>context)._functions:
                return # type:ignore
            
            self._check_call_loop(context,func) # type:ignore
            
            func_data = (<VecLangContext>context)._functions[func._function_name]
            func_body,func_signature = func_data
            args = func._args
            sig_args_len = len(func_signature)
            args_len = len(args._args)
            args = func._args
            if args_len != sig_args_len:
                error = SemanticError(f'Wrong number of args: got {args_len}, expected {sig_args_len}',args._start_line,args._start_column,args._end_line,args._end_column) # type:ignore
                context.add_semantic_error(error)
            else:
                for idx in range(args_len):
                    arg = args._args[idx]
                    param_type_tuple = func_signature[idx]
                    if arg._symbol == VariableExpression:
                        var_arg = arg # type:ignore
                        if not (<VecLangContext>context).look_for_var(var_arg._name)[0]:
                            error = SemanticError(f'Undeclared variable "{var_arg._name}"',var_arg._start_line,var_arg._start_column,var_arg._end_line,var_arg._end_column) # type:ignore
                            context.add_semantic_error(error)

cdef class VectorComponentsASTErrorCollector(ASTVisitor):

    def __init__(self) -> None:
        super().__init__(VecLangContext)
    
    cpdef void visit(self,AST ast, Context context):
        cdef VectorComponentsAST components = ast # type:ignore
        cdef VariableExpressionAST var
        cdef AST component
        cdef int idx
        cdef int length = len(components._components)
        cdef SemanticError error

        self._check_context_type(context)

        for idx in range(length):
            component = components._components[idx]
            if component._symbol == VariableExpression:
                var = component # type:ignore
                if not (<VecLangContext>context).look_for_var(var._name)[0]:
                    error = SemanticError(f'Undeclared variable "{var._name}"',var._start_line,var._start_column,var._end_line,var._end_column) # type:ignore
                    context.add_semantic_error(error)

cdef class SlicingASTErrorCollectorVisitor(ASTVisitor):
    
    def __init__(self) -> None:
        super().__init__(VecLangContext)
    
    cpdef void visit(self,AST ast,Context context):
        cdef SemanticError error1,error2
        cdef SlicingAST slice = ast # type:ignore
        cdef AST target = slice._target
        cdef RangeAST _range = slice._range
        cdef VectorComponentsAST components
        cdef RangeAST inner_range
        cdef VariableExpressionAST var

        self._check_context_type(context)
        if _range._min < 0:
            error1 = SemanticError(f'min index can\'t be less than 0',_range._start_line,_range._start_column,_range._end_line,_range._end_column) # type:ignore
            context.add_semantic_error(error1)
        if target._symbol == Vector:
            components = (<VectorAST>target)._components
            if _range._max > len(components._components):
                error2 = SemanticError(f'max index can\'t be greater than vector size',_range._start_line,_range._start_column,_range._end_line,_range._end_column) # type:ignore
                context.add_semantic_error(error2)
        elif target._symbol == Range:
            if _range._max > (<RangeAST>target)._max - (<RangeAST>target)._min:
                error2 = SemanticError(f'max index can\'t be greater than range size',_range._start_line,_range._start_column,_range._end_line,_range._end_column) # type:ignore
                context.add_semantic_error(error2)
        elif target._symbol == Slicing:
            inner_range = (<SlicingAST>target)._range
            if _range._max > inner_range._max - inner_range._min:
                error2 = SemanticError(f'max index can\'t be greater than range size',_range._start_line,_range._start_column,_range._end_line,_range._end_column) # type:ignore
                context.add_semantic_error(error2)
        elif target._symbol == VariableExpression:
            var = target # type:ignore
            if not (<VecLangContext>context).look_for_var(var._name)[0]:
                error2 = SemanticError(f'undeclared variable "{var._name}"',var._start_line,var._start_column,var._end_line,var._end_column) # type:ignore
                context.add_semantic_error(error2)

cdef class IndexingASTErrorCollectorVisitor(ASTVisitor):
    
    def __init__(self) -> None:
        super().__init__(VecLangContext)
    
    cpdef void visit(self,AST ast, Context context):
        cdef SemanticError error
        cdef IndexingAST indexing = ast # type:ignore
        cdef AST target = indexing._target
        cdef VectorComponentsAST components

        self._check_context_type(context)
        if target._symbol == Vector:
            components = (<VectorAST>target)._components
            if indexing._index > len(components._components) - 1 or indexing._index < 0:
                error = SemanticError(f'index out of range',indexing._start_line,indexing._start_column,indexing._end_line,indexing._end_column) # type:ignore
                context.add_semantic_error(error)
        elif target._symbol == Range:
            if indexing._index < 0 or indexing._index > (<RangeAST>target)._max - (<RangeAST>target)._min - 1:
                error = SemanticError(f'index out of range',indexing._start_line,indexing._start_column,indexing._end_line,indexing._end_column) # type:ignore
                context.add_semantic_error(error)

cdef class BinaryASTErrorCollectorVisitor(ASTVisitor):
    
    def __init__(self) -> None:
        super().__init__(VecLangContext)
    
    cpdef void visit(self, AST ast, Context context):
        cdef SemanticError error1,error2
        cdef BinaryAST op = ast # type:ignore
        cdef VecLangContext _context = context # type:ignore
        cdef VariableExpressionAST var

        self._check_context_type(context)
        if op._left._symbol == VariableExpression:
            var = op._left # type:ignore
            if op._symbol != eq:
                if not _context.look_for_var(var._name)[0]:
                    error1 = SemanticError(f'variable "{var._name}" doesn\'t exists',var._start_line,var._start_column,var._end_line,var._end_column) # type:ignore
                    context.add_semantic_error(error1)

        if op._right._symbol == VariableExpression:
            var = op._right # type:ignore
            if not _context.look_for_var(var._name)[0]:
                error2 = SemanticError(f'variable "{var._name}" doesn\'t exists',var._start_line,var._start_column,var._end_line,var._end_column) # type:ignore
                context.add_semantic_error(error2)

cdef class VariableIndexerVisitor(ASTVisitor):

    def __init__(self) -> None:
        super().__init__(VecLangContext)
    
    cpdef void visit(self,AST ast,Context context):
        cdef AssignmentAST assignment = ast # type:ignore
        cdef VariableExpressionAST var = assignment._left # type:ignore
        cdef int idx

        if not (<VecLangContext>context).look_for_var(var._name)[0]:
            idx = len((<VecLangContext>context)._var_values)
            (<VecLangContext>context)._vars_index[var._name] = idx
            (<VecLangContext>context)._var_flags.append(False) # type:ignore
            (<VecLangContext>context)._var_values.append(None)
            (<VecLangContext>context)._var_types.append(None) # type:ignore
            var._index = idx

cdef class NumberASTEvaluatorVisitor(ASTVisitor):

    def __init__(self) -> None:
        super().__init__(VecLangContext) # type:ignore
    
    cpdef void visit(self,AST ast, Context context):
        cdef NumberAST number = ast # type:ignore
        
        self._check_context_type(context)
        (<VecLangContext>context)._eval_stack.append(number._type(number._value)) # type:ignore

cdef class BinaryASTEvaluatorVisitor(ASTVisitor):

    def __init__(self) -> None:
        super().__init__(VecLangContext)
        self._runtime_error = False # type:ignore
    
    cpdef void visit(self,AST ast, Context context):
        cdef BinaryAST binary = ast # type:ignore
        cdef VariableExpressionAST var
        cdef NumberAST number
        cdef RuntimeError error

        self._check_context_type(context)
        if binary._right._symbol == VariableExpression:
            var = binary._right # type:ignore
            self._right_value = (<VecLangContext>context).look_for_var(var._name)[1]
        else:
            self._right_value = (<VecLangContext>context)._eval_stack.pop()
        self._right_type = type(self._right_value)
        
        if binary._left._symbol == VariableExpression:
            var = binary._left # type:ignore
            self._left_value = (<VecLangContext>context).look_for_var(var._name)[1]
        else:
            self._left_value = (<VecLangContext>context)._eval_stack.pop()
        self._left_type = type(self._left_value)
        if self._left_type == self._right_type and self._left_type == np.ndarray:
            if self._left_value.shape != self._right_value.shape: # type:ignore
                error = InvalidOperationError(context._stack,ast._start_line,ast._start_column,ast._end_line,ast._end_column,'Vectors operands must have same size') # type:ignore
                context.add_runtime_error(ast,error)
                self._runtime_error = True # type:ignore

cdef class AssignmentASTEvaluatorVisitor(BinaryASTEvaluatorVisitor):

    cpdef void visit(self,AST ast, Context context):
        cdef AssignmentAST assignment = ast # type:ignore
        cdef VariableExpressionAST var = assignment._left # type:ignore

        super(AssignmentASTEvaluatorVisitor,self).visit(ast,context)
        (<VecLangContext>context).assign_var(var._name,self._right_value)

cdef class PlusASTEvaluatorVisitor(BinaryASTEvaluatorVisitor):

    cpdef void visit(self,AST ast, Context context):

        super(PlusASTEvaluatorVisitor,self).visit(ast,context)
        if self._left_value is None:
            (<VecLangContext>context)._eval_stack.append(None)
            self._runtime_error = True # type:ignore
        if self._right_value is None:
            (<VecLangContext>context)._eval_stack.append(None)
            self._runtime_error = True # type:ignore
        if not self._runtime_error:
            (<VecLangContext>context)._eval_stack.append(self._left_value + self._right_value) # type:ignore

cdef class MinusASTEvaluatorVisitor(BinaryASTEvaluatorVisitor):

    cpdef void visit(self,AST ast, Context context):

        super(MinusASTEvaluatorVisitor,self).visit(ast,context)
        if self._left_value is None:
            (<VecLangContext>context)._eval_stack.append(None)
            self._runtime_error = True # type:ignore
        if self._right_value is None:
            (<VecLangContext>context)._eval_stack.append(None)
            self._runtime_error = True # type:ignore
        if not self._runtime_error:
            (<VecLangContext>context)._eval_stack.append(self._left_value - self._right_value) # type:ignore

cdef class MulASTEvaluatorVisitor(BinaryASTEvaluatorVisitor):

    cpdef void visit(self,AST ast, Context context):

        super(MulASTEvaluatorVisitor,self).visit(ast,context)
        if self._left_value is None:
            (<VecLangContext>context)._eval_stack.append(None)
            self._runtime_error = True # type:ignore
        if self._right_value is None:
            (<VecLangContext>context)._eval_stack.append(None)
            self._runtime_error = True # type:ignore
        if not self._runtime_error:
            (<VecLangContext>context)._eval_stack.append(self._left_value * self._right_value) # type:ignore

cdef class DivASTEvaluatorVisitor(BinaryASTEvaluatorVisitor):

    cpdef void visit(self,AST ast, Context context):
        cdef RuntimeError error
        
        super(DivASTEvaluatorVisitor,self).visit(ast,context)
        
        if self._left_value is None:
            (<VecLangContext>context)._eval_stack.append(None)
            self._runtime_error = True # type:ignore
        if self._right_value is None:
            (<VecLangContext>context)._eval_stack.append(None)
            self._runtime_error = True # type:ignore
        if not self._runtime_error:
            if self._right_value == 0:
                error = DivisionByZeroError(context._stack,ast._start_line,ast._start_column,ast._end_line,ast._end_column) # type:ignore
                (<VecLangContext>context).add_runtime_error(ast,error)
                (<VecLangContext>context)._eval_stack.append(None)
            else:
                (<VecLangContext>context)._eval_stack.append(self._left_value / self._right_value) # type:ignore

cdef class ModASTEvaluatorVisitor(BinaryASTEvaluatorVisitor):

    cpdef void visit(self,AST ast,Context context):
        cdef RuntimeError error

        super(ModASTEvaluatorVisitor,self).visit(ast,context)
        if self._left_value is None:
            (<VecLangContext>context)._eval_stack.append(None)
            self._runtime_error = True # type:ignore
        if self._right_value is None:
            (<VecLangContext>context)._eval_stack.append(None)
            self._runtime_error = True # type:ignore
        if not self._runtime_error:
            if self._left_type == np.complex128 or self._right_type == np.complex128:
                error = UnSupportedOperationForTypesError(context._stack,ast._start_line,ast._start_column,ast._end_line,ast._end_column,"%",self._left_type,self._right_type) # type:ignore
                (<VecLangContext>context).add_runtime_error(ast,error)
                (<VecLangContext>context)._eval_stack.append(None)
            elif self._right_value == 0:
                error = ModuleByZeroError(context._stack,ast._start_line,ast._start_column,ast._end_line,ast._end_column) # type:ignore
                (<VecLangContext>context).add_runtime_error(ast,error)
                (<VecLangContext>context)._eval_stack.append(None)
            else:
                (<VecLangContext>context)._eval_stack.append(self._left_value % self._right_value) # type:ignore

cdef class ExpASTEvaluatorVisitor(BinaryASTEvaluatorVisitor):

    cpdef void visit(self,AST ast, Context context):
        cdef int line,column

        super(ExpASTEvaluatorVisitor,self).visit(ast,context)
        if self._left_value is None:
            (<VecLangContext>context)._eval_stack.append(None)
            self._runtime_error = True # type:ignore
        if self._right_value is None:
            (<VecLangContext>context)._eval_stack.append(None)
            self._runtime_error = True # type:ignore
        if not self._runtime_error:
            (<VecLangContext>context)._eval_stack.append(self._left_value ** self._right_value) # type:ignore

cdef class VectorComponentsASTEvaluatorVisitor(ASTVisitor):

    def __init__(self) -> None:
        super().__init__(VecLangContext)
    
    cpdef void visit(self, AST ast, Context context):
        cdef int line,column
        cdef RuntimeError error
        cdef VectorComponentsAST components = ast # type:ignore
        cdef int length = len(components._components)
        cdef int idx
        cdef AST component
        cdef VariableExpressionAST var
        cdef VecLangContext _context
        cdef object value
        cdef str type_name
        cdef list values = [0] * length

        self._check_context_type(context)
        _context = context # type:ignore

        for idx in range(length - 1 ,-1,-1):
            component = components._components[idx]
            if component._symbol == VariableExpression:
                var = component # type:ignore
                value = _context.look_for_var(var._name)[1]
                if value is None:
                    continue
                else:
                    values[idx] = value # type:ignore
            else:
                value = _context._eval_stack.pop()
                if value is None:
                    continue
                else:
                    values[idx] = value # type:ignore
        
        (<VecLangContext>context)._eval_stack.append(np.array(values))

cdef class VectorASTEvaluatorVisitor(ASTVisitor):

    def __init__(self) -> None:
        super().__init__(VecLangContext)
    
    cpdef void visit(self,AST ast, Context context):

        self._check_context_type(context)

cdef class RangeASTEvaluatorVisitor(ASTVisitor):

    def __init__(self) -> None:
        super().__init__(VecLangContext)
    
    cpdef void visit(self,AST ast, Context context):
        cdef RangeAST _range = ast # type:ignore

        self._check_context_type(context)

        _components = np.arange(_range._min,_range._max,dtype=np.int64)
        (<VecLangContext>context)._eval_stack.append(_components)

cdef class SlicingASTEvaluatorVisitor(ASTVisitor):

    def __init__(self) -> None:
        super().__init__(VecLangContext)

    cpdef void visit(self,AST ast, Context context):
        cdef SlicingAST slice = ast # type:ignore
        cdef RangeAST _range = slice._range
        cdef AST target = slice._target
        cdef object value
        cdef VariableExpressionAST var
        cdef type var_type # type:ignore
        cdef RuntimeError error

        self._check_context_type(context)

        (<VecLangContext>context)._eval_stack.pop()
        if target._symbol == Vector or target._symbol == Range or target._symbol == Slicing:
            components = (<VecLangContext>context)._eval_stack.pop()
            (<VecLangContext>context)._eval_stack.append(components[_range._min:_range._max]) # type:ignore
        elif target._symbol == VariableExpression:
            var = target # type:ignore
            value = (<VecLangContext>context).look_for_var(var._name)[1]
            var_type = type(value)
            if var_type != np.ndarray:
                error = InvalidOperationError(context._stack,ast._start_line,ast._start_column,ast._end_line,ast._end_column,f'Slicing operation not supported for type "{var_type}"') # type:ignore
                (<VecLangContext>context).add_runtime_error(ast,error)
                (<VecLangContext>context)._eval_stack.append(None)
            elif _range._max >= len(value): # type:ignore
                error = InvalidOperationError(context._stack,ast._start_line,ast._start_column,ast._end_line,ast._end_column,f'max index is greater than vector size {len(value)}') # type:ignore
                (<VecLangContext>context).add_runtime_error(ast,error)
                (<VecLangContext>context)._eval_stack.append(None)
            else:
                (<VecLangContext>context)._eval_stack.append(value[_range._min:_range._max]) # type:ignore

cdef class IndexingASTEvaluatorVisitor(ASTVisitor):

    def __init__(self) -> None:
        super().__init__(VecLangContext)
    
    cpdef void visit(self,AST ast, Context context):
        cdef IndexingAST indexing = ast # type:ignore
        cdef AST target = indexing._target
        cdef VariableExpressionAST var
        cdef object value
        cdef type var_type # type:ignore
        cdef RuntimeError error

        self._check_context_type(context)

        if target._symbol == VariableExpression:
            var = target # type:ignore
            value = (<VecLangContext>context).look_for_var(var._name)[1]
            var_type = type(value)
            if var_type != np.ndarray:
                error = InvalidOperationError(context._stack,ast._start_line,ast._start_column,ast._end_line,ast._end_column,f'Indexing operation not supported for type "{var_type}"') # type:ignore
                (<VecLangContext>context).add_runtime_error(ast,error)
                (<VecLangContext>context)._eval_stack.append(None)
            elif indexing._index >= len(value): # type:ignore
                error = IndexOutOfRangeError(context._stack,ast._start_line,ast._start_column,ast._end_line,ast._end_column,indexing._index,len(value)) # type:ignore
                (<VecLangContext>context).add_runtime_error(ast,error)
                (<VecLangContext>context)._eval_stack.append(None)
            else:
                (<VecLangContext>context)._eval_stack.append(value[indexing._index]) # type:ignore
        elif target._symbol == Vector or target._symbol == Range or target._symbol == Slicing:
            components = (<VecLangContext>context)._eval_stack.pop()
            if indexing._index >= len(components): # type:ignore
                error = IndexOutOfRangeError(context._stack,ast._start_line,ast._start_column,ast._end_line,ast._end_column,indexing._index,len(components)) # type:ignore
                (<VecLangContext>context).add_runtime_error(ast,error)
                (<VecLangContext>context)._eval_stack.append(None)
            else:
                (<VecLangContext>context)._eval_stack.append(components[indexing._index]) # type:ignore

cdef class FunctionCallASTEvaluatorVisitor(ASTVisitor):

    def __init__(self) -> None:
        cdef TraversalStrategy eval_strategy = PostOrderTraversalEvaluatorStrategy()
        
        super().__init__(VecLangContext)
        self._evaluators = {
            'print':self._print,
            'sum':self._sum,
            'dot':self._dot,
            'mean':self._mean
        }
    
        eval_strategy.set_default_selector_without_signature_checking(DefaultChildrenSelector()) # type:ignore
        eval_strategy.add_selector_without_signature_checking(FunctionDeclAST,FunctionDeclASTChildrenSelector()) # type:ignore
        
        self._evaluator = ASTWalker(VecLangContext(),eval_strategy) # type:ignore

        self._evaluator.add_visitor_without_signature_checking(NumberAST,NumberASTEvaluatorVisitor())
        self._evaluator.add_visitor_without_signature_checking(AssignmentAST,AssignmentASTEvaluatorVisitor())
        self._evaluator.add_visitor_without_signature_checking(PlusAST,PlusASTEvaluatorVisitor())
        self._evaluator.add_visitor_without_signature_checking(MinusAST,MinusASTEvaluatorVisitor())
        self._evaluator.add_visitor_without_signature_checking(MulAST,MulASTEvaluatorVisitor())
        self._evaluator.add_visitor_without_signature_checking(DivAST,DivASTEvaluatorVisitor())
        self._evaluator.add_visitor_without_signature_checking(ModAST,ModASTEvaluatorVisitor())
        self._evaluator.add_visitor_without_signature_checking(ExpAST,ExpASTEvaluatorVisitor())
        self._evaluator.add_visitor_without_signature_checking(VectorComponentsAST,VectorComponentsASTEvaluatorVisitor())
        self._evaluator.add_visitor_without_signature_checking(VectorAST,VectorASTEvaluatorVisitor())
        self._evaluator.add_visitor_without_signature_checking(RangeAST,RangeASTEvaluatorVisitor())
        self._evaluator.add_visitor_without_signature_checking(SlicingAST,SlicingASTEvaluatorVisitor())
        self._evaluator.add_visitor_without_signature_checking(IndexingAST,IndexingASTEvaluatorVisitor())
        self._evaluator.add_visitor_without_signature_checking(FunctionCallAST,self)

    cdef void _mean(self,VecLangContext context, FunctionArgsAST args):
        cdef AST arg
        cdef RuntimeError error
        cdef VariableExpressionAST var
        cdef type var_type # type:ignore
        cdef object val,var_val

        arg = args._args[0]
        
        if arg._symbol == VariableExpression:
            var = arg # type:ignore
            var_val = context.look_for_var(var._name)[1]
            var_type = type(var_val)
            if var_type != np.ndarray and not var_val is None:
                error = InvalidOperationError(context._stack,arg._start_line,arg._start_column,arg._end_line,arg._end_column,f'arg1 must be of type "Vector"; got {var_type}') # type:ignore
                context.add_runtime_error(arg,error)
                val = None
            else:
                val = var_val
        else:
            val = context._eval_stack.pop()
            var_type = type(val)
            if var_type != np.ndarray and not val is None:
                error = InvalidOperationError(context._stack,arg._start_line,arg._start_column,arg._end_line,arg._end_column,f'arg1 must be of type "Vector"; got {var_type}') # type:ignore
                context.add_runtime_error(arg,error)
        
        if val is None:
            context._eval_stack.append(None)
        else:
            context._eval_stack.append(float(np.mean(val)))

    cdef void _dot(self,VecLangContext context, FunctionArgsAST args):
        cdef AST arg1,arg2
        cdef RuntimeError error
        cdef VariableExpressionAST var
        cdef type var_type # type:ignore
        cdef object val1,val2,var_val

        arg1 = args._args[0]
        arg2 = args._args[1]

        if arg2._symbol == VariableExpression:
            var = arg2 # type:ignore
            var_val = context.look_for_var(var._name)[1]
            var_type = type(var_val)
            if var_type != np.ndarray and not var_val is None:
                error = InvalidOperationError(context._stack,arg2._start_line,arg2._start_column,arg2._end_line,arg2._end_column,f'arg2 must be of type "Vector"; got {var_type}') # type:ignore
                context.add_runtime_error(arg2,error)
                val2 = None
            else:
                val2 = context.look_for_var(var._name)[1]
        else:
            val2 = context._eval_stack.pop()
            var_type = type(val2)
            if var_type != np.ndarray and not val2 is None:
                error = InvalidOperationError(context._stack,arg2._start_line,arg2._start_column,arg2._end_line,arg2._end_column,f'arg2 must be of type "Vector"; got {var_type}') # type:ignore
                context.add_runtime_error(arg1,error)
        
        if arg1._symbol == VariableExpression:
            var = arg1 # type:ignore
            var_val = context.look_for_var(var._name)[1]
            var_type = type(var_val)
            if var_type != np.ndarray and not var_val is None:
                error = InvalidOperationError(context._stack,arg1._start_line,arg1._start_column,arg1._end_line,arg1._end_column,f'arg1 must be of type "Vector"; got {var_type}') # type:ignore
                context.add_runtime_error(arg1,error)
                val1 = None
            else:
                val1 = context.look_for_var(var._name)[1]
        else:
            val1 = context._eval_stack.pop()
            var_type = type(val1)
            if var_type != np.ndarray and not val1 is None:
                error = InvalidOperationError(context._stack,arg1._start_line,arg1._start_column,arg1._end_line,arg1._end_column,f'arg1 must be of type "Vector"; got {var_type}') # type:ignore
                context.add_runtime_error(arg1,error)
        
        if val1 is None:
            context._eval_stack.append(None)
        elif val2 is None:
            context._eval_stack.append(None)
        else:
            if val1.shape != val2.shape: # type:ignore
                error = InvalidOperationError(context._stack,arg1._start_line,arg1._start_column,arg2._end_line,arg2._end_column,f'dot product invalid; vectors must have the same size') # type:ignore
                context.add_runtime_error(args,error)
                context._eval_stack.append(None)
            else:
                context._eval_stack.append(np.dot(val1,val2))

    cdef void _sum(self,VecLangContext context,FunctionArgsAST args):
        cdef AST arg
        cdef RuntimeError error
        cdef VariableExpressionAST var
        cdef type var_type # type:ignore
        cdef object val,var_val

        arg = args._args[0]
        
        if arg._symbol == VariableExpression:
            var = arg # type:ignore
            var_val = context.look_for_var(var._name)[1]
            var_type = type(var_val)
            if var_type != np.ndarray and not var_val is None:
                error = InvalidOperationError(context._stack,arg._start_line,arg._start_column,arg._end_line,arg._end_column,f'arg1 must be of type "Vector"; got {var_type}') # type:ignore
                context.add_runtime_error(arg,error)
                val = None
            else:
                val = var_val
        else:
            val = context._eval_stack.pop()
            var_type = type(val)
            if var_type != np.ndarray and not val is None:
                error = InvalidOperationError(context._stack,arg._start_line,arg._start_column,arg._end_line,arg._end_column,f'arg1 must be of type "Vector"; got {var_type}') # type:ignore
                context.add_runtime_error(arg,error)
        
        if val is None:
            context._eval_stack.append(None)
        else:
            context._eval_stack.append(np.sum(val))

    cdef void _print(self,VecLangContext context,FunctionArgsAST args):
        cdef AST arg = args._args[0]
        cdef VariableExpressionAST var
        cdef object val

        if context._runtime_errors:
            return # type:ignore

        if arg._symbol == VariableExpression:
            var = arg # type:ignore
            print(context.look_for_var(var._name)[1])
        else:
            val = context._eval_stack[-1]
            if not val is None:
                print(val)

    cpdef void visit(self,AST ast, Context context):
        cdef FunctionCallAST call = ast # type:ignore
        cdef FunctionArgsAST args = call._args
        cdef RuntimeError error
        cdef AST func_body
        cdef list[tuple[str,str]] func_signature
        cdef int idx,call_var_arg_index
        cdef tuple[str,str] param_type_tuple
        cdef bint runtime_error = False # type:ignore
        cdef object  arg_value
        cdef type arg_type
        cdef AST arg
        cdef VariableExpressionAST var
        cdef list[object] arguments = [None] * len(args._args)

        self._check_context_type(context)

        for idx in range(len(args._args)):
            arg = args._args[idx]
            if arg._symbol == VariableExpression:
                var = arg # type:ignore
                arguments[idx] = (<VecLangContext>context).look_for_var(var._name)[1]
            else:
                arguments[idx] = (<VecLangContext>context)._eval_stack.pop()
        
        (<VecLangContext>context).push_new_scope()
        (<VecLangContext>context).push_trace(call._function_name)
        (<VecLangContext>context)._eval_stack.extend(arguments)

        if call._function_name in (<VecLangContext>context)._built_in_functions:
            self._evaluators[call._function_name](context,call._args) # type:ignore
        else:

            func_body,func_signature = (<VecLangContext>context)._functions[call._function_name]
            
            for idx in range(len(args._args) - 1, -1, -1):
                param_type_tuple = func_signature[idx]
                arg_value = (<VecLangContext>context)._eval_stack.pop()
                arg_type = type(arg_value)

                if arg_value is None:
                    continue
                
                if param_type_tuple[1] == 'vector' and arg_type != np.ndarray:
                    error = RuntimeError(context._stack,ast._start_line,ast._start_column,ast._end_line,ast._end_column,f' expected type for param{idx} is {param_type_tuple[1]}; got {arg_type}') # type:ignore
                    context.add_runtime_error(ast,error)
                    runtime_error = True # type:ignore
                elif param_type_tuple[1] == 'complex' and arg_type == np.ndarray:
                    error = RuntimeError(context._stack,ast._start_line,ast._start_column,ast._end_line,ast._end_column,f' expected type for param{idx} is {param_type_tuple[1]}; got {arg_type}') # type:ignore
                    context.add_runtime_error(ast,error)
                    runtime_error = True # type:ignore
                elif param_type_tuple[1] == 'float' and (arg_type == np.array or arg_type == np.complex128):
                    error = RuntimeError(context._stack,ast._start_line,ast._start_column,ast._end_line,ast._end_column,f' expected type for param{idx} is {param_type_tuple[1]}; got {arg_type}') # type:ignore
                    context.add_runtime_error(ast,error)
                    runtime_error = True # type:ignore
                elif param_type_tuple[1] == 'int' and arg_type != np.int64:
                    error = RuntimeError(context._stack,ast._start_line,ast._start_column,ast._end_line,ast._end_column,f' expected type for param{idx} is {param_type_tuple[1]}; got {arg_type}') # type:ignore
                    runtime_error = True # type:ignore
                    context.add_runtime_error(ast,error)
                
                if param_type_tuple[0] in (<VecLangContext>context)._vars_index:
                    call_var_arg_index = (<VecLangContext>context)._vars_index[param_type_tuple[0]]
                    (<VecLangContext>context)._var_values[call_var_arg_index] = arg_value
                    (<VecLangContext>context)._var_types[call_var_arg_index] = type(arg_value)
                else:
                    call_var_arg_index = idx
                    (<VecLangContext>context)._vars_index[param_type_tuple[0]] = call_var_arg_index
                    (<VecLangContext>context)._var_values.append(arg_value)
                    (<VecLangContext>context)._var_types.append(type(arg_value))

            if not runtime_error:
                self._evaluator._context = context
                self._evaluator.walk(func_body)
                arg_value = (<VecLangContext>context)._eval_stack.pop()
            
            (<VecLangContext>context).pop_scope()
            (<VecLangContext>context).pop_trace()

            if not runtime_error:
                (<VecLangContext>context)._eval_stack.append(arg_value)
            else:
                (<VecLangContext>context)._eval_stack.append(None)

cpdef tuple[VecLangContext,ASTWalker,ASTWalker,ASTWalker] build_walkers():
    cdef VecLangContext context = VecLangContext()
    cdef TraversalStrategy strategy = PostOrderTraversalStrategy()
    cdef TraversalStrategy eval_strategy = PostOrderTraversalEvaluatorStrategy()
    cdef ASTWalker error_collector_walker = ASTWalker(context,strategy) # type:ignore
    cdef ASTWalker functions_collector = ASTWalker(context,strategy) # type:ignore
    cdef ASTWalker evaluator_walker = ASTWalker(context,eval_strategy) # type:ignore

    strategy.set_default_selector_without_signature_checking(DefaultChildrenSelector()) # type:ignore
    
    eval_strategy.set_default_selector_without_signature_checking(DefaultChildrenSelector()) # type:ignore
    eval_strategy.add_selector_without_signature_checking(FunctionDeclAST,FunctionDeclASTChildrenSelector()) # type:ignore

    functions_collector.add_visitor_without_signature_checking(FunctionDeclAST,FunctionDeclASTCollectorVisitor())

    error_collector_walker.add_visitor_without_signature_checking(FunctionCallAST,FunctionCallASTErrorCollectorVisitor())
    error_collector_walker.add_visitor_without_signature_checking(SlicingAST,SlicingASTErrorCollectorVisitor())
    error_collector_walker.add_visitor_without_signature_checking(IndexingAST,IndexingASTErrorCollectorVisitor())
    error_collector_walker.add_visitor_without_signature_checking(PlusAST,BinaryASTErrorCollectorVisitor())
    error_collector_walker.add_visitor_without_signature_checking(MinusAST,BinaryASTErrorCollectorVisitor())
    error_collector_walker.add_visitor_without_signature_checking(MulAST,BinaryASTErrorCollectorVisitor())
    error_collector_walker.add_visitor_without_signature_checking(ExpAST,BinaryASTErrorCollectorVisitor())
    error_collector_walker.add_visitor_without_signature_checking(DivAST,BinaryASTErrorCollectorVisitor())
    error_collector_walker.add_visitor_without_signature_checking(ModAST,BinaryASTErrorCollectorVisitor())
    error_collector_walker.add_visitor_without_signature_checking(AssignmentAST,BinaryASTErrorCollectorVisitor())
    error_collector_walker.add_visitor_without_signature_checking(AssignmentAST,VariableIndexerVisitor())
    error_collector_walker.add_visitor_without_signature_checking(VectorComponentsAST,VectorComponentsASTErrorCollector())

    evaluator_walker.add_visitor_without_signature_checking(NumberAST,NumberASTEvaluatorVisitor())
    evaluator_walker.add_visitor_without_signature_checking(AssignmentAST,AssignmentASTEvaluatorVisitor())
    evaluator_walker.add_visitor_without_signature_checking(PlusAST,PlusASTEvaluatorVisitor())
    evaluator_walker.add_visitor_without_signature_checking(MinusAST,MinusASTEvaluatorVisitor())
    evaluator_walker.add_visitor_without_signature_checking(MulAST,MulASTEvaluatorVisitor())
    evaluator_walker.add_visitor_without_signature_checking(DivAST,DivASTEvaluatorVisitor())
    evaluator_walker.add_visitor_without_signature_checking(ModAST,ModASTEvaluatorVisitor())
    evaluator_walker.add_visitor_without_signature_checking(ExpAST,ExpASTEvaluatorVisitor())
    evaluator_walker.add_visitor_without_signature_checking(VectorComponentsAST,VectorComponentsASTEvaluatorVisitor())
    evaluator_walker.add_visitor_without_signature_checking(VectorAST,VectorASTEvaluatorVisitor())
    evaluator_walker.add_visitor_without_signature_checking(RangeAST,RangeASTEvaluatorVisitor())
    evaluator_walker.add_visitor_without_signature_checking(SlicingAST,SlicingASTEvaluatorVisitor())
    evaluator_walker.add_visitor_without_signature_checking(IndexingAST,IndexingASTEvaluatorVisitor())
    evaluator_walker.add_visitor_without_signature_checking(FunctionCallAST,FunctionCallASTEvaluatorVisitor())

    return context,error_collector_walker,functions_collector,evaluator_walker

cpdef object get_ast_value(AST ast,VecLangContext context):
    cdef AST ast_result = ast
    cdef VariableExpressionAST var

    if isinstance(ast,VecLangInstructionsSequenceAST):
        ast_result = (<VecLangInstructionsSequenceAST>ast)._instructions[-1]

    if isinstance(ast_result,VariableExpressionAST):
        var = ast_result
        return context.look_for_var(var._name)[1]
    return None
```

File `visitors.pyi`
```python
from typing import Any, Tuple,List

from pylgen.analysis.visitor import ASTWalker
from pylgen.analysis.error import RuntimeError
from pylgen.analysis.context import Context
from pylgen.common.types import AST

class VecLangContext(Context):

    def __init__(self) -> None: ...

    def get_runtime_errors(self) -> List[RuntimeError]: ...
    
    def clear_runtime_errors(self) -> None: ...

def build_walkers() -> Tuple[VecLangContext,ASTWalker,ASTWalker,ASTWalker]: ...

def get_ast_value(ast:AST, context:VecLangContext) -> Any: ...
```

## From Python to Cython: Performance-Driven Changes

Compared to the pure-Python implementation in the earlier tutorial, the VecLang semantic layer has undergone significant changes to squeeze out every ounce of performance. Let's examine the key transformations and why they matter.

> ### 1. Typed Attributes in Visitors

All visitor classes declare their attributes as `cdef` with explicit types. This eliminates Python attribute lookups and allows Cython to generate efficient C code.

> ### 2. Use of NumPy for Vector Operations

VecLang use NumPy arrays to represent vectors. Operations like addition, multiplication, and dot product are performed using NumPy's vectorised C-level functions, which are orders of magnitude faster than Python loops.

> ### 3. Cython-Level Functions and Method Calls

All visitors and strategies are `cdef` classes with `cdef` or `cpdef` methods. This means calls between them are resolved at compile time and are not subject to Python's dynamic dispatch. The overhead is minimal.



<!-- source: docs/tutorials/complete-languages/veclang/veclang-evolution.md -->

# Language Evolution: From Arithmetic to VecLang

The journey from the simple arithmetic language in the tutorial to VecLang is a testament to the extensibility of the visitor-based architecture. In the pure-Python version, adding a new feature like vectors or functions required:

 - `1`: Creating new AST classes (e.g., `VectorAST`,`FunctionCallAST`).
 - `2`: Adding new visitors for semantic checks and evaluation.
 - `3`: Updating the grammar and reductors.
 - `4`: Possibly extending the context to handle new data types.

The process was straightforward because the codebase was small and all in Python. The visitor pattern decoupled the AST structure from operations, so existing visitors remained untouched, we simply added new ones.

In VecLang, we've scaled that same approach to a much richer language. The key insight is that **the visitor patterns makes the system open for extension but closed for modification**. To add a new construct (say, a `map` function), we would:

 - `1`: Add a new AST class (e.g., `MapAST`) and its corresponding symbol in `asts.pxd` and `asts.pyx`.
 - `2`: Add production rules in the grammar (`parser.pyx`) to parse it.
 - `3`: Add a reductor to build the AST.
 - `4`: Add semantic error collectors (if needed) as new visitor classes.
 - `5`: Add an evaluator visitor.

Crucially, **existing visitors, selectors, and the traversal strategy remain unchanged**. The new visitors simply register with the existing walkers. In Cython, we also need to declare the new classes in `.pxd` files and recompile, but the logical steps are identical to the pure-Python case.

The added complexity in Cython comes from managing type declarations and ensuring that all new classes are properly `cdef`-ed for performance. However, this is a one-time cost per new feature; the runtime performance benefits far outweigh the development overhead. Moreover, because the framework is generic and type-aware, the compiler catches many mistakes early (e.g., mismatched types in visitor signatures), reducing debugging time.

## Reflection: Is it ***always*** that easy?

Not quite. If a new feature requires changes to the traversal strategy (e.g., a different visiting order) or to the context (e.g., a new kind of storage), then we might need to modify existing code. But in practice, most language extensions fit cleanly into the existing visitor skeleton. The design we've built is robust enough to accommodate a wide range of features without forcing rewrites, a **strong** indicator of a well-architected system.

## Leveraging the Python Ecosystem

One of the strongest arguments for building a language on top of Python (and Cython) is the access to the vast Python ecosystem. VecLang uses [**NumPy**](https://numpy.org/) extensively for vector operations. Without NumPy, we would have to implement array operations in pure Python loops, which would be painfully slow. With NumPy, operations like element-wise addition, dot product, and slicing are delegated to highly optimised C/Fortran libraries.

This is not just a convenience; it's a strategic advantage. It allows VecLang to be a high-performance DSL for numerical computing, similar to what NumPy does for Python itself, but with a custom syntax tailored to the problem domain. The ability to call any Python library from within VecLang (if we exposed it) would be trivial, thanks to the seamless integration.

The pure-Python arithmetic interpreter didn't need NumPy because it only handled scalars. But as soon as we introduced vectors, NumPy became essential. This illustrates how the ecosystem can be leveraged incrementally as the language grows. Moreover, we could easily add support for [`matplotlib`](https://matplotlib.org/) to plot vectors, or [`scipy`](https://scipy.org/) for advanced statistics, simply by calling those libraries from within our evaluator visitors.

> ### Trade-offs:

Relying on NumPy adds a dependency and increases the interpreter's footprint. For environments where NumPy is not available, this would be a problem. However, for a DSL aimed at data science or numerical computing, it's a natural fit. Additionally, for very small vectors (size < 10), the overhead of calling NumPy might outweigh the benefits; in such cases, a pure-Python loop could be faster. VecLang could be enhanced to choose the implementation based on vector size, but we haven't implemented that optimisation.

> ### Counter-argument

Some might argue that using NumPy ties the language to a specific library, making it less portable. However, the design is modular: the visitors could be swapped to use a different array library (e.g., `array` module or `list`) without changing the grammar or AST. This is another benefit of the visitor pattern, the evaluation logic is isolated.

## Next Steps

With semantic analysis and evaluation in place, our interpreter is functionally complete. The only missing piece is a user interface. Let's do it!



<!-- source: docs/tutorials/complete-languages/veclang/veclang-step-4.md -->

# Step 4: Running VecLang from a File

Our interpreter is now fully functional: we have a lexer, a parser, an AST, semantic checks, and evaluator. But an interpreter that only works in an interactive console is just a toy, a real-world languages are used to process files, run scripts, and produce output. In this final step, we'll build a **batch-mode interpreter** that reads a VecLang source file, executes it, and reports results or errors.

VecLang is designed for production-scale workloads: processing millions of lines of code, running complex numerical computations, or generating data. The REPL is great for experimentation, but for automation and performance, we need a file-based runner.

## From Interactive to Batch

The REPL from the [**arithmetic repl**](../arithmetic-repl/arithmetic-repl-intro.md) tutorial worked as follows:

 - `1`: Prompt the user for input.
 - `2`: For each line, tokenize, parse, run semantic checks, evaluate, and print the result.
 - `3`: Repeat until the user types `exit()`.

This is fine for learning and experimenting, but it has limitations:

 - **Performance**: The pipeline is re-initialised for each line, which is wasteful for large programs.
 - **State persistence**: Variables persist across lines, but the context must be carefully managed.
 - **No batch processing**: You cannot run a script without manual intervention.

VecLang takes a different approach: it expects a single file, parses the entire file as a **sequence of instructions**, and executes them in a single pass. This is similar to how Python, Ruby, or JavaScript run scripts.

## The Command-Line Interface

We'll create a single entry point, a `main.py` that accepts a filename as a command-line argument. For example:

```bash
python main.py main.vcl
```

The main function will:

 - `1`: Build the lexer, parser, and walkers with the context.
 - `2`: Read the file content.
 - `3`: Tokenize and parse the content.
 - `4`: If lexical or syntax errors, run the semantic error collector.
 - `5`: If no semantic error, run the evaluator.
 - `6`: Show the runtime errors (if any).

We'll also support the `--help` flag and optionally print the AST for debugging.

> **NOTE: Error Handling in Batch Mode**
In a REPL, a syntax error can be caught and the user can retry. In batch mode, any error should abort execution and report the error clearly.

## Modifications to the Pipeline

The core pipeline (lexer -> parser -> semantic checks -> evaluator) remains unchanged. The difference lies in how we orchestrate the passes and manage the context.

> ### 1. Reading the file

We'll use Python's built-in function `open()` to read the file as a string. The lexer expects a string input, so we pass the entire content at once.

> ### 2. Parsing the Whole Program

The grammar's start symbol is `VecLangProgram`, which is a sequence of instructions separated by newlines. The parser will produce a `VecLangInstructionsSequenceAST` containing all top level statements.

> ### 3. Semantic Analysis Passes

We'll run the `functions_collector` first to register all function definitions, then the `error_collector_walker` to perform static checks. If any semantic errors are found, we print them.

> ### 4. Evaluation Pass

If all checks pass, we run the `evaluator_walker` on the program AST. The evaluator will process each instruction in order, updating the context (variables, scopes, etc.).

## Implementation Sketch

Before write our main runner, we must to compile **veclang**, this is made through a `setup.py`.

```python
from setuptools.extension import Extension
from setuptools import setup
from Cython.Build import cythonize

interpreter_extensions = Extension(
    name='veclang.parser',
    sources=[
        'veclang/parser.pyx'
    ]
)

asts_extensions = Extension(
    name='veclang.asts',
    sources=[
        'veclang/asts.pyx'
    ]
)

visitors_extensions = Extension(
    name='veclang.visitors',
    sources=[
        'veclang/visitors.pyx'
    ]
)

errors_extension = Extension(
    name='veclang.errors',
    sources=[
        'veclang/errors.pyx'
    ]
)

lexer_extensions = Extension(
    name='veclang.lexer',
    sources=[
        'veclang/lexer.pyx'
    ]
)

setup(
    ext_modules=cythonize([
        interpreter_extensions,
        asts_extensions,
        visitors_extensions,
        errors_extension,
        lexer_extensions
    ]),
    language_level=3
)
```
Then run this command in your terminal inside the `veclang` folder:

```bash
python setup.py build_ext --inplace
```

This will compile the `.pyx` files into `.pyd` files extensions that Python can import by `import` statement.

Here's how the main runner might look.

File: `main.py`

```python
import os
from sys import argv

from veclang.lexer import build_lexer
from veclang.parser import build_parser
from veclang.visitors import build_walkers,get_ast_value

lexer = build_lexer()
VecLangParser = build_parser()
context,error_collector,functions_collector,evaluator = build_walkers()

if len(argv) < 2:
    raise ValueError('not input provided')

file = argv[1]

if not (os.path.exists(file) or os.path.isfile(file)):
    raise ValueError('Invalid argument')

help_flag = False
if len(argv) >= 3 and argv[2] == '--help':
    from pylgen.visual import set_cache_file,draw_ast
    help_flag = True
    set_cache_file('cache')

with open(file,'r') as f:
    text = f.read()
    lexer.load_text(text)
    ast = VecLangParser.parse(lexer.tokens)
    errors = []
    errors += list(lexer.errors)
    errors += VecLangParser.errors

    if not errors:
        if help_flag:
            draw_ast(ast,show=True,cache=True,select_menu=True) # type: ignore
        functions_collector.walk(ast)

    if not errors:
        error_collector.walk(ast)

    errors += context.errors

    if not errors:
        evaluator.walk(ast)
        errors += context.errors

    if not errors:
        result = get_ast_value(ast,context)
        if result is not None:
            print(result)

    if errors:
        for error in errors:
            print(error)
```

> **TIP: CLI scalability**
In this example, we use a simple `sys.argv` check for clarity. However, for a robust tool, consider using Python's `argparse` module, which allows for easy management of subcommands, optional flags, and automatic help messages.

> ### Differences from the REPL

| **Aspect** | **REPL (tutorial)** | **Batch (VecLang)** |
| :---: | :---: | :---: |
| **Input** | User lines | Whole file |
| **Context persistence** | Across lines | Across the entire file, then discarded |
| **Error handling** | Print error and continue | Collects as many as it can, and abort execution |
| **Output** | Print result of each expression | Print final result (if any) |
| **Performance** | Re-parses each line | Single parse for the whole program |
| **Use case** | Learning, experimentation | Scripting, automation, large-scale processing |

## Performance Considerations

In batch mode, the entire file is parsed and processed in one go. This allows the lexer and parser to be built only once, and the context is reused for all instructions. The evaluator benefits from having the full AST in memory, enabling optimisations like constant folding or dead-code elimination (which we haven't implemented, but could be added later). The use of Cython ensures that all passes are fast. The semantic checks and evaluation run in native code, making VecLang suitable for processing large datasets.

## Access to the Python Ecosystem in Batch Mode

The batch interpreter inherits all the ecosystem advantages we discussed earlier: it can call NumPy, SciPy, Matplotlib, or any other Python library. This makes VecLang a powerful glue language for scientific computing. You can write a script that reads data from a file, performs vectorised operations, and plot the results, all within VecLang syntax, while leveraging Python's extensive libraries underneath.

## Error Reporting in Batch Mode

In batch mode, it's crucial to report errors with enough context to fix them. The error classes we defined carry line and column numbers, and the stack trace helps locate the source of runtime errors. The main script prints each error with its location, making it easy to identify issues.

For example:

```bash
RUNTIME ERROR: Division by zero not allowed at line 11
```

This is much more useful than a cryptic traceback.



<!-- source: docs/tutorials/complete-languages/veclang/veclang-next-steps.md -->

# Where to Go Next

You've built VecLang from the ground up: a lexer, a parser, an AST, a full set of visitors, a context with scopes and signals, and a batch-mode runner that compiles everything with Cython. The interpreter works, it's correct, and it handles a language with vectors, complex numbers, functions, and slicing. That's a real achievement.

But there's one question we haven't answered yet: ***how fast is it, really?***

That's the subject of the [**VecLang Benchmark**](../../../benchmarks/veclang-benchmark.md). It's a rigorous, end-to-end performance analysis on a 2-million-line, 40 MB source file, comparing VecLang against **Lark** (a popular, production-grade parsing library) in its best-performing configuration (`lark_cython`, `LALR(1)`, `contextual lexer`).

The benchmark covers:

 - **Parsing speed**: measured in seconds over multiple runs, with warm-up and scaling tests.

 - **Memory usage**: tracked with [**Scalene**](https://github.com/plasma-umass/scalene) to show the real footprint of each approach.

 - **Full-pipeline timing**: breaking down parsing, function collection, semantic checks, and evaluation.

 - **Correctness validation**: confirming that both interpreters produce identical output on the same input.

 - **Architectural analysis**: explaining why the numbers look the way they do.

If you're planning to use PyLGEN in production, or if you're just curious how a hand-built, Cython-compiled interpreter compares to a mature, widely-used library, the benchmark is the next thing you should read. It's the payoff for everything you built in this tutorial, and it answers the question we started with: ***how fast could it be?***
