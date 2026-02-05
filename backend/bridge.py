"""Hue Bridge connection manager."""

import json
from pathlib import Path
from phue import Bridge, PhueRegistrationException


CONFIG_FILE = Path.home() / ".irispanel_config.json"

ROOM_CLASSES = [
    "Living room", "Kitchen", "Dining", "Bedroom", "Kids bedroom",
    "Bathroom", "Nursery", "Recreation", "Office", "Gym", "Hallway",
    "Toilet", "Front door", "Garage", "Terrace", "Garden", "Driveway",
    "Carport", "Home", "Downstairs", "Upstairs", "Top floor", "Attic",
    "Guest room", "Staircase", "Lounge", "Man cave", "Computer",
    "Studio", "Music", "TV", "Reading", "Closet", "Storage", "Laundry room",
    "Balcony", "Porch", "Barbecue", "Pool", "Other",
]


class HueBridgeConnection:
    """Wraps phue Bridge with config persistence."""

    def __init__(self):
        self.bridge: Bridge | None = None
        self.bridge_ip: str | None = None

    # -- config --------------------------------------------------------

    def load_config(self) -> dict:
        try:
            if CONFIG_FILE.exists():
                with open(CONFIG_FILE, "r") as f:
                    return json.load(f)
        except Exception:
            pass
        return {}

    def save_config(self, config: dict) -> None:
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(config, f)
        except Exception:
            pass

    # -- connection ----------------------------------------------------

    @property
    def connected(self) -> bool:
        return self.bridge is not None

    def connect(self, ip: str) -> None:
        """Connect to a Hue bridge. Raises on failure."""
        b = Bridge(ip)
        b.connect()
        self.bridge = b
        self.bridge_ip = ip
        config = self.load_config()
        config["bridge_ip"] = ip
        self.save_config(config)

    def auto_connect(self) -> None:
        """Try to reconnect using saved IP. Silently fails."""
        config = self.load_config()
        saved_ip = config.get("bridge_ip")
        if saved_ip:
            try:
                self.connect(saved_ip)
                print(f"Auto-connected to bridge at {saved_ip}")
            except Exception as e:
                print(f"Auto-connect failed: {e}")

    # -- lights --------------------------------------------------------

    def get_lights(self) -> dict:
        light_objects = self.bridge.get_light_objects("id")
        result = {}
        for light_id, light in light_objects.items():
            state = self.bridge.get_light(light_id)
            ls = state.get("state", {})
            result[light_id] = {
                "id": light_id,
                "name": light.name,
                "on": ls.get("on", False),
                "brightness": ls.get("bri", 254),
                "reachable": ls.get("reachable", False),
                "has_color": "hue" in ls or "xy" in ls,
                "hue": ls.get("hue"),
                "sat": ls.get("sat"),
            }
        return result

    def update_light(self, light_id: int, *, on: bool | None = None,
                     brightness: int | None = None, hue: int | None = None,
                     sat: int | None = None) -> None:
        if on is not None:
            self.bridge.set_light(light_id, "on", on)
        if brightness is not None:
            self.bridge.set_light(light_id, "bri", brightness)
        if hue is not None and sat is not None:
            self.bridge.set_light(light_id, {"hue": hue, "sat": sat})

    # -- groups --------------------------------------------------------

    def get_groups(self) -> dict:
        groups = self.bridge.get_group()
        result = {}
        for gid, gdata in groups.items():
            if gid == "0" or not isinstance(gdata, dict):
                continue
            action = gdata.get("action", {})
            result[gid] = {
                "id": gid,
                "name": gdata.get("name", f"Group {gid}"),
                "type": gdata.get("type", "LightGroup"),
                "class": gdata.get("class", "Other"),
                "lights": gdata.get("lights", []),
                "on": action.get("on", False),
                "brightness": action.get("bri", 254),
                "has_color": "hue" in action or "xy" in action,
                "hue": action.get("hue"),
                "sat": action.get("sat"),
            }
        return result

    def update_group(self, group_id: int, *, on: bool | None = None,
                     brightness: int | None = None, hue: int | None = None,
                     sat: int | None = None, name: str | None = None,
                     lights: list[str] | None = None,
                     room_class: str | None = None) -> None:
        if on is not None:
            self.bridge.set_group(group_id, "on", on)
        if brightness is not None:
            self.bridge.set_group(group_id, "bri", brightness)
        if hue is not None and sat is not None:
            self.bridge.set_group(group_id, {"hue": hue, "sat": sat})

        if name is not None or lights is not None or room_class is not None:
            import httpx
            url = f"http://{self.bridge_ip}/api/{self.bridge.username}/groups/{group_id}"
            attrs: dict = {}
            if name is not None:
                attrs["name"] = name
            if lights is not None:
                attrs["lights"] = lights
            if room_class is not None:
                attrs["class"] = room_class
            if attrs:
                httpx.put(url, json=attrs)

    def create_group(self, name: str, lights: list[str],
                     room_class: str = "Other"):
        return self.bridge.create_group(
            name, lights, group_type="Room", room_class=room_class
        )

    def delete_group(self, group_id: int) -> None:
        self.bridge.delete_group(group_id)
