import sqlite3


class LoginManager:
    def __init__(self):
        self.database_path = './server/accounts/accounts.db'
        try:
            self.conn = sqlite3.connect(self.database_path)
            print("[INFO] Connected to database")
        except sqlite3.Error as e:
            print("[ERROR] Unable to connect to database:", e)

    def login(self, username: str):

        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE login=?", (username,))
        user = cursor.fetchone()
        if user:
            print(f"[INFO] Player {username} logged in successfully!")
        else:
            print("[INFO] Creating new account...")
            self.register(username)

    def register(self, username):
        cursor = self.conn.cursor()
        try:
            cursor.execute("INSERT INTO users (login) VALUES (?)", (username,))
            self.conn.commit()
            print(f"[INFO] Player {username} logged in successfully!")
        except sqlite3.IntegrityError:
            print("[Error] Problems with database...")
