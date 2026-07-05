# NeatCLI
A simple yet powerful framework for quickly and reliably writing command-line applications in Python.

## Architecture
NeatCLI is organized into three distinct, decoupled toolkits to manage every aspect of a command-line application without external dependencies:

* **`App`**: Handles command routing, option/flag parsing, and grouping.
* **`Prompt`**: Handles user input collection, data validation, and sensitive masking.
* **`Interface`**: Handles visual layouts, ANSI styling, status indicators, and grids.

## Core Applications (`App`)
The `App` class serves as the entry point and router for your CLI tool. Commands are registered using decorators, and parameters are automatically populated from `sys.argv`.

### Basic Usage
```python
import sys
from ncli import App

app = App()

@app.command
def version(opts):
    """Print version"""
    print("1.0.0")

db = app.group("db", help="Database management commands")

@db.command
@app.argument("name", help="Migration name")
@app.help("Create a new migration")
def create(opts, name):
    print(f"Creating migration: {name}")

@db.command
@app.option("force", short="f", default=False, help="Force the reset")
@app.help("Reset the database")
def reset(opts):
    print(f"Resetting db (force={opts.force})")

app.run(sys.argv[1:])
```

### Routing & Options API
* **`@app.command`**: Registers the decorated function as a runnable command. The function's name becomes the subcommand keyword.
* **`@app.option(name, short=None, default=None)`**: Attaches a flag option to the command. Options are bundled and passed as the first argument (`options`) to the target function.
* **`@app.help(text)`**: Attaches a descriptive help string to the command for documentation generation. A docstring does the same thing, but the decorator takes priority over it.

## Interactive Inputs (`Prompt`)
`Prompt` provides utilities for gathering input dynamically mid-execution, enforcing validations, and safely processing secure variables.

### API Reference
* **`Prompt.ask(prompt: str, default: str = None, type: Callable = None) -> Any`**
Prompts the user for inline string input. If a `type` is specified (e.g., `int`), it automatically verifies compliance and prompts again if invalid.
* **`Prompt.confirm(prompt: str, default: bool = False) -> bool`**
Appends a standard binary choice marker (`[y/N]` or `[Y/n]`). Enforces explicit confirmation and returns a boolean value.
* **`Prompt.secret(prompt: str) -> str`**
Masks terminal keystrokes, completely hiding sensitive values (like passwords or tokens) while they are typed.

### Example
```python
from neatcli import Prompt

username = Prompt.ask("Admin username", default="root")
threads = Prompt.ask("Worker threads", default=4, type=int)

if Prompt.confirm("Proceed with initialization?"):
    password = Prompt.secret("Enter encryption key")
```

## Terminal Presentation (`Interface`)
The `Interface` module provides components for formatting layouts, generating text styles, and animating operations safely using standard streaming outputs.

### ANSI Styling
Apply inline constants to control text attributes. Always append `Interface.RESET` to avoid leakage across lines.

```python
from neatcli import Interface

print(f"{Interface.GREEN}Success:{Interface.RESET} Process completed.")
print(f"{Interface.RED}{Interface.BOLD}Error:{Interface.RESET} Build halted.")
```

* **Colors**: `RED`, `GREEN`, `YELLOW`, `BLUE`, `CYAN`, `GRAY`
* **Attributes**: `BOLD`, `RESET`

### Status Indicators
Both `spinner` and `progress_bar` use context managers (`with` blocks) to manage lifecycle states, safely hide the terminal cursor, and handle line clears upon exit.

```python
import time
from neatcli import Interface

# background animation thread
with Interface.spinner("Compiling plane binaries..."):
    time.sleep(2.0)

# block tracking bar
steps = 4
with Interface.progress_bar("Flashing ROM memory", total=steps) as pbar:
    for _ in range(steps):
        time.sleep(0.5)
        pbar.update(1)
```

### Dynamic Grids
`Interface.table` takes header sequences and nested row arrays, calculating matching margin widths automatically.

```python
from neatcli import Interface

headers = ["Register", "Value", "Status"]
rows = [
    ["R0", "0x0000", "Hardwired Zero"],
    ["R1", "0x0A2F", "Active"],
    ["PC", "0x0084", "Program Counter"]
]

Interface.table(headers, rows)
```

## Complete Example Integration
```python
import time
from neatcli import App, Prompt, Interface

app = App()

@app.command
@app.help("Deploy code to target ecosystem.")
def deploy(options):
    print(f"{Interface.BOLD}NEATCLI Deployment Suite{Interface.RESET}\n")
    
    target = Prompt.ask("Target device address", default="127.0.0.1")
    if not Prompt.confirm("Do you want to clear volatile storage before write?"):
        print("Aborted.")
        return

    with Interface.spinner(f"Establishing link to {target}..."):
        time.sleep(1.5)

    with Interface.progress_bar("Uploading sectors", total=100) as pbar:
        for _ in range(10):
            time.sleep(0.1)
            pbar.update(10)

    print(f"\n{Interface.GREEN}Deployment complete.{Interface.RESET}")

if __name__ == "__main__":
    app.run()

```