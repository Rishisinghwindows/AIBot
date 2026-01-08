from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import select, func

from ohgrt_api.config import get_settings
from ohgrt_api.db.base import SessionLocal, is_db_available
from ohgrt_api.db.models import ConversationContext, WhatsAppChatMessage

router = APIRouter(prefix="/admin", tags=["admin"])


def _get_whatsapp_counts() -> dict:
    if not is_db_available():
        raise HTTPException(status_code=503, detail="Database not available")

    db = SessionLocal()
    try:
        total_stmt = select(func.count(func.distinct(ConversationContext.client_id))).where(
            ConversationContext.client_type == "whatsapp"
        )
        total = db.execute(total_stmt).scalar() or 0

        since = datetime.now(timezone.utc) - timedelta(hours=24)
        active_stmt = select(func.count(func.distinct(ConversationContext.client_id))).where(
            ConversationContext.client_type == "whatsapp",
            ConversationContext.updated_at >= since,
        )
        active_24h = db.execute(active_stmt).scalar() or 0

        return {"total": total, "active_24h": active_24h}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database error: {e}") from e
    finally:
        db.close()


@router.get("/whatsapp-users", response_class=JSONResponse)
async def whatsapp_users_stats() -> dict:
    """Return WhatsApp user counts for admin dashboard."""
    counts = _get_whatsapp_counts()
    return {
        "whatsapp_users_total": counts["total"],
        "whatsapp_users_active_24h": counts["active_24h"],
    }


@router.get("/whatsapp-chats", response_class=JSONResponse)
async def whatsapp_chat_messages(
    phone: str = Query(..., min_length=6),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> dict:
    """Return recent WhatsApp chat messages for a phone number."""
    if not is_db_available():
        raise HTTPException(status_code=503, detail="Database not available")

    db = SessionLocal()
    try:
        stmt = (
            select(WhatsAppChatMessage)
            .where(WhatsAppChatMessage.phone_number == phone)
            .order_by(WhatsAppChatMessage.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        rows = db.execute(stmt).scalars().all()
        messages = [
            {
                "direction": r.direction,
                "text": r.text,
                "message_id": r.message_id,
                "response_type": r.response_type,
                "media_url": r.media_url,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in reversed(rows)
        ]
        return {"phone": phone, "count": len(messages), "messages": messages}
    finally:
        db.close()


@router.get("/whatsapp-users-list", response_class=JSONResponse)
async def whatsapp_users_list() -> dict:
    """Return WhatsApp users list with last activity."""
    if not is_db_available():
        raise HTTPException(status_code=503, detail="Database not available")

    db = SessionLocal()
    try:
        stmt = (
            select(
                WhatsAppChatMessage.phone_number,
                func.max(WhatsAppChatMessage.created_at).label("last_seen"),
                func.count(WhatsAppChatMessage.id).label("message_count"),
            )
            .group_by(WhatsAppChatMessage.phone_number)
            .order_by(func.max(WhatsAppChatMessage.created_at).desc())
        )
        rows = db.execute(stmt).all()
        users = [
            {
                "phone": r.phone_number,
                "last_seen": r.last_seen.isoformat() if r.last_seen else None,
                "message_count": r.message_count,
            }
            for r in rows
        ]
        return {"count": len(users), "users": users}
    finally:
        db.close()


@router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard() -> HTMLResponse:
    """Simple admin dashboard for WhatsApp metrics."""
    settings = get_settings()
    error_detail = None
    counts = {"total": 0, "active_24h": 0}
    try:
        counts = _get_whatsapp_counts()
    except HTTPException as exc:
        error_detail = exc.detail
    error_block = (
        f"<div class=\"card\"><div class=\"label\">Status</div>"
        f"<div class=\"value\" style=\"color:#b91c1c;\">DB Unavailable</div>"
        f"<div class=\"meta\">{error_detail}</div></div>"
    ) if error_detail else ""
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>WhatsApp Admin Dashboard</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&display=swap');
    :root {{
      --bg1: #f7f2e9;
      --bg2: #f2e8d8;
      --ink: #1f2937;
      --muted: #6b7280;
      --accent: #0f766e;
      --card: #ffffff;
      --shadow: 0 20px 60px rgba(15, 118, 110, 0.12);
    }}
    * {{ box-sizing: border-box; }}
    html, body {{
      height: 100%;
      overflow: hidden;
    }}
    body {{
      margin: 0;
      font-family: "Space Grotesk", sans-serif;
      color: var(--ink);
      background: radial-gradient(1200px 800px at 10% -20%, var(--bg2), transparent),
                  radial-gradient(900px 600px at 90% 0%, #efe7d7, transparent),
                  linear-gradient(135deg, var(--bg1), #faf7f0 60%);
      min-height: 100vh;
    }}
    .wrap {{
      max-width: 980px;
      margin: 0 auto;
      padding: 24px;
      height: 100vh;
      display: flex;
      flex-direction: column;
      gap: 18px;
    }}
    .chat-card {{
      display: flex;
      flex-direction: column;
      height: calc(100vh - 260px);
    }}
    .title {{
      display: flex;
      align-items: center;
      gap: 12px;
      font-size: 28px;
      font-weight: 700;
      letter-spacing: 0.2px;
    }}
    .subtitle {{
      color: var(--muted);
      margin-top: 6px;
      font-size: 14px;
    }}
    .grid {{
      margin-top: 12px;
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 18px;
      min-height: 0;
    }}
    .chat-grid {{
      flex: 1;
      min-height: 0;
      align-items: stretch;
      height: calc(100vh - 230px);
    }}
    .card {{
      background: var(--card);
      border-radius: 16px;
      padding: 22px;
      box-shadow: var(--shadow);
      border: 1px solid #eef2f3;
    }}
    .chat-grid .card {{
      height: 100%;
      display: flex;
      flex-direction: column;
      min-height: 0;
    }}
    .label {{
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 1px;
      color: var(--muted);
      margin-bottom: 8px;
    }}
    .value {{
      font-size: 36px;
      font-weight: 700;
      color: var(--accent);
    }}
    .meta {{
      margin-top: 18px;
      font-size: 12px;
      color: var(--muted);
    }}
    .pill {{
      display: inline-block;
      margin-top: 10px;
      padding: 6px 10px;
      background: #e6fffb;
      color: #115e59;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 600;
    }}
    .chat-window {{
      flex: 1;
      overflow-y: auto;
      padding-right: 6px;
      min-height: 0;
    }}
    .panel-body {{
      flex: 1;
      overflow-y: auto;
      padding-right: 6px;
      min-height: 0;
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="title">WhatsApp Admin Dashboard</div>
    <div class="subtitle">Connected users based on unique phone numbers.</div>
    <div class="grid">
      <div class="card">
        <div class="label">Total Connected Users</div>
        <div class="value">{counts['total']}</div>
        <div class="pill">All time</div>
      </div>
      <div class="card">
        <div class="label">Active in Last 24 Hours</div>
        <div class="value">{counts['active_24h']}</div>
        <div class="pill">Rolling window</div>
      </div>
      {error_block}
    </div>
    <div class="meta">Environment: {settings.environment}</div>
    <div class="meta">Chat API: /admin/whatsapp-chats?phone=+91XXXXXXXXXX</div>
    <div class="grid chat-grid" style="margin-top: 12px;">
      <div class="card">
        <div class="label">Users</div>
        <div id="users" class="meta panel-body">Loading...</div>
      </div>
      <div class="card chat-card">
        <div class="label">Chat</div>
        <div id="chat" class="meta chat-window panel-body">Select a user to view messages.</div>
      </div>
    </div>
  </div>
  <script>
    async function loadUsers() {{
      const res = await fetch('/admin/whatsapp-users-list');
      const data = await res.json();
      const root = document.getElementById('users');
      if (!data.users || data.users.length === 0) {{
        root.textContent = 'No users yet.';
        return;
      }}
      const rows = data.users.map(u => `
        <div style="display:flex;justify-content:space-between;align-items:center;padding:10px 0;border-bottom:1px solid #f1f5f9;cursor:pointer;" onclick="loadChat('${{u.phone}}')">
          <div>
            <div style="font-weight:600;">${{u.phone}}</div>
            <div style="color:#6b7280;font-size:12px;">Messages: ${{u.message_count}}</div>
          </div>
          <div style="color:#6b7280;font-size:12px;">${{(u.last_seen || '').replace('T',' ').replace('Z','')}}</div>
        </div>
      `).join('');
      root.innerHTML = rows;
    }}

    const PAGE_SIZE = 15;
    let chatState = {{ phone: null, offset: 0 }};

    function renderMessages(messages) {{
      return messages.map(m => {{
        const align = m.direction === 'incoming' ? 'flex-start' : 'flex-end';
        const bg = m.direction === 'incoming' ? '#f1f5f9' : '#e6fffb';
        return `
          <div style="display:flex;justify-content:${{align}};margin:8px 0;">
            <div style="max-width:70%;background:${{bg}};padding:10px 12px;border-radius:12px;">
              <div style="font-size:13px;white-space:pre-wrap;">${{m.text || ''}}</div>
              <div style="font-size:10px;color:#6b7280;margin-top:6px;">${{m.created_at || ''}}</div>
            </div>
          </div>
        `;
      }}).join('');
    }}

    async function fetchMoreMessages(reset = false) {{
      if (!chatState.phone) return;
      const res = await fetch(`/admin/whatsapp-chats?phone=${{encodeURIComponent(chatState.phone)}}&limit=${{PAGE_SIZE}}&offset=${{chatState.offset}}`);
      const data = await res.json();
      const root = document.getElementById('chat');
      const messages = data.messages || [];
      if (reset) {{
        root.innerHTML = `
          <div style="font-weight:600;margin-bottom:8px;">${{data.phone}}</div>
          <div id="chat-messages"></div>
          <div id="chat-load-more" style="margin-top:10px;display:flex;justify-content:center;">
            <button style="border:1px solid #e2e8f0;background:#fff;border-radius:8px;padding:6px 10px;cursor:pointer;" onclick="loadMore()">Load more</button>
          </div>
        `;
      }}
      const container = document.getElementById('chat-messages');
      if (!messages.length) {{
        const btn = document.getElementById('chat-load-more');
        if (btn) btn.style.display = 'none';
        return;
      }}
      container.insertAdjacentHTML('afterbegin', renderMessages(messages));
      chatState.offset += messages.length;
      if (messages.length < PAGE_SIZE) {{
        const btn = document.getElementById('chat-load-more');
        if (btn) btn.style.display = 'none';
      }}
    }}

    async function loadChat(phone) {{
      chatState = {{ phone, offset: 0 }};
      await fetchMoreMessages(true);
    }}

    async function loadMore() {{
      await fetchMoreMessages(false);
    }}

    loadUsers();
  </script>
</body>
</html>"""
    return HTMLResponse(content=html)
