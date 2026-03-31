from flask import Flask, render_template, Response
import subprocess, json, time, threading

app = Flask(__name__)
cache = {"data": {}, "lock": threading.Lock()}

def get_lan_hosts():
    try:
        print("DEBUG: Starting LAN scan...")
        # Use --interface to be explicit if possible, but --localnet is the fallback
        result = subprocess.run(
            ["arp-scan", "--localnet", "--quiet", "--retry=1", "--timeout=500"],
            capture_output=True, text=True, timeout=20
        )
        hosts = []
        for line in result.stdout.splitlines():
            parts = line.split("\t")
            if len(parts) >= 2:
                hosts.append({"ip": parts[0], "mac": parts[1],
                               "label": parts[2] if len(parts) > 2 else parts[0]})
        print(f"DEBUG: LAN scan found {len(hosts)} hosts.")
        return hosts
    except Exception as e:
        print(f"ERROR in get_lan_hosts: {e}")
        return []

def get_tailscale_peers():
    try:
        print("DEBUG: Starting Tailscale scan...")
        result = subprocess.run(
            ["tailscale", "status", "--json"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            print(f"ERROR: Tailscale status returned code {result.returncode}")
            return None, []
            
        data = json.loads(result.stdout)
        self_node = {
            "hostname": data["Self"]["HostName"],
            "tailscale_ip": data["Self"]["TailscaleIPs"][0],
            "online": True,
            "direct": True,
            "is_self": True,
        }
        peers = []
        for _, peer in data.get("Peer", {}).items():
            peers.append({
                "hostname": peer["HostName"],
                "tailscale_ip": peer["TailscaleIPs"][0] if peer.get("TailscaleIPs") else "N/A",
                "online": peer.get("Online", False),
                "direct": not peer.get("CurAddr", ""),
                "relay": peer.get("Relay", None),
                "exit_node": peer.get("ExitNode", False),
                "is_self": False,
            })
        print(f"DEBUG: Tailscale scan found {len(peers)} peers.")
        return self_node, peers
    except Exception as e:
        print(f"ERROR in get_tailscale_peers: {e}")
        return None, []

def refresh_loop():
    while True:
        lan = get_lan_hosts()
        self_node, ts_peers = get_tailscale_peers()
        with cache["lock"]:
            cache["data"] = {
                "lan": lan,
                "tailscale_self": self_node,
                "tailscale_peers": ts_peers,
                "ts": time.time()
            }
        print(f"DEBUG: Cache updated at {time.ctime()}")
        time.sleep(15)

threading.Thread(target=refresh_loop, daemon=True).start()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/network")
def api_network():
    with cache["lock"]:
        return json.dumps(cache["data"])

@app.route("/stream")
def stream():
    def event_gen():
        last_ts = 0
        print("DEBUG: New SSE stream client connected.")
        while True:
            with cache["lock"]:
                d = cache["data"]
            
            # Send data if new, otherwise send a heartbeat ping
            if d.get("ts", 0) != last_ts:
                last_ts = d.get("ts", 0)
                yield f"data: {json.dumps(d)}\n\n"
            else:
                yield ": heartbeat\n\n"  # SSE comment to keep connection alive
            time.sleep(2)
    return Response(event_gen(), mimetype="text/event-stream")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, threaded=True)
