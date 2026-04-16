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

        // Ответ ассистента — через Markdown
        addMessage(data.response, 'assistant');

        // Источники RAG — если есть
        if (data.sources && data.sources.length > 0) {
            addSources(data.sources);
        }

        conversationHistory.push(
            { role: 'user', content: message },
            { role: 'assistant', content: data.response }
        );

    } catch (error) {
        console.error('Error:', error);
        addMessage(
            '❌ Ошибка соединения. Проверьте, что backend запущен.',
            'system'
        );
    } finally {
        setLoading(false);
    }
}


/**
 * Добавляет сообщение в чат.
 *
 * - role === 'assistant' → рендерит Markdown через window.renderMarkdown
 * - role === 'user'      → вставляет как plain text (безопасно)
 * - role === 'system'    → plain text, стиль ошибки
 */
function addMessage(text, role) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message message-${role}`;

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    if (role === 'assistant') {
        // Markdown → HTML → DOMPurify → innerHTML
        contentDiv.className += ' markdown-body';
        contentDiv.innerHTML = window.renderMarkdown(text);
    } else {
        // user и system — plain text, XSS невозможен
        contentDiv.textContent = text;
    }

    messageDiv.appendChild(contentDiv);
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}


/**
 * Отображает блок источников RAG под ответом ассистента.
 * sources — массив строк вида "файл > раздел"
 */
function addSources(sources) {
    const sourcesDiv = document.createElement('div');
    sourcesDiv.className = 'message-sources';

    const title = document.createElement('p');
    title.className = 'sources-title';
    title.textContent = '📚 Источники:';

    const list = document.createElement('ul');
    sources.forEach(src => {
        const item = document.createElement('li');
        item.textContent = src;
        list.appendChild(item);
    });

    sourcesDiv.appendChild(title);
    sourcesDiv.appendChild(list);
    messagesContainer.appendChild(sourcesDiv);
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