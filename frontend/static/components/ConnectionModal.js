import { html, React } from '../lib.js';
import { useBridge } from '../state.js';

const { useState } = React;

export default function ConnectionModal() {
    const { connected, savedIp, connect, initialChecked } = useBridge();
    const [ip, setIp] = useState('');
    const [error, setError] = useState('');
    const [busy, setBusy] = useState(false);
    const [initialized, setInitialized] = useState(false);

    // Pre-fill saved IP once
    React.useEffect(() => {
        if (savedIp && !initialized) {
            setIp(savedIp);
            setInitialized(true);
        }
    }, [savedIp, initialized]);

    if (!initialChecked || connected) return null;

    const handleConnect = async () => {
        const trimmed = ip.trim();
        if (!trimmed) { setError('Please enter an IP address'); return; }
        setBusy(true);
        setError('');
        try {
            await connect(trimmed);
        } catch (e) {
            setError(e.message || 'Connection failed');
        } finally {
            setBusy(false);
        }
    };

    const onKeyDown = (e) => { if (e.key === 'Enter') handleConnect(); };

    return html`
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
            <div class="bg-surface border border-surface-border rounded-2xl p-8 w-full max-w-sm text-center">
                <div class="w-16 h-16 rounded-full bg-iris-accent/20 flex items-center justify-center mx-auto mb-5">
                    <svg class="w-8 h-8 text-iris-accent" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                        <path d="M2 17l10 5 10-5"/>
                        <path d="M2 12l10 5 10-5"/>
                    </svg>
                </div>
                <h2 class="text-xl font-semibold mb-1">Connect to Hue Bridge</h2>
                <p class="text-iris-muted text-sm mb-6">Enter your bridge IP address</p>
                <input
                    type="text"
                    value=${ip}
                    onInput=${(e) => setIp(e.target.value)}
                    onKeyDown=${onKeyDown}
                    placeholder="192.168.1.x"
                    class="w-full px-4 py-3 rounded-xl bg-iris-bg border border-surface-border text-iris-text text-center text-lg outline-none focus:border-iris-accent transition"
                    autoFocus
                />
                ${error && html`<p class="text-red-400 text-sm mt-3">${error}</p>`}
                <button
                    onClick=${handleConnect}
                    disabled=${busy}
                    class="w-full mt-4 py-3 rounded-xl bg-iris-accent hover:bg-indigo-500 text-white font-semibold transition disabled:opacity-50"
                >
                    ${busy ? 'Connecting...' : 'Connect'}
                </button>
                <p class="text-iris-dim text-xs mt-4">You may need to press the link button on your bridge</p>
            </div>
        </div>
    `;
}
