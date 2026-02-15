import os
import sys

# Define file path
HISTORY_FILE = "history.txt"

def test_history_system():
    print("---------------------------------------------------")
    print(" 🛠️  HISTORY FILE DIAGNOSTIC")
    print("---------------------------------------------------")

    # 1. CHECK IF FILE EXISTS
    if os.path.exists(HISTORY_FILE):
        print(f"✅ Found '{HISTORY_FILE}'.")
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                lines = [l.strip() for l in f.readlines() if l.strip()]
            print(f"   - Current Item Count: {len(lines)}")
            print(f"   - Last 3 Topics: {lines[-3:] if lines else 'None'}")
        except Exception as e:
            print(f"❌ Error reading file: {e}")
    else:
        print(f"⚠️  '{HISTORY_FILE}' does not exist. Creating it now...")
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                f.write("System Test Entry\n")
            print("✅ File created successfully.")
        except Exception as e:
            print(f"❌ CRITICAL: Cannot create file. Permission denied? Error: {e}")
            return

    # 2. TEST WRITING (APPEND)
    print("\n[TEST] Attempting to save a new topic...")
    test_topic = "TEST_TOPIC_IGNORE_ME"
    
    try:
        with open(HISTORY_FILE, "a", encoding="utf-8") as f:
            f.write(test_topic + "\n")
        print("✅ Write successful.")
    except Exception as e:
        print(f"❌ Write FAILED: {e}")

    # 3. VERIFY WRITE
    print("\n[TEST] Verifying if it was actually saved...")
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        content = f.read()
        
    if test_topic in content:
        print("✅ PASS: The system CAN update history.")
    else:
        print("❌ FAIL: The file was written to, but the data is missing. (File lock issue?)")

    # 4. TEST GENERATOR INTEGRATION
    print("\n[TEST] Checking if 'generators.py' can see this...")
    try:
        import generators
        past_topics = generators.get_past_topics()
        print(f"   - Generator sees {len(past_topics)} past topics.")
        if test_topic in past_topics:
            print("✅ PASS: Generators.py is reading the exclusion list correctly.")
        else:
            print("❌ FAIL: Generators.py is ignoring the file.")
    except ImportError:
        print("⚠️  Could not import 'generators.py'. Make sure it's in the same folder.")
    except Exception as e:
        print(f"❌ Generator Error: {e}")

    print("---------------------------------------------------")

if __name__ == "__main__":
    test_history_system()