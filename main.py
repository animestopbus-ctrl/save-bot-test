# Copyright (c) 2025 LastPerson07 : https://github.com/LastPerson07.  
# Licensed under the GNU General Public License v3.0.  
# See LICENSE file in the repository root for full license text.

import asyncio
from LastPerson07.shared_client import start_client
import importlib
import os
import sys

# Get absolute path to plugins folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PLUGIN_DIR = os.path.join(BASE_DIR, 'plugins')

async def load_and_run_plugins():
    await start_client()
    plugins = [f[:-3] for f in os.listdir(PLUGIN_DIR) if f.endswith(".py") and f != "__init__.py"]

    for plugin in plugins:
        module = importlib.import_module(f"LastPerson07.plugins.{plugin}")
        if hasattr(module, f"run_{plugin}_plugin"):
            print(f"Running {plugin} plugin...")
            await getattr(module, f"run_{plugin}_plugin")()  

async def main():
    await load_and_run_plugins()
    while True:
        await asyncio.sleep(1)  

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    print("Starting clients ...")
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("Shutting down...")
    except Exception as e:
        print(e)
        sys.exit(1)
    finally:
        try:
            loop.close()
        except Exception:
            pass
