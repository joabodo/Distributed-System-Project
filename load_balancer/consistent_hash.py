import hashlib
import bisect

class ConsistentHashRing:
    def __init__(self, slots=512):
        self.slots = slots
        self.replicas = {}
        self.ring = []
        self.server_map = {}

    # H(i): main hash function using SHA-256
    def _hash(self, key):
        return int(hashlib.sha256(key.encode()).hexdigest(), 16) % self.slots

    # Φ(i, j): replica position using MD5
    def _vhash(self, server_id, replica_id):
        key = f"{server_id}-{replica_id}"
        return int(hashlib.md5(key.encode()).hexdigest(), 16) % self.slots

    def add_server(self, server_id, k=9):
        self.replicas[server_id] = []
        for j in range(k):
            slot = self._vhash(server_id, j)
            bisect.insort(self.ring, slot)
            self.server_map[slot] = server_id
            self.replicas[server_id].append(slot)

    def remove_server(self, server_id):
        for slot in self.replicas.get(server_id, []):
            self.ring.remove(slot)
            del self.server_map[slot]
        del self.replicas[server_id]

    def get_server(self, request_id):
        h = self._hash(request_id)
        if not self.ring:
            raise Exception("No servers in ring")
        idx = bisect.bisect(self.ring, h) % len(self.ring)
        slot = self.ring[idx]
        return self.server_map[slot]
