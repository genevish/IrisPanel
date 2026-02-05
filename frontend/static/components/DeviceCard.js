import { html } from '../lib.js';
import { useBridge } from '../state.js';
import { hsbToHex } from '../utils.js';

export default function DeviceCard({ item, type, onSettings }) {
    const { toggleLight, toggleGroup } = useBridge();

    const isOn = item.on;
    const pct = Math.round((item.brightness / 254) * 100);

    let glowColor = null;
    if (isOn && item.has_color && item.hue != null) {
        glowColor = hsbToHex(item.hue, item.sat || 254, 254);
    }

    const handleToggle = (e) => {
        e.stopPropagation();
        type === 'light' ? toggleLight(item.id) : toggleGroup(item.id);
    };

    const handleSettings = (e) => {
        e.stopPropagation();
        onSettings(item.id, type);
    };

    const statusText = type === 'light'
        ? (isOn ? `${pct}%` : 'Off')
        : `${isOn ? `${pct}%` : 'Off'} \u00B7 ${item.lights?.length || 0} light${(item.lights?.length || 0) !== 1 ? 's' : ''}`;

    return html`
        <div class="group bg-surface border ${isOn ? 'border-surface-border/60' : 'border-surface-border/40'} rounded-xl p-4 relative overflow-hidden transition-all hover:bg-surface-hover hover:scale-[1.02] hover:shadow-lg cursor-default">
            ${isOn && html`<div class="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-iris-accent to-indigo-400"></div>`}
            <div class="flex gap-3 mb-3">
                <button
                    onClick=${handleToggle}
                    class="w-12 h-12 rounded-full flex items-center justify-center transition-all shrink-0 ${isOn ? 'text-gray-900' : 'bg-white/[.07] text-iris-muted hover:bg-white/[.12]'}"
                    style=${isOn ? `background:${glowColor || '#fbbf24'};box-shadow:0 0 20px ${glowColor || '#fbbf24'}60` : ''}
                    title="Toggle"
                >
                    <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="5"/>
                        <line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/>
                        <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
                        <line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/>
                        <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
                    </svg>
                </button>
                <button
                    onClick=${handleSettings}
                    class="w-12 h-12 rounded-full bg-white/[.05] hover:bg-white/[.10] text-iris-dim hover:text-iris-muted flex items-center justify-center transition shrink-0"
                    title="Settings"
                >
                    <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="3"/>
                        <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.6 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.6a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
                    </svg>
                </button>
            </div>
            <div class="text-sm font-semibold truncate">${item.name}</div>
            <div class="text-xs ${isOn ? 'text-iris-muted' : 'text-iris-dim'} mt-0.5">${statusText}</div>
            <div class="absolute bottom-0 left-0 h-0.5 bg-gradient-to-r from-iris-accent to-indigo-400 transition-all duration-300" style="width:${isOn ? pct : 0}%"></div>
        </div>
    `;
}
