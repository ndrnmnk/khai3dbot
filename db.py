import sqlite3
import shutil

conn = sqlite3.connect('targets.db')
cur = conn.cursor()


async def id_init(user_id, user_nickname):
    cur.execute("CREATE TABLE IF NOT EXISTS targets(id int, nickname text, phone text, creds text)")
    cur.execute("INSERT OR REPLACE INTO targets VALUES(?,?,?,?)", (user_id, "none", "none", "none"))
    if user_nickname is not None:
        cur.execute("UPDATE targets SET nickname=? WHERE id=?", (user_nickname, user_id))
    conn.commit()


async def phone_init(user_id, num):
    cur.execute("UPDATE targets SET phone=? WHERE id=?", (num, user_id))
    conn.commit()


async def save_full_name(user_id, creds):
    cur.execute("UPDATE targets SET creds=? WHERE id=?", (creds, user_id))
    conn.commit()


async def unregister(user_id):
    await rm_dir(user_id, 1)
    cur.execute("DELETE FROM targets WHERE id=?", (user_id, ))
    conn.commit()


async def rm_dir(user_id, rm_completely):
    try:
        shutil.rmtree(f'videos/{user_id}')
        if rm_completely:
            shutil.rmtree(f'splats/{user_id}.splat')
            shutil.rmtree(f'htmls/{user_id}.html')
    except FileNotFoundError:
        pass