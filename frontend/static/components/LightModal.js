import { html, React } from '../lib.js';
import { useBridge } from '../state.js';
import { hsbToHex, hexToHsb } from '../utils.js';

const { useState, useEffect, useCallback } = React;

export default function LightModal({ deviceId, deviceType, onClose }) {
    const {
        lights, groups, roomClasses,
        updateLight, updateGroup, updateGroupSettings, deleteGroup,
    } = useBridge();

    const item = deviceType === 'light' ? lights[deviceId] : groups[deviceId];

    // Room settings local state
    const [roomClass, setRoomClass] = useState('Other');
    const [selectedLights, setSelectedLights] = useState([]);
    const [roomError, setRoomError] = useState('');

    useEffect(() => {
        if (item && deviceType === 'group') {
            setRoomClass(item.class || 'Other');
            setSelectedLights(item.lights || []);
        }
    }, [item, deviceType]);

    const handlePower = useCallback(() => {
        if (!item) return;
        const data = { on: !item.on };
        deviceType === 'light'
            ? updateLight(deviceId, data)
            : updateGroup(deviceId, data);
    }, [item, deviceId, deviceType, updateLight, updateGroup]);

    const handleBrightness = useCallback((e) => {
        const brightness = parseInt(e.target.value);
        deviceType === 'light'
            ? updateLight(deviceId, { brightness }, true)
            : updateGroup(deviceId, { brightness }, true);
    }, [deviceId, deviceType, updateLight, updateGroup]);

    const handleColor = useCallback((e) => {
        const { hue, sat } = hexToHsb(e.target.value);
        deviceType === 'light'
            ? updateLight(deviceId, { hue, sat }, true)
            : updateGroup(deviceId, { hue, sat }, true);
    }, [deviceId, deviceType, updateLight, updateGroup]);

    const handleSaveRoom = useCallback(async () => {
        if (selectedLights.length === 0) {
            setRoomError('Select at least one light');
            return;
        }
        setRoomError('');
        try {
            await updateGroupSettings(deviceId, {
                lights: selectedLights,
                room_class: roomClass,
            });
            onClose();
        } catch {
            setRoomError('Failed to save');
        }
    }, [deviceId, selectedLights, roomClass, updateGroupSettings, onClose]);

    const handleDelete = useCallback(async () => {
        if (!confirm(`Delete room "${item?.name}"?`)) return;
        try {
            await deleteGroup(deviceId);
            onClose();
        } catch {
            setRoomError('Failed to delete');
        }
    }, [deviceId, item, deleteGroup, onClose]);

    const toggleLightSelection = useCallback((lid) => {
        setSelectedLights(prev =>
            prev.includes(lid) ? prev.filter(x => x !== lid) : [...prev, lid]
        );
    }, []);

    if (!item) return null;

    const pct = Math.round((item.brightness / 254) * 100);
    let colorHex = '#ffffff';
    if (item.has_color && item.hue != null && item.sat != null) {
        colorHex = hsbToHex(item.hue, item.sat, item.brightness);
    }

    const isGroup = deviceType === 'group';

    return html`
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-2" onClick=${(e) => { if (e.target === e.currentTarget) onClose(); }}>
            <div class="bg-surface border border-surface-border rounded-xl p-3 w-full max-w-3xl max-h-full overflow-y-auto relative">
                <!-- Close -->
                <button onClick=${onClose} class="absolute top-2 right-2 w-8 h-8 rounded-full bg-white/[.07] hover:bg-white/[.12] flex items-center justify-center text-iris-dim hover:text-iris-muted transition z-10">
                    <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                    </svg>
                </button>

                <div class="flex gap-4 ${isGroup ? '' : 'justify-center'}">
                    <!-- Left: Header + Controls -->
                    <div class="${isGroup ? 'flex-1' : 'w-64'}">
                        <!-- Header -->
                        <div class="flex items-center gap-3 mb-3">
                            <div class="w-10 h-10 rounded-full ${item.on ? 'bg-amber-400 shadow-[0_0_20px_rgba(251,191,36,.5)]' : 'bg-white/[.07]'} flex items-center justify-center shrink-0 transition-all">
                                ${deviceType === 'light' ? html`
                                    <svg class="w-5 h-5 ${item.on ? 'text-gray-900' : 'text-iris-muted'}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <path d="M9 18h6"/><path d="M10 22h4"/>
                                        <path d="M15.09 14c.18-.98.65-1.74 1.41-2.5A4.65 4.65 0 0 0 18 8 6 6 0 0 0 6 8c0 1 .23 2.23 1.5 3.5A4.61 4.61 0 0 1 8.91 14"/>
                                    </svg>
                                ` : html`
                                    <svg class="w-5 h-5 ${item.on ? 'text-gray-900' : 'text-iris-muted'}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/>
                                        <rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>
                                    </svg>
                                `}
                            </div>
                            <h2 class="text-base font-semibold truncate">${item.name}</h2>
                        </div>

                        <!-- Controls -->
                        <div class="space-y-3">
                            <!-- Power -->
                            <div class="flex items-center justify-between">
                                <span class="text-iris-muted text-sm">Power</span>
                                <div class="toggle-track ${item.on ? 'on' : ''}" onClick=${handlePower}>
                                    <div class="toggle-thumb"></div>
                                </div>
                            </div>

                            <!-- Brightness -->
                            <div class="flex items-center justify-between gap-3">
                                <span class="text-iris-muted text-sm shrink-0">Brightness</span>
                                <input type="range" min="1" max="254" value=${item.brightness} onInput=${handleBrightness} class="flex-1" />
                                <span class="text-sm font-medium w-10 text-right">${pct}%</span>
                            </div>

                            <!-- Color -->
                            ${item.has_color && html`
                                <div class="flex items-center justify-between">
                                    <span class="text-iris-muted text-sm">Color</span>
                                    <div class="color-swatch w-8 h-8 rounded-full border-2 border-white/30 hover:border-white/50 transition" style=${{ background: colorHex }}>
                                        <input type="color" value=${colorHex} onInput=${handleColor} />
                                    </div>
                                </div>
                            `}
                        </div>
                    </div>

                    <!-- Right: Room settings (groups only) -->
                    ${isGroup && html`
                        <div class="flex-1 border-l border-surface-border pl-4">
                            <h3 class="text-sm font-semibold text-iris-muted mb-2">Room Settings</h3>

                            <div class="flex gap-3">
                                <div class="flex-1">
                                    <label class="block text-xs text-iris-dim mb-1">Room Type</label>
                                    <select
                                        value=${roomClass}
                                        onChange=${(e) => setRoomClass(e.target.value)}
                                        class="w-full px-2 py-1.5 rounded-lg bg-iris-bg border border-surface-border text-iris-text text-sm outline-none focus:border-iris-accent appearance-none pr-6 transition"
                                    >
                                        ${roomClasses.map(rc => html`<option key=${rc} value=${rc}>${rc}</option>`)}
                                    </select>
                                </div>
                                <div class="flex-1">
                                    <label class="block text-xs text-iris-dim mb-1">Lights</label>
                                    <div class="h-20 overflow-y-auto rounded-lg bg-iris-bg border border-surface-border">
                                        ${Object.values(lights).map(l => html`
                                            <label key=${l.id} class="flex items-center gap-2 px-2 py-1 hover:bg-white/[.03] cursor-pointer text-xs">
                                                <input
                                                    type="checkbox"
                                                    checked=${selectedLights.includes(String(l.id))}
                                                    onChange=${() => toggleLightSelection(String(l.id))}
                                                    class="accent-iris-accent w-3 h-3"
                                                />
                                                <span class="truncate">${l.name}</span>
                                            </label>
                                        `)}
                                    </div>
                                </div>
                            </div>

                            ${roomError && html`<p class="text-red-400 text-xs mt-1">${roomError}</p>`}

                            <div class="flex gap-2 mt-2">
                                <button
                                    onClick=${handleSaveRoom}
                                    class="flex-1 py-2 rounded-lg bg-iris-accent hover:bg-indigo-500 text-white text-sm font-semibold transition"
                                >Save</button>
                                <button
                                    onClick=${handleDelete}
                                    class="px-4 py-2 rounded-lg border border-red-500/40 text-red-400 hover:bg-red-500 hover:text-white text-sm font-medium transition"
                                >Delete</button>
                            </div>
                        </div>
                    `}
                </div>
            </div>
        </div>
    `;
}
