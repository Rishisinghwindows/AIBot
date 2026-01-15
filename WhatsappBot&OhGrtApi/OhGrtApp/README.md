# OhGrt iOS – MCP OAuth & Tools

This app supports one-touch OAuth for MCP providers and surfaces tools returned by the backend.

## OAuth Providers
- **Scheme**: The app expects callback scheme `ohgrt` (Info.plist).
- **Flow**: The app calls `/auth/providers/{provider}/start`, validates `state`, and exchanges via `/auth/providers/{provider}/exchange`.
- **Redirect URIs**: Backend `authUrl` must include `redirect_uri` with scheme `ohgrt://...`. If not, the app shows a misconfiguration error and won’t open the sheet.

Supported providers (when backend exposes them via `/auth/providers`):
- GitHub (existing)
- Slack (configure `SLACK_CLIENT_ID/SECRET/REDIRECT_URI=ohgrt://oauth/slack` on backend & Slack app)
- Gmail (configure Google OAuth with redirect `ohgrt://oauth/google`; include Gmail scopes)
- Google Drive (same Google OAuth client, Drive scopes)

## Tools UI
- The tools list comes from `GET /chat/tools` and respects provider availability.
- Tools can be preselected per conversation; selections are passed in chat requests.
- Providers list lives in the MCP config screen; any `authType == "oauth"` provider uses the generic OAuth sheet.

## Build/Test
- Build: `xcodebuild -scheme OhGrt -destination 'platform=iOS Simulator,name=iPhone 16' build` (use any available simulator).
- Firebase config lives in `OhGrt/GoogleService-Info.plist` (do not alter secrets).
