# API examples

## Create a student

```http
POST /api/v1/students
Authorization: Bearer <supabase-access-token>
Content-Type: application/json
```

```json
{
  "admission_number": "2026-001",
  "first_name": "Aarav",
  "last_name": "Kumar",
  "date_of_birth": "2015-04-20",
  "class_name": "5",
  "section": "A",
  "roll_number": "12"
}
```

## Record attendance

```http
POST /api/v1/attendance/bulk
Authorization: Bearer <supabase-access-token>
Content-Type: application/json
```

```json
{
  "records": [
    {
      "student_id": "0a9eb87e-6b3e-44f9-bf44-ea44870cf5e8",
      "attendance_date": "2026-11-01",
      "session": "full_day",
      "status": "present",
      "remarks": null
    }
  ]
}
```

## Paginated response

```json
{
  "success": true,
  "data": {
    "items": [],
    "page": 1,
    "page_size": 20,
    "total": 0,
    "total_pages": 0
  },
  "message": "Operation completed",
  "meta": null
}
```
