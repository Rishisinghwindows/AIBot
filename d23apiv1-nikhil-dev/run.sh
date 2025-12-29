#!/bin/bash
# D23Bot Run Script
# Usage: ./run.sh [cli|web|test] [port]

cd /Users/pawansingh/Desktop/puch/D23Bot
export PYTHONPATH=/Users/pawansingh/Desktop/puch/D23Bot

PYTHON=/Users/pawansingh/Desktop/puch/D23Bot/venv/bin/python
PORT=${2:-8000}

case "${1:-cli}" in
    cli)
        echo "Starting CLI Chat..."
        $PYTHON cli_chat.py --v2 --lite
        ;;
    web)
        # Kill any existing process on the port
        lsof -ti:$PORT | xargs kill -9 2>/dev/null
        sleep 1
        echo "Starting Chainlit Web UI on http://localhost:$PORT"
        $PYTHON -m chainlit run chainlit_app.py -w --port $PORT
        ;;
    test)
        echo "Running quick test..."
        $PYTHON -c "
from cli_chat import CLIChat
import asyncio

async def test():
    chat = CLIChat(use_v2=True, lite_mode=True)
    await chat.initialize()

    tests = ['Hello', 'Aries horoscope', 'Weather in Mumbai']
    for q in tests:
        print(f'\\n--- {q} ---')
        r = await chat.chat(q)
        print(r[:200] + '...' if len(r) > 200 else r)

asyncio.run(test())
"
        ;;
    *)
        echo "Usage: ./run.sh [cli|web|test]"
        echo "  cli  - Interactive CLI chat (default)"
        echo "  web  - Chainlit web interface"
        echo "  test - Run quick tests"
        ;;
esac
