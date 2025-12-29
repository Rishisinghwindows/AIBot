# OAuth Provider Setup Guide

This guide explains how to configure OAuth providers for OhGrt integrations.

## Current Status

| Provider | Status | Environment Variables |
|----------|--------|----------------------|
| GitHub | Ready | `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET` |
| Slack | Ready | `SLACK_CLIENT_ID`, `SLACK_CLIENT_SECRET` |
| Gmail | Needs Setup | `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET` |
| Jira | Needs Setup | `ATLASSIAN_CLIENT_ID`, `ATLASSIAN_CLIENT_SECRET` |
| Uber | Needs Setup | `UBER_CLIENT_ID`, `UBER_CLIENT_SECRET` |

---

## GitHub OAuth Setup

GitHub OAuth is already configured. Credentials are in `.env`.

### Redirect URI
```
http://localhost:3000/settings/github/callback
```

### Scopes
- `user` - Read user profile
- `repo` - Access repositories
- `read:org` - Read organization data

---

## Slack OAuth Setup

Slack OAuth is already configured. Credentials are in `.env`.

### Redirect URI
```
http://localhost:3000/settings/slack/callback
```

### Scopes
- `channels:read` - View channels
- `chat:write` - Send messages
- `users:read` - Read user info
- `team:read` - Read team info

---

## Gmail (Google OAuth) Setup

### Step 1: Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Gmail API:
   - Go to "APIs & Services" > "Library"
   - Search for "Gmail API" and enable it

### Step 2: Create OAuth Credentials
1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. Select "Web application"
4. Add authorized redirect URI:
   ```
   http://localhost:3000/settings/gmail/callback
   ```
5. Copy the Client ID and Client Secret

### Step 3: Configure .env
```bash
GOOGLE_OAUTH_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:3000/settings/gmail/callback
```

### Step 4: Configure OAuth Consent Screen
1. Go to "APIs & Services" > "OAuth consent screen"
2. Select "External" user type
3. Fill in app name, support email, developer email
4. Add scopes: `gmail.readonly`, `openid`, `email`, `profile`
5. Add test users (for development)

### Scopes Used
- `openid` - OpenID Connect
- `email` - User email
- `profile` - User profile
- `https://www.googleapis.com/auth/gmail.readonly` - Read Gmail messages

---

## Jira (Atlassian OAuth) Setup

### Step 1: Create Atlassian Developer App
1. Go to [Atlassian Developer Console](https://developer.atlassian.com/console/myapps/)
2. Click "Create" > "OAuth 2.0 integration"
3. Enter app name and agree to terms

### Step 2: Configure OAuth 2.0
1. In your app, go to "Authorization"
2. Click "Add" next to OAuth 2.0 (3LO)
3. Add callback URL:
   ```
   http://localhost:3000/settings/jira/callback
   ```
4. Add required scopes:
   - `read:jira-work` - Read issues
   - `read:jira-user` - Read user data
   - `write:jira-work` - Create/update issues

### Step 3: Get Credentials
1. Go to "Settings"
2. Copy the Client ID and Secret

### Step 4: Configure .env
```bash
ATLASSIAN_CLIENT_ID=your-atlassian-client-id
ATLASSIAN_CLIENT_SECRET=your-atlassian-client-secret
ATLASSIAN_REDIRECT_URI=http://localhost:3000/settings/jira/callback
```

---

## Uber OAuth Setup

### Step 1: Create Uber Developer App
1. Go to [Uber Developer Dashboard](https://developer.uber.com/dashboard)
2. Create a new app
3. Select "Rides API" access

### Step 2: Configure OAuth
1. Go to "Auth" tab in your app
2. Add redirect URI:
   ```
   http://localhost:3000/settings/uber/callback
   ```
3. Select required scopes:
   - `profile` - User profile
   - `history` - Ride history
   - `request` - Request rides

### Step 3: Get Credentials
1. Go to "Settings"
2. Copy Client ID and Client Secret

### Step 4: Configure .env
```bash
UBER_CLIENT_ID=your-uber-client-id
UBER_CLIENT_SECRET=your-uber-client-secret
UBER_REDIRECT_URI=http://localhost:3000/settings/uber/callback
```

---

## Production Deployment

For production, update redirect URIs to your production domain:

```bash
# Production example
GITHUB_REDIRECT_URI=https://app.ohgrt.com/settings/github/callback
SLACK_REDIRECT_URI=https://app.ohgrt.com/settings/slack/callback
GOOGLE_OAUTH_REDIRECT_URI=https://app.ohgrt.com/settings/gmail/callback
ATLASSIAN_REDIRECT_URI=https://app.ohgrt.com/settings/jira/callback
UBER_REDIRECT_URI=https://app.ohgrt.com/settings/uber/callback
```

Remember to add these URLs to each OAuth provider's allowed redirect URIs.

---

## Troubleshooting

### 503 Service Unavailable
- OAuth provider not configured
- Missing `CLIENT_ID` in environment variables
- Solution: Set the required environment variables

### 401 Unauthorized
- User not logged in
- Expired access token
- Solution: Refresh the page and log in again

### OAuth callback error
- Redirect URI mismatch
- Solution: Ensure redirect URI in `.env` matches exactly what's configured in the OAuth provider console

### CORS errors
- Backend not handling preflight requests
- Solution: OAuth endpoints are now exempt from security headers middleware
