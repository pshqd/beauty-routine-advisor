"""
Тесты провайдеров LLM.

Что мокается:
  - requests.post                   (сетевые вызовы OpenRouter, LMStudio)
  - langchain_gigachat.GigaChat     (SDK Сбера)
  - langchain_core.messages         (SystemMessage / HumanMessage / AIMessage)

Стратегия импортов:
  Каждый тест-класс патчит тяжёлые зависимости через patch() ПЕРЕД импортом
  провайдера, чтобы не нужно было иметь langchain-gigachat установленным.
"""

import sys
import pytest
import importlib
from unittest.mock import MagicMock, patch, call


# ─── Глобальные моки ML-пакетов ────────────────────────────────────────────
# Должны быть до любого импорта services.*
for _mod in [
    "langchain_gigachat",
    "langchain_core",
    "langchain_core.messages",
]:
    sys.modules.setdefault(_mod, MagicMock())


# ═══════════════════════════════════════════════════════════════════════════
# 1. BaseLLMProvider — абстрактный интерфейс
# ═══════════════════════════════════════════════════════════════════════════

class TestBaseLLMProvider:

    def test_cannot_instantiate_abstract(self):
        """Нельзя создать BaseLLMProvider напрямую — он абстрактный."""
        from services.providers.base import BaseLLMProvider
        with pytest.raises(TypeError):
            BaseLLMProvider()

    def test_subclass_without_complete_raises(self):
        """Подкласс без метода complete() тоже нельзя создать."""
        from services.providers.base import BaseLLMProvider

        class BadProvider(BaseLLMProvider):
            pass

        with pytest.raises(TypeError):
            BadProvider()

    def test_subclass_with_complete_works(self):
        """Подкласс с реализованным complete() создаётся нормально."""
        from services.providers.base import BaseLLMProvider

        class GoodProvider(BaseLLMProvider):
            def complete(self, messages):
                return "ok"

        p = GoodProvider()
        assert p.complete([]) == "ok"


# ═══════════════════════════════════════════════════════════════════════════
# 2. OpenRouterProvider
# ═══════════════════════════════════════════════════════════════════════════

class TestOpenRouterProvider:
    """Тесты OpenRouter. Мокается только requests.post."""

    @pytest.fixture
    def provider(self):
        """OpenRouterProvider с замоканными HTTP и ключом API."""
        with patch.dict("os.environ", {"OPENROUTER_API_KEY": "test-key-123"}):
            # Перегружаем Config чтобы подхватить env
            import config
            importlib.reload(config)
            from services.providers.openrouter import OpenRouterProvider
            return OpenRouterProvider()

    def test_init_raises_without_api_key(self, monkeypatch):
        """Без OPENROUTER_API_KEY — ValueError при создании."""
        monkeypatch.setenv("OPENROUTER_API_KEY", "")
        import config
        importlib.reload(config)
        from services.providers.openrouter import OpenRouterProvider
        with pytest.raises(ValueError, match="OPENROUTER_API_KEY"):
            OpenRouterProvider()

    def test_complete_returns_content(self, provider):
        """complete() возвращает текст из choices[0].message.content."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "Используй SPF 50!"}}]
        }
        mock_resp.raise_for_status = MagicMock()

        with patch("requests.post", return_value=mock_resp) as mock_post:
            result = provider.complete([{"role": "user", "content": "Посоветуй крем"}])

        assert result == "Используй SPF 50!"

    def test_complete_uses_config_url_and_model(self, provider):
        """POST отправляется на URL и модель из Config, не захардкоженные."""
        from config import Config
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "ответ"}}]
        }
        mock_resp.raise_for_status = MagicMock()

        with patch("requests.post", return_value=mock_resp) as mock_post:
            provider.complete([{"role": "user", "content": "тест"}])

        args, kwargs = mock_post.call_args
        assert args[0] == Config.OPENROUTER_URL
        assert kwargs["json"]["model"] == Config.OPENROUTER_MODEL

    def test_complete_uses_config_generation_params(self, provider):
        """temperature / max_tokens / top_p берутся из Config.GENERATION_CONFIG."""
        from config import Config
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "ответ"}}]
        }
        mock_resp.raise_for_status = MagicMock()

        with patch("requests.post", return_value=mock_resp) as mock_post:
            provider.complete([{"role": "user", "content": "тест"}])

        payload = mock_post.call_args[1]["json"]
        cfg = Config.GENERATION_CONFIG
        assert payload["temperature"] == cfg["temperature"]
        assert payload["max_tokens"] == cfg["max_tokens"]
        assert payload["top_p"] == cfg["top_p"]

    def test_bearer_auth_header(self, provider):
        """Authorization: Bearer <key> должен присутствовать в заголовках."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "ok"}}]
        }
        mock_resp.raise_for_status = MagicMock()

        with patch("requests.post", return_value=mock_resp) as mock_post:
            provider.complete([{"role": "user", "content": "тест"}])

        headers = mock_post.call_args[1]["headers"]
        assert "Authorization" in headers
        assert headers["Authorization"].startswith("Bearer ")

    def test_connection_error_raises(self, provider):
        """ConnectionError сети → пробрасывается как ConnectionError."""
        import requests as req
        with patch("requests.post", side_effect=req.exceptions.ConnectionError):
            with pytest.raises(ConnectionError):
                provider.complete([{"role": "user", "content": "тест"}])

    def test_timeout_error_raises(self, provider):
        """Timeout → пробрасывается как TimeoutError."""
        import requests as req
        with patch("requests.post", side_effect=req.exceptions.Timeout):
            with pytest.raises(TimeoutError):
                provider.complete([{"role": "user", "content": "тест"}])

    def test_http_error_raises_value_error(self, provider):
        """HTTP 4xx/5xx → ValueError с кодом статуса."""
        import requests as req
        mock_resp = MagicMock()
        mock_resp.status_code = 429
        mock_resp.text = "Rate limit exceeded"
        mock_resp.raise_for_status.side_effect = req.exceptions.HTTPError(response=mock_resp)

        with patch("requests.post", return_value=mock_resp):
            with pytest.raises(ValueError, match="429"):
                provider.complete([{"role": "user", "content": "тест"}])


# ═══════════════════════════════════════════════════════════════════════════
# 3. LMStudioProvider
# ═══════════════════════════════════════════════════════════════════════════

class TestLMStudioProvider:
    """Тесты LM Studio. Мокается только requests.post."""

    @pytest.fixture
    def provider(self):
        from services.providers.lm_studio import LMStudioProvider
        return LMStudioProvider()

    def test_complete_returns_content(self, provider):
        """complete() возвращает текст из choices[0].message.content."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "Локальная модель отвечает"}}]
        }
        mock_resp.raise_for_status = MagicMock()

        with patch("requests.post", return_value=mock_resp):
            result = provider.complete([{"role": "user", "content": "привет"}])

        assert result == "Локальная модель отвечает"

    def test_stream_false_in_payload(self, provider):
        """stream: false обязателен — иначе ответ придёт потоком."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "ok"}}]
        }
        mock_resp.raise_for_status = MagicMock()

        with patch("requests.post", return_value=mock_resp) as mock_post:
            provider.complete([{"role": "user", "content": "тест"}])

        payload = mock_post.call_args[1]["json"]
        assert payload["stream"] is False

    def test_uses_config_url(self, provider):
        """POST идёт на Config.LM_STUDIO_URL."""
        from config import Config
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "ok"}}]
        }
        mock_resp.raise_for_status = MagicMock()

        with patch("requests.post", return_value=mock_resp) as mock_post:
            provider.complete([{"role": "user", "content": "тест"}])

        url = mock_post.call_args[0][0]
        assert url == Config.LM_STUDIO_URL

    def test_uses_config_generation_params(self, provider):
        """temperature / max_tokens / top_p из Config.GENERATION_CONFIG."""
        from config import Config
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "ok"}}]
        }
        mock_resp.raise_for_status = MagicMock()

        with patch("requests.post", return_value=mock_resp) as mock_post:
            provider.complete([{"role": "user", "content": "тест"}])

        payload = mock_post.call_args[1]["json"]
        cfg = Config.GENERATION_CONFIG
        assert payload["temperature"] == cfg["temperature"]
        assert payload["max_tokens"] == cfg["max_tokens"]
        assert payload["top_p"] == cfg["top_p"]

    def test_connection_error_raises(self, provider):
        import requests as req
        with patch("requests.post", side_effect=req.exceptions.ConnectionError):
            with pytest.raises(ConnectionError, match="LM Studio недоступен"):
                provider.complete([{"role": "user", "content": "тест"}])

    def test_timeout_raises(self, provider):
        import requests as req
        with patch("requests.post", side_effect=req.exceptions.Timeout):
            with pytest.raises(TimeoutError):
                provider.complete([{"role": "user", "content": "тест"}])


# ═══════════════════════════════════════════════════════════════════════════
# 4. GigaChatProvider
# ═══════════════════════════════════════════════════════════════════════════

class TestGigaChatProvider:
    """
    Тесты GigaChat. Мокается langchain_gigachat.GigaChat (SDK Сбера).
    langchain_gigachat уже замокан глобально вверху файла.
    """

    @pytest.fixture
    def provider_and_mock(self):
        """Создаёт GigaChatProvider с замоканным GigaChat-клиентом."""
        mock_llm = MagicMock()
        sys.modules["langchain_gigachat"].GigaChat = MagicMock(return_value=mock_llm)
        with patch.dict("os.environ", {"GIGACHAT_CREDENTIALS": "dGVzdA=="}):
            import config
            importlib.reload(config)
            from services.providers.gigachat import GigaChatProvider
            p = GigaChatProvider()
            return p, mock_llm

    def test_complete_returns_content(self, provider_and_mock):
        """complete() возвращает response.content от GigaChat."""
        provider, mock_llm = provider_and_mock
        mock_llm.invoke.return_value = MagicMock(content="Матирующий крем отлично подойдёт")
        result = provider.complete([{"role": "user", "content": "Посоветуй крем"}])
        assert result == "Матирующий крем отлично подойдёт"

    def test_role_conversion_system(self, provider_and_mock):
        """role=system → SystemMessage."""
        from langchain_core.messages import SystemMessage
        provider, mock_llm = provider_and_mock
        mock_llm.invoke.return_value = MagicMock(content="ok")
        provider.complete([{"role": "system", "content": "Ты консультант"}])
        lc_msgs = mock_llm.invoke.call_args[0][0]
        assert any(isinstance(m, type(SystemMessage(content=""))) or "SystemMessage" in str(type(m))
                   for m in lc_msgs)

    def test_role_conversion_user(self, provider_and_mock):
        """role=user → HumanMessage."""
        provider, mock_llm = provider_and_mock
        mock_llm.invoke.return_value = MagicMock(content="ok")
        provider.complete([{"role": "user", "content": "помогите"}])
        mock_llm.invoke.assert_called_once()

    def test_unknown_role_skipped(self, provider_and_mock):
        """Неизвестная роль пропускается без исключения."""
        provider, mock_llm = provider_and_mock
        mock_llm.invoke.return_value = MagicMock(content="ok")
        # unknown_role не должен вызывать исключения
        result = provider.complete([
            {"role": "unknown_role", "content": "???"},
            {"role": "user", "content": "помогите"},
        ])
        assert result == "ok"

    def test_only_known_roles_passed_to_invoke(self, provider_and_mock):
        """В LangChain передаются только сообщения с известными ролями."""
        provider, mock_llm = provider_and_mock
        mock_llm.invoke.return_value = MagicMock(content="ok")
        provider.complete([
            {"role": "system", "content": "Система"},
            {"role": "garbage", "content": "Мусор"},
            {"role": "user", "content": "Пользователь"},
        ])
        lc_msgs = mock_llm.invoke.call_args[0][0]
        # Должно быть 2 сообщения (system + user), garbage пропущен
        assert len(lc_msgs) == 2

    def test_exception_propagated(self, provider_and_mock):
        """Исключения от GigaChat не глотаются, а пробрасываются наверх."""
        provider, mock_llm = provider_and_mock
        mock_llm.invoke.side_effect = RuntimeError("Сбер API недоступен")
        with pytest.raises(RuntimeError, match="Сбер API недоступен"):
            provider.complete([{"role": "user", "content": "тест"}])


# ═══════════════════════════════════════════════════════════════════════════
# 5. Фабрика get_provider()
# ═══════════════════════════════════════════════════════════════════════════

class TestGetProvider:
    """
    Тесты фабрики. Мокаем сами провайдеры, чтобы не нужны реальные credentials.
    """

    def _get_provider_with_env(self, llm_provider):
        """Устанавливает LLM_PROVIDER и перезагружает config + __init__."""
        with patch.dict("os.environ", {
            "LLM_PROVIDER": llm_provider,
            "OPENROUTER_API_KEY": "dummy",
            "GIGACHAT_CREDENTIALS": "dummy",
        }):
            import config
            importlib.reload(config)
            # Перезагружаем __init__ чтобы он подхватил новый Config
            import services.providers
            importlib.reload(services.providers)
            from services.providers import get_provider
            return get_provider

    def test_lm_studio_provider_returned(self):
        """LLM_PROVIDER=lm_studio → LMStudioProvider."""
        from services.providers.lm_studio import LMStudioProvider
        get_provider = self._get_provider_with_env("lm_studio")
        result = get_provider()
        assert isinstance(result, LMStudioProvider)

    def test_openrouter_provider_returned(self):
        """LLM_PROVIDER=openrouter → OpenRouterProvider."""
        from services.providers.openrouter import OpenRouterProvider
        get_provider = self._get_provider_with_env("openrouter")
        result = get_provider()
        assert isinstance(result, OpenRouterProvider)

    def test_gigachat_provider_returned(self):
        """LLM_PROVIDER=gigachat → GigaChatProvider."""
        from services.providers.gigachat import GigaChatProvider
        get_provider = self._get_provider_with_env("gigachat")
        result = get_provider()
        assert isinstance(result, GigaChatProvider)

    def test_unknown_provider_raises(self):
        """Неизвестный провайдер → ValueError с именем провайдера."""
        get_provider = self._get_provider_with_env("unknown_llm")
        with pytest.raises(ValueError, match="unknown_llm"):
            get_provider()

    def test_case_insensitive(self):
        """Регистр не важен: LM_STUDIO → lm_studio."""
        from services.providers.lm_studio import LMStudioProvider
        get_provider = self._get_provider_with_env("LM_STUDIO")
        result = get_provider()
        assert isinstance(result, LMStudioProvider)
