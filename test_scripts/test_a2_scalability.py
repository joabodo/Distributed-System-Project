import asyncio
import aiohttp
import matplotlib.pyplot as plt
from collections import Counter
import json
import subprocess
import time

BASE_URL = "http://localhost:5000"
REQUESTS = 10000
replica_range = range(2, 7)
averages = []

# Register replicas using /add
def register_replicas(n):
    hostnames = [f"server{i}" for i in range(1, n+1)]
    payload = {"n": n, "hostnames": hostnames}
    response = subprocess.getoutput(f'curl -s -X POST {BASE_URL}/add -H "Content-Type: application/json" -d \'{json.dumps(payload)}\'')
    print(f"Added {n} replicas:", response)

# Remove all replicas using /rm
def remove_all():
    subprocess.getoutput(f'curl -s -X DELETE {BASE_URL}/rm -H "Content-Type: application/json" -d \'{{"n": 10, "hostnames": []}}\'')

# Make a single request to /home
async def fetch(session):
    try:
        async with session.get(f"{BASE_URL}/home") as resp:
            if resp.status == 200:
                data = await resp.json()
                return data["message"].split(":")[-1].strip()
            else:
                return "HTTP_ERR"
    except:
        return "error"

# Run N requests and count how they distribute
async def run_test():
    counter = Counter()
    async with aiohttp.ClientSession() as session:
        tasks = [fetch(session) for _ in range(REQUESTS)]
        results = await asyncio.gather(*tasks)

    for server_id in results:
        counter[server_id] += 1

    return counter

# Main testing loop
def main():
    for n in replica_range:
        print(f"\n🧪 Testing with N={n} replicas...")
        remove_all()
        time.sleep(2)
        register_replicas(n)
        time.sleep(5)

        counts = asyncio.run(run_test())

        print("Request Distribution:", dict(counts))

        server_loads = [count for sid, count in counts.items() if "server" in sid]
        avg = round(sum(server_loads) / len(server_loads), 2) if server_loads else 0
        averages.append(avg)

    # Plot
    plt.plot(list(replica_range), averages, marker='o', color='green')
    plt.title("Average Server Load vs Number of Replicas (A-2)")
    plt.xlabel("Number of Replicas")
    plt.ylabel("Average Requests per Server")
    plt.grid(True)
    plt.xticks(replica_range)
    plt.tight_layout()
    plt.savefig("a2_avg_load_plot.png")
    plt.show()

if __name__ == "__main__":
    main()
