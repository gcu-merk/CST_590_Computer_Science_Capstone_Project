"""Run OPS243 service unit tests without pytest present."""

import importlib.util
import sys
import traceback
from pathlib import Path

# Ensure repo root is on path so imports like `edge_processing...` resolve
ROOT = str(Path(__file__).resolve().parents[1])
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

spec = importlib.util.spec_from_file_location('tests_module', 'edge_processing/test_ops243_service.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

fail = False
for name in dir(mod):
    if name.startswith('test_'):
        func = getattr(mod, name)
        try:
            func()
            print(f"{name}: OK")
        except AssertionError as e:
            print(f"{name}: FAIL - {e}")
            fail = True
        except Exception:
            print(f"{name}: ERROR")
            traceback.print_exc()
            fail = True

sys.exit(1 if fail else 0)
