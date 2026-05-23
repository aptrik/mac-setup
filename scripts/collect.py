#!/usr/bin/env python3

import os
import plistlib
import urllib.parse
import getpass

ARRANGEMENT_MAP = {
    1: "name",
    2: "dateadded",
    3: "datemodified",
    4: "datecreated",
    5: "kind",
}

DISPLAYAS_MAP = {
    0: "stack",
    1: "folder",
}

SHOWAS_MAP = {
    0: "auto",
    1: "fan",
    2: "grid",
    3: "list",
}

current_user = getpass.getuser()
user_home = f"/Users/{current_user}"


def clean_path(url):
    if not url:
        return ""
    if url.startswith("file://"):
        url = url[7:]
    path = urllib.parse.unquote(url)
    if path.startswith(user_home):
        path = "~" + path[len(user_home) :]
    # Remove trailing slash for consistency (unless it's just '/')
    if path.endswith("/") and len(path) > 1:
        path = path[:-1]
    return path


def to_yaml(data, indent=0):
    lines = []
    spacer = " " * indent
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, (dict, list)):
                lines.append(f"{spacer}{k}:")
                lines.append(to_yaml(v, indent + 2))
            elif isinstance(v, bool):
                lines.append(f"{spacer}{k}: {str(v).lower()}")
            elif isinstance(v, (int, float)):
                lines.append(f"{spacer}{k}: {v}")
            elif v is None:
                lines.append(f"{spacer}{k}: null")
            else:
                val = str(v).replace('"', '\\"')
                lines.append(f'{spacer}{k}: "{val}"')
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, (dict, list)):
                nested_yaml = to_yaml(item, indent + 2).lstrip()
                lines.append(f"{spacer}- {nested_yaml}")
            else:
                if isinstance(item, bool):
                    lines.append(f"{spacer}- {str(item).lower()}")
                elif isinstance(item, (int, float)):
                    lines.append(f"{spacer}- {item}")
                elif item is None:
                    lines.append(f"{spacer}- null")
                else:
                    val = str(item).replace('"', '\\"')
                    lines.append(f'{spacer}- "{val}"')
    return "\n".join(lines)


def load_plist(path):
    expanded_path = os.path.expanduser(path)
    if not os.path.exists(expanded_path):
        return {}
    try:
        with open(expanded_path, "rb") as f:
            return plistlib.load(f)
    except Exception as e:
        print(f"Warning: Failed to load {path}: {e}")
        return {}


def collect():
    dock_plist = load_plist("~/Library/Preferences/com.apple.dock.plist")
    finder_plist = load_plist("~/Library/Preferences/com.apple.finder.plist")
    global_plist = load_plist("~/Library/Preferences/.GlobalPreferences.plist")

    settings = {
        "macos_settings": {
            "dock": {
                "settings": {
                    "autohide": dock_plist.get("autohide", False),
                    "magnification": dock_plist.get("magnification", False),
                    "tilesize": dock_plist.get("tilesize", 48),
                    "largesize": dock_plist.get("largesize", 128),
                    "minimize_to_application": dock_plist.get(
                        "minimize-to-application", False
                    ),
                    "show_recents": dock_plist.get("show-recents", False),
                },
                "apps": [],
                "others": [],
            },
            "finder": {
                "ShowPathbar": finder_plist.get("ShowPathbar", False),
                "ShowSidebar": finder_plist.get("ShowSidebar", True),
                "ShowStatusBar": finder_plist.get("ShowStatusBar", False),
                "FXEnableExtensionChangeWarning": finder_plist.get(
                    "FXEnableExtensionChangeWarning", True
                ),
                "AppleShowAllExtensions": global_plist.get(
                    "AppleShowAllExtensions", False
                ),
            },
            "keyboard": {
                "AppleKeyboardUIMode": global_plist.get("AppleKeyboardUIMode", 0),
                "InitialKeyRepeat": global_plist.get("InitialKeyRepeat", 15),
                "KeyRepeat": global_plist.get("KeyRepeat", 2),
            },
        }
    }

    # Extract Dock Apps
    for item in dock_plist.get("persistent-apps", []):
        tile_data = item.get("tile-data", {})
        label = tile_data.get("file-label")
        file_data = tile_data.get("file-data", {})
        url = file_data.get("_CFURLString")
        if url:
            path = clean_path(url)
            settings["macos_settings"]["dock"]["apps"].append(
                {
                    "name": label,
                    "path": path,
                }
            )

    # Extract Dock Folders/Files (Others)
    for item in dock_plist.get("persistent-others", []):
        tile_data = item.get("tile-data", {})
        label = tile_data.get("file-label")
        file_data = tile_data.get("file-data", {})
        url = file_data.get("_CFURLString")
        if url:
            path = clean_path(url)
            arrangement = tile_data.get("arrangement", 1)
            displayas = tile_data.get("displayas", 0)
            showas = tile_data.get("showas", 0)

            settings["macos_settings"]["dock"]["others"].append(
                {
                    "name": label,
                    "path": path,
                    "sort": ARRANGEMENT_MAP.get(arrangement, "name"),
                    "display": DISPLAYAS_MAP.get(displayas, "stack"),
                    "view": SHOWAS_MAP.get(showas, "auto"),
                }
            )

    # Output to settings.yml
    output_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "settings.yml"
    )
    yaml_content = "---\n" + to_yaml(settings) + "\n"
    with open(output_path, "w") as f:
        f.write(yaml_content)

    print(f"Successfully collected settings to {output_path}")


if __name__ == "__main__":
    collect()
