// ============================================================
// chat.js — SkinCare Advisor Frontend
// ============================================================

let conversationHistory = [];
const messagesContainer = document.getElementById("messages");
const userInput = document.getElementById("user-input");
const sendButton = document.getElementById("send-button");

// ── Инициализация ───────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
    addMessage(
        "Привет! 👋 Я AI-консультант по уходу за кожей. Расскажите о ваших проблемах или типе кожи.",
        "assistant"
    );

    userInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Автоматически растягивать textarea при наборе
    userInput.addEventListener("input", () => {
        userInput.style.height = "auto";
        userInput.style.height = Math.min(userInput.scrollHeight, 160) + "px";
    });
});

// ── Отправка сообщения ──────────────────────────────────────
async function sendMessage() {
    const message = userInput.value.trim();
    if (!message) return;

    // Убираем welcome-заглушку если есть
    const welcomeMsg = document.querySelector(".welcome-message");
    if (welcomeMsg) welcomeMsg.remove();

    addMessage(message, "user");
    userInput.value = "";
    userInput.style.height = "auto";
    setLoading(true);

    try {
        const response = await fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                message,
                conversation_history: conversationHistory,
            }),
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        if (!data.response) {
            throw new Error("Empty response from server");
        }

        addMessage(data.response, "assistant", data.sources || []);

        conversationHistory.push(
            { role: "user",      content: message       },
            { role: "assistant", content: data.response }
        );

    } catch (error) {
        console.error("sendMessage error:", error);
        addMessage(
            "❌ Ошибка соединения. Проверьте, что backend запущен.",
            "system"
        );
    } finally {
        setLoading(false);
    }
}

// ── Добавление сообщения в чат ──────────────────────────────
/**
 * @param {string} text    — текст / markdown
 * @param {string} role    — 'user' | 'assistant' | 'system'
 * @param {Array}  sources — источники из RAG (только для assistant)
 */
function addMessage(text, role, sources = []) {
    const wrapper = document.createElement("div");
    wrapper.className = `message-wrapper ${role}`;

    const bubble = document.createElement("div");
    bubble.className = `message ${role}`;

    if (role === "assistant") {
        // Рендерим markdown, оборачиваем в .markdown-body для стилей
        bubble.classList.add("message-content", "markdown-body");
        bubble.innerHTML = window.renderMarkdown(text);

        // Открывать внешние ссылки в новой вкладке
        bubble.querySelectorAll("a").forEach((a) => {
            a.setAttribute("target", "_blank");
            a.setAttribute("rel", "noopener noreferrer");
        });
    } else if (role === "system") {
        bubble.textContent = text;
    } else {
        // user — plain text, экранируем XSS
        bubble.textContent = text;
    }

    wrapper.appendChild(bubble);

    // Источники RAG — только для assistant
    if (role === "assistant" && sources.length > 0) {
        wrapper.appendChild(renderSources(sources));
    }

    messagesContainer.appendChild(wrapper);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// ── Блок источников RAG ─────────────────────────────────────
/**
 * @param {Array} sources — [{title, file, preview, score}]
 * @returns {HTMLElement}
 */
function renderSources(sources) {
    const block = document.createElement("div");
    block.className = "sources-block";

    const label = document.createElement("p");
    label.className = "sources-label";
    label.textContent = "📚 Источники из базы знаний";
    block.appendChild(label);

    sources.forEach((src) => {
        const card = document.createElement("details");
        card.className = "source-card";

        const summary = document.createElement("summary");
        summary.className = "source-summary";
        summary.innerHTML = [
            `<span class="source-icon">📄</span>`,
            `<span class="source-title">${escapeHtml(src.title || "Без названия")}</span>`,
            src.score > 0
                ? `<span class="source-score">${Math.round(src.score * 100)}%</span>`
                : "",
        ].join("");
        card.appendChild(summary);

        const body = document.createElement("div");
        body.className = "source-body";

        if (src.preview) {
            const preview = document.createElement("div");
            preview.className = "source-preview markdown-body";
            // preview тоже может содержать markdown
            preview.innerHTML = window.renderMarkdown(src.preview);
            body.appendChild(preview);
        }

        if (src.file) {
            const file = document.createElement("span");
            file.className = "source-file";
            file.textContent = `📁 ${src.file}`;
            body.appendChild(file);
        }

        card.appendChild(body);
        block.appendChild(card);
    });

    return block;
}

// ── Утилиты ─────────────────────────────────────────────────
function escapeHtml(str) {
    return String(str)
        .replace(/&/g,  "&amp;")
        .replace(/</g,  "&lt;")
        .replace(/>/g,  "&gt;")
        .replace(/"/g,  "&quot;")
        .replace(/'/g,  "&#039;");
}

function setLoading(isLoading) {
    sendButton.disabled = isLoading;
    userInput.disabled  = isLoading;

    if (isLoading) {
        const loader = document.createElement("div");
        loader.className = "loading";
        loader.id = "loading-indicator";
        loader.innerHTML = `
            <div class="typing-dots">
                <span></span><span></span><span></span>
            </div>
            <p>Агент анализирует...</p>
        `;
        messagesContainer.appendChild(loader);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    } else {
        document.getElementById("loading-indicator")?.remove();
    }
}