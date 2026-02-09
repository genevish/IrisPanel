/**
 * BridgeContext — global state for connection, lights, groups.
 */
import { html, React } from './lib.js';
import { api } from './api.js';

const { createContext, useContext, useState, useCallback, useRef, useEffect } = React;

const BridgeContext = createContext(null);

export function useBridge() {
    return useContext(BridgeContext);
}

export function BridgeProvider({ children }) {
    const [connected, setConnected] = useState(false);
    const [bridgeIp, setBridgeIp] = useState(null);
    const [savedIp, setSavedIp] = useState(null);
    const [lights, setLights] = useState({});
    const [groups, setGroups] = useState({});
    const [roomClasses, setRoomClasses] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [initialChecked, setInitialChecked] = useState(false);
    const debounceRef = useRef(null);

    const checkStatus = useCallback(async () => {
        try {
            const status = await api('/api/status');
            setConnected(status.connected);
            setBridgeIp(status.bridge_ip);
            setSavedIp(status.saved_ip);
            return status.connected;
        } catch {
            return false;
        } finally {
            setInitialChecked(true);
        }
    }, []);

    const refresh = useCallback(async (silent = false) => {
        if (!silent) setLoading(true);
        setError(null);
        try {
            const [l, g, rc] = await Promise.all([
                api('/api/lights'),
                api('/api/groups'),
                api('/api/room-classes'),
            ]);
            setLights(l);
            setGroups(g);
            setRoomClasses(rc);
        } catch (e) {
            console.error('Failed to load data:', e);
            setError(e.message || 'Failed to load lights');
        } finally {
            if (!silent) setLoading(false);
        }
    }, []);

    const connect = useCallback(async (ip) => {
        await api('/api/connect', {
            method: 'POST',
            body: JSON.stringify({ ip }),
        });
        setConnected(true);
        setBridgeIp(ip);
        await refresh();
    }, [refresh]);

    const toggleLight = useCallback(async (id) => {
        setLights(prev => {
            const light = prev[id];
            if (!light) return prev;
            return { ...prev, [id]: { ...light, on: !light.on } };
        });
        const light = lights[id];
        if (!light) return;
        try {
            await api(`/api/lights/${id}`, {
                method: 'PUT',
                body: JSON.stringify({ on: !light.on }),
            });
        } catch {
            setLights(prev => ({ ...prev, [id]: { ...prev[id], on: light.on } }));
        }
    }, [lights]);

    const toggleGroup = useCallback(async (id) => {
        const group = groups[id];
        if (!group) return;
        const newOn = !group.on;

        setGroups(prev => ({ ...prev, [id]: { ...prev[id], on: newOn } }));
        // Optimistically update member lights
        setLights(prev => {
            const next = { ...prev };
            (group.lights || []).forEach(lid => {
                const numId = parseInt(lid);
                if (next[numId]) next[numId] = { ...next[numId], on: newOn };
            });
            return next;
        });

        try {
            await api(`/api/groups/${id}`, {
                method: 'PUT',
                body: JSON.stringify({ on: newOn }),
            });
        } catch {
            setGroups(prev => ({ ...prev, [id]: { ...prev[id], on: !newOn } }));
        }
    }, [groups]);

    const updateLight = useCallback((id, data, debounce = false) => {
        // Optimistic local update
        setLights(prev => ({ ...prev, [id]: { ...prev[id], ...data } }));

        const send = async () => {
            try {
                await api(`/api/lights/${id}`, {
                    method: 'PUT',
                    body: JSON.stringify(data),
                });
            } catch (e) {
                console.error('Failed to update light:', e);
            }
        };

        if (debounce) {
            clearTimeout(debounceRef.current);
            debounceRef.current = setTimeout(() => {
                debounceRef.current = null;
                send();
            }, 150);
        } else {
            send();
        }
    }, []);

    const updateGroup = useCallback((id, data, debounce = false) => {
        setGroups(prev => ({ ...prev, [id]: { ...prev[id], ...data } }));

        // If color change, also update member lights
        if (data.hue !== undefined && data.sat !== undefined) {
            setLights(prev => {
                const group = groups[id];
                if (!group) return prev;
                const next = { ...prev };
                (group.lights || []).forEach(lid => {
                    const numId = parseInt(lid);
                    if (next[numId] && next[numId].has_color) {
                        next[numId] = { ...next[numId], hue: data.hue, sat: data.sat };
                    }
                });
                return next;
            });
        }

        const send = async () => {
            try {
                await api(`/api/groups/${id}`, {
                    method: 'PUT',
                    body: JSON.stringify(data),
                });
            } catch (e) {
                console.error('Failed to update group:', e);
            }
        };

        if (debounce) {
            clearTimeout(debounceRef.current);
            debounceRef.current = setTimeout(() => {
                debounceRef.current = null;
                send();
            }, 150);
        } else {
            send();
        }
    }, [groups]);

    const createGroup = useCallback(async (name, selectedLights, roomClass) => {
        await api('/api/groups', {
            method: 'POST',
            body: JSON.stringify({ name, lights: selectedLights, room_class: roomClass }),
        });
        await refresh();
    }, [refresh]);

    const deleteGroup = useCallback(async (id) => {
        await api(`/api/groups/${id}`, { method: 'DELETE' });
        await refresh();
    }, [refresh]);

    const updateGroupSettings = useCallback(async (id, data) => {
        await api(`/api/groups/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
        await refresh();
    }, [refresh]);

    // Auto-refresh every 3s when connected; skip if a debounced update is in flight
    useEffect(() => {
        if (!connected) return;
        const id = setInterval(() => {
            if (debounceRef.current) return;
            refresh(true);
        }, 3000);
        return () => clearInterval(id);
    }, [connected, refresh]);

    const value = {
        connected, bridgeIp, savedIp, lights, groups, roomClasses,
        loading, error, initialChecked,
        checkStatus, connect, refresh,
        toggleLight, toggleGroup, updateLight, updateGroup,
        createGroup, deleteGroup, updateGroupSettings,
    };

    return html`<${BridgeContext.Provider} value=${value}>${children}</${BridgeContext.Provider}>`;
}
