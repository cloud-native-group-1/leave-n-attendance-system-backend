# API modify note
## POST /api/auth/login
### Modify reason
- Modify request format to comply with `OAuth2PasswordRequestForm`
    - Modify the field name from "email" to "username", but the content that you need to fill in is still user's email.
- Modify response format to let fastAPI Swagger UI automatically get token and  speedup backen testing
### request
```json
{
  "username": "user@example.com",
  "password": "securepassword"
}
```

### response
```json
{
    "access_token": "jwt_token",
    "token_type": "bearer"
}
```
## POST /api/leave-requests
- We change the basic unit of leave from half day to the whole day, so I remove the `start_half_day` and `end_half_day` field in the request
### request
```json
{
  "leave_type_id": 1,
  "start_date": "2023-12-24",
  "end_date": "2023-12-31",
  "reason": "Year-end holiday",
  "proxy_user_id": 3
}
```

## GET /api/leave-requests
- ADD two query parameter `page` and `per_page` to support pagination
### query parameters
- status (optional): Filter by status (Pending, Approved, Rejected)
- startDate (optional): Filter by start date
- endDate (optional): Filter by end date
- page: Which page you want to get
- per_page: How many entries per page

## GET /api/users/subordinates
- formerly know as `GET /api/users/team`
- Used for manager to get his / her subordinates
- To reduce ambiguity, we change the API name

## GET /api/users/team
- Used for GENERAL user to get his / her teammates
### Response (200 OK)
- Same as `GET /api/users/subordinates`
```json
{
  "team_members": [
    {
      "id": 3,
      "employee_id": "EMP003",
      "first_name": "Alice",
      "last_name": "Johnson",
      "position": "Junior Developer",
      "email": "alice.johnson@example.com"
    },
    {
      "id": 4,
      "employee_id": "EMP004",
      "first_name": "Bob",
      "last_name": "Smith",
      "position": "Senior Developer",
      "email": "bob.smith@example.com"
    }
  ]
}
```
