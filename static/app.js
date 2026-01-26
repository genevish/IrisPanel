// The Iris Panel - JavaScript Application

const API_BASE = '';

// State
let lights = {};
let groups = {};
let currentLight = null;
let currentGroup = null;
let debounceTimer = null;

// DOM Elements
const connectionModal = document.getElementById('connection-modal');
const bridgeIpInput = document.getElementById('bridge-ip');
const connectBtn = document.getElementById('connect-btn');
const connectionError = document.getElementById('connection-error');
const connectionStatus = document.getElementById('connection-status');
const refreshBtn = document.getElementById('refresh-btn');
const addGroupBtn = document.getElementById('add-group-btn');
const loadingEl = document.getElementById('loading');
const contentEl = document.getElementById('content');
const groupsSection = document.getElementById('groups-section');
const lightsSection = document.getElementById('lights-section');
const groupsGrid = document.getElementById('groups-grid');
const lightsGrid = document.getElementById('lights-grid');

// Group Modal
const groupModal = document.getElementById('group-modal');
const groupModalTitle = document.getElementById('group-modal-title');
const groupNameInput = document.getElementById('group-name');
const lightSelectList = document.getElementById('light-select-list');
const groupError = document.getElementById('group-error');
const cancelGroupBtn = document.getElementById('cancel-group-btn');
const saveGroupBtn = document.getElementById('save-group-btn');

// Light Modal
const lightModal = document.getElementById('light-modal');
const closeLightModal = document.getElementById('close-light-modal');
const lightName = document.getElementById('light-name');
const lightIcon = document.getElementById('light-icon');
const lightPower = document.getElementById('light-power');
const lightBrightness = document.getElementById('light-brightness');
const brightnessValue = document.getElementById('brightness-value');
const colorControl = document.getElementById('color-control');
const lightColor = document.getElementById('light-color');
const colorBtn = document.getElementById('color-btn');

// Initialize
document.addEventListener('DOMContentLoaded', init);

async function init() {
    setupEventListeners();
    await checkConnection();
}

function setupEventListeners() {
    // Connection
    connectBtn.addEventListener('click', connect);
    bridgeIpInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') connect();
    });

    // Header actions
    refreshBtn.addEventListener('click', loadData);
    addGroupBtn.addEventListener('click', () => openGroupModal());

    // Group modal
    cancelGroupBtn.addEventListener('click', closeGroupModal);
    saveGroupBtn.addEventListener('click', saveGroup);

    // Light modal
    closeLightModal.addEventListener('click', closeLightDetailModal);
    lightPower.addEventListener('change', handlePowerChange);
    lightBrightness.addEventListener('input', handleBrightnessInput);
    lightBrightness.addEventListener('change', handleBrightnessChange);
    lightColor.addEventListener('input', handleColorChange);

    // Close modals on backdrop click
    lightModal.addEventListener('click', (e) => {
        if (e.target === lightModal) closeLightDetailModal();
    });
    groupModal.addEventListener('click', (e) => {
        if (e.target === groupModal) closeGroupModal();
    });
}

// API Functions
async function api(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            headers: { 'Content-Type': 'application/json' },
            ...options
        });
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

async function checkConnection() {
    // Show loading state while checking connection
    loadingEl.classList.remove('hidden');
    loadingEl.innerHTML = '<div class="spinner"></div><p>Connecting to Hue Bridge...</p>';

    try {
        const status = await api('/api/status');
        if (status.connected) {
            showConnected();
            await loadData();
        } else {
            // Not connected - show modal with saved IP if available
            loadingEl.classList.add('hidden');
            showConnectionModal(status.saved_ip);
        }
    } catch (error) {
        loadingEl.classList.add('hidden');
        showConnectionModal();
    }
}

async function connect() {
    const ip = bridgeIpInput.value.trim();
    if (!ip) {
        connectionError.textContent = 'Please enter an IP address';
        return;
    }

    connectBtn.classList.add('loading');
    connectionError.textContent = '';

    try {
        const result = await api('/api/connect', {
            method: 'POST',
            body: JSON.stringify({ ip })
        });

        if (result.success) {
            connectionModal.classList.add('hidden');
            showConnected();
            await loadData();
        } else {
            connectionError.textContent = result.error;
        }
    } catch (error) {
        connectionError.textContent = 'Connection failed. Please try again.';
    } finally {
        connectBtn.classList.remove('loading');
    }
}

function showConnectionModal(savedIp = null) {
    connectionModal.classList.remove('hidden');
    if (savedIp) {
        bridgeIpInput.value = savedIp;
    }
    bridgeIpInput.focus();
}

function showConnected() {
    connectionStatus.classList.add('connected');
    connectionStatus.querySelector('.status-text').textContent = 'Connected';
}

// Data Loading
async function loadData() {
    loadingEl.classList.remove('hidden');
    contentEl.classList.add('hidden');

    try {
        const [lightsData, groupsData] = await Promise.all([
            api('/api/lights'),
            api('/api/groups')
        ]);

        lights = lightsData;
        groups = groupsData;

        renderGroups();
        renderLights();

        loadingEl.classList.add('hidden');
        contentEl.classList.remove('hidden');
    } catch (error) {
        console.error('Failed to load data:', error);
        loadingEl.innerHTML = '<p>Failed to load lights. Please refresh.</p>';
    }
}

// Rendering
function renderGroups() {
    const groupIds = Object.keys(groups);

    if (groupIds.length === 0) {
        groupsSection.classList.add('hidden');
        return;
    }

    groupsSection.classList.remove('hidden');
    groupsGrid.innerHTML = '';

    groupIds.forEach(id => {
        const group = groups[id];
        const card = createGroupCard(group);
        groupsGrid.appendChild(card);
    });
}

function renderLights() {
    lightsGrid.innerHTML = '';

    Object.values(lights).forEach(light => {
        const card = createLightCard(light);
        lightsGrid.appendChild(card);
    });
}

function createLightCard(light) {
    const card = document.createElement('div');
    card.className = `device-card ${light.on ? 'on' : ''}`;
    card.dataset.id = light.id;
    card.dataset.type = 'light';

    const brightnessPercent = Math.round((light.brightness / 254) * 100);

    // Get light color for the toggle button
    let toggleColor = '';
    if (light.on && light.has_color && light.hue !== null && light.hue !== undefined) {
        toggleColor = hsbToHex(light.hue, light.sat || 254, 254);
    }

    card.innerHTML = `
        <div class="card-buttons">
            <button class="card-btn toggle-btn ${light.on ? 'on' : ''}" title="Toggle" ${light.on && toggleColor ? `style="background: ${toggleColor}; box-shadow: 0 0 25px ${toggleColor}80;"` : ''}>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="5"/>
                    <line x1="12" y1="1" x2="12" y2="3"/>
                    <line x1="12" y1="21" x2="12" y2="23"/>
                    <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
                    <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
                    <line x1="1" y1="12" x2="3" y2="12"/>
                    <line x1="21" y1="12" x2="23" y2="12"/>
                    <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
                    <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
                </svg>
            </button>
            <button class="card-btn settings-btn" title="Settings">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="3"/>
                    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
                </svg>
            </button>
        </div>
        <div class="card-name">${escapeHtml(light.name)}</div>
        <div class="card-status">${light.on ? `${brightnessPercent}%` : 'Off'}</div>
        <div class="card-brightness" style="width: ${light.on ? brightnessPercent : 0}%"></div>
    `;

    // Toggle button
    card.querySelector('.toggle-btn').addEventListener('click', (e) => {
        e.stopPropagation();
        toggleDevice(light.id, 'light');
    });

    // Settings button
    card.querySelector('.settings-btn').addEventListener('click', (e) => {
        e.stopPropagation();
        openLightDetail(light.id, 'light');
    });

    return card;
}

function createGroupCard(group) {
    const card = document.createElement('div');
    card.className = `device-card group-card ${group.on ? 'on' : ''}`;
    card.dataset.id = group.id;
    card.dataset.type = 'group';

    const brightnessPercent = Math.round((group.brightness / 254) * 100);
    const lightCount = group.lights.length;

    // Get group color for the toggle button
    let toggleColor = '';
    if (group.on && group.has_color && group.hue !== null && group.hue !== undefined) {
        toggleColor = hsbToHex(group.hue, group.sat || 254, 254);
    }

    card.innerHTML = `
        <div class="card-buttons">
            <button class="card-btn toggle-btn ${group.on ? 'on' : ''}" title="Toggle" ${group.on && toggleColor ? `style="background: ${toggleColor}; box-shadow: 0 0 25px ${toggleColor}80;"` : ''}>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="5"/>
                    <line x1="12" y1="1" x2="12" y2="3"/>
                    <line x1="12" y1="21" x2="12" y2="23"/>
                    <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
                    <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
                    <line x1="1" y1="12" x2="3" y2="12"/>
                    <line x1="21" y1="12" x2="23" y2="12"/>
                    <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
                    <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
                </svg>
            </button>
            <button class="card-btn settings-btn" title="Settings">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="3"/>
                    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
                </svg>
            </button>
        </div>
        <div class="card-name">${escapeHtml(group.name)}</div>
        <div class="card-status">${group.on ? `${brightnessPercent}%` : 'Off'} · ${lightCount} light${lightCount !== 1 ? 's' : ''}</div>
        <div class="card-brightness" style="width: ${group.on ? brightnessPercent : 0}%"></div>
    `;

    // Toggle button
    card.querySelector('.toggle-btn').addEventListener('click', (e) => {
        e.stopPropagation();
        toggleDevice(group.id, 'group');
    });

    // Settings button
    card.querySelector('.settings-btn').addEventListener('click', (e) => {
        e.stopPropagation();
        openLightDetail(group.id, 'group');
    });

    return card;
}

// Light Detail Modal
async function openLightDetail(id, type) {
    // Fetch fresh data for this light/group
    try {
        const endpoint = type === 'light' ? '/api/lights' : '/api/groups';
        const data = await api(endpoint);
        if (type === 'light') {
            lights = data;
        } else {
            groups = data;
        }
    } catch (error) {
        console.error('Failed to fetch fresh data:', error);
    }

    const item = type === 'light' ? lights[id] : groups[id];
    if (!item) return;

    currentLight = { id, type, ...item };

    lightName.textContent = item.name;
    lightPower.checked = item.on;
    lightBrightness.value = item.brightness;
    brightnessValue.textContent = `${Math.round((item.brightness / 254) * 100)}%`;

    // Update light icon state
    lightIcon.className = `light-icon-large ${item.on ? 'on' : ''}`;
    lightIcon.innerHTML = type === 'light' ? `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="40" height="40">
            <path d="M9 18h6"/>
            <path d="M10 22h4"/>
            <path d="M15.09 14c.18-.98.65-1.74 1.41-2.5A4.65 4.65 0 0 0 18 8 6 6 0 0 0 6 8c0 1 .23 2.23 1.5 3.5A4.61 4.61 0 0 1 8.91 14"/>
        </svg>
    ` : `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="40" height="40">
            <rect x="3" y="3" width="7" height="7" rx="1"/>
            <rect x="14" y="3" width="7" height="7" rx="1"/>
            <rect x="3" y="14" width="7" height="7" rx="1"/>
            <rect x="14" y="14" width="7" height="7" rx="1"/>
        </svg>
    `;

    // Color control
    if (item.has_color) {
        colorControl.classList.remove('hidden');
        if (item.hue !== null && item.hue !== undefined && item.sat !== null && item.sat !== undefined) {
            const color = hsbToHex(item.hue, item.sat, item.brightness);
            lightColor.value = color;
            colorBtn.style.background = color;
        } else {
            // Default to warm white if no color data
            lightColor.value = '#ffffff';
            colorBtn.style.background = '#ffffff';
        }
    } else {
        colorControl.classList.add('hidden');
    }

    lightModal.classList.remove('hidden');
}

function closeLightDetailModal() {
    // Re-render the card to reflect any color changes
    if (currentLight) {
        const { id, type } = currentLight;
        const card = document.querySelector(`.device-card[data-id="${id}"][data-type="${type}"]`);
        if (card) {
            const item = type === 'light' ? lights[id] : groups[id];
            if (item) {
                const newCard = type === 'light' ? createLightCard(item) : createGroupCard(item);
                card.replaceWith(newCard);
            }
        }

        // If it's a group, also update all lights in that group
        if (type === 'group') {
            const group = groups[id];
            if (group && group.lights) {
                // Re-render each light card in the group using already-updated local state
                group.lights.forEach(lightId => {
                    const lightIdNum = parseInt(lightId);
                    const lightCard = document.querySelector(`.device-card[data-id="${lightIdNum}"][data-type="light"]`);
                    if (lightCard && lights[lightIdNum]) {
                        const newLightCard = createLightCard(lights[lightIdNum]);
                        lightCard.replaceWith(newLightCard);
                    }
                });
            }
        }
    }
    lightModal.classList.add('hidden');
    currentLight = null;
}

// Toggle device from card button
async function toggleDevice(id, type) {
    const item = type === 'light' ? lights[id] : groups[id];
    if (!item) return;

    const newState = !item.on;

    // Update local state
    item.on = newState;
    updateCard(id, type);

    // Send to API
    const endpoint = type === 'light'
        ? `/api/lights/${id}`
        : `/api/groups/${id}`;

    try {
        await api(endpoint, {
            method: 'PUT',
            body: JSON.stringify({ on: newState })
        });
    } catch (error) {
        console.error('Failed to toggle:', error);
        // Revert on failure
        item.on = !newState;
        updateCard(id, type);
    }
}

// Control Handlers
async function handlePowerChange() {
    if (!currentLight) return;

    const on = lightPower.checked;
    lightIcon.className = `light-icon-large ${on ? 'on' : ''}`;

    // Update local state
    if (currentLight.type === 'light') {
        lights[currentLight.id].on = on;
    } else {
        groups[currentLight.id].on = on;
    }
    updateCard(currentLight.id, currentLight.type);

    // Send to API
    const endpoint = currentLight.type === 'light'
        ? `/api/lights/${currentLight.id}`
        : `/api/groups/${currentLight.id}`;

    try {
        await api(endpoint, {
            method: 'PUT',
            body: JSON.stringify({ on })
        });
    } catch (error) {
        console.error('Failed to update power:', error);
    }
}

function handleBrightnessInput() {
    const value = parseInt(lightBrightness.value);
    brightnessValue.textContent = `${Math.round((value / 254) * 100)}%`;
}

async function handleBrightnessChange() {
    if (!currentLight) return;

    const brightness = parseInt(lightBrightness.value);

    // Debounce
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(async () => {
        // Update local state
        if (currentLight.type === 'light') {
            lights[currentLight.id].brightness = brightness;
        } else {
            groups[currentLight.id].brightness = brightness;
        }
        updateCard(currentLight.id, currentLight.type);

        // Send to API
        const endpoint = currentLight.type === 'light'
            ? `/api/lights/${currentLight.id}`
            : `/api/groups/${currentLight.id}`;

        try {
            await api(endpoint, {
                method: 'PUT',
                body: JSON.stringify({ brightness })
            });
        } catch (error) {
            console.error('Failed to update brightness:', error);
        }
    }, 150);
}

async function handleColorChange() {
    if (!currentLight) return;

    const hex = lightColor.value;
    colorBtn.style.background = hex;

    const { hue, sat } = hexToHsb(hex);

    // Update local state
    const item = currentLight.type === 'light' ? lights[currentLight.id] : groups[currentLight.id];
    if (item) {
        item.hue = hue;
        item.sat = sat;
    }

    // If it's a group, also update local state for all lights in the group
    if (currentLight.type === 'group' && item && item.lights) {
        item.lights.forEach(lightId => {
            const lightIdNum = parseInt(lightId);
            if (lights[lightIdNum] && lights[lightIdNum].has_color) {
                lights[lightIdNum].hue = hue;
                lights[lightIdNum].sat = sat;
            }
        });
    }

    // Debounce
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(async () => {
        const endpoint = currentLight.type === 'light'
            ? `/api/lights/${currentLight.id}`
            : `/api/groups/${currentLight.id}`;

        try {
            await api(endpoint, {
                method: 'PUT',
                body: JSON.stringify({ hue, sat })
            });
        } catch (error) {
            console.error('Failed to update color:', error);
        }
    }, 150);
}

function updateCard(id, type) {
    const item = type === 'light' ? lights[id] : groups[id];
    const card = document.querySelector(`.device-card[data-id="${id}"][data-type="${type}"]`);

    if (!card || !item) return;

    const brightnessPercent = Math.round((item.brightness / 254) * 100);

    card.classList.toggle('on', item.on);
    card.querySelector('.toggle-btn').classList.toggle('on', item.on);
    card.querySelector('.card-status').textContent = type === 'light'
        ? (item.on ? `${brightnessPercent}%` : 'Off')
        : `${item.on ? `${brightnessPercent}%` : 'Off'} · ${item.lights?.length || 0} lights`;
    card.querySelector('.card-brightness').style.width = `${item.on ? brightnessPercent : 0}%`;
}

// Group Modal
function openGroupModal(group = null) {
    currentGroup = group;
    groupModalTitle.textContent = group ? 'Edit Group' : 'Create Group';
    groupNameInput.value = group ? group.name : '';
    groupError.textContent = '';

    // Populate light list
    lightSelectList.innerHTML = '';
    Object.values(lights).forEach(light => {
        const isSelected = group ? group.lights.includes(String(light.id)) : false;
        const item = document.createElement('div');
        item.className = 'light-select-item';
        item.innerHTML = `
            <input type="checkbox" id="light-${light.id}" value="${light.id}" ${isSelected ? 'checked' : ''}>
            <label for="light-${light.id}">${escapeHtml(light.name)}</label>
        `;
        lightSelectList.appendChild(item);
    });

    groupModal.classList.remove('hidden');
    groupNameInput.focus();
}

function closeGroupModal() {
    groupModal.classList.add('hidden');
    currentGroup = null;
}

async function saveGroup() {
    const name = groupNameInput.value.trim();
    if (!name) {
        groupError.textContent = 'Please enter a group name';
        return;
    }

    const selectedLights = Array.from(
        lightSelectList.querySelectorAll('input:checked')
    ).map(input => input.value);

    if (selectedLights.length === 0) {
        groupError.textContent = 'Please select at least one light';
        return;
    }

    try {
        if (currentGroup) {
            // Update existing group
            await api(`/api/groups/${currentGroup.id}`, {
                method: 'PUT',
                body: JSON.stringify({ name, lights: selectedLights })
            });
        } else {
            // Create new group
            await api('/api/groups', {
                method: 'POST',
                body: JSON.stringify({ name, lights: selectedLights })
            });
        }

        closeGroupModal();
        await loadData();
    } catch (error) {
        groupError.textContent = 'Failed to save group. Please try again.';
    }
}

async function deleteGroup(id, name) {
    if (!confirm(`Delete group "${name}"?`)) return;

    try {
        await api(`/api/groups/${id}`, { method: 'DELETE' });
        await loadData();
    } catch (error) {
        console.error('Failed to delete group:', error);
    }
}

// Color Conversion Utilities
function hsbToHex(hue, sat, bri) {
    const h = hue / 65535;
    const s = sat / 254;
    const v = bri / 254;

    let r, g, b;
    const i = Math.floor(h * 6);
    const f = h * 6 - i;
    const p = v * (1 - s);
    const q = v * (1 - f * s);
    const t = v * (1 - (1 - f) * s);

    switch (i % 6) {
        case 0: r = v; g = t; b = p; break;
        case 1: r = q; g = v; b = p; break;
        case 2: r = p; g = v; b = t; break;
        case 3: r = p; g = q; b = v; break;
        case 4: r = t; g = p; b = v; break;
        case 5: r = v; g = p; b = q; break;
    }

    const toHex = (x) => {
        const hex = Math.round(x * 255).toString(16);
        return hex.length === 1 ? '0' + hex : hex;
    };

    return `#${toHex(r)}${toHex(g)}${toHex(b)}`;
}

function hexToHsb(hex) {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    if (!result) return { hue: 0, sat: 0 };

    const r = parseInt(result[1], 16) / 255;
    const g = parseInt(result[2], 16) / 255;
    const b = parseInt(result[3], 16) / 255;

    const max = Math.max(r, g, b);
    const min = Math.min(r, g, b);
    const d = max - min;

    let h = 0;
    const s = max === 0 ? 0 : d / max;

    if (max !== min) {
        switch (max) {
            case r: h = (g - b) / d + (g < b ? 6 : 0); break;
            case g: h = (b - r) / d + 2; break;
            case b: h = (r - g) / d + 4; break;
        }
        h /= 6;
    }

    return {
        hue: Math.round(h * 65535),
        sat: Math.round(s * 254)
    };
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
