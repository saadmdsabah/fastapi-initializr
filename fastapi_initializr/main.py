import os
import subprocess
import platform
import sys
import shutil
import questionary
from colorama import Fore, init
import requests
import pkg_resources
import argparse
from yaspin import yaspin


def main():
    init(autoreset=True)

    # =====================================================
    # === Update Checker ==================================
    # =====================================================
    def check_for_updates(package_name="fastapi-initializr"):
        try:
            current_version = pkg_resources.get_distribution(package_name).version
            response = requests.get(f"https://pypi.org/pypi/{package_name}/json", timeout=3)
            latest_version = response.json()["info"]["version"]

            if latest_version != current_version:
                print(Fore.YELLOW + f"\n⚡ Update available: {package_name} {current_version} → {latest_version}")
                print(Fore.YELLOW + "   Run: pip install -U fastapi-initializr\n")
        except Exception:
            pass  


    # =====================================================
    # === Utility Functions ===============================
    # =====================================================
    def safe_run(cmd, cwd=None, check=True, silent=False):
        """Run a command with spinner and handle errors."""
        try:
            if(not silent):
                with yaspin(text=f"Running: {cmd}", color="cyan"):
                    subprocess.run(cmd, shell=True, check=check, cwd=cwd)
            else:
                subprocess.run(cmd, shell=True, check=check, cwd=cwd)
        except subprocess.CalledProcessError as e:
            print(Fore.RED + f"❌ Command failed: {cmd}")
            print(Fore.RED + f"Error: {e}")
            sys.exit(1)

    def create_file(path, content=""):
        """Create file safely."""
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            print(Fore.RED + f"⚠️ Failed to create file {path}: {e}")

    def create_folder_structure(project_name):
        """Create FastAPI folder and file structure."""
        base = project_name
        src = os.path.join(base, "src")
        tests = os.path.join(base, "tests")

        folders = [
            base,
            src,
            os.path.join(src, "routes"),
            os.path.join(src, "services"),
            os.path.join(src, "auth"),
            tests,
            os.path.join(tests, "routes"),
            os.path.join(tests, "services"),
            os.path.join(tests, "auth"),
        ]

        files = [
            os.path.join(src, "dependencies.py"),
            os.path.join(src, "__init__.py"),
            os.path.join(src, "database.py"),
            os.path.join(src, "config.py"),
            os.path.join(src, "models.py"),
            os.path.join(src, "schemas.py"),
            os.path.join(base, ".env"),
            os.path.join(base, ".gitignore"),
            os.path.join(base, "README.md"),
            os.path.join(base, "requirements.txt"),
        ]

        for folder in folders:
            os.makedirs(folder, exist_ok=True)

        for file in files:
            if file.endswith(".gitignore"):
                create_file(file, ".venv/\n.env\n__pycache__/\n")
            elif file.endswith("requirements.txt"):
                create_file(file, "fastapi\nuvicorn\n")
            else:
                create_file(file)

    def get_activate_command(terminal_type):
        """Return correct virtual environment activation command."""
        system = platform.system().lower()
        if "windows" in system:
            if terminal_type and ("linux" in terminal_type.lower() or "bash" in terminal_type.lower()):
                return "source .venv/Scripts/activate"
            else:
                return ".venv\\Scripts\\activate"
        else:
            return "source .venv/bin/activate"
        
    def startsh_or_startbat(terminal_type):
        if terminal_type and ("linux" in terminal_type.lower() or "bash" in terminal_type.lower()):
            return "./start.sh"
        else:
            return ".\\start.bat"

    def fastapi_main_template():
        return (
            "from fastapi import FastAPI\n\n"
            "app = FastAPI()\n\n"
            "@app.get('/')\n"
            "async def root():\n"
            "    return {'message': 'Hello World'}\n"
        )

    def create_run_scripts():
        """Create automatic uvicorn run scripts for Windows/Linux."""
        start_sh = (
            "#!/bin/bash\n"
            "uvicorn src.main:app --reload\n"
        )
        start_bat = (
            "@echo off\n"
            "uvicorn src.main:app --reload\n"
        )
        create_file("start.sh", start_sh)
        create_file("start.bat", start_bat)
        os.chmod("start.sh", 0o755)

    # =====================================================
    # === Setup Functions ================================
    # =====================================================
    def setup_with_pip(project_name, use_git, terminal_type):
        os.chdir(project_name)
        safe_run(f"{sys.executable} -m venv .venv")

        if use_git:
            safe_run("git init")

        create_file(os.path.join("src", "main.py"), fastapi_main_template())
        create_run_scripts()

        print(Fore.GREEN + "\n👉 Next steps:")
        print(Fore.GREEN + f"   cd {project_name}")
        print(Fore.GREEN + f"   {get_activate_command(terminal_type)}")
        print(Fore.GREEN + "   pip install -r requirements.txt")
        print(Fore.GREEN + f"   {startsh_or_startbat(terminal_type)}")

        check_for_updates()

    def setup_with_poetry(project_name, init_git, terminal_type):
        os.chdir(project_name)
        safe_run(f"{sys.executable} -m venv .venv")

        system = platform.system().lower()
        python_cmd = ".venv\\Scripts\\python" if "windows" in system else ".venv/bin/python"
        poetry_cmd = ".venv\\Scripts\\poetry" if "windows" in system else ".venv/bin/poetry"

        safe_run(f"{python_cmd} -m pip install poetry", silent=True)
        safe_run(f"{poetry_cmd} init -n", silent=True)

        if init_git:
            safe_run("git init")

        create_file(os.path.join("src", "main.py"), fastapi_main_template())
        create_run_scripts()

        print(Fore.GREEN + "\n👉 Next steps:")
        print(Fore.GREEN + f"   cd {project_name}")
        print(Fore.GREEN + f"   {get_activate_command(terminal_type)}")
        print(Fore.GREEN + "   poetry add $(cat requirements.txt)")
        print(Fore.GREEN + f"   {startsh_or_startbat(terminal_type)}")

        check_for_updates()

    def setup_with_uv(project_name, init_git, terminal_type):
        os.chdir(project_name)
        safe_run(f"{sys.executable} -m venv .venv")

        system = platform.system().lower()
        python_cmd = ".venv\\Scripts\\python" if "windows" in system else ".venv/bin/python"
        uv_cmd = ".venv\\Scripts\\uv" if "windows" in system else ".venv/bin/uv"

        safe_run(f"{python_cmd} -m pip install uv", silent=True)
        safe_run(f"{uv_cmd} init", silent=True)

        if not init_git:
            git_dir = os.path.join(os.getcwd(), ".git")
            if os.path.exists(git_dir):
                shutil.rmtree(git_dir)
            
        create_file(os.path.join("src", "main.py"), fastapi_main_template())
        create_run_scripts()

        print(Fore.GREEN + "\n👉 Next steps:")
        print(Fore.GREEN + f"   cd {project_name}")
        print(Fore.GREEN + f"   {get_activate_command(terminal_type)}")
        print(Fore.GREEN + "   uv add -r requirements.txt")
        print(Fore.GREEN + f"   {startsh_or_startbat(terminal_type)}")

        check_for_updates()

    def is_linux_based():
        system = platform.system().lower()
        release = platform.release().lower()
        msystem = os.environ.get("MSYSTEM", "").lower()

        if (
            system == "linux"
            or "microsoft" in release  # WSL
            or "mingw" in msystem      # Git Bash
            or "msys" in msystem       # MSYS2
            or "cygwin" in os.environ.get("TERM", "").lower()  # Cygwin
        ):
            return "Linux"
        return "Windows"

    # =====================================================
    # === Argparse + Questionary ==========================
    # =====================================================
    parser = argparse.ArgumentParser(description="FastAPI Project Initializer")
    parser.add_argument("--name", help="Project name")
    parser.add_argument("--pkg", choices=["pip", "poetry", "uv"], help="Package manager")
    parser.add_argument("--git", action="store_true", help="Initialize Git")
    parser.add_argument("--no-git", action="store_true", help="Skip Git init")
    args = parser.parse_args()

    # --- Interactive fallback ---
    project_name = args.name or questionary.text("Enter your FastAPI project name:").ask().strip()
    if not project_name:
        print(Fore.RED + "Error: Project name cannot be empty.")
        sys.exit(1)

    package_manager = args.pkg or questionary.select(
        "Which package manager do you want to use?",
        choices=["pip", "poetry", "uv"]
    ).ask()

    git_choice = True if args.git else False
    if not args.git and not args.no_git:
        git_choice = questionary.confirm("Initialize a Git repository?").ask()

    # Automatically detect terminal type (no manual input)
    terminal_type = is_linux_based()

    # =====================================================
    # === Execute Setup ==================================
    # =====================================================
    create_folder_structure(project_name)
    if package_manager == "pip":
        setup_with_pip(project_name, git_choice, terminal_type)
    elif package_manager == "poetry":
        setup_with_poetry(project_name, git_choice, terminal_type)
    elif package_manager == "uv":
        setup_with_uv(project_name, git_choice, terminal_type)
    else:
        print(Fore.RED + "Error: Invalid package manager selected.")
        sys.exit(1)


if __name__ == "__main__":
    main()