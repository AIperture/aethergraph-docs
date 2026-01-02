# debug_mkdocs.py
import sys
import importlib

# The path you are trying to use in markdown
TARGET = "aethergraph.services.memory.facade.core.MemoryFacade"

print(f"--- Debugging: {TARGET} ---")
print(f"Python Executable: {sys.executable}")
print(f"Path: {sys.path}")

try:
    module_name, class_name = TARGET.rsplit(".", 1)
    print(f"1. Attempting to import module: {module_name}")
    mod = importlib.import_module(module_name)
    print("   ✅ Module imported successfully!")
    print(f"   📂 File location: {mod.__file__}")

    print(f"2. Looking for class: {class_name}")
    cls = getattr(mod, class_name)
    print("   ✅ Class found!")
    print(f"   👉 Proper import path: {mod.__name__}.{class_name}")

except ImportError as e:
    print(f"   ❌ IMPORT ERROR: {e}")
    print("   (This means Python cannot find the file or a dependency is missing)")
except AttributeError as e:
    print(f"   ❌ CLASS NOT FOUND: {e}")
    print(f"   (The module '{module_name}' loads, but class '{class_name}' isn't in it)")
    print(f"   Available contents: {dir(mod)}")
except Exception as e:
    print(f"   ❌ RUNTIME CRASH: {e}")
    print("   (Your code has a bug/circular import that prevents loading)")