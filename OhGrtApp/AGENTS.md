# Codex Agent Guide

- Scope: SwiftUI iOS app using SwiftData + Firebase/Google Sign-In. Keep Auth flows intact and do not modify `GoogleService-Info.plist` secrets.
- Editing: Stay ASCII, prefer `apply_patch`, keep comments minimal; match existing Swift style and SwiftUI patterns.
- Project layout: `OhGrtApp.swift` bootstraps Firebase + SwiftData; features under `OhGrt/Features`; shared models/resources live in `OhGrt/Models`, `OhGrt/Core`, `OhGrt/Resources`.
- Dependencies: SwiftData requires iOS 17+/Xcode 15+; Auth uses `AuthManager.shared` to flip `isAuthenticated` and show `ConversationListView` vs `AuthView`.
- Testing/build: Use `xcodebuild -scheme OhGrt -destination 'platform=iOS Simulator,name=iPhone 15' test` (or `… build`) from repo root; ensure Firebase configs remain valid.
- Tooling: Prefer `rg`/`rg --files` for search, avoid destructive git commands, and never undo user changes.
