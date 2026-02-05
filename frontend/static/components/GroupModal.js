import { html, React } from '../lib.js';
import { useBridge } from '../state.js';

const { useState, useCallback } = React;

export default function GroupModal({ onClose }) {
    const { lights, roomClasses, createGroup } = useBridge();

    const [name, setName] = useState('');
    const [roomClass, setRoomClass] = useState('Living room');
    const [selected, setSelected] = useState([]);
    const [error, setError] = useState('');
    const [busy, setBusy] = useState(false);

    const toggleLight = useCallback((lid) => {
        setSelected(prev =>
            prev.includes(lid) ? prev.filter(x => x !== lid) : [...prev, lid]
        );
    }, []);

    const handleSave = useCallback(async () => {
        const trimmed = name.trim();
        if (!trimmed) { setError('Enter a room name'); return; }
        if (selected.length === 0) { setError('Select at least one light'); return; }
        setBusy(true);
        setError('');
        try {
            await createGroup(trimmed, selected, roomClass);
            onClose();
        } catch (e) {
            setError(e.message || 'Failed to create room');
        } finally {
            setBusy(false);
        }
    }, [name, selected, roomClass, createGroup, onClose]);

    return html`
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4" onClick=${(e) => { if (e.target === e.currentTarget) onClose(); }}>
            <div class="bg-surface border border-surface-border rounded-2xl p-6 w-full max-w-sm">
                <h2 class="text-lg font-semibold mb-4">Create Room</h2>

                <input
                    type="text"
                    value=${name}
                    onInput=${(e) => setName(e.target.value)}
                    placeholder="Room name"
                    class="w-full px-3 py-2.5 rounded-lg bg-iris-bg border border-surface-border text-iris-text text-sm outline-none focus:border-iris-accent transition"
                    autoFocus
                />

                <label class="block text-xs text-iris-dim mt-4 mb-1.5">Room Type</label>
                <select
                    value=${roomClass}
                    onChange=${(e) => setRoomClass(e.target.value)}
                    class="w-full px-3 py-2.5 rounded-lg bg-iris-bg border border-surface-border text-iris-text text-sm outline-none focus:border-iris-accent appearance-none pr-8 transition"
                >
                    ${roomClasses.map(rc => html`<option key=${rc} value=${rc}>${rc}</option>`)}
                </select>

                <label class="block text-xs text-iris-dim mt-4 mb-1.5">Select Lights</label>
                <div class="max-h-44 overflow-y-auto rounded-lg bg-iris-bg border border-surface-border">
                    ${Object.values(lights).map(l => html`
                        <label key=${l.id} class="flex items-center gap-2.5 px-3 py-2 hover:bg-white/[.03] cursor-pointer text-sm">
                            <input
                                type="checkbox"
                                checked=${selected.includes(String(l.id))}
                                onChange=${() => toggleLight(String(l.id))}
                                class="accent-iris-accent w-4 h-4"
                            />
                            ${l.name}
                        </label>
                    `)}
                </div>

                ${error && html`<p class="text-red-400 text-xs mt-3">${error}</p>`}

                <div class="flex gap-3 mt-5">
                    <button
                        onClick=${onClose}
                        class="flex-1 py-2.5 rounded-lg border border-surface-border text-iris-muted hover:bg-surface-hover text-sm font-medium transition"
                    >Cancel</button>
                    <button
                        onClick=${handleSave}
                        disabled=${busy}
                        class="flex-1 py-2.5 rounded-lg bg-iris-accent hover:bg-indigo-500 text-white text-sm font-semibold transition disabled:opacity-50"
                    >${busy ? 'Creating...' : 'Create'}</button>
                </div>
            </div>
        </div>
    `;
}
