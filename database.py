import aiosqlite

DB_NAME = "gifcraft.db"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        # User settings table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                user_id INTEGER PRIMARY KEY,
                speed TEXT DEFAULT 'Normal',
                quality TEXT DEFAULT 'Standard',
                size TEXT DEFAULT 'Original',
                loop_opt TEXT DEFAULT 'Infinite'
            )
        ''')
        # Generation logs history table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                file_path TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await db.commit()

async def get_settings(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT speed, quality, size, loop_opt FROM settings WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return {"speed": row[0], "quality": row[1], "size": row[2], "loop_opt": row[3]}
            await db.execute("INSERT INTO settings (user_id) VALUES (?)", (user_id,))
            await db.commit()
            return {"speed": "Normal", "quality": "Standard", "size": "Original", "loop_opt": "Infinite"}

async def update_setting(user_id: int, column: str, value: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(f"UPDATE settings SET {column} = ? WHERE user_id = ?", (value, user_id))
        await db.commit()

async def log_gif(user_id: int, file_path: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT INTO history (user_id, file_path) VALUES (?, ?)", (user_id, file_path))
        # Maintain a clean threshold limit of last 10 entries
        await db.execute("DELETE FROM history WHERE user_id = ? AND id NOT IN (SELECT id FROM history WHERE user_id = ? ORDER BY timestamp DESC LIMIT 10)", (user_id, user_id))
        await db.commit()

