from __future__ import annotations

import os
import shutil
from typing import Optional

from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from starlette.routing import Route, Mount
from starlette.staticfiles import StaticFiles

from .sandbox import run_command, RunLimits
from .utils import session_workspace, write_text_file


def _win_to_wsl_path(win_path: str) -> str:
    drive, rest = os.path.splitdrive(os.path.abspath(win_path))
    drive_letter = drive.replace(':', '').lower()
    path_part = rest.replace('\\', '/')
    return f"/mnt/{drive_letter}{path_part}"


async def compile_run(request):
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)

    code = body.get("code", "")
    if not isinstance(code, str) or code.strip() == "":
        return JSONResponse({"error": "'code' must be a non-empty string"}, status_code=400)

    stdin_val = body.get("stdin", "")
    if not isinstance(stdin_val, str):
        return JSONResponse({"error": "'stdin' must be a string"}, status_code=400)

    compile_options = body.get("compileOptions") or []
    if not isinstance(compile_options, list) or any(not isinstance(x, str) for x in compile_options):
        return JSONResponse({"error": "'compileOptions' must be an array of strings"}, status_code=400)

    run_after = body.get("run", True)
    if not isinstance(run_after, bool):
        return JSONResponse({"error": "'run' must be a boolean"}, status_code=400)

    base_flags = ["-O2", "-pipe", "-Wall", "-Wextra", "-pedantic"]
    standards = ["-std=c++20", "-std=c++17", "-std=c++14", "-std=c++11", "-std=c++03"]
    # User can override/add flags (we will prepend the chosen standard)
    user_flags = compile_options

    with session_workspace() as workdir:
        source_path = os.path.join(workdir, "main.cpp")
        bin_name = "program.exe" if os.name == "nt" else "program.out"
        bin_path = os.path.join(workdir, bin_name)
        write_text_file(source_path, code)

        # Scan step (optional)
        if shutil.which("codescan") is not None:
            scan_outcome = run_command(["codescan", source_path], working_directory=workdir, limits=RunLimits(cpu_time_seconds=1, wall_time_seconds=2, memory_megabytes=128))
        else:
            class S:
                stdout = "codescan not found: scanner skipped.\n"
                stderr = ""
                exit_code = 0
                duration_ms = 0
                was_killed_by_timeout = False
            scan_outcome = S()

        # Compile with fallback across standards and environments
        compiled_in = None
        last_outcome = None
        def try_compile_host(std_flag: str):
            flags = [std_flag, *base_flags, *user_flags]
            cmd = ["g++", *flags, source_path, "-o", bin_path]
            return run_command(cmd, working_directory=workdir, limits=RunLimits(cpu_time_seconds=20, wall_time_seconds=30, memory_megabytes=1024, file_size_megabytes=256))
        def try_compile_wsl(std_flag: str):
            flags = [std_flag, *base_flags, *user_flags]
            wsl_dir = _win_to_wsl_path(workdir)
            cmd = ["wsl", "--cd", wsl_dir, "g++", *flags, "main.cpp", "-o", bin_name]
            return run_command(cmd, working_directory=None, limits=RunLimits(cpu_time_seconds=20, wall_time_seconds=30, memory_megabytes=1024, file_size_megabytes=256))

        # Attempt host
        if shutil.which("g++") is not None:
            for std in standards:
                outcome = try_compile_host(std)
                last_outcome = outcome
                if outcome.exit_code == 0:
                    compiled_in = "host"
                    break
                # If the error indicates unknown std flag, continue trying
                if "unrecognized command line option" in (outcome.stderr or ""):
                    continue
                # Otherwise accept failure for this env
            
        # Attempt WSL if not compiled
        if compiled_in is None and os.name == "nt" and shutil.which("wsl") is not None:
            for std in standards:
                outcome = try_compile_wsl(std)
                last_outcome = outcome
                if outcome.exit_code == 0:
                    compiled_in = "wsl"
                    break

        if compiled_in is None and last_outcome is None:
            return JSONResponse({
                "scan": {
                    "stdout": scan_outcome.stdout,
                    "stderr": scan_outcome.stderr,
                    "exitCode": scan_outcome.exit_code,
                    "durationMs": scan_outcome.duration_ms,
                    "wasKilledByTimeout": scan_outcome.was_killed_by_timeout,
                },
                "compile": {
                    "stdout": "",
                    "stderr": (
                        "C++ compiler not found. Options:\n"
                        "- Start Docker Desktop and run via Docker (recommended).\n"
                        "- Install MSYS2/MinGW-w64 on Windows and add g++ to PATH.\n"
                        "- Or install WSL with g++ and ensure 'wsl' is available.\n"
                    ),
                    "exitCode": -1,
                    "durationMs": 0,
                    "wasKilledByTimeout": False,
                },
                "run": None,
            }, status_code=200)
        # If compiled_in is still None, we have a last_outcome failure to report
        if compiled_in is None:
            compile_outcome = last_outcome
        else:
            compile_outcome = last_outcome

        run_result_payload = None
        if run_after and compile_outcome.exit_code == 0:
            if os.name == "nt" and shutil.which("g++") is None and shutil.which("wsl") is not None:
                wsl_dir = _win_to_wsl_path(workdir)
                run_cmd = ["wsl", "--cd", wsl_dir, f"./{bin_name}"]
                run_outcome = run_command(run_cmd, input_data=stdin_val or "", working_directory=None, limits=RunLimits(cpu_time_seconds=2, wall_time_seconds=3, memory_megabytes=256))
            else:
                run_outcome = run_command([bin_path], input_data=stdin_val or "", working_directory=workdir, limits=RunLimits(cpu_time_seconds=2, wall_time_seconds=3, memory_megabytes=256))
            run_result_payload = {
                "stdout": run_outcome.stdout,
                "stderr": run_outcome.stderr,
                "exitCode": run_outcome.exit_code,
                "durationMs": run_outcome.duration_ms,
                "wasKilledByTimeout": run_outcome.was_killed_by_timeout,
            }

        return JSONResponse({
            "scan": {
                "stdout": scan_outcome.stdout,
                "stderr": scan_outcome.stderr,
                "exitCode": scan_outcome.exit_code,
                "durationMs": scan_outcome.duration_ms,
                "wasKilledByTimeout": scan_outcome.was_killed_by_timeout,
            },
            "compile": {
                "stdout": "",
                "stderr": compile_outcome.stderr,
                "exitCode": compile_outcome.exit_code,
                "durationMs": compile_outcome.duration_ms,
                "wasKilledByTimeout": compile_outcome.was_killed_by_timeout,
            },
            "run": run_result_payload,
        })


routes = [
    Route("/api/compile-run", compile_run, methods=["POST"]),
    Mount("/", app=StaticFiles(directory=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "web")), html=True), name="web"),
]

app = Starlette(routes=routes)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
