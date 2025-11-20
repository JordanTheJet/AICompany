# AICompany - Social Media Integration Platform

A comprehensive Python-based platform for automated social media posting to Twitter, Instagram, and TikTok.

## Features

- **Multi-Platform Support**: Post to Twitter, Instagram, and TikTok from a single API
- **Async Operations**: Built with FastAPI for high-performance async operations
- **Authentication Management**: Secure credential storage and OAuth handling
- **Media Support**: Upload images, videos, and other media types
- **Error Handling**: Robust error handling and retry mechanisms
- **Rate Limiting**: Built-in rate limiting to respect platform limits
- **Extensible Architecture**: Easy to add new social media platforms

## Supported Platforms

### Twitter (X)
- Text posts (tweets)
- Images and videos
- Thread support
- Quote tweets and replies

### Instagram
- Feed posts with images
- Carousel posts
- Stories
- Captions and hashtags

### TikTok
- Video uploads
- Captions and hashtags
- Privacy settings

## Installation

1. Clone the repository:
```bash
git clone https://github.com/JordanTheJet/AICompany.git
cd AICompany
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your API credentials
```

## Configuration

### Twitter Setup
1. Create a Twitter Developer account at https://developer.twitter.com/
2. Create a new app and generate API keys
3. Add credentials to `.env` file

### Instagram Setup
1. Create a Facebook Developer account at https://developers.facebook.com/
2. Create an app and get Instagram API access
3. Add credentials to `.env` file

### TikTok Setup
1. Register as a TikTok developer at https://developers.tiktok.com/
2. Create an app and obtain client credentials
3. Add credentials to `.env` file

## Usage

### Starting the API Server

```bash
uvicorn src.main:app --reload
```

The API will be available at `http://localhost:8000`

### API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Example Usage

#### Post to Twitter

```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/twitter/post",
    json={
        "text": "Hello from AICompany! 🚀",
        "media_urls": []
    },
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)
print(response.json())
```

#### Post to Instagram

```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/instagram/post",
    json={
        "caption": "Check out this amazing content! #AICompany",
        "image_path": "/path/to/image.jpg"
    },
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)
print(response.json())
```

#### Post to TikTok

```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/tiktok/post",
    json={
        "caption": "Amazing video content #TikTok",
        "video_path": "/path/to/video.mp4",
        "privacy_level": "public"
    },
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)
print(response.json())
```

### Python SDK Usage

```python
from src.integrations import TwitterIntegration, InstagramIntegration, TikTokIntegration

# Twitter
twitter = TwitterIntegration()
result = await twitter.post_text("Hello Twitter! 🐦")

# Instagram
instagram = InstagramIntegration()
result = await instagram.post_image(
    image_path="image.jpg",
    caption="Hello Instagram! 📸"
)

# TikTok
tiktok = TikTokIntegration()
result = await tiktok.post_video(
    video_path="video.mp4",
    caption="Hello TikTok! 🎵"
)
```

## Project Structure

```
AICompany/
├── src/
│   ├── main.py                    # FastAPI application
│   ├── config/
│   │   └── settings.py           # Configuration management
│   ├── integrations/
│   │   ├── __init__.py
│   │   ├── base.py               # Base integration class
│   │   ├── twitter.py            # Twitter integration
│   │   ├── instagram.py          # Instagram integration
│   │   └── tiktok.py             # TikTok integration
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes/
│   │       ├── twitter.py        # Twitter endpoints
│   │       ├── instagram.py      # Instagram endpoints
│   │       └── tiktok.py         # TikTok endpoints
│   ├── models/
│   │   └── schemas.py            # Pydantic models
│   └── utils/
│       ├── auth.py               # Authentication utilities
│       └── media.py              # Media handling utilities
├── tests/
│   ├── test_twitter.py
│   ├── test_instagram.py
│   └── test_tiktok.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Security

- Never commit `.env` file or credentials to version control
- Use environment variables for all sensitive data
- Enable 2FA on all social media accounts
- Rotate API keys regularly
- Use HTTPS in production

## Rate Limits

Each platform has different rate limits:

- **Twitter**: 300 tweets per 3 hours, 50 requests per 15 minutes
- **Instagram**: Varies by endpoint, typically 200 requests per hour
- **TikTok**: 100 requests per day (varies by API tier)

## Error Handling

The platform includes comprehensive error handling:
- Network errors with retry logic
- API rate limit detection and backoff
- Authentication error handling
- Media validation errors

## Testing

Run tests with pytest:

```bash
pytest tests/ -v
```

Run with coverage:

```bash
pytest tests/ --cov=src --cov-report=html
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - See LICENSE file for details

## Support

For issues and questions:
- GitHub Issues: https://github.com/JordanTheJet/AICompany/issues
- Documentation: Coming soon

## Roadmap

- [ ] LinkedIn integration
- [ ] Facebook integration
- [ ] Scheduling system
- [ ] Analytics dashboard
- [ ] Webhook support
- [ ] Multi-account management
- [ ] Content calendar
- [ ] AI-powered content suggestions

## Credits

Built with:
- FastAPI
- Tweepy
- Instagrapi
- TikTokApi
