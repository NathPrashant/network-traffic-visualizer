from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.dropdown import DropDown
from kivy.uix.button import Button
from kivy.uix.modalview import ModalView
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.metrics import dp
from kivy_garden.graph import Graph, MeshLinePlot
import psutil
import math
import subprocess
import os
import platform
import datetime
import csv
import time

# --- NEW COLOR CONSTANTS ---
COLOR_DOWN = [0, 1, 0, 1]       # Green
COLOR_UP   = [0.2, 0.8, 1, 1]   # Bright Sky Blue (High Visibility)
COLOR_TEXT = [1, 1, 1, 1]       # White

# =========================
#   1. TRAFFIC GRAPH
# =========================
class TrafficGraph(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.graph = Graph(
            xlabel='Time (Seconds)', ylabel='Speed (KB/s)',
            x_ticks_minor=0, x_ticks_major=10, y_ticks_major=100,
            y_grid_label=True, x_grid_label=True, padding=5,
            x_grid=True, y_grid=True, xmin=0, xmax=60, ymin=0, ymax=100,
            label_options={'color': [1, 1, 1, 1], 'bold': True}
        )
        self.plot_down = MeshLinePlot(color=COLOR_DOWN)
        self.plot_up = MeshLinePlot(color=COLOR_UP)  # <-- New Bright Color
        self.graph.add_plot(self.plot_down)
        self.graph.add_plot(self.plot_up)
        self.add_widget(self.graph)
        self.points_down = []
        self.points_up = []

    def update_graph(self, down_val, up_val):
        current_x = len(self.points_down)
        self.points_down.append((current_x, down_val))
        self.points_up.append((current_x, up_val))

        if len(self.points_down) > 60:
            self.points_down.pop(0)
            self.points_up.pop(0)
            self.points_down = [(x - 1, y) for x, y in self.points_down]
            self.points_up = [(x - 1, y) for x, y in self.points_up]

        max_v = max(
            max([y for x, y in self.points_down] or [0]), 
            max([y for x, y in self.points_up] or [0])
        )
        
        target_ymax = max(100, math.ceil(max_v / 100) * 100)
        self.graph.ymax = int(target_ymax)
        self.graph.y_ticks_major = int(target_ymax / 4)
        
        self.plot_down.points = self.points_down
        self.plot_up.points = self.points_up


# =========================
#   2. APP GRAPH POPUP
# =========================
class AppGraphPopup(ModalView):
    def __init__(self, app_name, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (0.9, 0.7)
        self.auto_dismiss = True
        
        layout = BoxLayout(orientation='vertical', padding=10)
        header = BoxLayout(size_hint_y=None, height=dp(30))
        header.add_widget(Label(text=f"Traffic: {app_name}", bold=True, font_size='18sp'))
        close_btn = Button(text="Close", size_hint_x=None, width=100)
        close_btn.bind(on_release=self.dismiss)
        header.add_widget(close_btn)
        
        layout.add_widget(header)
        self.graph_widget = TrafficGraph()
        layout.add_widget(self.graph_widget)
        self.add_widget(layout)

    def update(self, down, up):
        self.graph_widget.update_graph(down, up)


# =========================
#   3. TABLE HEADER (NOW CLICKABLE)
# =========================
class TableHeader(BoxLayout):
    def __init__(self, sort_callback, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.height = dp(40)
        self.padding = (dp(10), 0)
        
        # Helper to create invisible buttons that look like labels
        def create_header_btn(text, key, color, size_x):
            btn = Button(
                text=text, 
                size_hint_x=size_x, 
                background_color=(0,0,0,0), # Transparent
                color=color,
                bold=True
            )
            # When clicked, call the dashboard's sorting function
            btn.bind(on_release=lambda x: sort_callback(key))
            return btn

        self.add_widget(create_header_btn("APPLICATION (Sort A-Z)", 'name', [1,1,0,1], 0.5))
        self.add_widget(create_header_btn("DOWNLOAD ⬇", 'download', COLOR_DOWN, 0.25))
        self.add_widget(create_header_btn("UPLOAD ⬆", 'upload', COLOR_UP, 0.25))


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
        self.popup = None

        self.lbl_name = Label(
            text=app_name, 
            size_hint_x=0.5, 
            halign='left', 
            valign='middle',
            shorten=True,
            color=COLOR_TEXT
        )
        self.lbl_name.bind(size=self.lbl_name.setter('text_size'))
        self.add_widget(self.lbl_name)

        self.lbl_down = Label(text="0.00", size_hint_x=0.25, color=COLOR_DOWN)
        self.add_widget(self.lbl_down)

        self.lbl_up = Label(text="0.00", size_hint_x=0.25, color=COLOR_UP) # <-- New Color
        self.add_widget(self.lbl_up)

        self.dropdown = self._create_dropdown()

    def update_data(self, down, up):
        self.lbl_down.text = f"{down:.2f} KB/s"
        self.lbl_up.text = f"{up:.2f} KB/s"
        if self.popup and self.popup.parent:
            self.popup.update(down, up)

    def _create_dropdown(self):
        dropdown = DropDown(auto_width=False, width=dp(160))
        def add_item(text, cb):
            btn = Button(text=text, size_hint_y=None, height=dp(30), font_size="13sp")
            btn.bind(on_release=lambda *_: (cb(), dropdown.dismiss()))
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
        if not self.popup: self.popup = AppGraphPopup(self.app_name)
        self.popup.open()

    def close_app(self):
        for proc in psutil.process_iter(["name"]):
            try:
                if proc.info["name"] == self.app_name:
                    proc.terminate()
            except Exception: pass


# =========================
#   5. APP DASHBOARD (SORTING LOGIC ADDED)
# =========================
class AppDashboard(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        
        # SORTING STATE
        self.sort_key = 'download' # Default sort by download
        self.sort_desc = True      # Default High -> Low

        # Pass 'self.change_sort' to the Header so buttons can call it
        self.add_widget(TableHeader(self.change_sort))
        
        self.scroll_view = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        self.rows_container = BoxLayout(orientation='vertical', size_hint_y=None)
        self.rows_container.bind(minimum_height=self.rows_container.setter('height'))
        self.scroll_view.add_widget(self.rows_container)
        self.add_widget(self.scroll_view)
        self.rows = {}

    def change_sort(self, key):
        """Called when user clicks a header button"""
        if self.sort_key == key:
            # Toggle Ascending/Descending if clicking same column
            self.sort_desc = not self.sort_desc
        else:
            # New column? Default to Descending (Big numbers first)
            self.sort_key = key
            self.sort_desc = True

    def update_apps(self, rates):
        current_apps = set(rates.keys())
        existing_apps = set(self.rows.keys())
        
        # Remove old apps
        for app in existing_apps - current_apps:
            self.rows_container.remove_widget(self.rows[app])
            del self.rows[app]

        # --- SORTING LOGIC ---
        # Convert dict to list so we can sort it: [('Chrome', (100, 50)), ...]
        data_list = list(rates.items())

        if self.sort_key == 'name':
            # Sort A-Z. 'not self.sort_desc' makes A top, Z bottom default
            data_list.sort(key=lambda x: x[0].lower(), reverse=not self.sort_desc)
        elif self.sort_key == 'download':
            # Sort by Download Speed (Index 0 of tuple)
            data_list.sort(key=lambda x: x[1][0], reverse=self.sort_desc)
        elif self.sort_key == 'upload':
            # Sort by Upload Speed (Index 1 of tuple)
            data_list.sort(key=lambda x: x[1][1], reverse=self.sort_desc)

        # --- RENDER IN ORDER ---
        # We clear the container and re-add widgets in the new sorted order
        # (This is efficient enough for ~50 apps)
        self.rows_container.clear_widgets()

        for app_name, (down, up) in data_list:
            # Only create row if it doesn't exist
            if app_name not in self.rows:
                self.rows[app_name] = AppRow(app_name)
            
            # Update data
            self.rows[app_name].update_data(down, up)
            
            # Add to container (in the new sorted order)
            self.rows_container.add_widget(self.rows[app_name])


# =========================
#   6. LOG VIEWER CLASSES (PRESERVED)
# =========================

class LogRow(BoxLayout):
    def __init__(self, log_entry, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.height = dp(30)
        self.log_entry = log_entry # (ts, app, down, up, src, dst)
        
        ts = datetime.datetime.fromtimestamp(log_entry[0]).strftime('%H:%M:%S')
        self.add_widget(Label(text=ts, size_hint_x=0.15))
        
        self.app_name = log_entry[1]
        self.add_widget(Label(text=self.app_name, size_hint_x=0.25, shorten=True))
        
        spd = f"D:{log_entry[2]:.1f} U:{log_entry[3]:.1f}"
        self.add_widget(Label(text=spd, size_hint_x=0.2))
        
        ips = f"{log_entry[4]} -> {log_entry[5]}"
        self.add_widget(Label(text=ips, size_hint_x=0.4, font_size='11sp'))

        self.dropdown = DropDown()
        btn_loc = Button(text="Open Location", size_hint_y=None, height=dp(30))
        btn_loc.bind(on_release=lambda x: (self.open_location(), self.dropdown.dismiss()))
        self.dropdown.add_widget(btn_loc)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos) and touch.button == "right":
            self.dropdown.open(self)
            return True
        return super().on_touch_down(touch)

    def open_location(self):
        exe_path = None
        for proc in psutil.process_iter(['name', 'exe']):
            try:
                if proc.info['name'] == self.app_name:
                    exe_path = proc.info['exe']
                    break
            except: pass
        
        if exe_path and os.path.exists(exe_path):
            if platform.system() == "Windows":
                subprocess.Popen(['explorer', '/select,', exe_path])
            elif platform.system() == "Linux":
                subprocess.Popen(['xdg-open', os.path.dirname(exe_path)])
        else:
            print(f"Path not found for {self.app_name}")


class LogViewer(ModalView):
    def __init__(self, aggregator, **kwargs):
        super().__init__(**kwargs)
        self.aggregator = aggregator
        self.size_hint = (0.95, 0.9)
        self.current_logs = []
        
        layout = BoxLayout(orientation='vertical', padding=10)
        
        # Header
        header = BoxLayout(size_hint_y=None, height=dp(40), spacing=10)
        header.add_widget(Label(text="Instance Logs", bold=True, font_size='20sp', size_hint_x=0.3))
        
        self.search_input = TextInput(hint_text="Search App Name...", size_hint_x=0.5, multiline=False)
        self.search_input.bind(text=self.on_search)
        header.add_widget(self.search_input)
        
        btn_close = Button(text="Close", size_hint_x=0.2)
        btn_close.bind(on_release=self.dismiss)
        header.add_widget(btn_close)
        layout.add_widget(header)

        # Actions
        actions = BoxLayout(size_hint_y=None, height=dp(40), spacing=10)
        btn_refresh = Button(text="Refresh", size_hint_x=None, width=100)
        btn_refresh.bind(on_release=self.refresh_logs)
        actions.add_widget(btn_refresh)
        
        btn_export = Button(text="Export to CSV", size_hint_x=None, width=120)
        btn_export.bind(on_release=self.export_csv)
        actions.add_widget(btn_export)
        actions.add_widget(Label(text="")) # Spacer
        layout.add_widget(actions)
        
        # Columns
        headers = BoxLayout(size_hint_y=None, height=dp(30))
        headers.add_widget(Label(text="Time", size_hint_x=0.15, bold=True, color=[1,1,0,1]))
        headers.add_widget(Label(text="App", size_hint_x=0.25, bold=True, color=[1,1,0,1]))
        headers.add_widget(Label(text="Speed (KB/s)", size_hint_x=0.2, bold=True, color=[1,1,0,1]))
        headers.add_widget(Label(text="Src -> Dst IP", size_hint_x=0.4, bold=True, color=[1,1,0,1]))
        layout.add_widget(headers)

        # List
        self.scroll = ScrollView()
        self.list_container = BoxLayout(orientation='vertical', size_hint_y=None)
        self.list_container.bind(minimum_height=self.list_container.setter('height'))
        self.scroll.add_widget(self.list_container)
        layout.add_widget(self.scroll)
        self.add_widget(layout)
        
        self.refresh_logs()

    def on_search(self, instance, value):
        self.refresh_logs()

    def refresh_logs(self, *args):
        self.list_container.clear_widgets()
        search_text = self.search_input.text.strip()
        self.current_logs = self.aggregator.get_logs(app_filter=search_text if search_text else None)
        for log in self.current_logs:
            self.list_container.add_widget(LogRow(log))

    def export_csv(self, *args):
        if not self.current_logs: return
        filename = f"traffic_logs_{int(time.time())}.csv"
        try:
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Timestamp", "App Name", "Download (KB/s)", "Upload (KB/s)", "Src IP", "Dst IP"])
                for log in self.current_logs:
                    ts_str = datetime.datetime.fromtimestamp(log[0]).strftime('%Y-%m-%d %H:%M:%S')
                    writer.writerow([ts_str, log[1], log[2], log[3], log[4], log[5]])
            
            print(f"Exported to {filename}")
            # Button feedback
            original_text = args[0].text
            args[0].text = "Saved!"
            from kivy.clock import Clock
            Clock.schedule_once(lambda dt: setattr(args[0], 'text', original_text), 2)
        except Exception as e:
            print(f"Export Error: {e}")