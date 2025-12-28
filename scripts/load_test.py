"""
Load Testing Script for Twilio Voice AI Assistant

Tests the system's ability to handle concurrent calls.

Usage:
    python scripts/load_test.py [--calls 50] [--url http://localhost:8000]
"""

import asyncio
import aiohttp
import time
import argparse
from datetime import datetime


async def simulate_call(session, call_number, base_url):
    """Simulate a single call with multiple speech exchanges"""
    start_time = time.time()
    call_sid = None

    try:
        # Initiate call
        async with session.post(
            f"{base_url}/make-call",
            json={"to_number": f"+1234567{call_number:04d}"}
        ) as response:
            if response.status == 200:
                call_data = await response.json()
                call_sid = call_data.get('call_sid')
            else:
                return {
                    "call_number": call_number,
                    "success": False,
                    "error": f"Failed to initiate call: {response.status}",
                    "duration": 0
                }

        # Simulate 3 speech exchanges
        for i in range(3):
            await asyncio.sleep(1)  # Simulate speech delay

            async with session.post(
                f"{base_url}/voice/process-speech",
                data={
                    "CallSid": call_sid,
                    "SpeechResult": f"Test message {i} from call {call_number}",
                    "Confidence": "0.95"
                }
            ) as response:
                if response.status != 200:
                    return {
                        "call_number": call_number,
                        "success": False,
                        "error": f"Speech processing failed: {response.status}",
                        "duration": time.time() - start_time
                    }

        duration = time.time() - start_time
        return {
            "call_number": call_number,
            "success": True,
            "duration": duration,
            "call_sid": call_sid
        }

    except Exception as e:
        return {
            "call_number": call_number,
            "success": False,
            "error": str(e),
            "duration": time.time() - start_time
        }


async def load_test(num_calls: int = 50, base_url: str = "http://localhost:8000"):
    """Run load test with N concurrent calls"""
    print(f"\n{'='*60}")
    print(f"  Load Test: {num_calls} Concurrent Calls")
    print(f"  Target: {base_url}")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    start_time = time.time()

    async with aiohttp.ClientSession() as session:
        tasks = [simulate_call(session, i, base_url) for i in range(num_calls)]
        results = await asyncio.gather(*tasks)

    total_duration = time.time() - start_time

    # Analyze results
    successful = [r for r in results if r.get('success')]
    failed = [r for r in results if not r.get('success')]
    durations = [r['duration'] for r in successful]

    print(f"\n{'='*60}")
    print(f"  Load Test Results")
    print(f"{'='*60}")
    print(f"  Total calls:      {num_calls}")
    print(f"  Successful:       {len(successful)} ({len(successful)/num_calls*100:.1f}%)")
    print(f"  Failed:           {len(failed)} ({len(failed)/num_calls*100:.1f}%)")
    print(f"  Total time:       {total_duration:.2f}s")
    print(f"{'='*60}")

    if durations:
        print(f"  Call Duration Stats:")
        print(f"    Average:        {sum(durations)/len(durations):.2f}s")
        print(f"    Minimum:        {min(durations):.2f}s")
        print(f"    Maximum:        {max(durations):.2f}s")
        print(f"    Median:         {sorted(durations)[len(durations)//2]:.2f}s")
        print(f"{'='*60}")

    if failed:
        print(f"\n  Failed Calls:")
        for fail in failed[:5]:  # Show first 5 failures
            print(f"    Call #{fail['call_number']}: {fail.get('error', 'Unknown error')}")
        if len(failed) > 5:
            print(f"    ... and {len(failed) - 5} more")
        print(f"{'='*60}")

    print(f"\n  Performance: {num_calls/total_duration:.2f} calls/second")
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(description="Load test for Twilio Voice AI Assistant")
    parser.add_argument('--calls', type=int, default=50, help='Number of concurrent calls (default: 50)')
    parser.add_argument('--url', type=str, default='http://localhost:8000', help='Base URL (default: http://localhost:8000)')

    args = parser.parse_args()

    try:
        asyncio.run(load_test(num_calls=args.calls, base_url=args.url))
    except KeyboardInterrupt:
        print("\n\nLoad test interrupted by user")
    except Exception as e:
        print(f"\nError during load test: {e}")


if __name__ == "__main__":
    main()
