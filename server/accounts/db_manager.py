import sqlite3


class DBManager:
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

    def update_wins(self, username):
        self.update_user_stats(username, "wins")

    def update_losses(self, username):
        self.update_user_stats(username, "losses")

    def update_user_stats(self, username, stat):
        cursor = self.conn.cursor()
        cursor.execute(f"SELECT {stat} FROM users WHERE login = ?", (username,))
        current_value = cursor.fetchone()[0]

        updated_value = current_value + 1

        sql_query = f"""
                       UPDATE users
                       SET {stat} = ?
                       WHERE login = ?
                       """
        cursor.execute(sql_query, (updated_value, username))
        self.conn.commit()

    def get_user_stats(self, username):
        cursor = self.conn.cursor()

        cursor.execute("SELECT wins FROM users WHERE login = ?", (username,))
        result = cursor.fetchone()

        if result is not None:
            wins = result[0]

        cursor.execute("SELECT losses FROM users WHERE login = ?", (username,))
        result = cursor.fetchone()

        if result is not None:
            losses = result[0]

        return wins, losses
