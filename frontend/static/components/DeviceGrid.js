import { html } from '../lib.js';
import { useBridge } from '../state.js';
import DeviceCard from './DeviceCard.js';

export default function DeviceGrid({ onSettings }) {
    const { lights, groups, loading, error, refresh } = useBridge();

    if (loading) {
        return html`
            <div class="flex flex-col items-center justify-center py-24 text-iris-muted">
                <div class="spinner mb-4"></div>
                <p class="text-sm">Loading lights...</p>
            </div>
        `;
    }

    if (error) {
        return html`
            <div class="flex flex-col items-center justify-center py-24 text-iris-muted">
                <svg class="w-12 h-12 text-red-400 mb-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"/>
                    <line x1="12" y1="8" x2="12" y2="12"/>
                    <line x1="12" y1="16" x2="12.01" y2="16"/>
                </svg>
                <p class="text-sm text-red-400 mb-4">${error}</p>
                <button
                    onClick=${refresh}
                    class="px-4 py-2 rounded-lg bg-surface-hover hover:bg-surface-border text-iris-muted text-sm transition"
                >Try Again</button>
            </div>
        `;
    }

    const groupIds = Object.keys(groups);
    const lightIds = Object.keys(lights);

    return html`
        <main class="max-w-6xl mx-auto px-2 sm:px-4 py-3 space-y-4">
            ${groupIds.length > 0 && html`
                <section>
                    <h2 class="flex items-center gap-2 text-lg font-semibold text-iris-muted mb-4">
                        <svg class="w-5 h-5 opacity-60" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/>
                            <rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>
                        </svg>
                        Rooms
                    </h2>
                    <div class="grid grid-cols-4 gap-2">
                        ${groupIds.map(id => html`
                            <${DeviceCard} key=${'g' + id} item=${groups[id]} type="group" onSettings=${onSettings} />
                        `)}
                    </div>
                </section>
            `}
            <section>
                <h2 class="flex items-center gap-2 text-lg font-semibold text-iris-muted mb-4">
                    <svg class="w-5 h-5 opacity-60" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M9 18h6"/><path d="M10 22h4"/>
                        <path d="M15.09 14c.18-.98.65-1.74 1.41-2.5A4.65 4.65 0 0 0 18 8 6 6 0 0 0 6 8c0 1 .23 2.23 1.5 3.5A4.61 4.61 0 0 1 8.91 14"/>
                    </svg>
                    Lights
                </h2>
                <div class="grid grid-cols-4 gap-2">
                    ${lightIds.map(id => html`
                        <${DeviceCard} key=${'l' + id} item=${lights[id]} type="light" onSettings=${onSettings} />
                    `)}
                </div>
            </section>
        </main>
    `;
}
