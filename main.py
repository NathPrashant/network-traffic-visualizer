# --- FIX 2: Disable the Red Dots (Must be at the very top) ---
from kivy.config import Config
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')

from kivy.app import App
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.core.window import Window

from core.packet_sniffer import PacketSniffer
from core.aggregator import TrafficAggregator
from ui.widgets import TrafficGraph, AppDashboard

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

        # 3. Schedule UI updates (Every 1 second)
        Clock.schedule_interval(self.update_ui, 1.0)
        
        # --- NEW: Schedule Database Auto-Save (Every 5 seconds) ---
        Clock.schedule_interval(self.save_database, 5.0)

    def update_ui(self, dt):
        traffic_data = self.sniffer.get_traffic_data()
        rates = self.aggregator.calculate_rates(traffic_data)
        total_download = sum(down for down, up in rates.values())
        
        if "main_graph" in self.root.ids:
            self.root.ids.main_graph.update_graph(total_download)

        if "dashboard" in self.root.ids:
            self.root.ids.dashboard.update_apps(rates)

    def save_database(self, dt):
        """Helper function to save data"""
        if hasattr(self, 'aggregator'):
            self.aggregator.save_data()

    def on_stop(self):
        # Clean up threads and Save one last time
        if hasattr(self, 'sniffer'):
            self.sniffer.stop()
        if hasattr(self, 'aggregator'):
            self.aggregator.save_data() # <--- Final Save

if __name__ == "__main__":
    NetworkApp().run()