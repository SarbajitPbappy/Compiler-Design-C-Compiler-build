%{
#include <stdio.h>
#include <stdlib.h>
int yylex(void);
void yyerror(const char *s);
%}

%define api.value.type {int}

%token USING_NS_STD
%token BITS_HEADER
%token SYSTEM_CALL
%token TEXT

%%
program:
    /* empty */
  | program token
  ;

token:
    USING_NS_STD
  | BITS_HEADER
  | SYSTEM_CALL
  | TEXT
  ;

%%

void yyerror(const char *s) {
    // Suppress default error printing; scanner handles messages
}

int main(void) {
    return yyparse();
}
