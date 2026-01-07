from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.dropdown import DropDown
from kivy.uix.button import Button
from kivy.uix.modalview import ModalView
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle

# --- GRAPH IMPORTS ---
from kivy_garden.graph import Graph, MeshLinePlot
import psutil
import math

# =========================
#   1. TRAFFIC GRAPH (Dual Line Support)
# =========================
class TrafficGraph(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        
        self.graph = Graph(
            xlabel='Time (Seconds)',
            ylabel='Speed (KB/s)',
            x_ticks_minor=0,
            x_ticks_major=10,
            y_ticks_major=100,
            y_grid_label=True,
            x_grid_label=True,
            padding=5,
            x_grid=True,
            y_grid=True,
            xmin=0, xmax=60,
            ymin=0, ymax=100,
            label_options={'color': [1, 1, 1, 1], 'bold': True}
        )

        # Download Plot (Green)
        self.plot_down = MeshLinePlot(color=[0, 1, 0, 1])
        self.graph.add_plot(self.plot_down)
        
        # Upload Plot (Blue)
        self.plot_up = MeshLinePlot(color=[0, 0.5, 1, 1])
        self.graph.add_plot(self.plot_up)
        
        self.add_widget(self.graph)
        
        # Initialize history for both
        self.points_down = []
        self.points_up = []

    def update_graph(self, down_val, up_val):
        # 1. Update Download Line
        current_x = len(self.points_down)
        self.points_down.append((current_x, down_val))
        self.points_up.append((current_x, up_val))

        # Shift X axis if we exceed 60 seconds
        if len(self.points_down) > 60:
            self.points_down.pop(0)
            self.points_up.pop(0)
            self.points_down = [(x - 1, y) for x, y in self.points_down]
            self.points_up = [(x - 1, y) for x, y in self.points_up]

        # 2. Auto-scale Y-Axis based on the HIGHEST value of either line
        max_down = max([y for x, y in self.points_down]) if self.points_down else 0
        max_up = max([y for x, y in self.points_up]) if self.points_up else 0
        current_max = max(max_down, max_up)

        if current_max < 100:
            target_ymax = 100
        else:
            target_ymax = math.ceil(current_max / 100) * 100
        
        self.graph.ymax = int(target_ymax)
        self.graph.y_ticks_major = int(target_ymax / 4)
        
        # 3. Apply points
        self.plot_down.points = self.points_down
        self.plot_up.points = self.points_up


# =========================
#   2. APP GRAPH POPUP (New)
# =========================
class AppGraphPopup(ModalView):
    def __init__(self, app_name, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (0.9, 0.7)
        self.auto_dismiss = True
        self.app_name = app_name
        
        layout = BoxLayout(orientation='vertical', padding=10)
        
        # Header
        header = BoxLayout(size_hint_y=None, height=dp(30))
        header.add_widget(Label(text=f"Traffic: {app_name}", bold=True, font_size='18sp'))
        close_btn = Button(text="Close", size_hint_x=None, width=100)
        close_btn.bind(on_release=self.dismiss)
        header.add_widget(close_btn)
        
        layout.add_widget(header)
        
        # Legend
        legend = BoxLayout(size_hint_y=None, height=dp(30))
        legend.add_widget(Label(text="Download (Green)", color=[0,1,0,1]))
        legend.add_widget(Label(text="Upload (Blue)", color=[0,0.5,1,1]))
        layout.add_widget(legend)

        # The Graph
        self.graph_widget = TrafficGraph()
        layout.add_widget(self.graph_widget)
        
        self.add_widget(layout)

    def update(self, down, up):
        self.graph_widget.update_graph(down, up)


# =========================
#   3. TABLE HEADER
# =========================
class TableHeader(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.height = dp(40)
        self.padding = (dp(10), 0)
        
        # Yellow Text for Header
        self.add_widget(Label(text="APPLICATION", size_hint_x=0.5, halign='left', bold=True, color=[1,1,0,1]))
        self.add_widget(Label(text="DOWNLOAD", size_hint_x=0.25, bold=True, color=[0,1,0,1]))
        self.add_widget(Label(text="UPLOAD", size_hint_x=0.25, bold=True, color=[0,0.5,1,1]))


# =========================
#   4. APP ROW
# =========================
class AppRow(BoxLayout):
    def __init__(self, app_name, **kwargs):
        super().__init__(**kwargs)
        self.app_name = app_name
        self.size_hint_y = None
        self.height = dp(40)
        self.padding = (dp(10), 0)
        self.popup = None  # Reference to the graph popup

        # White App Name
        self.lbl_name = Label(
            text=app_name, 
            size_hint_x=0.5, 
            halign='left', 
            valign='middle',
            shorten=True,
            color=[1, 1, 1, 1]
        )
        self.lbl_name.bind(size=self.lbl_name.setter('text_size'))
        self.add_widget(self.lbl_name)

        self.lbl_down = Label(text="0.00", size_hint_x=0.25, color=[0,1,0,1])
        self.add_widget(self.lbl_down)

        self.lbl_up = Label(text="0.00", size_hint_x=0.25, color=[0,0.5,1,1])
        self.add_widget(self.lbl_up)

        self.dropdown = self._create_dropdown()

    def update_data(self, down, up):
        self.lbl_down.text = f"{down:.2f} KB/s"
        self.lbl_up.text = f"{up:.2f} KB/s"
        
        # If the popup is open, send data to it
        if self.popup and self.popup.parent:
            self.popup.update(down, up)

    def _create_dropdown(self):
        dropdown = DropDown(auto_width=False, width=dp(160))
        
        def add_item(text, callback):
            btn = Button(text=text, size_hint_y=None, height=dp(30), font_size="13sp")
            btn.bind(on_release=lambda *_: (callback(), dropdown.dismiss()))
            dropdown.add_widget(btn)
        
        add_item("Show Graph", self.open_graph)
        add_item("Close App", self.close_app)
        
        return dropdown

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos) and touch.button == "right":
            self.dropdown.open(self)
            return True
        return super().on_touch_down(touch)

    def open_graph(self):
        if not self.popup:
            self.popup = AppGraphPopup(self.app_name)
        self.popup.open()

    def close_app(self):
        for proc in psutil.process_iter(["name"]):
            try:
                if proc.info["name"] == self.app_name:
                    proc.terminate()
            except Exception:
                pass


# =========================
#   5. APP DASHBOARD
# =========================
class AppDashboard(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        
        # 1. Header
        self.add_widget(TableHeader())
        
        # 2. Scroll View
        from kivy.uix.scrollview import ScrollView
        self.scroll_view = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        
        # 3. Rows Container
        self.rows_container = BoxLayout(orientation='vertical', size_hint_y=None)
        self.rows_container.bind(minimum_height=self.rows_container.setter('height'))
        
        self.scroll_view.add_widget(self.rows_container)
        self.add_widget(self.scroll_view)
        
        self.rows = {}

    def update_apps(self, rates):
        current_apps = set(rates.keys())
        existing_apps = set(self.rows.keys())
        
        # Remove old
        for app in existing_apps - current_apps:
            self.rows_container.remove_widget(self.rows[app])
            del self.rows[app]

        # Add new
        for app, (down, up) in rates.items():
            if app not in self.rows:
                row = AppRow(app)
                self.rows[app] = row
                self.rows_container.add_widget(row)
            
            self.rows[app].update_data(down, up)