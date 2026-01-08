# --- FIX 2: Disable the Red Dots (Must be at the very top) ---
from kivy.config import Config
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')

from kivy.app import App
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.core.window import Window

from core.packet_sniffer import PacketSniffer
from core.aggregator import TrafficAggregator
from core.pinger import NetworkPinger  # <--- NEW IMPORT
from ui.widgets import TrafficGraph, AppDashboard, LogViewer, PingGraph

class NetworkApp(App):
    def build(self):
        Window.size = (900, 700)
        return Builder.load_file("ui/dashboard.kv")

    def on_start(self):
        # 1. Start Sniffer
        self.sniffer = PacketSniffer()
        self.sniffer.start()

        # 2. Start Aggregator
        self.aggregator = TrafficAggregator()
        
        # 3. Start Pinger (NEW)
        self.pinger = NetworkPinger()
        self.pinger.start()

        # 4. Schedule Updates
        Clock.schedule_interval(self.update_ui, 1.0)
        Clock.schedule_interval(self.save_database, 5.0)

    def update_ui(self, dt):
        # --- Update Traffic Tab ---
        traffic_data = self.sniffer.get_traffic_data()
        rates = self.aggregator.calculate_rates(traffic_data)
        total_download = sum(down for down, up in rates.values())
        
        if "main_graph" in self.root.ids:
            self.root.ids.main_graph.update_graph(total_download, sum(up for down, up in rates.values()))

        if "dashboard" in self.root.ids:
            self.root.ids.dashboard.update_apps(rates)
            
        # --- Update Latency Tab (NEW) ---
        if "ping_graph" in self.root.ids:
            pings = self.pinger.get_pings()
            # Pass data: Cloudflare, Google, Valve
            self.root.ids.ping_graph.update_graph(
                pings.get("Cloudflare (1.1.1.1)", 0),
                pings.get("Google (8.8.8.8)", 0),
            )

    def save_database(self, dt):
        if hasattr(self, 'aggregator'):
            self.aggregator.save_data()

    def open_db_view(self):
        """Opens the Log Viewer Popup"""
        viewer = LogViewer(self.aggregator)
        viewer.open()

    def on_stop(self):
        if hasattr(self, 'sniffer'): self.sniffer.stop()
        if hasattr(self, 'aggregator'): self.aggregator.save_data()
        if hasattr(self, 'pinger'): self.pinger.stop() # Stop Pinger

if __name__ == "__main__":
    NetworkApp().run()