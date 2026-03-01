# core/tests/test_http.py — Тесты для core.common.http
"""
Тесты модуля http:
- HttpClient.get()
- HttpClient.post()
- Retry logic
- Timeout handling
"""

import asyncio

import pytest

# Mock для aiohttp
try:
    from aioresponses import aioresponses
    AIORESPONSES_AVAILABLE = True
except ImportError:
    AIORESPONSES_AVAILABLE = False


class TestHttpClientImport:
    """Тесты импорта HttpClient."""
    
    def test_import_http_client(self):
        """Тест импорта HttpClient."""
        try:
            from common.http import HttpClient
            assert HttpClient is not None
        except ImportError:
            pytest.skip("aiohttp не установлен")


@pytest.mark.skipif(not AIORESPONSES_AVAILABLE, reason="aioresponses не установлен")
class TestHttpClientGet:
    """Тесты HttpClient.get()."""
    
    @pytest.mark.asyncio
    async def test_get_request(self):
        """Тест GET запроса."""
        try:
            from common.http import HttpClient
            
            with aioresponses() as m:
                # Мокаем ответ
                m.get("https://api.example.com/test", payload={"result": "success"})
                
                client = HttpClient()
                response = await client.get("https://api.example.com/test")
                
                assert response is not None
                assert response.get("result") == "success"
                
                await client.close()
        
        except ImportError:
            pytest.skip("aiohttp или HttpClient не доступен")
    
    @pytest.mark.asyncio
    async def test_get_with_params(self):
        """Тест GET запроса с параметрами."""
        try:
            from common.http import HttpClient
            
            with aioresponses() as m:
                m.get(
                    "https://api.example.com/search?q=test",
                    payload={"results": ["item1", "item2"]}
                )
                
                client = HttpClient()
                response = await client.get(
                    "https://api.example.com/search",
                    params={"q": "test"}
                )
                
                assert "results" in response
                assert len(response["results"]) == 2
                
                await client.close()
        
        except ImportError:
            pytest.skip("aiohttp или HttpClient не доступен")
    
    @pytest.mark.asyncio
    async def test_get_with_headers(self):
        """Тест GET запроса с заголовками."""
        try:
            from common.http import HttpClient
            
            with aioresponses() as m:
                m.get("https://api.example.com/auth", payload={"authenticated": True})
                
                client = HttpClient()
                response = await client.get(
                    "https://api.example.com/auth",
                    headers={"Authorization": "Bearer token123"}
                )
                
                assert response.get("authenticated") is True
                
                await client.close()
        
        except ImportError:
            pytest.skip("aiohttp или HttpClient не доступен")


@pytest.mark.skipif(not AIORESPONSES_AVAILABLE, reason="aioresponses не установлен")
class TestHttpClientPost:
    """Тесты HttpClient.post()."""
    
    @pytest.mark.asyncio
    async def test_post_request(self):
        """Тест POST запроса."""
        try:
            from common.http import HttpClient
            
            with aioresponses() as m:
                m.post("https://api.example.com/create", payload={"id": 1, "created": True})
                
                client = HttpClient()
                response = await client.post(
                    "https://api.example.com/create",
                    json={"name": "test"}
                )
                
                assert response.get("created") is True
                assert response.get("id") == 1
                
                await client.close()
        
        except ImportError:
            pytest.skip("aiohttp или HttpClient не доступен")
    
    @pytest.mark.asyncio
    async def test_post_with_data(self):
        """Тест POST запроса с данными."""
        try:
            from common.http import HttpClient
            
            with aioresponses() as m:
                m.post("https://api.example.com/submit", payload={"status": "ok"})
                
                client = HttpClient()
                response = await client.post(
                    "https://api.example.com/submit",
                    data={"field": "value"}
                )
                
                assert response.get("status") == "ok"
                
                await client.close()
        
        except ImportError:
            pytest.skip("aiohttp или HttpClient не доступен")


@pytest.mark.skipif(not AIORESPONSES_AVAILABLE, reason="aioresponses не установлен")
class TestHttpClientRetry:
    """Тесты retry логики."""
    
    @pytest.mark.asyncio
    async def test_retry_on_failure(self):
        """Тест retry при ошибке."""
        try:
            from common.http import HttpClient
            
            with aioresponses() as m:
                # Первые 2 запроса — ошибка, третий — успех
                m.get("https://api.example.com/retry", status=500)
                m.get("https://api.example.com/retry", status=500)
                m.get("https://api.example.com/retry", payload={"success": True})
                
                client = HttpClient(max_retries=3)
                response = await client.get("https://api.example.com/retry")
                
                assert response.get("success") is True
                
                await client.close()
        
        except ImportError:
            pytest.skip("aiohttp или HttpClient не доступен")


@pytest.mark.skipif(not AIORESPONSES_AVAILABLE, reason="aioresponses не установлен")
class TestHttpClientTimeout:
    """Тесты timeout handling."""
    
    @pytest.mark.asyncio
    async def test_timeout(self):
        """Тест таймаута запроса."""
        try:
            from common.http import HttpClient
            import aiohttp
            
            with aioresponses() as m:
                # Мокаем долгий ответ
                m.get(
                    "https://api.example.com/slow",
                    exception=asyncio.TimeoutError()
                )
                
                client = HttpClient(timeout=1)
                
                with pytest.raises((asyncio.TimeoutError, aiohttp.ClientError)):
                    await client.get("https://api.example.com/slow")
                
                await client.close()
        
        except ImportError:
            pytest.skip("aiohttp или HttpClient не доступен")


class TestHttpClientContextManager:
    """Тесты использования HttpClient как context manager."""
    
    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Тест использования HttpClient в async with."""
        try:
            from common.http import HttpClient
            
            with aioresponses() as m:
                m.get("https://api.example.com/test", payload={"data": "test"})
                
                async with HttpClient() as client:
                    response = await client.get("https://api.example.com/test")
                    assert response.get("data") == "test"
        
        except ImportError:
            pytest.skip("aiohttp или HttpClient не доступен")
