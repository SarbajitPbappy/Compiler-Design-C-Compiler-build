from __future__ import annotations

from pydantic import BaseModel, Field
from typing import List, Optional


class CompileRunRequest(BaseModel):
    code: str = Field(..., description="C++ source code")
    stdin: Optional[str] = Field(default="", description="Program standard input")
    compileOptions: Optional[List[str]] = Field(default=None, description="Extra g++ flags")
    run: bool = Field(default=True, description="Run the program after compiling")


class ProcessResult(BaseModel):
    stdout: str
    stderr: str
    exitCode: int
    durationMs: int | None = None
    wasKilledByTimeout: bool | None = None


class CompileRunResponse(BaseModel):
    scan: ProcessResult
    compile: ProcessResult
    run: Optional[ProcessResult] = None
