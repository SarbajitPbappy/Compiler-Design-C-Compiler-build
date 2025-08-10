from __future__ import annotations

import re
from typing import List, Dict, Any

from .compiler.ast import Level, Entity, Handler, Say, Move
from .compiler.semantic import validate_level
from .compiler.codegen import compile_to_ir
from .game.engine import Engine


TOKEN_SPEC = [
    ("WS", r"[ \t\r\n]+"),
    ("LEVEL", r"level\b"),
    ("ENTITY", r"entity\b"),
    ("AT", r"at\b"),
    ("ON", r"on\b"),
    ("START", r"start\b"),
    ("UPDATE", r"update\b"),
    ("SAY", r"say\b"),
    ("MOVE", r"move\b"),
    ("LBRACE", r"\{"),
    ("RBRACE", r"\}"),
    ("LPAREN", r"\("),
    ("RPAREN", r"\)"),
    ("COMMA", r","),
    ("SEMI", r";"),
    ("STRING", r'"([^"\\]|\\.)*"'),
    ("INT", r"-?[0-9]+"),
    ("IDENT", r"[A-Za-z_][A-Za-z0-9_]*"),
]

TOKEN_RE = re.compile("|".join(f"(?P<{name}>{pattern})" for name, pattern in TOKEN_SPEC))


class Token:
    def __init__(self, typ: str, val: str):
        self.type = typ
        self.value = val

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"Token({self.type}, {self.value})"


def tokenize(source: str) -> List[Token]:
    tokens: List[Token] = []
    for m in TOKEN_RE.finditer(source):
        typ = m.lastgroup
        val = m.group(typ)
        if typ == "WS":
            continue
        tokens.append(Token(typ, val))
    return tokens


class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.i = 0

    def peek(self, *types: str) -> bool:
        if self.i >= len(self.tokens):
            return False
        return self.tokens[self.i].type in types

    def expect(self, typ: str) -> Token:
        if not self.peek(typ):
            got = self.tokens[self.i].type if self.i < len(self.tokens) else "<eof>"
            raise SyntaxError(f"Expected {typ}, got {got}")
        tok = self.tokens[self.i]
        self.i += 1
        return tok

    def parse_level(self) -> Level:
        self.expect("LEVEL")
        name = self._parse_name()
        self.expect("LBRACE")
        entities: List[Entity] = []
        while not self.peek("RBRACE"):
            entities.append(self.parse_entity())
        self.expect("RBRACE")
        return Level(name=name, entities=entities)

    def parse_entity(self) -> Entity:
        self.expect("ENTITY")
        name = self._parse_name()
        if self.peek("AT"):
            self.expect("AT")
        self.expect("LPAREN")
        x = int(self.expect("INT").value)
        self.expect("COMMA")
        y = int(self.expect("INT").value)
        self.expect("RPAREN")
        self.expect("LBRACE")
        handlers: Dict[str, Handler] = {}
        while not self.peek("RBRACE"):
            h = self.parse_handler()
            handlers[h.name] = h
        self.expect("RBRACE")
        return Entity(name=name, x=x, y=y, handlers=handlers)

    def parse_handler(self) -> Handler:
        self.expect("ON")
        if self.peek("START"):
            self.expect("START")
            name = "start"
        else:
            self.expect("UPDATE")
            name = "update"
        self.expect("LBRACE")
        stmts = self.parse_statements()
        self.expect("RBRACE")
        return Handler(name=name, statements=stmts)

    def parse_statements(self) -> List[Any]:
        stmts: List[Any] = []
        while not self.peek("RBRACE"):
            stmts.append(self.parse_statement())
        return stmts

    def parse_statement(self):
        if self.peek("SAY"):
            self.expect("SAY")
            text_token = self.expect("STRING").value
            text = bytes(text_token[1:-1], "utf-8").decode("unicode_escape")
            self.expect("SEMI")
            return Say(text=text)
        if self.peek("MOVE"):
            self.expect("MOVE")
            if self.peek("LPAREN"):
                self.expect("LPAREN")
                dx = int(self.expect("INT").value)
                self.expect("COMMA")
                dy = int(self.expect("INT").value)
                self.expect("RPAREN")
            else:
                dx = int(self.expect("INT").value)
                self.expect("COMMA")
                dy = int(self.expect("INT").value)
            self.expect("SEMI")
            return Move(dx=dx, dy=dy)
        got = self.tokens[self.i].type if self.i < len(self.tokens) else "<eof>"
        raise SyntaxError(f"Unexpected token in statement: {got}")

    def _parse_name(self) -> str:
        if self.peek("IDENT"):
            return self.expect("IDENT").value
        if self.peek("STRING"):
            text_token = self.expect("STRING").value
            return bytes(text_token[1:-1], "utf-8").decode("unicode_escape")
        got = self.tokens[self.i].type if self.i < len(self.tokens) else "<eof>"
        raise SyntaxError(f"Expected name, got {got}")


def parse_agsl(source: str) -> Level:
    parser = Parser(tokenize(source))
    level = parser.parse_level()
    validate_level(level)
    return level


def compile_level(level: Level) -> Dict[str, Any]:
    return compile_to_ir(level)


def run_ir(ir: Dict[str, Any]) -> None:
    Engine(ir).run()


