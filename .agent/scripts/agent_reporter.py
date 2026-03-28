import subprocess
import sys
import os

def run_tests():
    print("Running tests with pytest...")
    # Run pytest and capture output formatted for an agent
    result = subprocess.run(
        ["pytest", "tests/e2e/", "--headed=false", "-v", "--tb=short"], 
        capture_output=True, 
        text=True
    )
    
    agent_summary_path = os.path.join(os.getcwd(), 'agent_summary.md')
    
    with open(agent_summary_path, 'w') as f:
        f.write("# Agent Test Run Summary\n\n")
        f.write("This artifact is designed for LLMs to easily read test failure contexts.\n\n")
        
        if result.returncode == 0:
            f.write("✅ **All tests passed!** No further agent action needed.\n")
        else:
            f.write("❌ **Tests Failed!**\n\n")
            f.write("## Pytest Output\n")
            f.write("```text\n")
            f.write(result.stdout)
            if result.stderr:
                f.write("\n" + result.stderr)
            f.write("\n```\n\n")
            
            f.write("## Playwright Trace Artifacts\n")
            f.write("If this was a UI failure, refer to the DOM traces and videos captured in:\n")
            f.write("- `test-traces/`\n")
            f.write("- `test-videos/`\n\n")
            f.write("**Instructions for Agent**: Please read the stack trace above, locate the failing file, and submit a PR to fix the UI logic.\n")
    
    if result.returncode == 0:
        print("✅ Tests passed. Generated agent_summary.md")
        sys.exit(0)
    else:
        print(f"❌ Tests failed. See 'agent_summary.md' for details formatted for AI Agents.")
        sys.exit(1)

if __name__ == "__main__":
    run_tests()
