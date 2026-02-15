import { html } from '../lib.js';
import { useBridge } from '../state.js';

export default function Header({ onAddRoom }) {
    const { connected, error, refresh } = useBridge();

    const hasError = !!error;
    const statusColor = hasError ? 'bg-amber-400' : connected ? 'bg-green-400 shadow-[0_0_6px_rgba(74,222,128,.6)]' : 'bg-red-400';
    const statusText = hasError ? 'Error' : connected ? 'Connected' : 'Disconnected';

    return html`
        <header class="sticky top-0 z-40 bg-surface/80 backdrop-blur-md border-b border-surface-border">
            <div class="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
                <h1 class="text-xl font-bold text-iris-text tracking-tight">The Iris Panel <span class="text-xs font-normal text-iris-muted/50">b3</span></h1>
                <div class="flex items-center gap-3">
                    <button
                        onClick=${refresh}
                        class="w-9 h-9 rounded-lg bg-surface-hover hover:bg-surface-border flex items-center justify-center transition"
                        title="Refresh"
                    >
                        <svg class="w-4.5 h-4.5 text-iris-muted" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M23 4v6h-6"/><path d="M1 20v-6h6"/>
                            <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
                        </svg>
                    </button>
                    <button
                        onClick=${onAddRoom}
                        class="w-9 h-9 rounded-lg bg-surface-hover hover:bg-surface-border flex items-center justify-center transition"
                        title="Create Room"
                    >
                        <svg class="w-4.5 h-4.5 text-iris-muted" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
                        </svg>
                    </button>
                    <div class="flex items-center gap-2 px-3 py-1.5 rounded-full bg-surface-hover text-sm">
                        <span class="w-2 h-2 rounded-full ${statusColor}"></span>
                        <span class="text-iris-muted">${statusText}</span>
                    </div>
                </div>
            </div>
        </header>
    `;
}
