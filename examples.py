"""
Example usage of the Twilio Voice AI Assistant API

This script demonstrates how to:
1. Check system health (including Redis, Chroma, RAG)
2. Make single outbound calls
3. Make multiple concurrent calls
4. Check active sessions
5. Interrupt calls
"""
import requests
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed


# Configuration
BASE_URL = "http://localhost:8000"
TO_NUMBER = "+917000978867"  # Replace with actual number


def check_health():
    """Example: Check system health including all components"""
    print("Checking system health...")

    response = requests.get(f"{BASE_URL}/health")

    if response.status_code == 200:
        data = response.json()
        print(f"✓ System Status: {data['status'].upper()}")
        print(f"  Timestamp: {data['timestamp']}")
        print(f"\n  Components:")
        for component, info in data['components'].items():
            status = info.get('status', 'unknown')
            message = info.get('message', '')
            icon = "✓" if status == "healthy" else "⚠" if status == "disabled" else "✗"
            print(f"    {icon} {component}: {status} - {message}")
        return data['status'] == 'healthy'
    else:
        print("✗ Server is not responding")
        return False


def check_basic_health():
    """Example: Basic health check (legacy endpoint)"""
    print("Checking basic server health...")

    response = requests.get(f"{BASE_URL}/")

    if response.status_code == 200:
        data = response.json()
        print(f"✓ Server is running: {data['message']}")
        print(f"  Active sessions: {data.get('active_sessions', 0)}")
        return True
    else:
        print("✗ Server is not responding")
        return False


def get_active_sessions():
    """Example: Get all active call sessions"""
    print("Fetching active sessions...")

    response = requests.get(f"{BASE_URL}/sessions")

    if response.status_code == 200:
        data = response.json()
        session_count = data['active_sessions']
        print(f"✓ Active sessions: {session_count}")

        if session_count > 0:
            print("\n  Sessions:")
            for call_sid, session in data['sessions'].items():
                print(f"    • {call_sid[:20]}...")
                print(f"      To: {session['to']}")
                print(f"      From: {session['from']}")
                print(f"      Messages: {session['message_count']}")
                print(f"      Started: {session['started_at']}")
        return data
    else:
        print(f"✗ Error: {response.text}")
        return None


def get_session_details(call_sid):
    """Example: Get specific session details"""
    print(f"Fetching session details for {call_sid[:20]}...")

    response = requests.get(f"{BASE_URL}/session/{call_sid}")

    if response.status_code == 200:
        data = response.json()
        print(f"✓ Session found")
        print(f"  To: {data.get('to')}")
        print(f"  From: {data.get('from')}")
        print(f"  Language: {data.get('language', 'en')}")
        print(f"  Started: {data.get('started_at')}")

        history = data.get('conversation_history', [])
        print(f"  Conversation ({len(history)} messages):")
        for msg in history[:5]:  # Show first 5 messages
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')[:50]
            print(f"    {role}: {content}...")

        if len(history) > 5:
            print(f"    ... and {len(history) - 5} more messages")

        return data
    else:
        print(f"✗ Error: {response.text}")
        return None


def make_outbound_call(to_number=None, custom_message=None):
    """Example: Make an outbound call"""
    to_number = to_number or TO_NUMBER
    print(f"Making outbound call to {to_number}...")

    payload = {"to_number": to_number}
    if custom_message:
        payload["initial_message"] = custom_message

    response = requests.post(
        f"{BASE_URL}/make-call",
        json=payload
    )

    if response.status_code == 200:
        data = response.json()
        print(f"✓ Call initiated successfully!")
        print(f"  Call SID: {data['call_sid']}")
        print(f"  Status: {data['status']}")
        print(f"  To: {data['to']}")
        print(f"  From: {data['from']}")
        return data['call_sid']
    else:
        print(f"✗ Error: {response.text}")
        return None


def make_concurrent_calls(num_calls=3):
    """Example: Make multiple concurrent calls"""
    print(f"\nMaking {num_calls} concurrent calls...")
    print("=" * 60)

    start_time = time.time()
    call_sids = []

    with ThreadPoolExecutor(max_workers=num_calls) as executor:
        # Submit all calls
        futures = [
            executor.submit(make_outbound_call, TO_NUMBER, f"Test call #{i+1}")
            for i in range(num_calls)
        ]

        # Collect results
        for future in as_completed(futures):
            call_sid = future.result()
            if call_sid:
                call_sids.append(call_sid)

    duration = time.time() - start_time

    print(f"\n✓ Initiated {len(call_sids)} calls in {duration:.2f} seconds")
    print(f"  Successful: {len(call_sids)}/{num_calls}")
    return call_sids


def interrupt_call(call_sid):
    """Example: Interrupt an active call"""
    print(f"\nInterrupting call {call_sid[:20]}...")

    response = requests.post(f"{BASE_URL}/interrupt-call/{call_sid}")

    if response.status_code == 200:
        print("✓ Call interrupted successfully!")
        return True
    else:
        print(f"✗ Error: {response.text}")
        return False


def run_simple_test():
    """Run a simple single call test"""
    print("\n" + "=" * 60)
    print("  SIMPLE TEST: Single Call")
    print("=" * 60)

    # 1. Check health
    check_health()

    # 2. Make a call
    print("\n" + "=" * 60)
    call_sid = make_outbound_call()

    if call_sid:
        # 3. Wait a bit and check session
        print("\nWaiting 3 seconds...")
        time.sleep(3)

        print("\n" + "=" * 60)
        get_session_details(call_sid)


def run_concurrent_test():
    """Run a concurrent calls test"""
    print("\n" + "=" * 60)
    print("  CONCURRENT TEST: Multiple Calls")
    print("=" * 60)

    # 1. Check health
    if not check_health():
        print("\n⚠ System not healthy, skipping concurrent test")
        return

    # 2. Make multiple calls
    call_sids = make_concurrent_calls(num_calls=3)

    # 3. Wait and check all sessions
    print("\nWaiting 3 seconds...")
    time.sleep(3)

    print("\n" + "=" * 60)
    get_active_sessions()


def run_full_test():
    """Run comprehensive test suite"""
    print("\n" + "=" * 60)
    print("  FULL TEST SUITE")
    print("=" * 60)

    # 1. System health
    print("\n[1/5] System Health Check")
    print("-" * 60)
    if not check_health():
        print("\n⚠ System not healthy, stopping tests")
        return

    # 2. Basic health
    print("\n[2/5] Basic Server Check")
    print("-" * 60)
    check_basic_health()

    # 3. Single call
    print("\n[3/5] Single Call Test")
    print("-" * 60)
    call_sid = make_outbound_call()

    # 4. Check sessions
    print("\n[4/5] Active Sessions")
    print("-" * 60)
    time.sleep(2)
    get_active_sessions()

    # 5. Session details
    if call_sid:
        print("\n[5/5] Session Details")
        print("-" * 60)
        get_session_details(call_sid)


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  Twilio Voice AI Assistant - Test Examples")
    print("=" * 60)

    print("\nAvailable tests:")
    print("  1. Simple Test (single call)")
    print("  2. Concurrent Test (multiple calls)")
    print("  3. Full Test Suite (comprehensive)")
    print("  4. Health Check Only")
    print("  5. Custom Call")

    choice = input("\nSelect test (1-5, or press Enter for simple test): ").strip()

    if choice == "2":
        run_concurrent_test()
    elif choice == "3":
        run_full_test()
    elif choice == "4":
        check_health()
    elif choice == "5":
        phone = input("Enter phone number (E.164 format, e.g., +1234567890): ").strip()
        if phone:
            make_outbound_call(to_number=phone)
        else:
            print("Invalid phone number")
    else:
        # Default: simple test
        run_simple_test()

    print("\n" + "=" * 60)
    print("  Tests completed")
    print("=" * 60 + "\n")
