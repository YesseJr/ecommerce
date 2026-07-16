import pymysql

# Django's mysql backend expects the MySQLdb (mysqlclient) API. PyMySQL is a
# pure-Python drop-in that implements that same API — this shim registers
# it so `django.db.backends.mysql` works without needing mysqlclient's C
# extension, which is often painful to install on Windows without build
# tools already set up.
pymysql.install_as_MySQLdb()
pymysql.version_info = (2, 2, 8, 'final', 0)  # satisfies Django's version check
