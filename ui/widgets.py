from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.dropdown import DropDown
from kivy.uix.button import Button
from kivy.metrics import dp

# --- GRAPH IMPORTS ---
from kivy_garden.graph import Graph, MeshLinePlot
import psutil
import math

# =========================
#   TRAFFIC GRAPH (FIXED)
# =========================
class TrafficGraph(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        
        # 1. Create the Graph with BETTER Spacing
        self.graph = Graph(
            xlabel='Time (Seconds)',
            ylabel='Speed (KB/s)',
            x_ticks_minor=0,
            x_ticks_major=10,            # Show X number every 10 seconds (Less clutter)
            y_ticks_major=20,            # Initial Y spacing
            y_grid_label=True,
            x_grid_label=True,
            padding=25,                  # <--- INCREASED THIS (Fixes text overlap)
            x_grid=True,
            y_grid=True,
            xmin=0, xmax=60,
            ymin=0, ymax=100             # Start with 100 KB/s max
        )

        # 2. Create the Plot
        self.plot = MeshLinePlot(color=[0, 1, 0, 1])  # Green Line
        self.graph.add_plot(self.plot)
        self.add_widget(self.graph)

        self.points_list = [] 

    def update_graph(self, value):
        # 1. Add new value
        current_x = len(self.points_list)
        self.points_list.append((current_x, value))

        # 2. Scrolling Logic (Keep last 60 points)
        if len(self.points_list) > 60:
            self.points_list.pop(0)
            self.points_list = [(x - 1, y) for x, y in self.points_list]

        # 3. INTELLIGENT SCALING (The Fix for the "Wall of Numbers")
        # We want roughly 5 labels on the Y-axis, no matter how fast the speed is.
        # If speed is 1000, ticks should be 200. If speed is 100, ticks should be 20.
        
        # Calculate ideal max height (add 20% buffer)
        current_max = max([y for x, y in self.points_list]) if self.points_list else 0
        target_ymax = max(100, current_max * 1.2) # Never go below 100 KB/s
        
        self.graph.ymax = int(target_ymax)
        self.graph.y_ticks_major = int(target_ymax / 5) # Always keep ~5 numbers on Y-axis

        # 4. Push data
        self.plot.points = self.points_list

# =========================
#   APP ROW (UNCHANGED)
# =========================
class AppRow(Label):
    def __init__(self, app_name, **kwargs):
        super().__init__(**kwargs)
        self.app_name = app_name
        self.size_hint_y = None
        self.height = dp(28)
        self.halign = "left"
        self.valign = "middle"
        self.padding = (dp(10), 0)
        self.bind(size=self._update_text)
        self.dropdown = self._create_dropdown()

    def _update_text(self, *_):
        self.text_size = self.size

    def _create_dropdown(self):
        dropdown = DropDown(auto_width=False, width=dp(160))
        def add_item(text, callback):
            btn = Button(text=text, size_hint_y=None, height=dp(30), font_size="13sp")
            btn.bind(on_release=lambda *_: (callback(), dropdown.dismiss()))
            dropdown.add_widget(btn)
        
        add_item("Information", self.show_info)
        add_item("Show Graph", self.show_graph)
        add_item("Close App", self.close_app)
        return dropdown

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos) and touch.button == "right":
            self.dropdown.open(self)
            return True
        return super().on_touch_down(touch)

    def show_info(self):
        from kivy.app import App
        App.get_running_app().show_app_info(self.app_name)

    def show_graph(self):
        from kivy.app import App
        App.get_running_app().show_app_graph(self.app_name)

    def close_app(self):
        for proc in psutil.process_iter(["name"]):
            try:
                if proc.info["name"] == self.app_name:
                    proc.terminate()
            except Exception:
                pass

# =========================
#   APP DASHBOARD (UNCHANGED)
# =========================
class AppDashboard(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.rows = {}

    def update_apps(self, rates):
        for app, (down, up) in rates.items():
            if app not in self.rows:
                row = AppRow(app)
                self.rows[app] = row
                self.add_widget(row)
            self.rows[app].text = f"{app}  |  ⬇ {down:.2f} kbps  |  ⬆ {up:.2f} kbps"