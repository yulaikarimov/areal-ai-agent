# check_import.py
import sys
import site

print("--- Python Executable ---")
print(sys.executable)
print("-" * 25)

print("--- sys.path ---")
for path_item in sys.path:
    print(path_item)
print("-" * 25)

print("--- Site Packages ---")
print(site.getsitepackages())
print("-" * 25)


print("--- Attempting Imports ---")
try:
    import langgraph_checkpoint_sqlite
    print("SUCCESS: 'import langgraph_checkpoint_sqlite'")

    try:
        from langgraph_checkpoint_sqlite import SqliteSaver
        print("SUCCESS: 'from langgraph_checkpoint_sqlite import SqliteSaver'")
    except ImportError as e:
        print(f"FAILED: 'from langgraph_checkpoint_sqlite import SqliteSaver': {e}")
    except Exception as e:
         print(f"UNEXPECTED ERROR during second import: {type(e).__name__}: {e}")

except ImportError as e:
    print(f"FAILED: 'import langgraph_checkpoint_sqlite': {e}")
except Exception as e:
    print(f"UNEXPECTED ERROR during first import: {type(e).__name__}: {e}")

print("-" * 25)
