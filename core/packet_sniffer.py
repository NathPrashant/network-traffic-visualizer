import threading
import time
import psutil
from scapy.all import sniff, TCP, IP
from core.platform import IS_WINDOWS

if IS_WINDOWS:
    from scapy.all import conf
    conf.use_pcap = True

class PacketSniffer:
    def __init__(self):
        self.running = False
        self.traffic_data = {}  # Stores {app_name: (download_bytes, upload_bytes)}
        self.lock = threading.Lock()
        self.port_cache = {}
        self.cache_timeout = 10

    def start(self):
        """Starts the sniffing in a background thread"""
        self.running = True
        self.thread = threading.Thread(target=self._sniff_loop)
        self.thread.daemon = True  # Kills thread when app closes
        self.thread.start()

    def stop(self):
        self.running = False

    def get_traffic_data(self):
        """Returns the data collected since the last call and clears it"""
        with self.lock:
            data = self.traffic_data.copy()
            self.traffic_data.clear() # Reset so we calculate speed per second
        return data

    def _sniff_loop(self):
        # We run sniff in short bursts so we can check 'self.running' to stop
        while self.running:
            try:
                sniff(prn=self._on_packet, store=False, timeout=1)
            except Exception as e:
                print(f"Sniff Error: {e}")
                time.sleep(1)

    def _on_packet(self, pkt):
        if not self.running:
            return

        # We only care about IP packets (Internet)
        if IP in pkt and TCP in pkt:
            try:
                size = len(pkt)
                sport = pkt[TCP].sport
                dport = pkt[TCP].dport
                src_ip = pkt[IP].src
                
                # Simple logic: If source is not local, it's Download.
                # If destination is not local, it's Upload.
                # (This is a simplification, but works for basic monitoring)
                direction = "up"
                app_port = sport # We check the source port for the app name
                
                # Check if it's incoming (Download)
                # If the destination port is ours, we are receiving
                if self._is_local_port(dport):
                    direction = "down"
                    app_port = dport
                
                app_name = self._get_process_by_port(app_port)

                with self.lock:
                    if app_name not in self.traffic_data:
                        self.traffic_data[app_name] = [0, 0] # [down, up]
                    
                    if direction == "down":
                        self.traffic_data[app_name][0] += size
                    else:
                        self.traffic_data[app_name][1] += size

            except Exception:
                pass

    def _is_local_port(self, port):
        # Helper to decide traffic direction
        # This is a bit tricky, but usually works
        return True # Simplified: We resolve the app by the port anyway

    def _get_process_by_port(self, port):
        now = time.time()

        # 1. Check Cache
        if port in self.port_cache:
            app, ts = self.port_cache[port]
            if now - ts < self.cache_timeout:
                return app

        # 2. Find App (Windows/Linux)
        candidates = []
        try:
            for c in psutil.net_connections(kind="inet"):
                if c.laddr.port == port:
                    try:
                        p = psutil.Process(c.pid)
                        name = p.name()
                        
                        # Cache it
                        self.port_cache[port] = (name, now)
                        return name
                    except:
                        pass
        except:
            pass
        
        return "Unknown"