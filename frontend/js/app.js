(function () {
    const chatMessages = document.getElementById('chatMessages');
    const chatInput = document.getElementById('chatInput');
    const sendBtn = document.getElementById('sendBtn');
    const codeContent = document.getElementById('codeContent');
    const settingsBtn = document.getElementById('settingsBtn');
    const settingsOverlay = document.getElementById('settingsOverlay');
    const settingsClose = document.getElementById('settingsClose');
    const saveSettingsBtn = document.getElementById('saveSettingsBtn');
    const endpointInput = document.getElementById('endpointInput');
    const modelInput = document.getElementById('modelInput');
    const apiKeyInput = document.getElementById('apiKeyInput');
    const exportStlBtn = document.getElementById('exportStlBtn');
    const exportStepBtn = document.getElementById('exportStepBtn');

    let isProcessing = false;

    async function loadSettings() {
        try {
            const res = await fetch('/api/settings');
            const data = await res.json();
            endpointInput.value = data.endpoint || '';
            modelInput.value = data.model || '';
            apiKeyInput.value = data.api_key || '';
        } catch (e) {
            console.error('Failed to load settings:', e);
        }
    }

    async function saveSettings() {
        const payload = {
            endpoint: endpointInput.value.trim(),
            model: modelInput.value.trim(),
            api_key: apiKeyInput.value || null,
        };
        try {
            await fetch('/api/settings', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
            settingsOverlay.classList.remove('active');
        } catch (e) {
            console.error('Failed to save settings:', e);
        }
    }

    function addMessage(text, type) {
        const div = document.createElement('div');
        div.className = `chat-msg ${type}`;
        div.textContent = text;
        chatMessages.appendChild(div);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return div;
    }

    function updateCode(code) {
        codeContent.textContent = code;
    }

    async function sendMessage() {
        const text = chatInput.value.trim();
        if (!text || isProcessing) return;

        isProcessing = true;
        chatInput.value = '';
        addMessage(text, 'user');
        const loadingMsg = addMessage('Thinking...', 'loading');

        try {
            const res = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text }),
            });

            if (!res.ok) {
                const err = await res.json().catch(() => ({ detail: res.statusText }));
                loadingMsg.remove();
                addMessage(`Error: ${err.detail || 'Request failed'}`, 'error');
                return;
            }

            const data = await res.json();
            loadingMsg.remove();
            addMessage(data.response || 'Model generated.', 'assistant');
            updateCode(data.code);

            if (data.obj) {
                window.loadObj(data.obj);
            }
        } catch (e) {
            loadingMsg.remove();
            addMessage(`Error: ${e.message}`, 'error');
        } finally {
            isProcessing = false;
            chatInput.focus();
        }
    }

    function exportModel(fmt) {
        fetch('/api/export', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ fmt }),
        })
        .then(res => {
            if (!res.ok) throw new Error('Export failed');
            return res.blob();
        })
        .then(blob => {
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `model.${fmt}`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        })
        .catch(e => addMessage(`Export error: ${e.message}`, 'error'));
    }

    sendBtn.addEventListener('click', sendMessage);
    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') sendMessage();
    });
    settingsBtn.addEventListener('click', () => settingsOverlay.classList.add('active'));
    settingsClose.addEventListener('click', () => settingsOverlay.classList.remove('active'));
    settingsOverlay.addEventListener('click', (e) => {
        if (e.target === settingsOverlay) settingsOverlay.classList.remove('active');
    });
    saveSettingsBtn.addEventListener('click', saveSettings);
    exportStlBtn.addEventListener('click', () => exportModel('stl'));
    exportStepBtn.addEventListener('click', () => exportModel('step'));

    loadSettings();
    chatInput.focus();
})();
