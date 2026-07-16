# Migrating BookMyStay from SQLite to MySQL

This was tested end-to-end in a sandboxed MySQL 8.0 instance before being
handed to you: schema created cleanly, all 200 records loaded with zero
mismatches, search/login/booking-creation all verified working against the
MySQL-backed database. What's below is exactly what was run, adapted for
your real MySQL Workbench setup.

## What's already done for you (in the code)

- `requirements.txt` — added `PyMySQL` (pure-Python driver, no C compiler
  needed — avoids the classic "Microsoft Visual C++ 14.0 required" error
  that `mysqlclient` often hits on Windows)
- `bookmystay/__init__.py` — registers PyMySQL so Django's MySQL backend
  works with it transparently
- `bookmystay/settings.py` — `DATABASES` now points at MySQL, reading
  connection details from environment variables (nothing hardcoded)
- `datadump.json` — a full export of your real data (users, properties,
  bookings, payments, reviews, everything) in Django's fixture format,
  ready to load straight into your empty `BookMyStay` database

Your original `db.sqlite3` is still included, untouched, as a fallback —
if anything goes wrong, you can always point `DATABASES` back at it.

## Steps to run on your machine

**1. Install the new dependency**
```
pip install -r requirements.txt
```

**2. Create your `.env`** (copy `.env.example` if you don't have one yet)
and fill in your real MySQL Workbench credentials:
```
DB_NAME=BookMyStay
DB_USER=your_mysql_username
DB_PASSWORD=your_mysql_password
DB_HOST=localhost
DB_PORT=3306
```
Don't paste your password into chat with me — just put it directly in
this local file.

**3. Build the schema in MySQL**
```
python manage.py migrate
```
This creates every table in your `BookMyStay` database, structured exactly
like your current SQLite schema.

**4. Load your real data**
```
python manage.py loaddata datadump.json
```
You should see: `Installed 200 object(s) from 1 fixture(s)`

**5. Verify it worked**
```
python manage.py shell -c "
from properties.models import Property
from users.models import User
print('Properties:', Property.objects.count(), '(expect 5)')
print('Users:', User.objects.count(), '(expect 13)')
"
```

**6. Start the app as normal** — `python manage.py runserver` — and click
around. Login, search, and booking creation were all specifically tested
against MySQL and confirmed working identically to SQLite.

## If something goes wrong

- **"Access denied for user"** — double-check `DB_USER`/`DB_PASSWORD` in
  `.env` match what Workbench has, and that this user has privileges on
  the `BookMyStay` database (`GRANT ALL PRIVILEGES ON BookMyStay.* TO
  'youruser'@'localhost';` in Workbench if unsure).
- **"Unknown database 'BookMyStay'"** — the database itself needs to
  exist before `migrate` runs; you mentioned it's already created, so
  this shouldn't hit, but worth confirming the name matches exactly
  (MySQL database names are case-sensitive on some setups).
- **Emoji/Swahili character issues** — shouldn't happen; the database
  was created with `utf8mb4` collation specifically to handle full
  Unicode. If you created your `BookMyStay` database with a different
  charset in Workbench, you may want to recreate it with:
  ```sql
  ALTER DATABASE BookMyStay CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
  ```
- **Want to go back to SQLite** — the untouched `db.sqlite3` file is
  still in the project. Temporarily restore the old `DATABASES` block
  in `settings.py` (SQLite engine, no env vars needed) and everything
  works exactly as before.

## Cleanup once you've confirmed everything works

`datadump.json` and `db.sqlite3` aren't needed by the running app anymore
once MySQL is confirmed working — safe to delete both, or keep them
around as a backup/rollback point. Your call.
