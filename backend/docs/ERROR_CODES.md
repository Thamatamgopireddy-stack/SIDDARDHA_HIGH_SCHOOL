# Error codes

| HTTP | Code | Meaning |
|---|---|---|
| 401 | `AUTHENTICATION_REQUIRED` | Missing bearer token |
| 401 | `INVALID_TOKEN` | Invalid, expired, wrong-issuer, or wrong-audience JWT |
| 403 | `PROFILE_UNAVAILABLE` | No active application profile |
| 403 | `PERMISSION_DENIED` | Profile lacks the required database-backed permission |
| 404 | `NOT_FOUND` | API path does not exist |
| 404 | Resource-specific `*_NOT_FOUND` | Resource is not visible in the caller's school |
| 409 | `CONFLICT` | Unique, foreign-key, or state conflict |
| 409 | `ADMISSION_NOT_APPROVED` | Conversion attempted before approval |
| 422 | `VALIDATION_ERROR` | Request schema validation failed |
| 503 | `DATABASE_NOT_CONFIGURED` / `DATABASE_UNAVAILABLE` | Database cannot serve the request |
| 503 | `AUTHENTICATION_PROVIDER_UNAVAILABLE` | Trusted JWKS key retrieval failed |
| 500 | `INTERNAL_ERROR` | Unexpected server error; details are logged server-side only |

Validation errors intentionally omit submitted field values to avoid echoing sensitive request data.
