PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "users"
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                         login TEXT NOT NULL UNIQUE,
                         wins INTEGER DEFAULT 0,
                         losses INTEGER DEFAULT 0);
COMMIT;
