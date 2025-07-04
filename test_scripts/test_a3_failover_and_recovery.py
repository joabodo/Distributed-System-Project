import requests
import time
import subprocess
import json

BASE_URL = "http://localhost:5000"

def print_title(title):
    print("\n" + "="*len(title))
    print(title)
    print("="*len(title))

def call(endpoint, method="GET", payload=None):
    url = f"{BASE_URL}{endpoint}"
    try:
        if method == "GET":
            res = requests.get(url)
        elif method == "POST":
            res = requests.post(url, json=payload)
        elif method == "DELETE":
            res = requests.delete(url, json=payload)
        else:
            return None
        return res
    except Exception as e:
        print(f"Request to {endpoint} failed: {e}")
        return None

def pretty(res):
    try:
        return json.dumps(res.json(), indent=2)
    except:
        return res.text

def main():
    # 1. Add replicas
    print_title("STEP 1: Adding 3 replicas")
    add_payload = {"n": 3, "hostnames": ["server1", "server2", "server3"]}
    res = call("/add", method="POST", payload=add_payload)
    print("Status:", res.status_code)
    print(pretty(res))

    time.sleep(3)

    # 2. Verify /home works
    print_title("STEP 2: Verifying /home endpoint works")
    for _ in range(3):
        res = call("/home")
        print("→", res.json())

    # 3. Simulate failure by stopping server2
    print_title("STEP 3: Simulating failure (docker stop server2)")
    subprocess.run("docker stop server2", shell=True)
    print("Waiting for heartbeat monitor to detect failure...")
    time.sleep(15)

    # 4. Check /rep after failure
    print_title("STEP 4: Checking /rep after failure")
    res = call("/rep")
    print("Status:", res.status_code)
    replicas_after = res.json()["message"]["replicas"]
    print("Replicas:", replicas_after)

    # 5. Confirm new server was spawned
    if "server2" not in replicas_after and len(replicas_after) == 3:
        print("✅ server2 was removed and replaced.")
    else:
        print("⚠️ server2 was not replaced correctly.")

    # 6. Test /home again after recovery
    print_title("STEP 5: Testing /home again")
    for _ in range(3):
        res = call("/home")
        print("→", res.json())

if __name__ == "__main__":
    main()
