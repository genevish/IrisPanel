#!/usr/bin/env python3
"""
IrisPanel Web - Flask backend for Philips Hue control.
"""

from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from phue import Bridge, PhueRegistrationException
from pathlib import Path
import json

app = Flask(__name__)
CORS(app)

# Global bridge connection
bridge = None
bridge_ip = None
CONFIG_FILE = Path.home() / ".irispanel_config.json"


def load_config():
    """Load saved configuration."""
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def save_config(config):
    """Save configuration."""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f)
    except Exception:
        pass


@app.route('/')
def index():
    """Serve the main page."""
    return render_template('index.html')


@app.route('/api/status')
def status():
    """Get connection status."""
    global bridge, bridge_ip
    config = load_config()
    return jsonify({
        'connected': bridge is not None,
        'bridge_ip': bridge_ip,
        'saved_ip': config.get('bridge_ip')
    })


@app.route('/api/connect', methods=['POST'])
def connect():
    """Connect to Hue Bridge."""
    global bridge, bridge_ip
    data = request.json
    ip = data.get('ip')

    if not ip:
        return jsonify({'success': False, 'error': 'IP address required'}), 400

    try:
        bridge = Bridge(ip)
        bridge.connect()
        bridge_ip = ip

        # Save IP for next time
        config = load_config()
        config['bridge_ip'] = ip
        save_config(config)

        return jsonify({'success': True})
    except PhueRegistrationException:
        bridge = None
        return jsonify({
            'success': False,
            'error': 'Press the link button on your Hue Bridge and try again.'
        }), 401
    except Exception as e:
        bridge = None
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/lights')
def get_lights():
    """Get all lights."""
    if not bridge:
        return jsonify({'error': 'Not connected'}), 503

    try:
        lights = bridge.get_light_objects('id')
        result = {}
        for light_id, light in lights.items():
            state = bridge.get_light(light_id)
            light_state = state.get('state', {})
            result[light_id] = {
                'id': light_id,
                'name': light.name,
                'on': light_state.get('on', False),
                'brightness': light_state.get('bri', 254),
                'reachable': light_state.get('reachable', False),
                'has_color': 'hue' in light_state or 'xy' in light_state,
                'hue': light_state.get('hue'),
                'sat': light_state.get('sat'),
            }
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/groups')
def get_groups():
    """Get all groups."""
    if not bridge:
        return jsonify({'error': 'Not connected'}), 503

    try:
        groups = bridge.get_group()
        result = {}
        for group_id, group_data in groups.items():
            if group_id == '0':  # Skip "all lights" group
                continue
            if not isinstance(group_data, dict):
                continue
            action = group_data.get('action', {})
            result[group_id] = {
                'id': group_id,
                'name': group_data.get('name', f'Group {group_id}'),
                'lights': group_data.get('lights', []),
                'on': action.get('on', False),
                'brightness': action.get('bri', 254),
                'has_color': 'hue' in action or 'xy' in action,
            }
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/lights/<int:light_id>', methods=['PUT'])
def update_light(light_id):
    """Update a light's state."""
    if not bridge:
        return jsonify({'error': 'Not connected'}), 503

    data = request.json
    try:
        if 'on' in data:
            bridge.set_light(light_id, 'on', data['on'])
        if 'brightness' in data:
            bridge.set_light(light_id, 'bri', data['brightness'])
        if 'hue' in data and 'sat' in data:
            bridge.set_light(light_id, {'hue': data['hue'], 'sat': data['sat']})
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/groups/<int:group_id>', methods=['PUT'])
def update_group(group_id):
    """Update a group's state."""
    if not bridge:
        return jsonify({'error': 'Not connected'}), 503

    data = request.json
    try:
        if 'on' in data:
            bridge.set_group(group_id, 'on', data['on'])
        if 'brightness' in data:
            bridge.set_group(group_id, 'bri', data['brightness'])
        if 'hue' in data and 'sat' in data:
            bridge.set_group(group_id, {'hue': data['hue'], 'sat': data['sat']})
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/groups', methods=['POST'])
def create_group():
    """Create a new group."""
    if not bridge:
        return jsonify({'error': 'Not connected'}), 503

    data = request.json
    name = data.get('name')
    lights = data.get('lights', [])

    if not name:
        return jsonify({'error': 'Group name required'}), 400
    if not lights:
        return jsonify({'error': 'At least one light required'}), 400

    try:
        result = bridge.create_group(name, lights)
        return jsonify({'success': True, 'group_id': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/groups/<int:group_id>', methods=['DELETE'])
def delete_group(group_id):
    """Delete a group."""
    if not bridge:
        return jsonify({'error': 'Not connected'}), 503

    try:
        bridge.delete_group(group_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # Try to auto-connect on startup
    config = load_config()
    saved_ip = config.get('bridge_ip')
    if saved_ip:
        try:
            bridge = Bridge(saved_ip)
            bridge.connect()
            bridge_ip = saved_ip
            print(f"Auto-connected to bridge at {saved_ip}")
        except Exception as e:
            print(f"Auto-connect failed: {e}")

    print("Starting IrisPanel Web on http://localhost:5050")
    app.run(debug=True, host='0.0.0.0', port=5050)
