#!/usr/bin/env python3

import os
import sys
import subprocess


def parse_settings_yml(path):
    apps = []
    others = []
    dock_settings = {}
    finder_settings = {}
    keyboard_settings = {}

    current_section = None
    current_item = {}

    with open(path, "r") as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or stripped == "---":
                continue

            # Detect section
            if line.startswith("  dock:"):
                current_section = "dock"
            elif line.startswith("  finder:"):
                current_section = "finder"
            elif line.startswith("  keyboard:"):
                current_section = "keyboard"
            elif line.startswith("    apps:"):
                current_section = "dock_apps"
                continue
            elif line.startswith("    others:"):
                current_section = "dock_others"
                continue
            elif line.startswith("    settings:"):
                current_section = "dock_settings"
                continue

            # Parse values
            if current_section == "dock_settings":
                parts = stripped.split(":", 1)
                if len(parts) == 2:
                    k, v = parts[0].strip(), parts[1].strip()
                    if v == "true":
                        v = True
                    elif v == "false":
                        v = False
                    else:
                        try:
                            v = float(v) if "." in v else int(v)
                        except ValueError:
                            pass
                    dock_settings[k] = v
            elif current_section == "finder":
                parts = stripped.split(":", 1)
                if len(parts) == 2:
                    k, v = parts[0].strip(), parts[1].strip()
                    if v == "true":
                        v = True
                    elif v == "false":
                        v = False
                    finder_settings[k] = v
            elif current_section == "keyboard":
                parts = stripped.split(":", 1)
                if len(parts) == 2:
                    k, v = parts[0].strip(), parts[1].strip()
                    try:
                        v = int(v)
                    except ValueError:
                        pass
                    keyboard_settings[k] = v
            elif current_section == "dock_apps":
                if stripped.startswith("- name:"):
                    if current_item:
                        apps.append(current_item)
                    name = stripped.split(":", 1)[1].strip().strip('"')
                    current_item = {"name": name}
                elif stripped.startswith("path:"):
                    path_val = stripped.split(":", 1)[1].strip().strip('"')
                    current_item["path"] = path_val
            elif current_section == "dock_others":
                if stripped.startswith("- name:"):
                    if current_item:
                        others.append(current_item)
                    name = stripped.split(":", 1)[1].strip().strip('"')
                    current_item = {"name": name}
                elif stripped.startswith("path:"):
                    path_val = stripped.split(":", 1)[1].strip().strip('"')
                    current_item["path"] = path_val
                elif stripped.startswith("sort:"):
                    sort = stripped.split(":", 1)[1].strip().strip('"')
                    current_item["sort"] = sort
                elif stripped.startswith("display:"):
                    disp = stripped.split(":", 1)[1].strip().strip('"')
                    current_item["display"] = disp
                elif stripped.startswith("view:"):
                    vw = stripped.split(":", 1)[1].strip().strip('"')
                    current_item["view"] = vw

        # Append last items
        if current_section == "dock_apps" and current_item:
            apps.append(current_item)
        elif current_section == "dock_others" and current_item:
            others.append(current_item)

    return {
        "macos_settings": {
            "dock": {"settings": dock_settings, "apps": apps, "others": others},
            "finder": finder_settings,
            "keyboard": keyboard_settings,
        }
    }


def get_current_dock():
    try:
        # Check if dockutil is installed
        subprocess.check_call(
            ["which", "dockutil"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    except subprocess.CalledProcessError:
        # Not installed
        return [], []

    try:
        output = subprocess.check_output(["dockutil", "--list"], text=True)
        apps = []
        others = []
        for line in output.strip().split("\n"):
            if not line:
                continue
            parts = line.split(":", 1)
            if len(parts) == 2:
                name = parts[0].strip()
                path = parts[1].strip()
                # If path ends in .app or contains /Applications, it's an app
                if (
                    path.endswith(".app")
                    or "/Applications" in path
                    or "/System/Applications" in path
                ):
                    apps.append({"name": name, "path": path})
                else:
                    others.append({"name": name, "path": path})
        return apps, others
    except Exception as e:
        print(f"Warning: Failed to list current Dock items: {e}")
        return [], []


def normalize(path):
    return os.path.normpath(os.path.expanduser(path)).rstrip("/")


def sync(settings, check_mode=False):
    dock = settings["macos_settings"]["dock"]
    cfg_apps = dock["apps"]
    cfg_others = dock["others"]

    # Get current Dock state
    curr_apps, curr_others = get_current_dock()

    # Compare
    cfg_apps_norm = [normalize(a["path"]) for a in cfg_apps]
    curr_apps_norm = [normalize(a["path"]) for a in curr_apps]

    cfg_others_norm = [normalize(o["path"]) for o in cfg_others]
    curr_others_norm = [normalize(o["path"]) for o in curr_others]

    if cfg_apps_norm == curr_apps_norm and cfg_others_norm == curr_others_norm:
        print("Dock items are already in sync.")
        return False

    print("Dock items are out of sync. Rebuilding Dock...")

    if check_mode:
        print("[Check Mode] Would rebuild Dock items.")
        return True

    # Rebuild Dock
    try:
        # Remove all
        subprocess.run(["dockutil", "--remove", "all", "--no-restart"], check=True)

        # Add apps
        for app in cfg_apps:
            path = os.path.expanduser(app["path"])
            subprocess.run(["dockutil", "--add", path, "--no-restart"], check=True)

        # Add others
        for other in cfg_others:
            path = os.path.expanduser(other["path"])
            cmd = [
                "dockutil",
                "--add",
                path,
                "--view",
                other["view"],
                "--display",
                other["display"],
                "--sort",
                other["sort"],
                "--no-restart",
            ]
            subprocess.run(cmd, check=True)

        # Restart Dock
        subprocess.run(["killall", "Dock"], check=True)
        print("Dock rebuilt successfully.")
        return True
    except Exception as e:
        print(f"Error rebuilding Dock: {e}")
        return False


if __name__ == "__main__":
    check_mode = "--check" in sys.argv or "-c" in sys.argv
    script_dir = os.path.dirname(os.path.abspath(__file__))
    settings_path = os.path.join(os.path.dirname(script_dir), "settings.yml")
    if not os.path.exists(settings_path):
        print(f"Settings file not found at {settings_path}")
        sys.exit(1)

    settings = parse_settings_yml(settings_path)
    changed = sync(settings, check_mode)
    sys.exit(0)
