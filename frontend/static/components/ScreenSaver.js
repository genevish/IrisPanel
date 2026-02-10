/**
 * ScreenSaver — dims after 1 min, goes dark after 5 min.
 * Wakes instantly on touch/mouse/key interaction.
 */
import { html, React } from '../lib.js';

const { useState, useEffect, useRef, useCallback } = React;

const DIM_AFTER = 120;   // seconds
const DARK_AFTER = 600;  // seconds

export default function ScreenSaver() {
    const [state, setState] = useState('awake'); // 'awake' | 'dim' | 'dark'
    const lastActivity = useRef(Date.now());

    const wake = useCallback(() => {
        lastActivity.current = Date.now();
        setState('awake');
    }, []);

    useEffect(() => {
        const events = ['touchstart', 'mousedown', 'keydown'];
        events.forEach(e => window.addEventListener(e, wake, { passive: true }));

        const timer = setInterval(() => {
            const elapsed = (Date.now() - lastActivity.current) / 1000;
            if (elapsed >= DARK_AFTER) setState('dark');
            else if (elapsed >= DIM_AFTER) setState('dim');
        }, 1000);

        return () => {
            events.forEach(e => window.removeEventListener(e, wake));
            clearInterval(timer);
        };
    }, [wake]);

    if (state === 'awake') return null;

    // dim: pointer-events-none so taps pass through to UI and also wake
    // dark: pointer-events-auto so the overlay captures the tap (wake only, no UI action)
    return html`
        <div
            class="fixed inset-0 bg-black transition-opacity duration-700"
            style=${{
                opacity: state === 'dark' ? 1 : 0.7,
                zIndex: 9999,
                pointerEvents: state === 'dark' ? 'auto' : 'none',
            }}
        />
    `;
}
