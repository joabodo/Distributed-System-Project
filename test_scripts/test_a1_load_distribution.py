import asyncio
import aiohttp
import matplotlib.pyplot as plt
from collections import Counter

URL = "http://localhost:5000/home"
REQUESTS = 10000

async def fetch(session):
    try:
        async with session.get(URL) as resp:
            if resp.status == 200:
                json = await resp.json()
                msg = json.get("message", "")
                return msg.split(":")[-1].strip()  # Extract "serverX"
            else:
                return f"HTTP {resp.status}"
    except Exception as e:
        return "error"

async def main():
    counter = Counter()
    async with aiohttp.ClientSession() as session:
        tasks = [fetch(session) for _ in range(REQUESTS)]
        results = await asyncio.gather(*tasks)

    for server_id in results:
        counter[server_id] += 1

    print("\n📊 Request Distribution:")
    for sid, count in counter.items():
        print(f"{sid}: {count}")

    if len(counter) == 1 and "error" in counter:
        print("\n⚠️ All requests failed. Please confirm your load balancer is running and servers are added.")
        return

    # Plot bar chart
    plt.bar(counter.keys(), counter.values(), color='skyblue')
    plt.title(f"Load Distribution across N=3 servers")
    plt.xlabel("Server ID")
    plt.ylabel("Number of Requests")
    plt.tight_layout()
    plt.savefig("a1_load_distribution.png")
    plt.show()

if __name__ == "__main__":
    asyncio.run(main())
