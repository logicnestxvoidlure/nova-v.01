# Nova

Nova is a small, batteries-included interpreted programming language implemented in Python.

## Requirements

- Python 3.10 or newer
- No third-party packages required

## Run a file

```bash
python nova.py examples/hello.nova
```

## REPL

```bash
python nova.py
```

Then:

```nova
let name = "world"
say "Hello, " + name

let total = 5 * 8
say total
```

Type `exit` to leave.

## Language

### Variables

```nova
let x = 10
set x = x + 5
say x
```

### Types

Nova supports:

- numbers
- strings
- booleans
- null
- arrays
- maps
- functions

```nova
let n = 42
let text = "Nova"
let ok = true
let nothing = null
let nums = [1, 2, 3]
let user = {"name": "Nova", "level": 1}
```

### Operators

Arithmetic:

`+ - * / % **`

Comparison:

`== != < <= > >=`

Logical:

`and or not`

Membership:

`in`

```nova
say 2 ** 8
say 10 % 3
say 5 >= 5
say "a" in ["a", "b"]
```

### Conditions

```nova
if score >= 90 {
    say "A"
} else if score >= 80 {
    say "B"
} else {
    say "Keep going"
}
```

### Loops

```nova
let i = 0
while i < 5 {
    say i
    set i = i + 1
}

for item in [10, 20, 30] {
    say item
}

for i in range(5) {
    say i
}
```

Use `break` and `continue` inside loops.

### Functions

```nova
fn add(a, b) {
    return a + b
}

say add(10, 20)
```

Functions can be assigned to variables and passed around.

### Lambdas

```nova
let double = fn(x) => x * 2
say double(21)
```

### Arrays

```nova
let a = [1, 2, 3]
push(a, 4)
say len(a)
say a[0]
```

### Maps

```nova
let user = {"name": "Nova", "score": 100}
say user["name"]
set user["score"] = 120
```

### Strings

String escapes are supported:

```nova
say "line 1\nline 2"
```

Built-ins include:

`len`, `type`, `str`, `num`, `bool`, `range`, `push`, `pop`, `join`, `split`, `upper`, `lower`, `trim`, `contains`, `keys`, `values`, `input`, `clock`, `assert`

### Comments

Comments are intentionally not used in Nova source files. The implementation is also comment-free as requested.

## Example

```nova
fn fib(n) {
    if n <= 1 {
        return n
    }
    return fib(n - 1) + fib(n - 2)
}

for i in range(10) {
    say fib(i)
}
```

## Project layout

- `nova.py` — complete interpreter and CLI
- `examples/hello.nova` — basics
- `examples/features.nova` — language feature demo
- `examples/fibonacci.nova` — recursive functions
- `examples/data.nova` — arrays and maps
- `LICENSE` — MIT license

## Commands

```bash
python nova.py
python nova.py examples/hello.nova
python nova.py --tokens examples/hello.nova
python nova.py --ast examples/hello.nova
```

Windows users can use `py` instead of `python`.

## License

MIT
