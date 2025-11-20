# Multi-Profile Social Media Automation System

## Overview

The AICompany platform now includes a comprehensive multi-profile system that allows users to manage multiple social media personas, each with their own accounts across Twitter, Instagram, and TikTok. The system features automated engagement between profiles to build authentic-looking social proof and engagement.

## Key Features

### 1. Multi-Profile Management

- **Multiple Personas**: Create unlimited profiles, each representing a different persona or brand
- **Separate Social Accounts**: Each profile can have independent accounts on Twitter, Instagram, and TikTok
- **Profile Metadata**: Store custom information about each persona (personality traits, topics, style)
- **Easy Switching**: Seamlessly manage and post from different profiles

### 2. Multi-Platform Posting

- **Unified Interface**: Post to multiple platforms simultaneously with a single API call
- **Platform-Specific Handling**: Automatic adaptation of content for each platform's requirements
- **Media Support**: Upload images and videos across all platforms
- **Scheduling**: Schedule posts for future publication

### 3. Automated Engagement

- **Cross-Profile Interaction**: Profiles automatically like, comment on, and share each other's content
- **Customizable Rules**: Define engagement probability and timing for each profile
- **Natural Behavior**: Random delays and probabilities create authentic engagement patterns
- **Comment Templates**: Use predefined comments or AI-generated responses
- **Engagement Analytics**: Track how profiles interact with each other

### 4. Engagement Rules Engine

- **Per-Profile Configuration**: Each profile can have unique engagement rules
- **Targeted Engagement**: Engage with specific profiles or all profiles
- **Probability Settings**: Control likelihood of likes (80%), comments (30%), retweets (10%)
- **Timing Control**: Set minimum and maximum delays before engagement (5-60 minutes)
- **Platform Filters**: Engage only on specific platforms

## Architecture

### Database Models

1. **User**: Platform users who own profiles
2. **Profile**: Social media personas with their own identity
3. **SocialAccount**: Links profiles to specific platform accounts
4. **Post**: Tracks all posts made by profiles
5. **EngagementRule**: Defines automation rules for profile interactions
6. **EngagementAction**: Records engagement actions (likes, comments, etc.)

### Services

1. **ProfileService**: Manages users, profiles, and social accounts
2. **PostService**: Handles post creation, tracking, and metrics
3. **EngagementService**: Orchestrates automated engagement between profiles

### Automation

- **Background Scheduler**: Runs every 5 minutes to process pending engagement actions
- **Intelligent Delays**: Randomized timing to avoid detection
- **Rate Limiting**: Respects platform limits and includes backoff strategies

## Getting Started

### Step 1: Create a User

```bash
POST /api/v1/profiles/users
{
  "email": "user@example.com",
  "username": "myusername",
  "password": "securepassword",
  "full_name": "My Name"
}
```

### Step 2: Create Profiles (Personas)

```bash
POST /api/v1/profiles/users/{user_id}/profiles
{
  "name": "TechEnthusiast",
  "display_name": "Tech Enthusiast",
  "description": "Passionate about AI and technology",
  "auto_engage": true,
  "engagement_delay_min": 5,
  "engagement_delay_max": 60
}
```

Create multiple profiles for different personas:
- TechEnthusiast
- FoodieLife
- TravelBlogger
- FitnessGuru

### Step 3: Add Social Accounts to Each Profile

```bash
POST /api/v1/profiles/{profile_id}/social-accounts
{
  "platform": "twitter",
  "credentials": {
    "api_key": "your_api_key",
    "api_secret": "your_api_secret",
    "access_token": "your_access_token",
    "access_token_secret": "your_access_token_secret"
  },
  "platform_username": "TechEnthusiast2024"
}
```

Repeat for Instagram and TikTok accounts.

### Step 4: Set Up Engagement Rules

```bash
POST /api/v1/engagement/rules
{
  "profile_id": 1,
  "engagement_types": ["like", "comment", "retweet"],
  "like_probability": 0.9,
  "comment_probability": 0.4,
  "retweet_probability": 0.15,
  "min_delay": 5,
  "max_delay": 45,
  "comment_templates": [
    "Great post! 👍",
    "Love this content!",
    "Really interesting perspective!",
    "Thanks for sharing!"
  ]
}
```

### Step 5: Post Content from Multiple Profiles

```bash
POST /api/v1/posts/multi-platform
{
  "profile_id": 1,
  "content": "Just discovered an amazing new AI tool! #AI #Tech",
  "platforms": ["twitter", "instagram"],
  "media_paths": ["image1.jpg"],
  "auto_engagement_enabled": true
}
```

The system will:
1. Post to Twitter and Instagram from this profile
2. Automatically schedule engagement actions from other profiles
3. Execute likes, comments, and retweets based on the engagement rules

## API Endpoints

### Profile Management

- `POST /api/v1/profiles/users` - Create a user
- `GET /api/v1/profiles/users/{user_id}` - Get user details
- `POST /api/v1/profiles/users/{user_id}/profiles` - Create a profile
- `GET /api/v1/profiles/users/{user_id}/profiles` - List user's profiles
- `GET /api/v1/profiles/{profile_id}` - Get profile details
- `PUT /api/v1/profiles/{profile_id}` - Update profile
- `DELETE /api/v1/profiles/{profile_id}` - Delete profile

### Social Accounts

- `POST /api/v1/profiles/{profile_id}/social-accounts` - Add social account
- `GET /api/v1/profiles/{profile_id}/social-accounts` - List social accounts
- `POST /api/v1/profiles/social-accounts/{account_id}/verify` - Verify account

### Posts

- `POST /api/v1/posts/create` - Create a single post
- `POST /api/v1/posts/multi-platform` - Post to multiple platforms
- `GET /api/v1/posts/{post_id}` - Get post details
- `GET /api/v1/posts/profile/{profile_id}` - Get profile's posts
- `DELETE /api/v1/posts/{post_id}` - Delete post
- `PUT /api/v1/posts/{post_id}/metrics` - Update engagement metrics

### Engagement Automation

- `POST /api/v1/engagement/rules` - Create engagement rule
- `GET /api/v1/engagement/rules/profile/{profile_id}` - Get profile's rules
- `GET /api/v1/engagement/rules/{rule_id}` - Get rule details
- `PUT /api/v1/engagement/rules/{rule_id}` - Update rule
- `DELETE /api/v1/engagement/rules/{rule_id}` - Delete rule
- `GET /api/v1/engagement/actions/pending` - Get pending actions
- `POST /api/v1/engagement/actions/execute` - Execute pending actions
- `POST /api/v1/engagement/posts/{post_id}/schedule` - Schedule engagement for post
- `GET /api/v1/engagement/stats/profile/{profile_id}` - Get engagement stats

## Example Workflow

### Creating an Automated Social Media Network

1. **Create 5-10 profiles** representing different personas
2. **Add social accounts** for each profile across platforms
3. **Set up engagement rules** so profiles interact with each other:
   - Profile A engages with profiles B, C, D
   - Profile B engages with profiles A, E, F
   - And so on...
4. **Post content** from different profiles throughout the day
5. **Watch automatic engagement** as profiles like, comment, and share each other's content
6. **Monitor analytics** to track engagement patterns

### Engagement Flow

```
Profile A posts → System schedules engagement actions →
Profile B (5 min delay) → Likes post →
Profile C (12 min delay) → Comments "Great post!" →
Profile D (23 min delay) → Retweets post →
Profile E (45 min delay) → Comments "Interesting!"
```

## Best Practices

### 1. Realistic Engagement Patterns

- **Vary probabilities**: Not every profile should engage with every post
- **Random delays**: Use min_delay=5 and max_delay=60 for natural timing
- **Diverse comments**: Provide 10-15 different comment templates
- **Platform-specific rules**: Engagement styles differ by platform

### 2. Profile Diversity

- **Different personalities**: Create distinct personas
- **Varied content**: Each profile should post about different topics
- **Unique voice**: Use different writing styles for each profile
- **Authentic accounts**: Use real-looking profile pictures and bios

### 3. Avoid Detection

- **Don't over-engage**: Keep probabilities reasonable (like: 70-90%, comment: 20-40%)
- **Natural timing**: Avoid instant engagement
- **Rate limiting**: The system respects platform limits
- **Human-like behavior**: Random delays and probabilities

### 4. Content Strategy

- **Quality over quantity**: Focus on good content, not just volume
- **Cross-promotion**: Profiles can reference each other naturally
- **Themed content**: Keep each profile focused on specific topics
- **Engagement hooks**: Create content that invites interaction

## Background Scheduler

The system includes an automated scheduler that runs continuously:

- **Engagement Processing**: Every 5 minutes, processes pending engagement actions
- **Scheduled Posts**: Every 1 minute, checks for posts due to be published
- **Rate Limiting**: Built-in delays between actions to avoid platform limits
- **Error Handling**: Failed actions are logged and can be retried

### Running the Scheduler

The scheduler starts automatically with the main application. To run it standalone:

```bash
python -m src.scheduler
```

## Monitoring and Analytics

### Engagement Stats

Get comprehensive stats for any profile:

```bash
GET /api/v1/engagement/stats/profile/{profile_id}
```

Returns:
- Total engagement performed (likes, comments, retweets)
- Engagement received on posts
- Success/failure rates
- Breakdown by engagement type
- Post metrics (total likes, comments received)

### Health Checks

Monitor system health:
- Database connection status
- Scheduler status
- Platform integrations
- Pending actions queue

## Security Considerations

1. **Credential Storage**: Credentials are stored in the database and can be encrypted
2. **API Authentication**: Implement authentication for production use
3. **Rate Limiting**: Respects platform rate limits
4. **Data Privacy**: User data is stored securely
5. **Compliance**: Ensure compliance with platform terms of service

## Limitations

1. **Platform Terms**: Automated engagement may violate platform terms of service
2. **Detection Risk**: Platforms may detect and ban automated behavior
3. **Ethical Concerns**: Consider the ethics of automated engagement
4. **Rate Limits**: Subject to platform-specific rate limits
5. **API Changes**: Platform APIs may change without notice

## Future Enhancements

- AI-generated comments based on post content
- Image recognition for contextual engagement
- Advanced scheduling with optimal posting times
- Network effect simulation
- Sentiment analysis for engagement
- Multi-language support
- Analytics dashboard
- Webhook notifications
- Content recommendation engine

## Support

For issues or questions:
- Check the API documentation at `/docs`
- Review logs for error messages
- Ensure database is initialized
- Verify social account credentials
- Check scheduler is running

## License

This system is for educational and authorized use only. Users are responsible for compliance with platform terms of service and applicable laws.
