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
        self.sniffer = PacketSniffer()
        self.sniffer.start()
        self.aggregator = TrafficAggregator()
        Clock.schedule_interval(self.update_ui, 1.0)

    def update_ui(self, dt):
        traffic_data = self.sniffer.get_traffic_data()
        rates = self.aggregator.calculate_rates(traffic_data)
        total_download = sum(down for down, up in rates.values())
        
        if "main_graph" in self.root.ids:
            self.root.ids.main_graph.update_graph(total_download)

        if "dashboard" in self.root.ids:
            self.root.ids.dashboard.update_apps(rates)

    def on_stop(self):
        if hasattr(self, 'sniffer'):
            self.sniffer.stop()

if __name__ == "__main__":
    NetworkApp().run()