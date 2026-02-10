import { html, React } from '../lib.js';
import { BridgeProvider, useBridge } from '../state.js';
import ConnectionModal from './ConnectionModal.js';
import Header from './Header.js';
import DeviceGrid from './DeviceGrid.js';
import LightModal from './LightModal.js';
import GroupModal from './GroupModal.js';
import ScreenSaver from './ScreenSaver.js';

const { useState, useEffect, useCallback } = React;

function AppInner() {
    const { connected, checkStatus, refresh } = useBridge();

    const [lightModal, setLightModal] = useState(null);   // { id, type }
    const [showGroupModal, setShowGroupModal] = useState(false);

    useEffect(() => {
        (async () => {
            const wasConnected = await checkStatus();
            if (wasConnected) await refresh();
        })();
    }, [checkStatus, refresh]);

    const openSettings = useCallback((id, type) => {
        setLightModal({ id, type });
    }, []);

    return html`
        <div class="min-h-screen flex flex-col">
            <${ScreenSaver} />
            <${ConnectionModal} />
            ${connected && html`
                <${Header} onAddRoom=${() => setShowGroupModal(true)} />
                <${DeviceGrid} onSettings=${openSettings} />
            `}
            ${lightModal && html`
                <${LightModal}
                    deviceId=${lightModal.id}
                    deviceType=${lightModal.type}
                    onClose=${() => setLightModal(null)}
                />
            `}
            ${showGroupModal && html`
                <${GroupModal} onClose=${() => setShowGroupModal(false)} />
            `}
        </div>
    `;
}

export default function App() {
    return html`
        <${BridgeProvider}>
            <${AppInner} />
        </${BridgeProvider}>
    `;
}
