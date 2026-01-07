import threading
import time
import psutil
# CHANGED: Added UDP to imports
from scapy.all import sniff, TCP, IP, UDP
from core.platform import IS_WINDOWS

if IS_WINDOWS:
    from scapy.all import conf
    conf.use_pcap = True

class PacketSniffer:
    def __init__(self):
        self.running = False
        self.traffic_data = {}
        self.lock = threading.Lock()
        self.port_cache = {}
        self.cache_timeout = 10

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._sniff_loop)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        self.running = False

    def get_traffic_data(self):
        with self.lock:
            data = self.traffic_data.copy()
            self.traffic_data.clear()
        return data

    def _sniff_loop(self):
        while self.running:
            try:
                # We still filter for IP, but the callback handles TCP vs UDP
                sniff(prn=self._on_packet, store=False, timeout=1)
            except Exception as e:
                print(f"Sniff Error: {e}")
                time.sleep(1)

    def _on_packet(self, pkt):
        if not self.running:
            return
        
        # 1. Check for IP Layer (Internet Traffic)
        if IP in pkt:
            try:
                size = len(pkt)
                app_name = "System (Unknown)"
                direction = "up" # Default assumption

                # A. Handle TCP/UDP (The ones with Ports)
                if TCP in pkt or UDP in pkt:
                    if TCP in pkt:
                        layer = TCP
                    else:
                        layer = UDP
                        
                    sport = pkt[layer].sport
                    dport = pkt[layer].dport
                    
                    # Logic to identify App
                    app_port = sport
                    if self._is_local_port(dport):
                        direction = "down"
                        app_port = dport
                    
                    app_name = self._get_process_by_port(app_port)

                # B. Handle ICMP (Ping) - Protocol 1
                elif pkt[IP].proto == 1:
                    app_name = "System (ICMP/Ping)"
                    # We can't tell direction easily without checking IP, 
                    # so we just assume 'down' for incoming pings to be safe
                    direction = "down" 

                # C. Handle Everything Else (IGMP, GRE, ESP, SCTP)
                else:
                    # pkt[IP].proto gives the ID (e.g., 2=IGMP, 47=GRE, 50=ESP)
                    proto_id = pkt[IP].proto
                    app_name = f"System (Proto {proto_id})"
                    direction = "down"

                # Save Data
                with self.lock:
                    if app_name not in self.traffic_data:
                        self.traffic_data[app_name] = [0, 0]
                    
                    if direction == "down":
                        self.traffic_data[app_name][0] += size
                    else:
                        self.traffic_data[app_name][1] += size

            except Exception:
                pass
        
        # 2. OPTIONAL: Check for ARP (Layer 2 - Local Network)
        # ARP is not 'IP', so it's outside the if IP block.
        # Warning: ARP packets are tiny and won't affect speed much.
        elif "ARP" in pkt:
            with self.lock:
                name = "System (ARP)"
                if name not in self.traffic_data:
                    self.traffic_data[name] = [0, 0]
                self.traffic_data[name][0] += len(pkt)
                    
    def _is_local_port(self, port):
        return True

    def _get_process_by_port(self, port):
        now = time.time()
        if port in self.port_cache:
            app, ts = self.port_cache[port]
            if now - ts < self.cache_timeout:
                return app

        # Try to resolve port
        try:
            for c in psutil.net_connections(kind="inet"):
                if c.laddr.port == port:
                    try:
                        p = psutil.Process(c.pid)
                        name = p.name()
                        self.port_cache[port] = (name, now)
                        return name
                    except:
                        pass
        except:
            pass
        
        return "Unknown"