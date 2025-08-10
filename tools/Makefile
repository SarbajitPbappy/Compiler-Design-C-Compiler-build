CXX := g++
CXXFLAGS := -O2 -pipe -Wall -Wextra -pedantic
LEX := flex
YACC := bison

all: codescan

parser.tab.c parser.tab.h: parser.y
	$(YACC) -d -o parser.tab.c parser.y

lex.yy.c: scanner.l
	$(LEX) -o lex.yy.c scanner.l

codescan: parser.tab.c lex.yy.c
	$(CXX) $(CXXFLAGS) -o codescan parser.tab.c lex.yy.c -lfl

clean:
	rm -f codescan parser.tab.c parser.tab.h lex.yy.c

.PHONY: all clean
