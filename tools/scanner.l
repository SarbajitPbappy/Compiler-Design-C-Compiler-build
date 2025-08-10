%{
#include "parser.tab.h"
#include <stdio.h>
#include <string.h>
%}

%x COMMENT

%%
"//"[^\n]*                 { /* line comment */ }
"/*"                      { BEGIN(COMMENT); }
<COMMENT>"*/"             { BEGIN(INITIAL); }
<COMMENT>.|\n              { /* consume */ }

[ \t\r\n]+                 { /* skip whitespace */ }

"using"[ \t\r\n]+"namespace"[ \t\r\n]+"std"[ \t\r\n]*";" {
    printf("Warning: avoid 'using namespace std;' for large projects.\n");
    return USING_NS_STD;
}

"#"[ \t]*"include"[ \t]*"<"[a-zA-Z0-9_./]+">" {
    if (strstr(yytext, "bits/stdc++.h") != NULL) {
        printf("Warning: header <bits/stdc++.h> is non-standard and not portable.\n");
        return BITS_HEADER;
    }
    return TEXT;
}

"system"[ \t\r\n]*"("           {
    printf("Warning: avoid system() due to security risks.\n");
    return SYSTEM_CALL;
}

(.|\n)                        { return TEXT; }

%%

int yywrap(void) { return 1; }
