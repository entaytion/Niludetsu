import asyncio
import sys

async def run_process(cmd, name):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    async def read_stream(stream, prefix):
        while True:
            line = await stream.readline()
            if not line:
                break
            # Декодуємо рядок і прибираємо зайві пробіли
            line_decoded = line.decode('utf-8', errors='replace').strip()
            if line_decoded:
                print(f"[{prefix}] {line_decoded}")

    await asyncio.gather(
        read_stream(proc.stdout, name),
        read_stream(proc.stderr, name)
    )
    await proc.wait()

async def main():
    print("🚀 Starting Discord Bot and FastAPI Web Dashboard...")
    await asyncio.gather(
        run_process("uv run python main.py", "BOT"),
        run_process("uv run python -m web.app", "WEB")
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Stopped all processes.")
        sys.exit(0)
