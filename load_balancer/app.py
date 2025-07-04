from flask import Flask, request, jsonify, send_from_directory
import os, uuid, requests, threading, time
from consistent_hash import ConsistentHashRing

# In-memory vote state
votes = {
    "kubernetes": 0,
    "docker": 0,
    "helm": 0,
    "prometheus": 0
}

app = Flask(__name__)
ring = ConsistentHashRing()
managed_replicas = {}

# --- Spawn and Remove Containers ---
def spawn_container(name):
    cmd = f"docker run -d --network net1 --network-alias {name} -e SERVER_ID={name} --name {name} server_image"
    os.system(cmd)
    return name

def remove_container(name):
    os.system(f"docker rm -f {name}")

# --- Replica Management ---
@app.route("/rep", methods=["GET"])
def replicas():
    return jsonify({
        "message": {
            "N": len(managed_replicas),
            "replicas": list(managed_replicas.keys())
        },
        "status": "successful"
    }), 200

@app.route("/add", methods=["POST"])
def add():
    data = request.get_json()
    n = data.get("n")
    hostnames = data.get("hostnames", [])

    if len(hostnames) > n:
        return jsonify({
            "message": "<Error> Length of hostname list is more than newly added instances",
            "status": "failure"
        }), 400

    for i in range(n):
        name = hostnames[i] if i < len(hostnames) else f"Server-{str(uuid.uuid4())[:4]}"
        spawn_container(name)
        ring.add_server(name)
        managed_replicas[name] = True

    return replicas()

@app.route("/rm", methods=["DELETE"])
def rm():
    data = request.get_json()
    n = data.get("n")
    hostnames = data.get("hostnames", [])

    if len(hostnames) > n:
        return jsonify({
            "message": "<Error> Length of hostname list is more than removable instances",
            "status": "failure"
        }), 400

    to_remove = hostnames + [k for k in managed_replicas.keys() if k not in hostnames][:n - len(hostnames)]
    for name in to_remove:
        remove_container(name)
        ring.remove_server(name)
        del managed_replicas[name]

    return replicas()

# --- Request Routing with Consistent Hashing ---
@app.route("/<path:path>", methods=["GET"])
def proxy(path):
    rid = str(uuid.uuid4().int % 1000000)
    try:
        target = ring.get_server(rid)
    except:
        return jsonify({"message": "<Error> No available servers", "status": "failure"}), 400

    try:
        res = requests.get(f"http://{target}:5000/{path}")
        return jsonify(res.json()), res.status_code
    except Exception as e:
        return jsonify({
            "message": f"<Error> Failed to contact server: {str(e)}",
            "status": "failure"
        }), 500

# --- Frontend Serving ---
@app.route("/")
def index():
    return send_from_directory("static", "index.html")

# --- Voting Endpoints ---
@app.route("/api/vote", methods=["POST"])
def vote():
    data = request.get_json()
    option = data.get("option")
    if option in votes:
        votes[option] += 1
    return jsonify({"votes": votes})

@app.route("/api/votes", methods=["GET"])
def get_votes():
    return jsonify(votes)

# --- Heartbeat Monitor for Failover ---
def monitor_heartbeats():
    while True:
        time.sleep(5)
        failed = []
        for server in list(managed_replicas.keys()):
            try:
                res = requests.get(f"http://{server}:5000/heartbeat", timeout=2)
                if res.status_code != 200:
                    raise Exception("Non-200 response")
            except:
                print(f"[⚠️] Heartbeat failed for {server}")
                failed.append(server)

        for dead in failed:
            print(f"[❌] Removing {dead}")
            remove_container(dead)
            ring.remove_server(dead)
            del managed_replicas[dead]

            new_id = f"Server-{str(uuid.uuid4())[:4]}"
            print(f"[🆕] Spawning replacement: {new_id}")
            spawn_container(new_id)
            ring.add_server(new_id)
            managed_replicas[new_id] = True

# --- Main ---
if __name__ == "__main__":
    threading.Thread(target=monitor_heartbeats, daemon=True).start()
    app.run(host="0.0.0.0", port=5000)
