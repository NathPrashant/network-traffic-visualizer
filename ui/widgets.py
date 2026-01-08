from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.dropdown import DropDown
from kivy.uix.button import Button
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle

# --- GRAPH IMPORTS ---
from kivy.garden.graph import Graph, MeshLinePlot
import psutil
import math

# =========================
#   1. TRAFFIC GRAPH
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

        self.plot = MeshLinePlot(color=[0, 1, 0, 1])
        self.graph.add_plot(self.plot)
        self.add_widget(self.graph)
        self.points_list = [] 

    def update_graph(self, value):
        current_x = len(self.points_list)
        self.points_list.append((current_x, value))

        if len(self.points_list) > 60:
            self.points_list.pop(0)
            self.points_list = [(x - 1, y) for x, y in self.points_list]

        current_max = max([y for x, y in self.points_list]) if self.points_list else 0
        if current_max < 100:
            target_ymax = 100
        else:
            target_ymax = math.ceil(current_max / 100) * 100
        
        self.graph.ymax = int(target_ymax)
        self.graph.y_ticks_major = int(target_ymax / 4)
        self.plot.points = self.points_list


# =========================
#   2. TABLE HEADER
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
#   3. APP ROW
# =========================
class AppRow(BoxLayout):
    def __init__(self, app_name, **kwargs):
        super().__init__(**kwargs)
        self.app_name = app_name
        self.size_hint_y = None
        self.height = dp(40)  # Fixed Height is Critical
        self.padding = (dp(10), 0)

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

    def _create_dropdown(self):
        dropdown = DropDown(auto_width=False, width=dp(160))
        def add_item(text, callback):
            btn = Button(text=text, size_hint_y=None, height=dp(30), font_size="13sp")
            btn.bind(on_release=lambda *_: (callback(), dropdown.dismiss()))
            dropdown.add_widget(btn)
        add_item("Close App", self.close_app)
        return dropdown

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos) and touch.button == "right":
            self.dropdown.open(self)
            return True
        return super().on_touch_down(touch)

    def close_app(self):
        for proc in psutil.process_iter(["name"]):
            try:
                if proc.info["name"] == self.app_name:
                    proc.terminate()
            except Exception:
                pass


# =========================
#   4. APP DASHBOARD (FIXED SCROLLING)
# =========================
class AppDashboard(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        
        # 1. Header
        self.add_widget(TableHeader())
        
        # 2. Scroll View (Must disable horizontal scroll)
        from kivy.uix.scrollview import ScrollView
        self.scroll_view = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        
        # 3. Rows Container (Binds height to content)
        self.rows_container = BoxLayout(orientation='vertical', size_hint_y=None)
        self.rows_container.bind(minimum_height=self.rows_container.setter('height'))
        
        self.scroll_view.add_widget(self.rows_container)
        self.add_widget(self.scroll_view)
        
        self.rows = {}

    def update_apps(self, rates):
        # DEBUG: Un-comment this print to see if data is arriving in terminal
        # print(f"[DEBUG] Updating Apps: {list(rates.keys())}") 

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