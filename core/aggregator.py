import time
from core.database import DatabaseManager

class TrafficAggregator:
    def __init__(self):
        self.last_check_time = time.time()
        self.db = DatabaseManager()
        
        # Load history from DB so we don't start at 0 every time
        # Format: {'Chrome': [Total_Down_Bytes, Total_Up_Bytes]}
        self.global_totals = self.db.load_traffic()

    def calculate_rates(self, fresh_traffic_data):
        """
        1. Takes fresh packet counts.
        2. Adds them to the Global Totals.
        3. Returns the Speed (KB/s) for the UI.
        """
        now = time.time()
        elapsed = now - self.last_check_time
        if elapsed < 0.1: elapsed = 0.1
        self.last_check_time = now
        
        current_rates = {} # Speed per second (for UI)
        
        for app_name, (new_down, new_up) in fresh_traffic_data.items():
            # 1. Update Global Totals (The "Time Machine" part)
            if app_name not in self.global_totals:
                self.global_totals[app_name] = [0, 0]
            
            self.global_totals[app_name][0] += new_down
            self.global_totals[app_name][1] += new_up
            
            # 2. Calculate Speed (The "Live Graph" part)
            down_speed = (new_down / 1024) / elapsed
            up_speed = (new_up / 1024) / elapsed
            current_rates[app_name] = (down_speed, up_speed)
            
        return current_rates

    def save_data(self):
        """Triggers a database save of the global totals"""
        self.db.save_traffic(self.global_totals)