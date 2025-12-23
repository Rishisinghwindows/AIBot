# WhatsApp Integration Setup Guide

This guide explains how to set up WhatsApp Cloud API integration for OhGrtApi.

## Overview

OhGrtApi now supports WhatsApp as a messaging channel alongside iOS and Web clients. The WhatsApp integration uses Meta's Cloud API to receive and send messages.

## Prerequisites

1. **Meta Business Account** - Create at [business.facebook.com](https://business.facebook.com)
2. **Meta Developer Account** - Create at [developers.facebook.com](https://developers.facebook.com)
3. **Phone Number** - Either use Meta's test number or verify your own business phone number

## Setup Steps

### Step 1: Create Meta App

1. Go to [Meta for Developers](https://developers.facebook.com)
2. Click "My Apps" → "Create App"
3. Select "Business" type
4. Enter app name (e.g., "OhGrt WhatsApp Bot")
5. Add your Business Account

### Step 2: Add WhatsApp Product

1. In your app dashboard, click "Add Products"
2. Find "WhatsApp" and click "Set Up"
3. Follow the setup wizard to configure your phone number

### Step 3: Get API Credentials

From the WhatsApp section of your app:

1. **Access Token**: Generate a permanent access token
   - Go to "System Users" in Business Settings
   - Create a system user and generate a token with `whatsapp_business_messaging` permission

2. **Phone Number ID**: Found in API Setup
   - This is the ID of your WhatsApp Business phone number

3. **App Secret**: Found in App Settings → Basic
   - Used for webhook signature verification

4. **Verify Token**: Create your own secret string
   - Used to verify webhook URL during setup

### Step 4: Configure Environment Variables

Add these to your `.env` file:

```env
# WhatsApp Cloud API
WHATSAPP_ACCESS_TOKEN=your_permanent_access_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_VERIFY_TOKEN=your_custom_verify_token
WHATSAPP_APP_SECRET=your_app_secret
```

### Step 5: Configure Webhook

1. Deploy your OhGrtApi (or use ngrok for testing)
2. In Meta App Dashboard, go to WhatsApp → Configuration
3. Set webhook URL: `https://your-domain.com/whatsapp/webhook`
4. Enter your verify token
5. Subscribe to these webhook fields:
   - `messages`
   - `message_deliveries` (optional)
   - `message_reads` (optional)

### Step 6: Test the Integration

1. Use Meta's test phone number to send a message
2. Check your server logs for incoming webhook events
3. The bot should respond based on detected intent

## Webhook Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/whatsapp/webhook` | GET | Webhook verification |
| `/whatsapp/webhook` | POST | Message handling |

## Features Supported

The WhatsApp bot supports:

- **Chat**: General conversation with AI
- **Weather**: Get current weather (e.g., "Weather in Delhi")
- **PNR Status**: Check Indian Railways PNR (e.g., "PNR 1234567890")
- **Train Status**: Live train status (e.g., "Train 12301 status")
- **News**: Get top headlines (e.g., "Latest news")
- **Horoscope**: Daily horoscope (e.g., "Aries horoscope")
- **Birth Chart**: Kundli generation
- **Numerology**: Numerology analysis
- **Tarot Reading**: Tarot card readings
- **Panchang**: Daily panchang
- **Image Generation**: Create AI images (e.g., "Generate image of sunset")

## Testing with ngrok

For local testing:

```bash
# Start ngrok
ngrok http 9002

# Use the HTTPS URL for webhook configuration
# Example: https://abc123.ngrok.io/whatsapp/webhook
```

## Production Deployment

1. Deploy OhGrtApi to your cloud provider (Railway, AWS, GCP, etc.)
2. Ensure HTTPS is enabled
3. Update webhook URL in Meta dashboard
4. Set up proper logging and monitoring

## Troubleshooting

### Webhook Verification Fails
- Check that `WHATSAPP_VERIFY_TOKEN` matches what you entered in Meta dashboard
- Ensure the endpoint is accessible and returns 200

### Messages Not Received
- Verify webhook is subscribed to `messages` field
- Check server logs for errors
- Ensure access token has correct permissions

### Bot Not Responding
- Check `WHATSAPP_ACCESS_TOKEN` is valid
- Verify `WHATSAPP_PHONE_NUMBER_ID` is correct
- Check server logs for API errors

### Signature Verification Failed
- Set `WHATSAPP_APP_SECRET` in environment variables
- Or temporarily disable verification for testing (not recommended for production)

## Security Notes

1. Always use HTTPS in production
2. Keep your access token and app secret secure
3. Implement rate limiting (already included in OhGrtApi)
4. Validate webhook signatures in production

## Environment Variables Summary

```env
# Required
WHATSAPP_ACCESS_TOKEN=EAAxxxxxxxxxxxxx
WHATSAPP_PHONE_NUMBER_ID=12345678901234
WHATSAPP_VERIFY_TOKEN=your_verify_token

# Optional (but recommended for production)
WHATSAPP_APP_SECRET=your_app_secret

# For image generation
FAL_KEY=your_fal_ai_key

# For weather
OPENWEATHER_API_KEY=your_openweather_key

# For news
NEWS_API_KEY=your_newsapi_key

# For railway services
RAILWAY_API_KEY=your_rapidapi_key
```

## API Documentation

Once deployed, access the API documentation at:
- Swagger UI: `https://your-domain.com/docs`
- ReDoc: `https://your-domain.com/redoc`
