# W++ Compiler — Recursive Descent Parser

A hand-written **recursive descent parser** for **W++**, a custom programming language built as a compiler construction project at UET Taxila (Department of Computer Science).

The parser performs full **syntax analysis** on W++ source code — validating structure, detecting errors with precise line numbers, and recovering to continue finding multiple errors in a single pass.

---

## Features

- **Recursive descent parsing** — each grammar rule maps to one method
- **Panic-mode error recovery** — finds all errors in one run, not just the first
- **Multi-variable declarations** — `int a = 1, b, c = 3;`
- **Full control flow** — `if / else if / else`, `while`, `for`
- **For-loop increment flexibility** — `i++`, `i += 1`, `i = i + 1`, `--i`
- **Logical operators** — `&&` and `||` in conditions
- **Print statements** — `print "x";`, `print(x, y);`, `cout << x << endl;`
- **Function definitions** — including `main()` and generic functions
- **Operator precedence** — correctly enforced through grammar layering
- **Meaningful error messages** — with line numbers for every detected issue

---

## Project Structure

```
wpp-compiler/
├── lexer.py          # Tokenizer — converts source code to token list
├── parser.py         # Recursive descent parser — syntax analysis
├── app.py            # Main entry point / web interface
├── examples/         # Sample W++ programs
│   └── sample.wpp
├── .gitignore
└── README.md
```

---

## Supported W++ Syntax

```cpp
// Variable declarations
int x = 5;
int a = 1, b, c = 3;
string name = "Ahmed";
float pi = 3.14;

// If / else if / else
if (age >= 18 && age <= 60) {
    print "Adult";
} else if (age > 60) {
    print "Senior";
} else {
    print "Minor";
}

// While loop
while (x < 10) {
    x = x + 1;
}

// For loop
for (int i = 0; i < 5; i = i + 1) {
    print i;
}

// Functions
int add(int a, int b) {
    return a + b;
}

// Print variants
print "Hello";
print(x);
cout << x << endl;
```

---

## Error Detection Examples

The parser detects and reports errors with line numbers:

| Error | Code | Message |
|---|---|---|
| Missing semicolon | `int x = 5` | `Expected ';' after declaration of 'x'` |
| Unknown type | `bool flag = true;` | `Unknown data type 'bool'` |
| Invalid identifier | `int 2x = 5;` | `Invalid identifier '2x': names must begin with a letter or underscore` |
| Orphan else | `else { }` | `'else' without a matching 'if'` |
| Unsupported NOT | `if (!flag)` | `Unexpected token '!'. Unary logical NOT operator is not supported.` |
| Missing brace | `if (x > 0) x = 1;` | `Expected '{' to open block` |

---

## Expression Grammar (Operator Precedence)

Precedence is enforced through the method call hierarchy (lowest → highest):

```
expression
  └── logical        &&  ||
        └── comparison   ==  !=  <  >  <=  >=
              └── term        +  -
                    └── factor     *  /  %
                          └── unary    ++  --
                                └── primary   literals, identifiers, (expr)
```

---

## How to Run

```bash
# Clone the repo
git clone https://github.com/<your-username>/wpp-compiler.git
cd wpp-compiler

# Run the app
python app.py
```

> Python 3.8+ required. No external dependencies.

---

## How the Parser Works

1. **Lexer** tokenizes the source into a list of `{"type", "value", "line"}` dicts
2. **Parser** strips comment tokens, then enters `parse()` which loops calling `statement()`
3. `statement()` dispatches to the correct method based on the current token
4. If a rule fails, `expect()` records the error and raises `ParseError`
5. `synchronize()` skips to the next safe boundary (`;`, `}`, or a keyword) and parsing continues
6. `parse()` returns the full list of errors — empty list means the program is valid

---

## Built With

- **Language:** Python 3
- **Parsing technique:** Recursive Descent (hand-written, no parser generators)
- **Error recovery:** Panic-mode synchronization

---

## Academic Context

**Institution:** University of Engineering & Technology (UET) Taxila  
**Department:** Computer Science  
**Course:** Compiler Construction  
**Supervisor:** Dr. Munwar Iqbal
