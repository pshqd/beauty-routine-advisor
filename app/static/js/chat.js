let conversationHistory = [];
const messagesContainer = document.getElementById("messages");
const userInput = document.getElementById("user-input");
const sendButton = document.getElementById("send-button");

document.addEventListener("DOMContentLoaded", () => {
  addMessage(
    "Привет! Я AI-консультант по уходу за кожей. Расскажите о ваших проблемах или типе кожи.",
    "assistant",
  );

  userInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });
});

async function sendMessage() {
  const message = userInput.value.trim();
  if (!message) return;

  const welcomeMsg = document.querySelector(".welcome-message");
  if (welcomeMsg) welcomeMsg.remove();

  addMessage(message, "user");
  userInput.value = "";
  setLoading(true);

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: message,
        conversation_history: conversationHistory,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();

    // Рендерим ответ вместе с источниками
    addMessage(data.response, "assistant", data.sources || []);

    conversationHistory.push(
      { role: "user", content: message },
      { role: "assistant", content: data.response },
    );
  } catch (error) {
    console.error("Error:", error);
    addMessage(
      "Ошибка. Проверьте, что backend и LM Studio запущены.",
      "system",
    );
  } finally {
    setLoading(false);
  }
}

/**
 * Добавляет сообщение в чат.
 * @param {string} text    - Текст сообщения
 * @param {string} role    - 'user' | 'assistant' | 'system'
 * @param {Array}  sources - Массив объектов источников (только для assistant)
 */
function addMessage(text, role, sources = []) {
  const wrapper = document.createElement("div");
  wrapper.className = `message-wrapper ${role}`;

  // Пузырь с текстом
  const messageDiv = document.createElement("div");
  messageDiv.className = `message ${role}${role === "assistant" ? " message-content markdown-body" : ""}`;
  messageDiv.textContent = text;
  wrapper.appendChild(messageDiv);

  // Источники — только для assistant и только если есть
  if (role === "assistant" && sources.length > 0) {
    wrapper.appendChild(renderSources(sources));
  }

  messagesContainer.appendChild(wrapper);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

/**
 * Строит блок источников в виде раскрывающихся карточек-статей.
 * @param {Array} sources
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
    summary.innerHTML = `
            <span class="source-icon">📄</span>
            <span class="source-title">${escapeHtml(src.title)}</span>
            ${
              src.score > 0
                ? `<span class="source-score">${Math.round(src.score * 100)}%</span>`
                : ""
            }
        `;
    card.appendChild(summary);

    const body = document.createElement("div");
    body.className = "source-body";

    if (src.preview) {
      const preview = document.createElement("p");
      preview.className = "source-preview";
      preview.innerHTML = window.renderMarkdown(src.preview);
      body.appendChild(preview);
    }

    if (src.file) {
      const file = document.createElement("span");
      file.className = "source-file";
      file.textContent = src.file;
      body.appendChild(file);
    }

    card.appendChild(body);
    block.appendChild(card);
  });

  return block;
}

/** Экранирует HTML-спецсимволы в тексте. */
function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function setLoading(isLoading) {
  sendButton.disabled = isLoading;
  userInput.disabled = isLoading;

  if (isLoading) {
    const loadingDiv = document.createElement("div");
    loadingDiv.className = "loading";
    loadingDiv.id = "loading-indicator";
    loadingDiv.innerHTML = `
            <div class="typing-dots">
                <span></span><span></span><span></span>
            </div>
            <p>Агент анализирует...</p>
        `;
    messagesContainer.appendChild(loadingDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  } else {
    const loadingDiv = document.getElementById("loading-indicator");
    if (loadingDiv) loadingDiv.remove();
  }
}
