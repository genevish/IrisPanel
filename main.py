#!/usr/bin/env python3
"""
The Iris Panel - Philips Hue Touch Control Panel
A touch-friendly GUI for controlling Philips Hue lights.
"""

import tkinter as tk
from tkinter import ttk, messagebox, colorchooser, simpledialog
import colorsys
import threading
import json
from pathlib import Path

try:
    from phue import Bridge, PhueRegistrationException
except ImportError:
    print("Please install phue: pip install phue")
    exit(1)


class HueBridgeConnection:
    """Manages connection to the Philips Hue Bridge."""

    CONFIG_FILE = Path.home() / ".irispanel_config.json"

    def __init__(self, config_path=None):
        self.bridge = None
        self.connected = False
        self.config_path = config_path or str(Path.home() / ".python_hue")
        self.bridge_ip = None

    def load_saved_ip(self):
        """Load saved bridge IP from config file."""
        try:
            if self.CONFIG_FILE.exists():
                with open(self.CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    return config.get('bridge_ip')
        except Exception:
            pass
        return None

    def save_ip(self, ip_address):
        """Save bridge IP to config file."""
        try:
            config = {}
            if self.CONFIG_FILE.exists():
                with open(self.CONFIG_FILE, 'r') as f:
                    config = json.load(f)
            config['bridge_ip'] = ip_address
            with open(self.CONFIG_FILE, 'w') as f:
                json.dump(config, f)
        except Exception:
            pass

    def connect(self, ip_address):
        """Connect to the Hue Bridge at the specified IP address."""
        try:
            self.bridge = Bridge(ip_address, config_file_path=self.config_path)
            self.bridge.connect()
            self.connected = True
            self.bridge_ip = ip_address
            self.save_ip(ip_address)  # Save for next time
            return True, "Connected successfully!"
        except PhueRegistrationException:
            return False, "Please press the link button on your Hue Bridge and try again."
        except Exception as e:
            return False, f"Connection failed: {str(e)}"

    def get_lights(self):
        """Get all lights from the bridge."""
        if not self.connected or not self.bridge:
            return {}
        return self.bridge.get_light_objects('id')

    def get_light_state(self, light_id):
        """Get the current state of a light."""
        if not self.connected:
            return None
        return self.bridge.get_light(light_id)

    def set_light_on(self, light_id, on):
        """Turn a light on or off."""
        if self.connected:
            try:
                self.bridge.set_light(light_id, 'on', on)
            except Exception:
                pass

    def set_light_brightness(self, light_id, brightness):
        """Set light brightness (0-254)."""
        if self.connected:
            try:
                self.bridge.set_light(light_id, 'bri', brightness)
            except Exception:
                pass

    def set_light_color_xy(self, light_id, x, y):
        """Set light color using xy coordinates."""
        if self.connected:
            try:
                self.bridge.set_light(light_id, 'xy', [x, y])
            except Exception:
                pass

    def set_light_color_hsb(self, light_id, hue, sat):
        """Set light color using hue and saturation."""
        if self.connected:
            try:
                self.bridge.set_light(light_id, {'hue': hue, 'sat': sat})
            except Exception:
                pass

    def get_groups(self):
        """Get all groups from the bridge."""
        if not self.connected or not self.bridge:
            return {}
        try:
            groups = self.bridge.get_group()
            # Filter out any invalid entries
            if isinstance(groups, dict):
                return {k: v for k, v in groups.items() if isinstance(v, dict)}
            return {}
        except Exception:
            return {}

    def get_group(self, group_id):
        """Get a specific group's details."""
        if not self.connected:
            return None
        return self.bridge.get_group(group_id)

    def set_group_on(self, group_id, on):
        """Turn all lights in a group on or off."""
        if self.connected:
            try:
                self.bridge.set_group(int(group_id), 'on', on)
            except Exception:
                pass

    def set_group_brightness(self, group_id, brightness):
        """Set brightness for all lights in a group."""
        if self.connected:
            try:
                self.bridge.set_group(int(group_id), 'bri', brightness)
            except Exception:
                pass

    def set_group_color_hsb(self, group_id, hue, sat):
        """Set color for all lights in a group."""
        if self.connected:
            try:
                self.bridge.set_group(int(group_id), {'hue': hue, 'sat': sat})
            except Exception:
                pass

    def create_group(self, name, light_ids):
        """Create a new group with the specified lights."""
        if self.connected:
            return self.bridge.create_group(name, light_ids)
        return None

    def delete_group(self, group_id):
        """Delete a group."""
        if self.connected:
            return self.bridge.delete_group(group_id)
        return None

    def set_group_lights(self, group_id, light_ids):
        """Update the lights in a group."""
        if self.connected:
            try:
                self.bridge.set_group(int(group_id), 'lights', light_ids)
            except Exception:
                pass


class TouchButton(tk.Canvas):
    """A large, touch-friendly button using Canvas for macOS compatibility."""

    def __init__(self, parent, text="", bg='#4D4D4D', fg='#FFFFFF',
                 activebackground=None, activeforeground=None,
                 font=('Helvetica', 16, 'bold'), padx=20, pady=15,
                 command=None, **kwargs):
        self.text = text
        self.bg_color = bg
        self.fg_color = fg
        self.active_bg = activebackground or self._darken_color(bg)
        self.active_fg = activeforeground or fg
        self.font = font
        self.padx = padx
        self.pady = pady
        self.command = command
        self._disabled = False

        # Calculate size based on text
        temp = tk.Label(parent, text=text, font=font)
        text_width = temp.winfo_reqwidth()
        text_height = temp.winfo_reqheight()
        temp.destroy()

        width = text_width + padx * 2
        height = text_height + pady * 2

        super().__init__(parent, width=width, height=height,
                        highlightthickness=0, **kwargs)

        self.width = width
        self.height = height

        self._draw()

        self.bind('<Button-1>', self._on_click)
        self.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)
        self.bind('<ButtonRelease-1>', self._on_release)

    def _darken_color(self, hex_color):
        """Darken a hex color by 20%."""
        hex_color = hex_color.lstrip('#')
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        r, g, b = int(r * 0.8), int(g * 0.8), int(b * 0.8)
        return f'#{r:02x}{g:02x}{b:02x}'

    def _draw(self, pressed=False):
        self.delete('all')
        bg = self.active_bg if pressed else self.bg_color
        fg = self.active_fg if pressed else self.fg_color

        # Rounded rectangle background
        radius = 8
        self._round_rect(2, 2, self.width - 2, self.height - 2, radius, fill=bg)

        # Text
        self.create_text(self.width // 2, self.height // 2,
                        text=self.text, font=self.font, fill=fg)

    def _round_rect(self, x1, y1, x2, y2, radius, **kwargs):
        """Draw a rounded rectangle."""
        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1,
            x1 + radius, y1,
        ]
        return self.create_polygon(points, smooth=True, **kwargs)

    def _on_click(self, event):
        if not self._disabled:
            self._draw(pressed=True)

    def _on_release(self, event):
        if not self._disabled:
            self._draw(pressed=False)
            if self.command:
                self.command()

    def _on_enter(self, event):
        if not self._disabled:
            self.configure(cursor='hand2')

    def _on_leave(self, event):
        self._draw(pressed=False)

    def configure(self, **kwargs):
        if 'state' in kwargs:
            self._disabled = kwargs.pop('state') == 'disabled'
        if 'text' in kwargs:
            self.text = kwargs.pop('text')
            self._draw()
        if 'bg' in kwargs:
            self.bg_color = kwargs.pop('bg')
            self._draw()
        super().configure(**kwargs)


class ToggleButton(tk.Canvas):
    """A touch-friendly toggle switch."""

    def __init__(self, parent, width=80, height=40, command=None, **kwargs):
        super().__init__(parent, width=width, height=height,
                        highlightthickness=0, **kwargs)
        self.width = width
        self.height = height
        self.command = command
        self.is_on = False

        self.off_color = '#666666'
        self.on_color = '#4CAF50'
        self.knob_color = '#FFFFFF'

        self.bind('<Button-1>', self._toggle)
        self._draw()

    def _draw(self):
        self.delete('all')
        radius = self.height // 2

        # Background pill shape
        color = self.on_color if self.is_on else self.off_color
        self.create_oval(0, 0, self.height, self.height, fill=color, outline='')
        self.create_oval(self.width - self.height, 0, self.width, self.height,
                        fill=color, outline='')
        self.create_rectangle(radius, 0, self.width - radius, self.height,
                             fill=color, outline='')

        # Knob
        knob_x = self.width - self.height + 4 if self.is_on else 4
        self.create_oval(knob_x, 4, knob_x + self.height - 8, self.height - 4,
                        fill=self.knob_color, outline='')

    def _toggle(self, event=None):
        self.is_on = not self.is_on
        self._draw()
        if self.command:
            self.command(self.is_on)

    def set_state(self, on):
        self.is_on = on
        self._draw()

    def get_state(self):
        return self.is_on


class BrightnessSlider(tk.Frame):
    """A touch-friendly brightness slider with debouncing."""

    def __init__(self, parent, command=None, bg_color='#2D2D2D', debounce_ms=150, **kwargs):
        super().__init__(parent, **kwargs)
        self.command = command
        self.bg_color = bg_color
        self.debounce_ms = debounce_ms
        self._debounce_id = None

        self.configure(bg=bg_color)

        # Brightness icon
        self.icon_label = tk.Label(self, text="☀", font=('Helvetica', 20),
                                   bg=bg_color, fg='#FFD700')
        self.icon_label.pack(side='left', padx=(0, 10))

        # Slider
        self.slider = ttk.Scale(self, from_=1, to=254, orient='horizontal',
                               length=200, command=self._on_change)
        self.slider.pack(side='left', fill='x', expand=True)

        # Value label
        self.value_label = tk.Label(self, text="100%", font=('Helvetica', 14),
                                    bg=bg_color, fg='#FFFFFF', width=5)
        self.value_label.pack(side='left', padx=(10, 0))

        self.slider.set(254)

    def _on_change(self, value):
        brightness = int(float(value))
        percent = int((brightness / 254) * 100)
        self.value_label.configure(text=f"{percent}%")

        # Debounce: cancel previous scheduled call and schedule a new one
        if self._debounce_id:
            self.after_cancel(self._debounce_id)
        self._debounce_id = self.after(self.debounce_ms, lambda: self._send_command(brightness))

    def _send_command(self, brightness):
        """Send the brightness command after debounce delay."""
        self._debounce_id = None
        if self.command:
            self.command(brightness)

    def set_value(self, value):
        self.slider.set(value)
        percent = int((value / 254) * 100)
        self.value_label.configure(text=f"{percent}%")

    def get_value(self):
        return int(self.slider.get())


class ColorPickerButton(tk.Canvas):
    """A touch-friendly color picker button."""

    def __init__(self, parent, size=60, command=None, **kwargs):
        super().__init__(parent, width=size, height=size,
                        highlightthickness=2, highlightbackground='#555555', **kwargs)
        self.size = size
        self.command = command
        self.current_color = '#FFFFFF'

        self.bind('<Button-1>', self._pick_color)
        self._draw()

    def _draw(self):
        self.delete('all')
        padding = 4
        self.create_oval(padding, padding, self.size - padding, self.size - padding,
                        fill=self.current_color, outline='#333333', width=2)

    def _pick_color(self, event=None):
        color = colorchooser.askcolor(
            initialcolor=self.current_color,
            title="Choose Light Color"
        )
        if color[1]:
            self.current_color = color[1]
            self._draw()
            if self.command:
                # Convert RGB to HSB for Hue API
                r, g, b = color[0]
                h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
                hue = int(h * 65535)
                sat = int(s * 254)
                self.command(hue, sat, self.current_color)

    def set_color(self, hex_color):
        self.current_color = hex_color
        self._draw()


class LightControlCard(tk.Frame):
    """A card widget for controlling a single light."""

    def __init__(self, parent, light_id, light_name, is_color_light,
                 on_toggle, on_brightness, on_color, **kwargs):
        super().__init__(parent, **kwargs)

        self.light_id = light_id
        self.is_color_light = is_color_light

        self.configure(bg='#3D3D3D', padx=15, pady=15)

        # Header row with name and toggle
        header = tk.Frame(self, bg='#3D3D3D')
        header.pack(fill='x', pady=(0, 15))

        # Light name
        name_label = tk.Label(header, text=light_name,
                             font=('Helvetica', 18, 'bold'),
                             bg='#3D3D3D', fg='#FFFFFF', anchor='w')
        name_label.pack(side='left', fill='x', expand=True)

        # Toggle switch
        self.toggle = ToggleButton(header, width=70, height=35, bg='#3D3D3D',
                                   command=lambda on: on_toggle(light_id, on))
        self.toggle.pack(side='right')

        # Brightness slider
        self.brightness_slider = BrightnessSlider(
            self,
            command=lambda bri: on_brightness(light_id, bri)
        )
        self.brightness_slider.pack(fill='x', pady=(0, 10))

        # Color picker (only for color-capable lights)
        if is_color_light:
            color_frame = tk.Frame(self, bg='#3D3D3D')
            color_frame.pack(fill='x')

            color_label = tk.Label(color_frame, text="Color:",
                                   font=('Helvetica', 14),
                                   bg='#3D3D3D', fg='#AAAAAA')
            color_label.pack(side='left', padx=(0, 10))

            self.color_picker = ColorPickerButton(
                color_frame, size=50, bg='#3D3D3D',
                command=lambda h, s, c: on_color(light_id, h, s)
            )
            self.color_picker.pack(side='left')
        else:
            self.color_picker = None

    def update_state(self, on, brightness, color_hex=None):
        """Update the card to reflect current light state."""
        self.toggle.set_state(on)
        self.brightness_slider.set_value(brightness)
        if self.color_picker and color_hex:
            self.color_picker.set_color(color_hex)


class GroupControlCard(tk.Frame):
    """A card widget for controlling a group of lights."""

    def __init__(self, parent, group_id, group_name, light_count, has_color,
                 on_toggle, on_brightness, on_color, on_edit, on_delete, **kwargs):
        super().__init__(parent, **kwargs)

        self.group_id = group_id
        self.has_color = has_color

        self.configure(bg='#2A4A5A', padx=15, pady=15)

        # Header row with name, light count, and toggle
        header = tk.Frame(self, bg='#2A4A5A')
        header.pack(fill='x', pady=(0, 10))

        # Group icon and name
        name_frame = tk.Frame(header, bg='#2A4A5A')
        name_frame.pack(side='left', fill='x', expand=True)

        icon_label = tk.Label(name_frame, text="◈", font=('Helvetica', 16),
                              bg='#2A4A5A', fg='#5DADE2')
        icon_label.pack(side='left', padx=(0, 8))

        name_label = tk.Label(name_frame, text=group_name,
                             font=('Helvetica', 18, 'bold'),
                             bg='#2A4A5A', fg='#FFFFFF', anchor='w')
        name_label.pack(side='left')

        count_label = tk.Label(name_frame, text=f"({light_count} lights)",
                              font=('Helvetica', 12),
                              bg='#2A4A5A', fg='#AAAAAA')
        count_label.pack(side='left', padx=(8, 0))

        # Toggle switch
        self.toggle = ToggleButton(header, width=70, height=35, bg='#2A4A5A',
                                   command=lambda on: on_toggle(group_id, on))
        self.toggle.pack(side='right')

        # Brightness slider
        self.brightness_slider = BrightnessSlider(
            self,
            command=lambda bri: on_brightness(group_id, bri),
            bg_color='#2A4A5A'
        )
        self.brightness_slider.pack(fill='x', pady=(0, 10))

        # Bottom row with color picker and action buttons
        bottom_frame = tk.Frame(self, bg='#2A4A5A')
        bottom_frame.pack(fill='x')

        # Color picker (only if group has color-capable lights)
        if has_color:
            color_frame = tk.Frame(bottom_frame, bg='#2A4A5A')
            color_frame.pack(side='left')

            color_label = tk.Label(color_frame, text="Color:",
                                   font=('Helvetica', 14),
                                   bg='#2A4A5A', fg='#AAAAAA')
            color_label.pack(side='left', padx=(0, 10))

            self.color_picker = ColorPickerButton(
                color_frame, size=50, bg='#2A4A5A',
                command=lambda h, s, c: on_color(group_id, h, s)
            )
            self.color_picker.pack(side='left')
        else:
            self.color_picker = None

        # Action buttons
        btn_frame = tk.Frame(bottom_frame, bg='#2A4A5A')
        btn_frame.pack(side='right')

        edit_btn = TouchButton(btn_frame, text="Edit", font=('Helvetica', 12, 'bold'),
                              bg='#3498DB', fg='#FFFFFF', padx=12, pady=6,
                              activebackground='#2980B9',
                              command=lambda: on_edit(group_id))
        edit_btn.pack(side='left', padx=(0, 8))

        delete_btn = TouchButton(btn_frame, text="Delete", font=('Helvetica', 12, 'bold'),
                                bg='#E74C3C', fg='#FFFFFF', padx=12, pady=6,
                                activebackground='#C0392B',
                                command=lambda: on_delete(group_id))
        delete_btn.pack(side='left')

    def update_state(self, on, brightness, color_hex=None):
        """Update the card to reflect current group state."""
        self.toggle.set_state(on)
        self.brightness_slider.set_value(brightness)
        if self.color_picker and color_hex:
            self.color_picker.set_color(color_hex)


class CreateGroupDialog(tk.Toplevel):
    """Dialog for creating or editing a light group."""

    def __init__(self, parent, lights, on_save, group_id=None, group_name="",
                 selected_light_ids=None):
        super().__init__(parent)
        self.on_save = on_save
        self.group_id = group_id
        self.lights = lights
        self.selected_lights = set(selected_light_ids or [])
        self.checkboxes = {}

        title = "Edit Group" if group_id else "Create Group"
        self.title(title)
        self.geometry("450x500")
        self.configure(bg='#2D2D2D')
        self.resizable(False, True)

        self.transient(parent)
        self.grab_set()

        # Title
        title_label = tk.Label(self, text=title,
                              font=('Helvetica', 24, 'bold'),
                              bg='#2D2D2D', fg='#FFFFFF')
        title_label.pack(pady=(20, 15))

        # Group name entry
        name_frame = tk.Frame(self, bg='#2D2D2D')
        name_frame.pack(fill='x', padx=30, pady=(0, 15))

        name_label = tk.Label(name_frame, text="Group Name:",
                             font=('Helvetica', 14),
                             bg='#2D2D2D', fg='#FFFFFF')
        name_label.pack(anchor='w')

        self.name_entry = tk.Entry(name_frame, font=('Helvetica', 16),
                                  bg='#4D4D4D', fg='#FFFFFF',
                                  insertbackground='#FFFFFF',
                                  relief='flat', bd=8)
        self.name_entry.pack(fill='x', pady=(5, 0))
        self.name_entry.insert(0, group_name)

        # Light selection
        lights_label = tk.Label(self, text="Select Lights:",
                               font=('Helvetica', 14),
                               bg='#2D2D2D', fg='#FFFFFF')
        lights_label.pack(anchor='w', padx=30, pady=(10, 5))

        # Scrollable light list
        list_frame = tk.Frame(self, bg='#2D2D2D')
        list_frame.pack(fill='both', expand=True, padx=30, pady=(0, 15))

        canvas = tk.Canvas(list_frame, bg='#3D3D3D', highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=canvas.yview)
        self.lights_inner = tk.Frame(canvas, bg='#3D3D3D')

        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        canvas.pack(side='left', fill='both', expand=True)

        canvas_window = canvas.create_window((0, 0), window=self.lights_inner, anchor='nw')
        self.lights_inner.bind('<Configure>',
                              lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.bind('<Configure>',
                   lambda e: canvas.itemconfig(canvas_window, width=e.width))

        # Add checkboxes for each light
        for light_id, light in lights.items():
            var = tk.BooleanVar(value=str(light_id) in self.selected_lights or
                                      light_id in self.selected_lights)
            self.checkboxes[light_id] = var

            cb_frame = tk.Frame(self.lights_inner, bg='#3D3D3D')
            cb_frame.pack(fill='x', padx=10, pady=5)

            cb = tk.Checkbutton(cb_frame, text=light.name,
                               variable=var,
                               font=('Helvetica', 14),
                               bg='#3D3D3D', fg='#FFFFFF',
                               selectcolor='#4D4D4D',
                               activebackground='#3D3D3D',
                               activeforeground='#FFFFFF',
                               cursor='hand2')
            cb.pack(side='left')

        # Status label
        self.status_label = tk.Label(self, text="", font=('Helvetica', 11),
                                     bg='#2D2D2D', fg='#FF6B6B')
        self.status_label.pack(pady=5)

        # Buttons
        btn_frame = tk.Frame(self, bg='#2D2D2D')
        btn_frame.pack(pady=(0, 20))

        cancel_btn = TouchButton(btn_frame, text="Cancel", bg='#7F8C8D', fg='#FFFFFF',
                                font=('Helvetica', 14, 'bold'), padx=20, pady=10,
                                activebackground='#636E72', activeforeground='#FFFFFF',
                                command=self.destroy)
        cancel_btn.pack(side='left', padx=(0, 10))

        save_btn = TouchButton(btn_frame, text="Save Group", bg='#2ECC71', fg='#FFFFFF',
                              font=('Helvetica', 14, 'bold'), padx=20, pady=10,
                              activebackground='#27AE60', activeforeground='#FFFFFF',
                              command=self._save)
        save_btn.pack(side='left')

        self.name_entry.focus_set()

    def _save(self):
        name = self.name_entry.get().strip()
        if not name:
            self.status_label.configure(text="Please enter a group name")
            return

        selected = [str(lid) for lid, var in self.checkboxes.items() if var.get()]
        if not selected:
            self.status_label.configure(text="Please select at least one light")
            return

        self.on_save(self.group_id, name, selected)
        self.destroy()


class ConnectionDialog(tk.Toplevel):
    """Dialog for connecting to Hue Bridge."""

    def __init__(self, parent, on_connect, default_ip=None):
        super().__init__(parent)
        self.on_connect = on_connect

        self.title("Connect to Hue Bridge")
        self.geometry("450x300")
        self.configure(bg='#2D2D2D')
        self.resizable(False, False)

        # Center the dialog
        self.transient(parent)
        self.grab_set()

        # Title
        title = tk.Label(self, text="Connect to Philips Hue",
                        font=('Helvetica', 24, 'bold'),
                        bg='#2D2D2D', fg='#FFFFFF')
        title.pack(pady=(30, 20))

        # Instructions
        instructions = tk.Label(
            self,
            text="Enter your Hue Bridge IP address.\nYou may need to press the link button on your bridge.",
            font=('Helvetica', 12),
            bg='#2D2D2D', fg='#AAAAAA',
            justify='center'
        )
        instructions.pack(pady=(0, 20))

        # IP Entry
        entry_frame = tk.Frame(self, bg='#2D2D2D')
        entry_frame.pack(pady=10)

        ip_label = tk.Label(entry_frame, text="Bridge IP:",
                           font=('Helvetica', 14),
                           bg='#2D2D2D', fg='#FFFFFF')
        ip_label.pack(side='left', padx=(0, 10))

        self.ip_entry = tk.Entry(entry_frame, font=('Helvetica', 16), width=20,
                                bg='#4D4D4D', fg='#FFFFFF',
                                insertbackground='#FFFFFF',
                                relief='flat', bd=10)
        self.ip_entry.pack(side='left')
        self.ip_entry.insert(0, default_ip or "192.168.1.2")

        # Status label
        self.status_label = tk.Label(self, text="", font=('Helvetica', 11),
                                     bg='#2D2D2D', fg='#FF6B6B')
        self.status_label.pack(pady=10)

        # Connect button
        self.connect_btn = TouchButton(
            self, text="Connect", bg='#2ECC71', fg='#FFFFFF',
            font=('Helvetica', 16, 'bold'),
            activebackground='#27AE60', activeforeground='#FFFFFF',
            command=self._connect
        )
        self.connect_btn.pack(pady=20)

        self.ip_entry.focus_set()
        self.bind('<Return>', lambda e: self._connect())

    def _connect(self):
        ip = self.ip_entry.get().strip()
        if not ip:
            self.status_label.configure(text="Please enter an IP address")
            return

        self.connect_btn.configure(state='disabled', text="Connecting...")
        self.status_label.configure(text="Connecting...", fg='#FFD700')
        self.update()

        # Run connection in thread to not block UI
        def connect_thread():
            success, message = self.on_connect(ip)
            self.after(0, lambda: self._handle_result(success, message))

        threading.Thread(target=connect_thread, daemon=True).start()

    def _handle_result(self, success, message):
        if success:
            self.destroy()
        else:
            self.status_label.configure(text=message, fg='#FF6B6B')
            self.connect_btn.configure(state='normal', text="Connect")


class IrisPanelApp:
    """Main application class for IrisPanel."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("The Iris Panel")
        self.root.geometry("800x600")
        self.root.configure(bg='#1E1E1E')
        self.root.minsize(600, 400)

        # Configure styles
        self._setup_styles()

        # Bridge connection
        self.hue = HueBridgeConnection()
        self.lights = {}
        self.light_cards = {}
        self.groups = {}
        self.group_cards = {}

        # Build UI
        self._build_ui()

        # Try auto-connect with saved IP, or show connection dialog
        self.root.after(100, self._try_auto_connect)

    def _setup_styles(self):
        """Configure ttk styles."""
        style = ttk.Style()
        style.theme_use('clam')

        # Scale style
        style.configure('TScale', background='#2D2D2D', troughcolor='#4D4D4D',
                       sliderthickness=30, sliderrelief='flat')

    def _build_ui(self):
        """Build the main user interface."""
        # Header
        header = tk.Frame(self.root, bg='#2D2D2D', height=70)
        header.pack(fill='x')
        header.pack_propagate(False)

        title = tk.Label(header, text="The Iris Panel",
                        font=('Helvetica', 28, 'bold'),
                        bg='#2D2D2D', fg='#FFFFFF')
        title.pack(side='left', padx=20, pady=15)

        # Connection status
        self.status_frame = tk.Frame(header, bg='#2D2D2D')
        self.status_frame.pack(side='right', padx=20)

        self.status_indicator = tk.Canvas(self.status_frame, width=16, height=16,
                                          bg='#2D2D2D', highlightthickness=0)
        self.status_indicator.pack(side='left', padx=(0, 8))
        self.status_indicator.create_oval(2, 2, 14, 14, fill='#FF6B6B', outline='')

        self.status_text = tk.Label(self.status_frame, text="Disconnected",
                                   font=('Helvetica', 12),
                                   bg='#2D2D2D', fg='#AAAAAA')
        self.status_text.pack(side='left')

        # Reconnect button
        self.reconnect_btn = TouchButton(
            header, text="Connect", bg='#2ECC71', fg='#FFFFFF',
            font=('Helvetica', 12, 'bold'), padx=15, pady=8,
            activebackground='#27AE60', activeforeground='#FFFFFF',
            command=self._show_connection_dialog
        )
        self.reconnect_btn.pack(side='right', padx=10)

        # Refresh button
        self.refresh_btn = TouchButton(
            header, text="Refresh", bg='#3498DB', fg='#FFFFFF',
            font=('Helvetica', 12, 'bold'), padx=15, pady=8,
            activebackground='#2980B9', activeforeground='#FFFFFF',
            command=self._refresh_lights
        )
        self.refresh_btn.pack(side='right')

        # Create Group button
        self.create_group_btn = TouchButton(
            header, text="+ Group", bg='#9B59B6', fg='#FFFFFF',
            font=('Helvetica', 12, 'bold'), padx=15, pady=8,
            activebackground='#8E44AD', activeforeground='#FFFFFF',
            command=self._show_create_group_dialog
        )
        self.create_group_btn.pack(side='right', padx=(0, 10))

        # Main content area with scrolling
        self.content_frame = tk.Frame(self.root, bg='#1E1E1E')
        self.content_frame.pack(fill='both', expand=True, padx=20, pady=20)

        # Canvas for scrolling
        self.canvas = tk.Canvas(self.content_frame, bg='#1E1E1E',
                               highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.content_frame, orient='vertical',
                                       command=self.canvas.yview)

        self.lights_frame = tk.Frame(self.canvas, bg='#1E1E1E')

        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side='right', fill='y')
        self.canvas.pack(side='left', fill='both', expand=True)

        self.canvas_window = self.canvas.create_window((0, 0), window=self.lights_frame,
                                                        anchor='nw')

        self.lights_frame.bind('<Configure>', self._on_frame_configure)
        self.canvas.bind('<Configure>', self._on_canvas_configure)

        # Mouse wheel scrolling
        self.canvas.bind_all('<MouseWheel>', self._on_mousewheel)
        self.canvas.bind_all('<Button-4>', self._on_mousewheel)
        self.canvas.bind_all('<Button-5>', self._on_mousewheel)

        # Placeholder message
        self.placeholder = tk.Label(
            self.lights_frame,
            text="No lights found.\nConnect to your Hue Bridge to get started.",
            font=('Helvetica', 16),
            bg='#1E1E1E', fg='#666666',
            justify='center'
        )
        self.placeholder.pack(pady=100)

    def _on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        if event.num == 4 or event.delta > 0:
            self.canvas.yview_scroll(-1, 'units')
        elif event.num == 5 or event.delta < 0:
            self.canvas.yview_scroll(1, 'units')

    def _try_auto_connect(self):
        """Try to auto-connect using saved IP address."""
        saved_ip = self.hue.load_saved_ip()
        if saved_ip:
            # Show a connecting status
            self.status_text.configure(text="Connecting...")
            self.root.update()

            def try_connect():
                success, message = self.hue.connect(saved_ip)
                self.root.after(0, lambda: self._handle_auto_connect(success, saved_ip))

            threading.Thread(target=try_connect, daemon=True).start()
        else:
            self._show_connection_dialog()

    def _handle_auto_connect(self, success, saved_ip):
        """Handle result of auto-connect attempt."""
        if success:
            self._update_connection_status(True)
            self._load_lights()
        else:
            # Auto-connect failed, show dialog with saved IP pre-filled
            self._show_connection_dialog(default_ip=saved_ip)

    def _show_connection_dialog(self, default_ip=None):
        """Show the bridge connection dialog."""
        if default_ip is None:
            default_ip = self.hue.load_saved_ip()
        ConnectionDialog(self.root, self._connect_to_bridge, default_ip=default_ip)

    def _connect_to_bridge(self, ip):
        """Attempt to connect to the Hue Bridge."""
        success, message = self.hue.connect(ip)
        if success:
            self._update_connection_status(True)
            self.root.after(100, self._load_lights)
        return success, message

    def _update_connection_status(self, connected):
        """Update the connection status indicator."""
        if connected:
            self.status_indicator.delete('all')
            self.status_indicator.create_oval(2, 2, 14, 14, fill='#4CAF50', outline='')
            self.status_text.configure(text="Connected")
            self.reconnect_btn.configure(text="Reconnect")
        else:
            self.status_indicator.delete('all')
            self.status_indicator.create_oval(2, 2, 14, 14, fill='#FF6B6B', outline='')
            self.status_text.configure(text="Disconnected")
            self.reconnect_btn.configure(text="Connect")

    def _load_lights(self):
        """Load lights and groups from the bridge and create control cards."""
        if not self.hue.connected:
            return

        self.lights = self.hue.get_lights()
        self.groups = self.hue.get_groups()

        # Clear existing cards
        for widget in self.lights_frame.winfo_children():
            widget.destroy()
        self.light_cards.clear()
        self.group_cards.clear()

        if not self.lights and not self.groups:
            self.placeholder = tk.Label(
                self.lights_frame,
                text="No lights found on this bridge.",
                font=('Helvetica', 16),
                bg='#1E1E1E', fg='#666666'
            )
            self.placeholder.pack(pady=100)
            return

        columns = 2
        row = 0
        col = 0

        # Groups section
        if self.groups:
            groups_header = tk.Label(
                self.lights_frame,
                text="Groups",
                font=('Helvetica', 20, 'bold'),
                bg='#1E1E1E', fg='#5DADE2',
                anchor='w'
            )
            groups_header.grid(row=row, column=0, columnspan=columns,
                              sticky='w', padx=10, pady=(10, 15))
            row += 1

            for group_id, group_data in self.groups.items():
                if group_id == '0':  # Skip the "all lights" group
                    continue

                group_name = group_data.get('name', f'Group {group_id}')
                light_ids = group_data.get('lights', [])
                light_count = len(light_ids)

                # Check if any lights in group support color
                has_color = False
                for lid in light_ids:
                    lid_int = int(lid)
                    if lid_int in self.lights:
                        state = self.hue.get_light_state(lid_int)
                        if state and ('hue' in state.get('state', {}) or
                                     'xy' in state.get('state', {})):
                            has_color = True
                            break

                card = GroupControlCard(
                    self.lights_frame,
                    group_id=group_id,
                    group_name=group_name,
                    light_count=light_count,
                    has_color=has_color,
                    on_toggle=self._on_group_toggle,
                    on_brightness=self._on_group_brightness,
                    on_color=self._on_group_color,
                    on_edit=self._on_group_edit,
                    on_delete=self._on_group_delete
                )
                card.grid(row=row, column=col, padx=10, pady=10, sticky='nsew')

                # Update with current state
                group_state = group_data.get('action', {})
                card.update_state(
                    on=group_state.get('on', False),
                    brightness=group_state.get('bri', 254)
                )

                self.group_cards[group_id] = card

                col += 1
                if col >= columns:
                    col = 0
                    row += 1

            # Reset column for lights section
            if col != 0:
                col = 0
                row += 1

        # Lights section header
        if self.lights:
            lights_header = tk.Label(
                self.lights_frame,
                text="Individual Lights",
                font=('Helvetica', 20, 'bold'),
                bg='#1E1E1E', fg='#FFFFFF',
                anchor='w'
            )
            lights_header.grid(row=row, column=0, columnspan=columns,
                              sticky='w', padx=10, pady=(20, 15))
            row += 1

            for light_id, light in self.lights.items():
                state = self.hue.get_light_state(light_id)

                # Check if it's a color light
                is_color = 'hue' in state.get('state', {}) or 'xy' in state.get('state', {})

                card = LightControlCard(
                    self.lights_frame,
                    light_id=light_id,
                    light_name=light.name,
                    is_color_light=is_color,
                    on_toggle=self._on_light_toggle,
                    on_brightness=self._on_brightness_change,
                    on_color=self._on_color_change
                )
                card.grid(row=row, column=col, padx=10, pady=10, sticky='nsew')

                # Update with current state
                light_state = state.get('state', {})
                card.update_state(
                    on=light_state.get('on', False),
                    brightness=light_state.get('bri', 254)
                )

                self.light_cards[light_id] = card

                col += 1
                if col >= columns:
                    col = 0
                    row += 1

        # Configure grid weights
        for i in range(columns):
            self.lights_frame.columnconfigure(i, weight=1)

    def _refresh_lights(self):
        """Refresh the light states."""
        if not self.hue.connected:
            messagebox.showwarning("Not Connected",
                                  "Please connect to a Hue Bridge first.")
            return
        self._load_lights()

    def _on_light_toggle(self, light_id, on):
        """Handle light toggle."""
        def toggle():
            self.hue.set_light_on(light_id, on)
        threading.Thread(target=toggle, daemon=True).start()

    def _on_brightness_change(self, light_id, brightness):
        """Handle brightness change."""
        def set_brightness():
            self.hue.set_light_brightness(light_id, brightness)
        threading.Thread(target=set_brightness, daemon=True).start()

    def _on_color_change(self, light_id, hue, sat):
        """Handle color change."""
        def set_color():
            self.hue.set_light_color_hsb(light_id, hue, sat)
        threading.Thread(target=set_color, daemon=True).start()

    def _on_group_toggle(self, group_id, on):
        """Handle group toggle."""
        def toggle():
            self.hue.set_group_on(group_id, on)
        threading.Thread(target=toggle, daemon=True).start()

    def _on_group_brightness(self, group_id, brightness):
        """Handle group brightness change."""
        def set_brightness():
            self.hue.set_group_brightness(group_id, brightness)
        threading.Thread(target=set_brightness, daemon=True).start()

    def _on_group_color(self, group_id, hue, sat):
        """Handle group color change."""
        def set_color():
            self.hue.set_group_color_hsb(group_id, hue, sat)
        threading.Thread(target=set_color, daemon=True).start()

    def _on_group_edit(self, group_id):
        """Handle editing a group."""
        if not self.hue.connected:
            return

        group_data = self.groups.get(group_id, {})
        group_name = group_data.get('name', '')
        light_ids = group_data.get('lights', [])

        CreateGroupDialog(
            self.root,
            lights=self.lights,
            on_save=self._save_group,
            group_id=group_id,
            group_name=group_name,
            selected_light_ids=light_ids
        )

    def _on_group_delete(self, group_id):
        """Handle deleting a group."""
        group_name = self.groups.get(group_id, {}).get('name', f'Group {group_id}')
        if messagebox.askyesno("Delete Group",
                              f"Are you sure you want to delete '{group_name}'?"):
            def delete():
                self.hue.delete_group(group_id)
                self.root.after(100, self._load_lights)
            threading.Thread(target=delete, daemon=True).start()

    def _show_create_group_dialog(self):
        """Show the dialog to create a new group."""
        if not self.hue.connected:
            messagebox.showwarning("Not Connected",
                                  "Please connect to a Hue Bridge first.")
            return

        CreateGroupDialog(
            self.root,
            lights=self.lights,
            on_save=self._save_group
        )

    def _save_group(self, group_id, name, light_ids):
        """Save a new or edited group."""
        def save():
            try:
                if group_id:
                    # Update existing group - use API directly
                    self.hue.bridge.set_group(int(group_id), {'name': name, 'lights': light_ids})
                else:
                    # Create new group
                    self.hue.create_group(name, light_ids)
            except Exception as e:
                print(f"Error saving group: {e}")
            self.root.after(100, self._load_lights)
        threading.Thread(target=save, daemon=True).start()

    def run(self):
        """Start the application."""
        # Center window on screen
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

        self.root.mainloop()


def main():
    """Main entry point."""
    app = IrisPanelApp()
    app.run()


if __name__ == '__main__':
    main()