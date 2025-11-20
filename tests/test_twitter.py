"""Tests for Twitter integration"""

import pytest
from src.integrations import TwitterIntegration


@pytest.mark.asyncio
async def test_twitter_integration_init():
    """Test Twitter integration initialization"""
    integration = TwitterIntegration()
    assert integration is not None
    assert integration.authenticated is False


@pytest.mark.asyncio
async def test_twitter_required_credentials():
    """Test required credentials list"""
    integration = TwitterIntegration()
    required = integration.get_required_credentials()
    assert "api_key" in required
    assert "api_secret" in required
    assert "access_token" in required
    assert "access_token_secret" in required


@pytest.mark.asyncio
async def test_twitter_platform_name():
    """Test platform name"""
    integration = TwitterIntegration()
    assert integration.get_platform_name() == "twitter"


@pytest.mark.asyncio
async def test_twitter_health_check():
    """Test health check"""
    integration = TwitterIntegration()
    health = await integration.health_check()
    assert "platform" in health
    assert health["platform"] == "twitter"
    assert "authenticated" in health
    assert "status" in health


# Note: The following tests require valid credentials
# They are marked to skip unless credentials are available

@pytest.mark.skip(reason="Requires valid Twitter credentials")
@pytest.mark.asyncio
async def test_twitter_authentication():
    """Test authentication with real credentials"""
    integration = TwitterIntegration()
    result = await integration.authenticate()
    assert result is True
    assert integration.authenticated is True


@pytest.mark.skip(reason="Requires valid Twitter credentials")
@pytest.mark.asyncio
async def test_twitter_post_text():
    """Test posting a tweet"""
    integration = TwitterIntegration()
    await integration.authenticate()

    result = await integration.post_text("Test tweet from AICompany")
    assert result["success"] is True
    assert "post_id" in result
    assert "post_url" in result
