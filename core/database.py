import sqlite3
import threading

class DatabaseManager:
    def __init__(self, db_name="traffic_history.db"):
        # check_same_thread=False allows multiple threads to save data
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.lock = threading.Lock()
        self._create_table()

    def _create_table(self):
        """Creates the table if it doesn't exist"""
        with self.lock:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS app_traffic (
                    app_name TEXT PRIMARY KEY,
                    download_bytes INTEGER,
                    upload_bytes INTEGER
                )
            """)
            self.conn.commit()

    def load_traffic(self):
        """Returns a dictionary of {app_name: [total_down, total_up]}"""
        with self.lock:
            self.cursor.execute("SELECT * FROM app_traffic")
            rows = self.cursor.fetchall()
            # Convert SQL rows back to Python Dictionary
            return {row[0]: [row[1], row[2]] for row in rows}

    def save_traffic(self, traffic_dict):
        """Saves the current totals to the database"""
        with self.lock:
            for app, (down, up) in traffic_dict.items():
                # INSERT OR REPLACE updates the row if it exists, creates it if not
                self.cursor.execute("""
                    INSERT OR REPLACE INTO app_traffic (app_name, download_bytes, upload_bytes)
                    VALUES (?, ?, ?)
                """, (app, down, up))
            self.conn.commit()

    def close(self):
        self.conn.close()