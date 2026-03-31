from flask import Flask, render_template, Response
import subprocess, json, time, threading

app = Flask(__name__)
cache = {"data": {}, "lock": threading.Lock()}

def get_lan_hosts():
    try:
        # Running arp-scan on localnet to find devices
        result = subprocess.run(
            ["arp-scan", "--localnet", "--quiet"],
            capture_output=True, text=True, timeout=15
        )
        hosts = []
        for line in result.stdout.splitlines():
            parts = line.split("\t")
            if len(parts) >= 2 and (parts[0].startswith("192.") or parts[0].startswith("10.") or parts[0].startswith("172.")):
                hosts.append({"ip": parts[0], "mac": parts[1],
                               "label": parts[2] if len(parts) > 2 else parts[0]})
        return hosts
    except Exception as e:
        print(f"Error in get_lan_hosts: {e}")
        return []

def get_tailscale_peers():
    try:
        # Running tailscale status --json for VPN mesh data
        result = subprocess.run(
            ["tailscale", "status", "--json"],
            capture_output=True, text=True, timeout=10
        )
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
                "direct": not peer.get("CurAddr", ""), # Check if CurAddr is direct or DERP
                "relay": peer.get("Relay", None),
                "exit_node": peer.get("ExitNode", False),
                "is_self": False,
            })
        return self_node, peers
    except Exception as e:
        print(f"Error in get_tailscale_peers: {e}")
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
        time.sleep(10)  # refresh every 10 seconds

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
        while True:
            with cache["lock"]:
                d = cache["data"]
            if d.get("ts", 0) != last_ts:
                last_ts = d.get("ts", 0)
                yield f"data: {json.dumps(d)}\n\n"
            time.sleep(2)
    return Response(event_gen(), mimetype="text/event-stream")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, threaded=True)
