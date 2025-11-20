"""Tests for TikTok integration"""

import pytest
from src.integrations import TikTokIntegration


@pytest.mark.asyncio
async def test_tiktok_integration_init():
    """Test TikTok integration initialization"""
    integration = TikTokIntegration()
    assert integration is not None
    assert integration.authenticated is False


@pytest.mark.asyncio
async def test_tiktok_required_credentials():
    """Test required credentials list"""
    integration = TikTokIntegration()
    required = integration.get_required_credentials()
    assert "client_key" in required
    assert "client_secret" in required
    assert "access_token" in required


@pytest.mark.asyncio
async def test_tiktok_platform_name():
    """Test platform name"""
    integration = TikTokIntegration()
    assert integration.get_platform_name() == "tiktok"


@pytest.mark.asyncio
async def test_tiktok_text_only_not_supported():
    """Test that text-only posts are not supported"""
    integration = TikTokIntegration()
    result = await integration.post_text("Test text")
    assert result["success"] is False
    assert "does not support text-only posts" in result["error"]


@pytest.mark.asyncio
async def test_tiktok_health_check():
    """Test health check"""
    integration = TikTokIntegration()
    health = await integration.health_check()
    assert "platform" in health
    assert health["platform"] == "tiktok"
    assert "authenticated" in health
    assert "status" in health


# Note: The following tests require valid credentials
# They are marked to skip unless credentials are available

@pytest.mark.skip(reason="Requires valid TikTok credentials")
@pytest.mark.asyncio
async def test_tiktok_authentication():
    """Test authentication with real credentials"""
    integration = TikTokIntegration()
    result = await integration.authenticate()
    assert result is True
    assert integration.authenticated is True


@pytest.mark.skip(reason="Requires valid TikTok credentials and video file")
@pytest.mark.asyncio
async def test_tiktok_post_video():
    """Test posting a video"""
    integration = TikTokIntegration()
    await integration.authenticate()

    result = await integration.post_media(
        media_paths=["test_video.mp4"],
        caption="Test video from AICompany",
        privacy_level="public"
    )
    assert result["success"] is True
    assert "post_id" in result
