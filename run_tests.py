import importlib
import inspect
import sys
import pathlib

tests_dir = pathlib.Path(__file__).parent / 'tests'
failed = []

for path in sorted(tests_dir.glob('test_*.py')):
    mod_name = f"tests.{path.stem}"
    mod = importlib.import_module(mod_name)
    for name, func in inspect.getmembers(mod, inspect.isfunction):
        if name.startswith('test_'):
            try:
                print('RUNNING', f"{mod_name}.{name}")
                func()
                print('  OK')
            except Exception as e:
                print('  FAIL:', e)
                failed.append((f"{mod_name}.{name}", e))

if failed:
    print('\nFAILED %d test(s)' % len(failed))
    for name, e in failed:
        print(name, e)
    sys.exit(1)
else:
    print('\nALL TESTS PASSED')
    sys.exit(0)
