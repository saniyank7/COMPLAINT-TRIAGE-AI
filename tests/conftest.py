import json
import os
import tempfile

_tmp = tempfile.mkdtemp()
_cat = os.path.join(_tmp, "categories.json")
with open(_cat, "w") as f:
    json.dump(["Credit card", "Mortgage", "Debt collection"], f)
os.environ["CATEGORIES_PATH"] = _cat
os.environ["DB_PATH"] = os.path.join(_tmp, "test.db")
