# Security Fixes and Deployment Roadmap

## Summary of Applied Fixes

This document summarizes the security fixes applied to the AIBot codebase during the code review.

---

## Critical Issues Fixed

### Backend (OhGrtApi)

| Issue | File | Fix Applied |
|-------|------|-------------|
| SQL Injection via string formatting | `app/services/postgres_service.py:139` | Changed to use `psycopg2.sql.Identifier` for safe identifier quoting |
| Credentials not decrypted when loaded | `app/chat/service.py:229-242` | Added `decrypt_if_needed()` call when loading credentials |
| LITE_MODE bypass in production | `app/middleware/security.py:60-62` | Added environment check to block bypass in production |

### Frontend (D23Web)

| Issue | File | Fix Applied |
|-------|------|-------------|
| CSP 'unsafe-inline' and 'unsafe-eval' | `next.config.mjs:8-9` | Only allow in development mode |
| Overly permissive img-src | `next.config.mjs:17` | Restricted to specific trusted domains |
| Overly permissive remotePatterns | `next.config.mjs:59-64` | Restricted to specific trusted domains |
| Missing env validation | N/A | Created `lib/env.ts` for startup validation |
| Context re-renders | `context/AuthContext.tsx` | Added useMemo for context value |

### iOS (OhGrtApp)

| Issue | File | Fix Applied |
|-------|------|-------------|
| Keychain access too permissive | `Core/Auth/KeychainManager.swift:126` | Changed to `kSecAttrAccessibleWhenUnlockedThisDeviceOnly` |
| SSL pinning bypass in production | `Core/Network/SSLPinning.swift:144-146` | Added production assertion and DEBUG guards |
| Silent error in logout | `Core/Auth/AuthManager.swift:178-181` | Added proper error logging |

---

## High Priority Issues Fixed

### Backend

| Issue | File | Fix Applied |
|-------|------|-------------|
| N+1 query in get_conversations | `app/chat/service.py:145-197` | Replaced with single query using subquery |

---

## Remaining Issues (To Be Fixed)

### Week 1 Priority

#### Backend
- [ ] Add query timeout to postgres_service.py
- [ ] Use read-only database user for LLM-generated queries
- [ ] Implement refresh token rotation in auth/router.py
- [ ] Add virus scanning to PDF uploads

#### Frontend
- [ ] Move tokens from localStorage to httpOnly cookies (requires API changes)
- [ ] Add ARIA labels to all interactive elements
- [ ] Implement code splitting for heavy components
- [ ] Add loading skeletons and Suspense boundaries

#### iOS
- [ ] Remove singleton patterns (APIClient, AuthManager, KeychainManager)
- [ ] Implement proper Sendable conformance (replace @unchecked Sendable)
- [ ] Add public key hashes to SSLPinning.swift
- [ ] Store certificate in bundle resource file

### Week 2 Priority

#### Backend
- [ ] Implement circuit breaker for external API calls
- [ ] Add Redis caching for schemas and credentials
- [ ] Standardize error handling across services
- [ ] Add API versioning to URLs

#### Frontend
- [ ] Split large components (page.tsx, chat/page.tsx)
- [ ] Add bundle analyzer
- [ ] Implement SWR/React Query for caching
- [ ] Add comprehensive testing

#### iOS
- [ ] Complete Clean Architecture migration
- [ ] Add crash reporting (Firebase Crashlytics)
- [ ] Implement proper DI (remove singletons in DependencyContainer)
- [ ] Add offline request queue size limit

---

## GitHub Issues Template

### Issue 1: [CRITICAL] SQL Injection Prevention Enhancement

**Labels:** security, critical, backend

**Description:**
While a fix has been applied to use `psycopg2.sql.Identifier`, additional hardening is needed:
- Add query execution timeout
- Use read-only database user for LLM-generated queries
- Implement query complexity limits

**Files:** `app/services/postgres_service.py`

---

### Issue 2: [CRITICAL] Implement httpOnly Cookie Token Storage

**Labels:** security, critical, frontend

**Description:**
Tokens are currently stored in localStorage, which is vulnerable to XSS attacks.
Implement secure token storage using httpOnly cookies:
1. Create API route `/api/auth/set-tokens`
2. Store tokens in httpOnly, secure, sameSite cookies
3. Update AuthContext to use cookies instead of localStorage

**Files:**
- `context/AuthContext.tsx`
- Create `app/api/auth/set-tokens/route.ts`
- Create `app/api/auth/clear-tokens/route.ts`

---

### Issue 3: [HIGH] Implement Refresh Token Rotation

**Labels:** security, high, backend

**Description:**
Current implementation returns the same refresh token on refresh.
Implement token rotation:
1. Generate new refresh token on each refresh
2. Invalidate old refresh token
3. Add token family tracking for revocation

**Files:** `app/auth/router.py:220-268`

---

### Issue 4: [HIGH] Remove Singleton Anti-Patterns (iOS)

**Labels:** architecture, high, ios

**Description:**
Replace singleton patterns with proper dependency injection:
- `APIClient.shared`
- `AuthManager.shared`
- `KeychainManager.shared`

Create instances in DependencyContainer and inject via protocols.

**Files:**
- `Core/Network/APIClient.swift`
- `Core/Auth/AuthManager.swift`
- `Core/Auth/KeychainManager.swift`
- `DI/DependencyContainer.swift`

---

### Issue 5: [HIGH] Add ARIA Accessibility Labels

**Labels:** accessibility, high, frontend

**Description:**
Add proper ARIA labels to all interactive elements:
- Buttons need `aria-label` attributes
- Chat messages need proper `role="log"` and `aria-live`
- Forms need proper label associations

**Files:**
- `components/chat/ChatInput.tsx`
- `components/chat/MessageBubble.tsx`
- `app/page.tsx`

---

### Issue 6: [MEDIUM] Add Circuit Breaker for External APIs

**Labels:** reliability, medium, backend

**Description:**
Implement circuit breaker pattern for external API calls:
- Weather API
- News API
- Jira, GitHub, Slack integrations

Use `pybreaker` library or implement custom solution.

**Files:** `app/graph/tool_agent.py`

---

### Issue 7: [MEDIUM] Implement Code Splitting

**Labels:** performance, medium, frontend

**Description:**
Large components should be code-split:
- Use `dynamic()` for heavy components
- Add Suspense boundaries with loading skeletons
- Lazy load locale files

**Files:**
- `app/page.tsx`
- `app/chat/page.tsx`
- `lib/i18n/LanguageContext.tsx`

---

## Deployment Checklist

### Pre-Production

- [ ] All critical issues fixed
- [ ] Security audit passed
- [ ] Environment variables validated
- [ ] Database migrations tested
- [ ] SSL certificates valid
- [ ] Rate limiting configured
- [ ] CORS properly restricted

### Production Deployment

1. **Backend**
   - [ ] Set `ENVIRONMENT=production`
   - [ ] Set `LITE_MODE=false`
   - [ ] Configure `ENCRYPTION_KEY`
   - [ ] Set up read-only DB user for SQL service
   - [ ] Enable rate limiting
   - [ ] Configure Redis for production

2. **Frontend**
   - [ ] Verify CSP headers in production
   - [ ] Test Firebase App Check
   - [ ] Verify API URL is production endpoint
   - [ ] Run production build successfully

3. **iOS**
   - [ ] Verify SSL pinning is enforced
   - [ ] Test with production API
   - [ ] Submit for App Store review
   - [ ] Monitor crash reports

---

## Testing Requirements

### Security Tests
- [ ] SQL injection attempts blocked
- [ ] XSS attempts blocked by CSP
- [ ] Authentication bypass attempts blocked
- [ ] Rate limiting working correctly
- [ ] Token rotation working

### Integration Tests
- [ ] OAuth flows work end-to-end
- [ ] Chat functionality with all intents
- [ ] File upload and processing
- [ ] External API integrations

### Performance Tests
- [ ] No N+1 queries
- [ ] Response times < 500ms for chat
- [ ] Bundle size < 500KB initial load
- [ ] iOS app launch < 2 seconds

---

*Generated by Code Review - December 2024*
