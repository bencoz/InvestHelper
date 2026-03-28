import ast
import sys
import os

def check_file(filepath):
    """
    Parses a python file and returns a list of failure dicts.
    Each failure has a line number, description, and remediation context for an agent.
    """
    try:
        with open(filepath, 'r') as f:
            tree = ast.parse(f.read(), filename=filepath)
    except Exception as e:
        return [{"line": 0, "msg": f"Syntax error: {str(e)}", "remediation": "Fix syntax error to allow parsing."}]

    failures = []
    
    for node in ast.walk(tree):
        # 1. Check for print statements (python 3)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'print':
            failures.append({
                "line": node.lineno,
                "msg": f"Found `print` statement.",
                "remediation": "Replace `print()` with structured logging.\n1. `from logging_config import get_logger`\n2. `logger = get_logger(__name__)`\n3. Replace the print call with `logger.info()`, `logger.debug()`, or `logger.error()`."
            })
            
        # 2. Check for bare except Exception
        if isinstance(node, ast.ExceptHandler):
            # If type is empty, it's a bare except:
            is_bare = node.type is None
            # If type is 'Exception', it's except Exception:
            is_exception = isinstance(node.type, ast.Name) and node.type.id == 'Exception'
            
            if is_bare or is_exception:
                failures.append({
                    "line": node.lineno,
                    "msg": "Found unspecific `except Exception:` or bare `except:` block.",
                    "remediation": "Catch specific exceptions or custom exceptions defined in `exceptions.py` (e.g., `from exceptions import DataFetchError`). This prevents swallowing critical bugs. If it is necessary, consider wrapping raising a specific custom Exception."
                })
                
    return failures

def main():
    if len(sys.argv) < 2:
        print("Usage: python agent_linter.py <directory_or_file>")
        sys.exit(1)
        
    target = sys.argv[1]
    files_to_check = []
    if os.path.isfile(target) and target.endswith('.py'):
        files_to_check.append(target)
    elif os.path.isdir(target):
        for root, _, files in os.walk(target):
            # skip venv, caches, etc.
            if any(part in root for part in ['.venv', '.git', '__pycache__', 'test-traces', '.agent/skills', '.agent/scripts', 'tests']):
                continue
            for f in files:
                if f.endswith('.py'):
                    files_to_check.append(os.path.join(root, f))
                    
    total_failures = 0
    print("# Agent Linter Report")
    print("This report is formatted for an AI agent to read and action.")
    
    for filepath in files_to_check:
        results = check_file(filepath)
        if results:
            total_failures += len(results)
            print(f"\n## ❌ Failures in `{filepath}`")
            for r in results:
                print(f"**Line {r['line']}**: {r['msg']}")
                print(f"**Remediation instructions**:\n{r['remediation']}\n")
                
    if total_failures == 0:
        print("\n✅ All files pass structural checks.")
        sys.exit(0)
    else:
        print(f"\nTotal failures found: {total_failures}. Agent, please apply the remediation steps.")
        sys.exit(1)

if __name__ == '__main__':
    main()
