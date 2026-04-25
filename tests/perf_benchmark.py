import asyncio
import time
import base64
import os
from unittest.mock import MagicMock, AsyncMock, patch
from research_cli.researcher import ResearchAgent

async def monitor_loop():
    latencies = []
    monitor_loop.running = True
    while monitor_loop.running:
        start = time.perf_counter()
        await asyncio.sleep(0.001)
        latencies.append(time.perf_counter() - start - 0.001)
    return latencies

async def run_benchmark():
    # Set up environment
    os.environ["RESEARCH_WORKSPACE"] = "/tmp"
    os.environ["RESEARCH_GEMINI_API_KEY"] = "fake"

    agent = ResearchAgent(api_key="fake")

    # Large image data (approx 10MB)
    image_bytes = b"a" * (10 * 1024 * 1024)
    large_data_b64 = base64.b64encode(image_bytes).decode("utf-8")

    mock_interaction = MagicMock()
    mock_interaction.outputs = [
        {"type": "image", "data": large_data_b64}
    ]

    # We want to measure the impact of base64.b64decode in the event loop
    # So we patch the actual save call but keep the decode call
    with patch("research_cli.researcher.async_save_binary_to_file", AsyncMock()) as mock_save, \
         patch("research_cli.researcher.genai.Client") as mock_genai_client:

        mock_client = mock_genai_client.return_value
        mock_client.aio.interactions.create = AsyncMock(return_value=mock_interaction)

        monitor_task = asyncio.create_task(monitor_loop())
        # Give monitor some time to start
        await asyncio.sleep(0.1)

        start_time = time.perf_counter()
        try:
            await agent.generate_image("prompt", "out.png", "model", True)
        except Exception as e:
            print(f"Error during generate_image: {e}")
            import traceback
            traceback.print_exc()
        end_time = time.perf_counter()

        monitor_loop.running = False
        latencies = await monitor_task

        max_latency = max(latencies) * 1000
        avg_latency = (sum(latencies) / len(latencies)) * 1000
        print(f"Total time: {(end_time - start_time)*1000:.2f}ms")
        print(f"Max loop latency: {max_latency:.2f}ms")
        print(f"Avg loop latency: {avg_latency:.2f}ms")

        # Verify that mock_save was called with bytes, meaning decode happened
        if mock_save.called:
            assert isinstance(mock_save.call_args[0][0], bytes)
        else:
            print("Warning: async_save_binary_to_file was not called!")

if __name__ == "__main__":
    try:
        asyncio.run(run_benchmark())
    except Exception as e:
        print(f"Benchmark failed: {e}")
        import traceback
        traceback.print_exc()
