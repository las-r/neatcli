import sys
import getpass
from typing import Optional, Any, Callable

# neatcli prompt engine
# by las-r

class Prompt:
    # normal prompt
    @staticmethod
    def ask(prompt: str, default: Optional[str] = None, type: Optional[Callable] = None) -> Any:
        msg = f"{prompt} [{default}]: " if default is not None else f"{prompt}: "
        while True:
            try:
                val = input(msg).strip()
                if not val:
                    if default is not None:
                        return default
                    print("Error: Input cannot be empty.")
                    continue
                if type:
                    try:
                        return type(val)
                    except ValueError:
                        print(f"Error: Invalid value for type {type.__name__}.")
                        continue
                return val
            except (KeyboardInterrupt, EOFError):
                print()
                sys.exit(1)

    # boolean prompt
    @staticmethod
    def confirm(prompt: str, default: bool = False) -> bool:
        suffix = " [Y/n]" if default else " [y/N]"
        msg = f"{prompt}{suffix}: "
        while True:
            try:
                val = input(msg).strip().lower()
                if not val:
                    return default
                if val in ["y", "yes"]:
                    return True
                if val in ["n", "no"]:
                    return False
                print("Error: Please enter yes or no.")
            except (KeyboardInterrupt, EOFError):
                print()
                sys.exit(1)

    # secret prompt
    @staticmethod
    def secret(prompt: str, char: Optional[str] = None) -> str:
        try:
            return getpass.getpass(f"{prompt}: ", echo_char=char)
        except (KeyboardInterrupt, EOFError):
            print()
            sys.exit(1)