# 🌐 NetMap: Automated Network Graphical Mapper

A self-hosted Flask + vis.js application that visualizes your local network (LAN) and Tailscale VPN mesh in real-time.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.12-blue.svg)
![Docker](https://img.shields.io/badge/docker-ready-blue.svg)

## 🚀 Features
- **Live LAN Discovery**: Uses `arp-scan` to find active devices on your local network.
- **Tailscale Integration**: Visualizes your VPN mesh, showing peers, online status, and connection paths (Direct vs. DERP relay).
- **Real-time Updates**: Uses Server-Sent Events (SSE) to push updates to the browser without refreshing.
- **Interactive Graph**: Powered by `vis.js` with force-directed layout, hover tooltips, and color-coded status.

## 🛠️ Installation & Deployment

### Prerequisites
- Docker and Docker Compose
- A host running Tailscale (if you want VPN visualization)

### Quick Start
1. **Clone the repository:**
   ```bash
   git clone https://github.com/augustcurry/netmap.git
   cd netmap
   ```

2. **Deploy with Docker Compose:**
   ```bash
   docker compose up -d --build
   ```

3. **Access the Map:**
   Open your browser and go to `http://<your-server-ip>:5050`

## 🐳 Docker Details
The container runs with `network_mode: host` to allow `arp-scan` to access the physical network interface and communicates with the Tailscale daemon via the shared socket at `/var/run/tailscale/tailscaled.sock`.

## 📜 License
This project is licensed under the MIT License.
