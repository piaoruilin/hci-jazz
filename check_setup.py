import subprocess
import sys
import importlib.metadata

def check_and_install():
    required = {'pygame', 'pandas', 'scipy', 'statsmodels', 'matplotlib', 'seaborn'}
    
    # Get set of installed packages
    installed = {pkg.metadata['Name'].lower() for pkg in importlib.metadata.distributions()}
    missing = {req for req in required if req.lower() not in installed}

    if missing:
        print(f"Missing: {missing}")
        python = sys.executable
        # Using --no-cache-dir can help if the install keeps hanging
        subprocess.check_call([python, '-m', 'pip', 'install', '--prefer-binary', *missing])
        print("Done!")
    else:
        print("All libraries are already installed in this venv!")

if __name__ == "__main__":
    check_and_install()