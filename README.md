# Network-Traffic-Visualizer

A real-time per-application network traffic visualizer built in Python with a Kivy-based GUI.
This project captures live network traffic, maps it to running applications, and displays
upload/download usage dynamically in a dashboard.

---

## Features

- Real-time network traffic monitoring
- Per-application bandwidth usage (Upload & Download)
- Live dashboard UI (Kivy)
- Dynamic graphs with auto-scaling Y-axis
- Right-click context menu on applications
  - View application information
  - Show per-app traffic graph (full screen)
  - Close application (where permitted)
- Stable application list (positions don’t jump)
- Linux and Windows support

---

## How It Works

Network Interface
-> Packet Capture Engine (Scapy / libpcap / Npcap)
-> Process–Connection Mapper (psutil)
-> Traffic Aggregator
-> Kivy Real-Time Visual Dashboard

Encrypted traffic is handled using metadata only.

---

## Tech Stack

- Python 3.10+
- Kivy
- Scapy / libpcap / Npcap
- psutil

---

## Installation

### Linux (Ubuntu / Debian / Arch)

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-dev libpcap-dev
```

```bash
git clone https://github.com/NathPrashant/network-traffic-visualizer.git
cd network-traffic-visualizer
```

```bash
python3 -m venv venv
source venv/bin/activate
```

```bash
pip install -r install.txt
```

```bash
sudo python main.py
```

Root privileges are required for packet capture.

---

### Windows (10 / 11)

1. Install Python 3.10+ and enable Add to PATH
2. Install Npcap (WinPcap API-compatible mode)

```bat
git clone https://github.com/NathPrashant/network-traffic-visualizer.git
```

change directory to network-traffic-visualizer via terminal. Eg:

```bat
cd network-traffic-visualizer
```

```bat
python -m venv venv
venv\Scripts\activate
```

```bat
pip install -r install.txt
```
Run terminal as Administrator:

```bat
python main.py
```

---

## Usage

- Launch the application to open the dashboard
- View live upload/download speeds per application
- Right-click an application to view details, graphs, or close it
- Use back button to return to dashboard

---

## Known Limitations

- Some system traffic may appear under System
- Application name resolution depends on OS permissions

---

## Contributing

Contributions are welcome.
Fork the repository, create a branch, commit changes, and open a pull request.

---

## License

MIT License
