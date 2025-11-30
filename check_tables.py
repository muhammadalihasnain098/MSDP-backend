import sqlite3
conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in cursor.fetchall()]
print(f'Total tables: {len(tables)}')
for t in tables[:20]:
    print(t)
if 'users_user' in tables:
    print('\n✓ users_user table EXISTS')
else:
    print('\n✗ users_user table MISSING - Need to run migrations!')
