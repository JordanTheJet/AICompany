"""Tests for Instagram integration"""

import pytest
from src.integrations import InstagramIntegration


@pytest.mark.asyncio
async def test_instagram_integration_init():
    """Test Instagram integration initialization"""
    integration = InstagramIntegration()
    assert integration is not None
    assert integration.authenticated is False


@pytest.mark.asyncio
async def test_instagram_required_credentials():
    """Test required credentials list"""
    integration = InstagramIntegration()
    required = integration.get_required_credentials()
    assert "username" in required
    assert "password" in required


@pytest.mark.asyncio
async def test_instagram_platform_name():
    """Test platform name"""
    integration = InstagramIntegration()
    assert integration.get_platform_name() == "instagram"


@pytest.mark.asyncio
async def test_instagram_text_only_not_supported():
    """Test that text-only posts are not supported"""
    integration = InstagramIntegration()
    result = await integration.post_text("Test text")
    assert result["success"] is False
    assert "does not support text-only posts" in result["error"]


@pytest.mark.asyncio
async def test_instagram_health_check():
    """Test health check"""
    integration = InstagramIntegration()
    health = await integration.health_check()
    assert "platform" in health
    assert health["platform"] == "instagram"
    assert "authenticated" in health
    assert "status" in health


# Note: The following tests require valid credentials
# They are marked to skip unless credentials are available

@pytest.mark.skip(reason="Requires valid Instagram credentials")
@pytest.mark.asyncio
async def test_instagram_authentication():
    """Test authentication with real credentials"""
    integration = InstagramIntegration()
    result = await integration.authenticate()
    assert result is True
    assert integration.authenticated is True


@pytest.mark.skip(reason="Requires valid Instagram credentials and media file")
@pytest.mark.asyncio
async def test_instagram_post_image():
    """Test posting an image"""
    integration = InstagramIntegration()
    await integration.authenticate()

    result = await integration.post_media(
        media_paths=["test_image.jpg"],
        caption="Test post from AICompany"
    )
    assert result["success"] is True
    assert "post_id" in result
    assert "post_url" in result
