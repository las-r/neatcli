import sys
from dataclasses import dataclass
from typing import Callable, List, Optional, Any

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

    def usage_line(self) -> str:
        parts = [self.name]
        for arg in self.arguments_metadata:
            parts.append(f"<{arg.name}>")
        if self.options_metadata:
            parts.append("[options]")
        return " ".join(parts)

    def print_detailed_help(self):
        print(f"Usage: python -m app {self.usage_line()}")
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

class App:
    def __init__(self):
        self.commands = {}
        self.option = option
        self.argument = argument
        self.help = help

    def command(self, func: Callable):
        cmd = Command(func)
        self.commands[cmd.name] = cmd
        return func

    def run(self, args: Optional[List[str]] = None):
        if args is None:
            args = sys.argv[1:]

        # general help
        if not args or args[0] in ("--help", "-h"):
            print(f"Usage: python -m app <command> [options]")
            print("\nAvailable commands:")
            for name, cmd in self.commands.items():
                print(f"  {cmd.usage_line():<28} {cmd.help}")
            print("\nRun 'python -m app <command> --help' for details on a specific command.")
            return

        # parse command
        cmd_name = args[0]
        if cmd_name not in self.commands:
            print(f"Unknown command: {cmd_name}")
            return
        cmd = self.commands[cmd_name]

        # per-command help
        if "--help" in args[1:] or "-h" in args[1:]:
            cmd.print_detailed_help()
            return

        positional_args = []
        parsed_options = {opt.name: opt.default for opt in cmd.options_metadata}

        # parse arguments
        iterator = iter(args[1:])
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

        # execute command callback
        options_obj = OptionsContext(parsed_options)
        cmd.func(options_obj, *positional_args)