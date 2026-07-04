import sys
from dataclasses import dataclass
from typing import Callable, List, Optional, Any, Dict, Union

# neat app framework
# by las-r

@dataclass
class OptionAttr:
    name: str
    short: Optional[str] = None
    default: Any = None
    help: str = ""

@dataclass
class ArgumentAttr:
    name: str
    help: str = ""

# decorators
def option(name: str, short: Optional[str] = None, default: Any = None, help: str = ""):
    def decorator(func: Callable):
        if not hasattr(func, "_neat_options"):
            func._neat_options = []
        func._neat_options.append(OptionAttr(name, short, default, help))
        return func
    return decorator

def argument(name: str, help: str = ""):
    def decorator(func: Callable):
        if not hasattr(func, "_neat_arguments"):
            func._neat_arguments = []
        func._neat_arguments.insert(0, ArgumentAttr(name, help))
        return func
    return decorator

def help(text: str):
    def decorator(func: Callable):
        func._neat_help = text
        return func
    return decorator

# options context
class OptionsContext:
    def __init__(self, data: dict):
        self.__dict__.update(data)

# core classes
class Command:
    def __init__(self, func: Callable):
        self.func = func
        self.name = func.__name__
        self.help = getattr(func, "_neat_help", func.__doc__ or "")
        self.options_metadata: List[OptionAttr] = getattr(func, "_neat_options", [])
        self.arguments_metadata: List[ArgumentAttr] = getattr(func, "_neat_arguments", [])

    def usage_line(self, prefix: str = "") -> str:
        parts = [f"{prefix}{self.name}".strip()]
        for arg in self.arguments_metadata:
            parts.append(f"<{arg.name}>")
        if self.options_metadata:
            parts.append("[options]")
        return " ".join(parts)

    def print_detailed_help(self, prefix: str = ""):
        print(f"Usage: python -m app {self.usage_line(prefix)}")
        if self.help:
            print(f"\n{self.help}")
        if self.arguments_metadata:
            print("\nArguments:")
            for arg in self.arguments_metadata:
                print(f"  {arg.name:<12} {arg.help}")
        if self.options_metadata:
            print("\nOptions:")
            for opt in self.options_metadata:
                flags = f"--{opt.name}"
                if opt.short:
                    flags += f", -{opt.short}"
                print(f"  {flags:<16} {opt.help}")


class Group:
    """A named collection of commands and/or nested groups."""
    def __init__(self, name: str, help: str = ""):
        self.name = name
        self.help = help
        self.commands: Dict[str, Command] = {}
        self.groups: Dict[str, "Group"] = {}

    def command(self, func: Callable):
        cmd = Command(func)
        self.commands[cmd.name] = cmd
        return func

    def group(self, name: str, help: str = ""):
        grp = Group(name, help)
        self.groups[name] = grp
        return grp

    def usage_line(self, prefix: str = "") -> str:
        return f"{prefix}{self.name} <subcommand>".strip()

    def print_group_help(self, prefix: str = ""):
        full_prefix = f"{prefix}{self.name} ".strip() + " " if prefix else f"{self.name} "
        print(f"Usage: python -m app {full_prefix.strip()}<subcommand> [options]")
        if self.help:
            print(f"\n{self.help}")
        if self.groups:
            print("\nSubgroups:")
            for name, grp in self.groups.items():
                print(f"  {name:<28} {grp.help}")
        if self.commands:
            print("\nCommands:")
            for name, cmd in self.commands.items():
                print(f"  {cmd.usage_line():<28} {cmd.help}")
        print(f"\nRun 'python -m app {full_prefix.strip()}<subcommand> --help' for details.")


class App:
    def __init__(self):
        self.commands: Dict[str, Command] = {}
        self.groups: Dict[str, Group] = {}
        self.option = option
        self.argument = argument
        self.help = help

    def command(self, func: Callable):
        cmd = Command(func)
        self.commands[cmd.name] = cmd
        return func

    def group(self, name: str, help: str = "") -> Group:
        grp = Group(name, help)
        self.groups[name] = grp
        return grp

    def _print_root_help(self):
        print("Usage: python -m app <command> [options]")
        if self.groups:
            print("\nCommand groups:")
            for name, grp in self.groups.items():
                print(f"  {name:<28} {grp.help}")
        if self.commands:
            print("\nAvailable commands:")
            for name, cmd in self.commands.items():
                print(f"  {cmd.usage_line():<28} {cmd.help}")
        print("\nRun 'python -m app <command> --help' for details on a specific command.")

    def _resolve(self, args: List[str]):
        """
        Walk args through nested groups to find the terminal Command.
        Returns (command_or_group, remaining_args, prefix) or (None, args, prefix) if unresolved.
        """
        container: Union[App, Group] = self
        prefix_parts: List[str] = []
        idx = 0
        while idx < len(args):
            token = args[idx]
            if token in ("--help", "-h"):
                break
            if token in container.groups:
                container = container.groups[token]
                prefix_parts.append(token)
                idx += 1
                continue
            if token in container.commands:
                return container.commands[token], args[idx + 1:], " ".join(prefix_parts)
            break
        return container, args[idx:], " ".join(prefix_parts)

    def run(self, args: Optional[List[str]] = None):
        if args is None:
            args = sys.argv[1:]

        # general help
        if not args or args[0] in ("--help", "-h"):
            self._print_root_help()
            return

        resolved, rest, prefix = self._resolve(args)

        # resolved to a Group (not a terminal command)
        if isinstance(resolved, Group):
            if "--help" in rest or "-h" in rest or not rest:
                resolved.print_group_help(prefix.rsplit(resolved.name, 1)[0] if prefix != resolved.name else "")
                return
            print(f"Unknown subcommand: {rest[0]}")
            return

        # resolved to App itself (nothing matched at top level)
        if isinstance(resolved, App):
            print(f"Unknown command: {args[0]}")
            return

        # resolved to a Command
        cmd: Command = resolved
        cmd_prefix = f"{prefix} " if prefix else ""

        if "--help" in rest or "-h" in rest:
            cmd.print_detailed_help(cmd_prefix)
            return

        positional_args = []
        parsed_options = {opt.name: opt.default for opt in cmd.options_metadata}

        iterator = iter(rest)
        for arg in iterator:
            if arg.startswith("-"):
                clean_arg = arg.lstrip("-")
                matched_opt = next(
                    (o for o in cmd.options_metadata if o.short == clean_arg or o.name == clean_arg),
                    None
                )
                if matched_opt:
                    try:
                        val = next(iterator)
                        if isinstance(matched_opt.default, int):
                            val = int(val)
                        parsed_options[matched_opt.name] = val
                    except StopIteration:
                        print(f"Missing value for option {arg}")
                        return
            else:
                positional_args.append(arg)

        options_obj = OptionsContext(parsed_options)
        cmd.func(options_obj, *positional_args)