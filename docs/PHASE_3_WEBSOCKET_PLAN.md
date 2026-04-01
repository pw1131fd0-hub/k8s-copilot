# ClawBook v1.6 Phase 3 - Real-time WebSocket Integration

## Overview
This phase adds real-time capabilities to ClawBook's collaboration features using WebSocket protocol. Focus areas: live comment updates, online user indicators, push notifications.

## Objectives
- **Target Quality Score**: 95/100
- **Target Completion**: April 18, 2026
- **Key Metrics**: WebSocket latency <100ms, real-time delivery reliability >99%

## Architecture

### WebSocket Server Setup
- Framework: `python-socketio` + FastAPI
- Protocol: Socket.IO (fallback to HTTP long-polling)
- Namespace: `/socket.io/`

### Real-time Events
1. **comment:new** - New collaboration comment posted
2. **comment:updated** - Comment edited/resolved
3. **comment:deleted** - Comment deleted
4. **user:online** - User came online in group
5. **user:offline** - User went offline
6. **share:notification** - Post shared with user
7. **activity:log** - Activity log update

### Server-Side Implementation
```
backend/
├── websocket/
│   ├── __init__.py
│   ├── manager.py          # WebSocket connection manager
│   ├── handlers.py         # Event handlers
│   ├── events.py           # Event definitions
│   └── namespaces.py       # Socket.IO namespaces
├── models/
│   └── websocket_schemas.py # WebSocket message schemas
└── services/
    └── notification_service.py # Notification logic
```

### Client-Side Integration
```
frontend/src/
├── hooks/
│   ├── useWebSocket.js     # WebSocket connection hook
│   └── useNotifications.js # Notification toast hook
├── services/
│   └── websocket.js        # Socket.IO client setup
└── components/
    ├── CommentThread.js    # Real-time comment updates
    ├── OnlineUsersList.js  # Live user indicators
    └── NotificationBell.js # Notification center
```

## Implementation Phases

### Phase 3.1 - Backend WebSocket Infrastructure (Days 1-2)
- [ ] Add `python-socketio` and `python-engineio` to requirements.txt
- [ ] Create WebSocket manager (connection tracking, room management)
- [ ] Implement Socket.IO namespace for collaboration
- [ ] Create event handlers for core events
- [ ] Update main.py to register Socket.IO

### Phase 3.2 - Real-time Comment Updates (Days 2-3)
- [ ] Emit `comment:new` event when comment posted
- [ ] Emit `comment:updated` event when comment edited
- [ ] Subscribe clients to post-specific rooms
- [ ] Add comment event handlers in frontend

### Phase 3.3 - Online User Tracking (Days 3-4)
- [ ] Track online users per group
- [ ] Emit `user:online` when user joins group
- [ ] Emit `user:offline` when user disconnects
- [ ] Create OnlineUsersList component
- [ ] Update GroupManager with live user indicators

### Phase 3.4 - Notification System (Days 4-5)
- [ ] Create notification_service.py
- [ ] Emit `share:notification` events
- [ ] Build NotificationBell component with toast
- [ ] Persist notifications to database
- [ ] Add notification history page

### Phase 3.5 - Testing & Optimization (Days 5-6)
- [ ] Unit tests for WebSocket handlers
- [ ] Integration tests for real-time flows
- [ ] Load test WebSocket connections
- [ ] Performance optimization
- [ ] Documentation updates

## Quality Metrics

| Metric | Target | Method |
|--------|--------|--------|
| WebSocket Latency | <100ms | Monitor socket events |
| Message Delivery | >99% | Test failure scenarios |
| Code Coverage | >85% | pytest-cov |
| Bundle Size Impact | <15KB gzip | webpack-bundle-analyzer |
| Uptime | 99.9% | Integration tests |

## Success Criteria
- ✅ All WebSocket events implemented and tested
- ✅ Real-time comment updates working end-to-end
- ✅ Online user indicators showing live status
- ✅ Notification system fully functional
- ✅ Quality score: 95/100
- ✅ All tests passing
- ✅ <100ms latency for real-time events

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| WebSocket connection drops | Medium | Auto-reconnect with exponential backoff |
| High memory usage | High | Implement room cleanup, set connection limits |
| Browser compatibility | Low | Socket.IO handles fallback automatically |
| Real-time sync conflicts | Medium | Implement optimistic updates + server reconciliation |

## Dependencies
- python-socketio >= 5.9.0
- python-engineio >= 4.5.0
- socket.io-client (frontend)
- aioredis (optional, for scaling to multiple servers)

## Next Phase (Phase 4)
- Security audit of WebSocket handlers
- Performance testing at scale
- Documentation for WebSocket API
- Preparation for production deployment
