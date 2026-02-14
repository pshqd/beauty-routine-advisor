let conversationHistory = [];
const messagesContainer = document.getElementById('messages');
const userInput = document.getElementById('user-input');
const sendButton = document.getElementById('send-button');

document.addEventListener('DOMContentLoaded', () => {
    addMessage(
        'Привет! 👋 Я AI-консультант по уходу за кожей. Расскажите о ваших проблемах или типе кожи.',
        'assistant'
    );
    
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
});

async function sendMessage() {
    const message = userInput.value.trim();
    if (!message) return;
    
    addMessage(message, 'user');
    userInput.value = '';
    setLoading(true);
    
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                conversation_history: conversationHistory
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        addMessage(data.response, 'assistant');
        
        conversationHistory.push(
            { role: 'user', content: message },
            { role: 'assistant', content: data.response }
        );
        
    } catch (error) {
        console.error('Error:', error);
        addMessage(
            '❌ Ошибка. Проверьте, что backend и LM Studio запущены.',
            'system'
        );
    } finally {
        setLoading(false);
    }
}

function addMessage(text, role) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    messageDiv.textContent = text;
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function setLoading(isLoading) {
    sendButton.disabled = isLoading;
    userInput.disabled = isLoading;
    
    if (isLoading) {
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'loading';
        loadingDiv.id = 'loading-indicator';
        loadingDiv.innerHTML = `
            <div class="typing-dots">
                <span></span>
                <span></span>
                <span></span>
            </div>
            <p>Агент анализирует...</p>
        `;
        messagesContainer.appendChild(loadingDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    } else {
        const loadingDiv = document.getElementById('loading-indicator');
        if (loadingDiv) loadingDiv.remove();
    }
}
