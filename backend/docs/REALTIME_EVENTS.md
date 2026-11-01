# Realtime event contract

Supabase Realtime publication and backend event publishing are not configured in this delivery. Do not treat database changes as an event contract or subscribe clients to private tables without authorization policies.

The planned event names and minimum payloads are:

| Event | Publisher/source | Audience and authorization | Client cache action |
|---|---|---|---|
| `attendance.updated` | Backend after attendance transaction | Scoped school/class users with attendance permission | Invalidate attendance register and student attendance |
| `notification.created` | Backend notification service | Recipient only | Add notification and update unread count |
| `announcement.published` | Backend after publication | Authorized school audience | Invalidate announcement feed |
| `message.created` | Backend messaging service | Conversation members only | Append conversation message |
| `payment.status_changed` | Verified payment webhook/service | Student guardian and finance users | Invalidate invoice and balance |
| `assignment.submitted` | Backend submission service | Assigned teacher and submitting student/guardian | Invalidate assignment submissions |
| `transport.location_updated` | Authorized GPS integration | Assigned route users only | Update current vehicle location |

Payloads must contain event ID, event name, school ID, resource ID, and occurrence timestamp; sensitive student or payment data should be fetched from an authorized API rather than broadcast. A Realtime subscription never replaces an authorized API read. These are design targets, not events emitted by current code.
