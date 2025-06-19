# src/utils/config_loader.py
import os
from typing import Any, Dict, Optional

import tomllib  # For Python 3.11+


def deep_merge(base: Dict, override: Dict) -> Dict:
    """
    Recursively merges two dictionaries.
    Override values take precedence over base values.
    """
    result = base.copy()
    for key, value in override.items():
        if isinstance(value, dict) and key in result and isinstance(result[key], dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config(task_config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Loads configuration by merging a global config with an optional task-specific config.

    1. Loads a 'global_config.toml' from the project root (if it exists).
    2. If a 'task_config_path' is provided, it loads that file.
    3. The task-specific config is merged on top of the global config, overriding any
       duplicate settings.

    Returns:
        A dictionary containing the final merged configuration.
    """
    # Assume the script is run from the project root
    project_root = os.getcwd()
    global_config_path = os.path.join(project_root, "global_config.toml")

    # Start with the global config as the base
    final_config = {}
    if os.path.exists(global_config_path):
        with open(global_config_path, "rb") as f:
            final_config = tomllib.load(f)

    # If a task-specific config is provided, load and merge it
    if task_config_path:
        if not os.path.exists(task_config_path):
            raise FileNotFoundError(
                f"Specified config file not found: {task_config_path}"
            )
        with open(task_config_path, "rb") as f:
            task_config = tomllib.load(f)

        # Merge task config over the global config
        final_config = deep_merge(final_config, task_config)

    return final_config
