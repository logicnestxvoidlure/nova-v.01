import sys
import math
import time
import random

class NovaError(Exception):
    pass

class ReturnSignal(Exception):
    def __init__(self, value):
        self.value = value

class BreakSignal(Exception):
    pass

class ContinueSignal(Exception):
    pass

class Token:
    def __init__(self, kind, value, line, col):
        self.kind = kind
        self.value = value
        self.line = line
        self.col = col
    def __repr__(self):
        return f"{self.kind}({self.value!r})"

KEYWORDS = {
    "let": "LET", "set": "SET", "if": "IF", "else": "ELSE",
    "while": "WHILE", "for": "FOR", "in": "IN", "fn": "FN",
    "return": "RETURN", "break": "BREAK", "continue": "CONTINUE",
    "true": "TRUE", "false": "FALSE", "null": "NULL",
    "and": "AND", "or": "OR", "not": "NOT", "say": "SAY"
}

TWO = {"==", "!=", "<=", ">=", "=>", "**", "&&", "||"}
ONE = set("{}[](),.:;+-*/%<>=!")

class Lexer:
    def __init__(self, source):
        self.source = source
        self.i = 0
        self.line = 1
        self.col = 1
        self.tokens = []

    def advance(self):
        ch = self.source[self.i]
        self.i += 1
        if ch == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def peek(self, n=0):
        p = self.i + n
        return self.source[p] if p < len(self.source) else ""

    def add(self, kind, value, line, col):
        self.tokens.append(Token(kind, value, line, col))

    def run(self):
        while self.i < len(self.source):
            ch = self.peek()
            line, col = self.line, self.col
            if ch.isspace():
                self.advance()
                continue
            if ch == "#":
                while self.i < len(self.source) and self.peek() != "\n":
                    self.advance()
                continue
            if ch.isalpha() or ch == "_":
                s = ""
                while self.peek().isalnum() or self.peek() == "_":
                    s += self.advance()
                self.add(KEYWORDS.get(s, "IDENT"), s, line, col)
                continue
            if ch.isdigit() or (ch == "." and self.peek(1).isdigit()):
                s = ""
                dots = 0
                while self.peek().isdigit() or self.peek() == ".":
                    if self.peek() == ".":
                        dots += 1
                    s += self.advance()
                if dots > 1:
                    raise NovaError(f"Invalid number at {line}:{col}")
                self.add("NUMBER", float(s) if "." in s else int(s), line, col)
                continue
            if ch in "\"'":
                quote = self.advance()
                s = ""
                while self.i < len(self.source) and self.peek() != quote:
                    if self.peek() == "\n":
                        raise NovaError(f"Unterminated string at {line}:{col}")
                    if self.peek() == "\\":
                        self.advance()
                        esc = self.advance()
                        s += {"n":"\n","t":"\t","r":"\r","\\":"\\","\"":"\"","'":"'","0":"\0"}.get(esc, esc)
                    else:
                        s += self.advance()
                if self.i >= len(self.source):
                    raise NovaError(f"Unterminated string at {line}:{col}")
                self.advance()
                self.add("STRING", s, line, col)
                continue
            pair = ch + self.peek(1)
            if pair in TWO:
                self.advance(); self.advance()
                self.add(pair, pair, line, col)
                continue
            if ch in ONE:
                self.advance()
                self.add(ch, ch, line, col)
                continue
            raise NovaError(f"Unexpected character {ch!r} at {line}:{col}")
        self.tokens.append(Token("EOF", "", self.line, self.col))
        return self.tokens

class Node:
    pass

class Program(Node):
    def __init__(self, statements): self.statements = statements

class Block(Node):
    def __init__(self, statements): self.statements = statements

class Literal(Node):
    def __init__(self, value): self.value = value

class Array(Node):
    def __init__(self, items): self.items = items

class Map(Node):
    def __init__(self, items): self.items = items

class Var(Node):
    def __init__(self, name): self.name = name

class Unary(Node):
    def __init__(self, op, expr): self.op, self.expr = op, expr

class Binary(Node):
    def __init__(self, left, op, right): self.left, self.op, self.right = left, op, right

class Assign(Node):
    def __init__(self, target, expr): self.target, self.expr = target, expr

class Index(Node):
    def __init__(self, obj, key): self.obj, self.key = obj, key

class Call(Node):
    def __init__(self, fn, args): self.fn, self.args = fn, args

class ExprStmt(Node):
    def __init__(self, expr): self.expr = expr

class Let(Node):
    def __init__(self, name, expr): self.name, self.expr = name, expr

class If(Node):
    def __init__(self, cond, yes, no): self.cond, self.yes, self.no = cond, yes, no

class While(Node):
    def __init__(self, cond, body): self.cond, self.body = cond, body

class For(Node):
    def __init__(self, name, iterable, body): self.name, self.iterable, self.body = name, iterable, body

class Function(Node):
    def __init__(self, name, params, body): self.name, self.params, self.body = name, params, body

class Lambda(Node):
    def __init__(self, params, body): self.params, self.body = params, body

class Return(Node):
    def __init__(self, expr): self.expr = expr

class Break(Node): pass
class Continue(Node): pass

class Parser:
    def __init__(self, tokens):
        self.t = tokens
        self.i = 0

    def cur(self): return self.t[self.i]
    def peek(self, n=1): return self.t[min(self.i+n, len(self.t)-1)]
    def check(self, kind): return self.cur().kind == kind
    def advance(self):
        x = self.cur(); self.i += 1; return x
    def match(self, *kinds):
        if self.cur().kind in kinds:
            return self.advance()
        return None
    def expect(self, kind):
        if not self.check(kind):
            x = self.cur()
            raise NovaError(f"Expected {kind}, got {x.kind} at {x.line}:{x.col}")
        return self.advance()

    def program(self):
        out = []
        while not self.check("EOF"):
            out.append(self.statement())
        return Program(out)

    def block(self):
        self.expect("{")
        out = []
        while not self.check("}") and not self.check("EOF"):
            out.append(self.statement())
        self.expect("}")
        return Block(out)

    def statement(self):
        if self.match(";"): return self.statement()
        if self.match("LET"):
            name = self.expect("IDENT").value
            self.expect("=")
            node = Let(name, self.expression())
            self.match(";")
            return node
        if self.match("SET"):
            target = self.expression()
            self.expect("=")
            node = Assign(target, self.expression())
            self.match(";")
            return node
        if self.match("SAY"):
            node = ExprStmt(Call(Var("__say__"), [self.expression()]))
            self.match(";")
            return node
        if self.match("IF"):
            cond = self.expression()
            yes = self.block()
            no = None
            if self.match("ELSE"):
                no = self.statement() if self.check("IF") else self.block()
            return If(cond, yes, no)
        if self.match("WHILE"):
            return While(self.expression(), self.block())
        if self.match("FOR"):
            name = self.expect("IDENT").value
            self.expect("IN")
            return For(name, self.expression(), self.block())
        if self.match("FN"):
            name = self.expect("IDENT").value
            params = self.params()
            return Function(name, params, self.block())
        if self.match("RETURN"):
            e = None if self.check("}") or self.check(";") else self.expression()
            self.match(";")
            return Return(e)
        if self.match("BREAK"):
            self.match(";"); return Break()
        if self.match("CONTINUE"):
            self.match(";"); return Continue()
        e = self.expression()
        self.match(";")
        return ExprStmt(e)

    def params(self):
        self.expect("(")
        p = []
        if not self.check(")"):
            while True:
                p.append(self.expect("IDENT").value)
                if not self.match(","): break
        self.expect(")")
        return p

    def expression(self):
        return self.assignment()

    def assignment(self):
        left = self.logic_or()
        if self.match("="):
            return Assign(left, self.assignment())
        return left

    def logic_or(self):
        x = self.logic_and()
        while self.match("OR", "||"): x = Binary(x, "or", self.logic_and())
        return x

    def logic_and(self):
        x = self.equality()
        while self.match("AND", "&&"): x = Binary(x, "and", self.equality())
        return x

    def equality(self):
        x = self.comparison()
        while True:
            op = self.match("==", "!=")
            if not op: break
            x = Binary(x, op.kind, self.comparison())
        return x

    def comparison(self):
        x = self.term()
        while True:
            op = self.match("<", "<=", ">", ">=", "IN")
            if not op: break
            x = Binary(x, "in" if op.kind == "IN" else op.kind, self.term())
        return x

    def term(self):
        x = self.factor()
        while True:
            op = self.match("+", "-")
            if not op: break
            x = Binary(x, op.kind, self.factor())
        return x

    def factor(self):
        x = self.power()
        while True:
            op = self.match("*", "/", "%")
            if not op: break
            x = Binary(x, op.kind, self.power())
        return x

    def power(self):
        x = self.unary()
        if self.match("**"): x = Binary(x, "**", self.power())
        return x

    def unary(self):
        op = self.match("-", "+", "NOT", "!")
        if op:
            return Unary("not" if op.kind == "NOT" else op.kind, self.unary())
        return self.postfix()

    def postfix(self):
        x = self.primary()
        while True:
            if self.match("("):
                args = []
                if not self.check(")"):
                    while True:
                        args.append(self.expression())
                        if not self.match(","): break
                self.expect(")")
                x = Call(x, args)
            elif self.match("["):
                key = self.expression()
                self.expect("]")
                x = Index(x, key)
            else:
                break
        return x

    def primary(self):
        x = self.cur()
        if self.match("NUMBER", "STRING"): return Literal(x.value)
        if self.match("TRUE"): return Literal(True)
        if self.match("FALSE"): return Literal(False)
        if self.match("NULL"): return Literal(None)
        if self.match("IDENT"): return Var(x.value)
        if self.match("("):
            e = self.expression()
            self.expect(")")
            return e
        if self.match("["):
            items = []
            if not self.check("]"):
                while True:
                    items.append(self.expression())
                    if not self.match(","): break
            self.expect("]")
            return Array(items)
        if self.match("{"):
            items = []
            if not self.check("}"):
                while True:
                    k = self.expression()
                    self.expect(":")
                    v = self.expression()
                    items.append((k, v))
                    if not self.match(","): break
            self.expect("}")
            return Map(items)
        if self.match("FN"):
            params = self.params()
            self.expect("=>")
            return Lambda(params, self.expression())
        raise NovaError(f"Unexpected token {x.kind} at {x.line}:{x.col}")

class Env:
    def __init__(self, parent=None):
        self.values = {}
        self.parent = parent
    def define(self, name, value):
        self.values[name] = value
        return value
    def get(self, name):
        if name in self.values: return self.values[name]
        if self.parent: return self.parent.get(name)
        raise NovaError(f"Undefined variable: {name}")
    def set(self, name, value):
        if name in self.values:
            self.values[name] = value
            return value
        if self.parent: return self.parent.set(name, value)
        raise NovaError(f"Undefined variable: {name}")

class UserFunction:
    def __init__(self, params, body, env, expression=False):
        self.params, self.body, self.env, self.expression = params, body, env, expression
    def __call__(self, *args):
        if len(args) != len(self.params):
            raise NovaError(f"Expected {len(self.params)} arguments, got {len(args)}")
        e = Env(self.env)
        for p, a in zip(self.params, args): e.define(p, a)
        try:
            if self.expression: return Evaluator(e).eval(self.body)
            Evaluator(e).exec_block(self.body)
        except ReturnSignal as r:
            return r.value
        return None
    def __repr__(self): return "<fn>"

def truth(v): return bool(v)
def equal(a, b): return a == b

class Evaluator:
    def __init__(self, env=None):
        self.env = env or Env()
    def eval(self, n):
        if isinstance(n, Literal): return n.value
        if isinstance(n, Var): return self.env.get(n.name)
        if isinstance(n, Array): return [self.eval(x) for x in n.items]
        if isinstance(n, Map): return {self.eval(k): self.eval(v) for k,v in n.items}
        if isinstance(n, Unary):
            v = self.eval(n.expr)
            if n.op == "-": return -v
            if n.op == "+": return +v
            if n.op in ("not","!"): return not truth(v)
        if isinstance(n, Binary):
            if n.op == "and":
                a = self.eval(n.left); return self.eval(n.right) if truth(a) else a
            if n.op == "or":
                a = self.eval(n.left); return a if truth(a) else self.eval(n.right)
            a, b = self.eval(n.left), self.eval(n.right)
            try:
                if n.op == "+": return a + b
                if n.op == "-": return a - b
                if n.op == "*": return a * b
                if n.op == "/": return a / b
                if n.op == "%": return a % b
                if n.op == "**": return a ** b
                if n.op == "==": return equal(a,b)
                if n.op == "!=": return not equal(a,b)
                if n.op == "<": return a < b
                if n.op == "<=": return a <= b
                if n.op == ">": return a > b
                if n.op == ">=": return a >= b
                if n.op == "in": return a in b
            except Exception as e:
                raise NovaError(str(e))
        if isinstance(n, Index):
            obj, key = self.eval(n.obj), self.eval(n.key)
            try: return obj[key]
            except Exception: raise NovaError("Invalid index or key")
        if isinstance(n, Call):
            fn = self.eval(n.fn)
            args = [self.eval(x) for x in n.args]
            if not callable(fn): raise NovaError("Value is not callable")
            try: return fn(*args)
            except NovaError: raise
            except Exception as e: raise NovaError(str(e))
        if isinstance(n, Assign):
            value = self.eval(n.expr)
            self.assign(n.target, value)
            return value
        if isinstance(n, Lambda):
            return UserFunction(n.params, n.body, self.env, True)
        raise NovaError("Invalid expression")

    def assign(self, target, value):
        if isinstance(target, Var):
            return self.env.set(target.name, value)
        if isinstance(target, Index):
            obj = self.eval(target.obj)
            key = self.eval(target.key)
            try: obj[key] = value
            except Exception: raise NovaError("Cannot assign to index")
            return value
        raise NovaError("Invalid assignment target")

    def exec(self, n):
        if isinstance(n, Program): return self.exec_block(n.statements)
        if isinstance(n, Block): return self.exec_block(n.statements)
        if isinstance(n, Let): return self.env.define(n.name, self.eval(n.expr))
        if isinstance(n, ExprStmt): return self.eval(n.expr)
        if isinstance(n, Assign): return self.eval(n)
        if isinstance(n, If):
            if truth(self.eval(n.cond)): return self.exec(n.yes)
            if n.no: return self.exec(n.no)
            return None
        if isinstance(n, While):
            while truth(self.eval(n.cond)):
                try: self.exec(n.body)
                except ContinueSignal: continue
                except BreakSignal: break
            return None
        if isinstance(n, For):
            iterable = self.eval(n.iterable)
            for value in iterable:
                self.env.define(n.name, value) if n.name not in self.env.values else self.env.set(n.name, value)
                try: self.exec(n.body)
                except ContinueSignal: continue
                except BreakSignal: break
            return None
        if isinstance(n, Function):
            return self.env.define(n.name, UserFunction(n.params, n.body.statements, self.env))
        if isinstance(n, Return):
            raise ReturnSignal(None if n.expr is None else self.eval(n.expr))
        if isinstance(n, Break): raise BreakSignal()
        if isinstance(n, Continue): raise ContinueSignal()
        raise NovaError("Invalid statement")

    def exec_block(self, statements):
        result = None
        for s in statements: result = self.exec(s)
        return result

def make_env():
    e = Env()
    e.define("pi", math.pi)
    e.define("e", math.e)
    e.define("len", lambda x: len(x))
    e.define("type", lambda x: "null" if x is None else ("bool" if isinstance(x,bool) else "number" if isinstance(x,(int,float)) else "string" if isinstance(x,str) else "array" if isinstance(x,list) else "map" if isinstance(x,dict) else "function" if callable(x) else "object"))
    e.define("str", lambda x: "null" if x is None else str(x).lower() if isinstance(x,bool) else str(x))
    e.define("num", lambda x: float(x) if "." in str(x) else int(x))
    e.define("bool", lambda x: bool(x))
    e.define("range", lambda *args: list(range(*[int(x) for x in args])))
    e.define("push", lambda a, x: (a.append(x) or x))
    e.define("pop", lambda a: a.pop())
    e.define("join", lambda a, sep=",": sep.join(str(x) for x in a))
    e.define("split", lambda s, sep=None: s.split(sep))
    e.define("upper", lambda s: str(s).upper())
    e.define("lower", lambda s: str(s).lower())
    e.define("trim", lambda s: str(s).strip())
    e.define("contains", lambda a, x: x in a)
    e.define("keys", lambda m: list(m.keys()))
    e.define("values", lambda m: list(m.values()))
    e.define("input", lambda prompt="": input(str(prompt)))
    e.define("clock", lambda: time.time())
    e.define("random", lambda: random.random())
    e.define("sqrt", math.sqrt)
    e.define("abs", abs)
    e.define("floor", math.floor)
    e.define("ceil", math.ceil)
    e.define("min", min)
    e.define("max", max)
    e.define("sum", sum)
    e.define("assert", lambda condition, message="Assertion failed": None if condition else (_ for _ in ()).throw(NovaError(str(message))))
    e.define("__say__", lambda x=None: print(x))
    return e

def ast_repr(n, depth=0):
    pad = "  " * depth
    if isinstance(n, Program): return pad + "Program\n" + "\n".join(ast_repr(x, depth+1) for x in n.statements)
    if isinstance(n, Block): return pad + "Block\n" + "\n".join(ast_repr(x, depth+1) for x in n.statements)
    if isinstance(n, Literal): return pad + f"Literal({n.value!r})"
    if isinstance(n, Var): return pad + f"Var({n.name})"
    if isinstance(n, Array): return pad + "Array\n" + "\n".join(ast_repr(x, depth+1) for x in n.items)
    if isinstance(n, Map): return pad + "Map\n" + "\n".join(ast_repr(k, depth+1)+" : "+ast_repr(v) for k,v in n.items)
    if isinstance(n, Unary): return pad + f"Unary({n.op})\n" + ast_repr(n.expr, depth+1)
    if isinstance(n, Binary): return pad + f"Binary({n.op})\n" + ast_repr(n.left, depth+1) + "\n" + ast_repr(n.right, depth+1)
    if isinstance(n, Assign): return pad + "Assign\n" + ast_repr(n.target, depth+1) + "\n" + ast_repr(n.expr, depth+1)
    if isinstance(n, Index): return pad + "Index\n" + ast_repr(n.obj, depth+1) + "\n" + ast_repr(n.key, depth+1)
    if isinstance(n, Call): return pad + "Call\n" + ast_repr(n.fn, depth+1) + "\n" + "\n".join(ast_repr(a, depth+1) for a in n.args)
    return pad + type(n).__name__

def run_source(source, show_tokens=False, show_ast=False, env=None):
    tokens = Lexer(source).run()
    if show_tokens:
        for token in tokens: print(token)
        return env or make_env()
    tree = Parser(tokens).program()
    if show_ast:
        print(ast_repr(tree))
        return env or make_env()
    evaluator = Evaluator(env or make_env())
    evaluator.exec(tree)
    return evaluator.env

def repl():
    env = make_env()
    print("Nova 1.0")
    print("Type exit to quit.")
    while True:
        try:
            source = input("nova> ")
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if source.strip() in ("exit", "quit"):
            break
        if not source.strip(): continue
        try:
            run_source(source, env=env)
        except Exception as ex:
            print(f"Error: {ex}")

def main():
    args = sys.argv[1:]
    if not args:
        repl()
        return
    show_tokens = "--tokens" in args
    show_ast = "--ast" in args
    args = [x for x in args if x not in ("--tokens","--ast")]
    if not args:
        repl()
        return
    path = args[0]
    try:
        with open(path, "r", encoding="utf-8") as f:
            run_source(f.read(), show_tokens=show_tokens, show_ast=show_ast)
    except FileNotFoundError:
        print(f"Nova: file not found: {path}")
        sys.exit(1)
    except Exception as ex:
        print(f"Nova error: {ex}")
        sys.exit(1)

if __name__ == "__main__":
    main()
