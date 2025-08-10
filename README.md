# C++ Online Compiler (Dockerized)

A secure, containerized web app to compile and run C++ code. Includes a small Flex/Bison-based code scanner that analyzes submitted source before compilation. Backend is FastAPI; frontend is a simple responsive page.

## Features

- Compile C++20 with `g++` inside a Docker container
- Run with CPU and memory limits
- Flex/Bison scanner (`codescan`) provides basic static analysis/warnings
- Clean UI with code editor, flags, input, and separate compile/run outputs

## Quick Start (Windows 10/11)

- Install Docker Desktop
- Ensure WSL2 backend is enabled (Docker Desktop setting)
- In a terminal in the project root:

```bash
docker compose up --build
```

- Open `http://localhost:8000` in your browser

## Project Structure

- `server/`: FastAPI app
- `web/`: frontend assets
- `tools/`: Flex/Bison scanner source and Makefile
- `Dockerfile`: container image with g++, flex, bison, python
- `docker-compose.yml`: runs the app

## API

- POST `/api/compile-run`
  - Request JSON:
    - `code` (string): C++ source
    - `stdin` (string, optional): input to feed the program
    - `compileOptions` (array of strings, optional): extra g++ flags
    - `run` (bool, optional, default true): run after compiling
  - Response JSON:
    - `scan`: { `stdout`, `stderr`, `exitCode` }
    - `compile`: { `stdout`, `stderr`, `exitCode`, `durationMs` }
    - `run` (if executed): { `stdout`, `stderr`, `exitCode`, `durationMs`, `wasKilledByTimeout` }

## Security Notes

- All compilation and execution happens inside a container with CPU/memory limits.
- Scanner provides lightweight warnings. Do not treat it as a substitute for full static analysis or sandboxing.
- For untrusted users, run this behind an API gateway with rate limiting and per-request containers.

## Local Development without Docker

- Requires Linux with `g++`, `python3`, `pip`, `flex`, `bison`
- Build scanner:

```bash
cd tools && make && cd ..
```

- Install server deps and run:

```bash
cd server
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Open `http://localhost:8000`.

## License

MIT

