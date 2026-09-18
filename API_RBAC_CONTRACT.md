# RailOpt — API and RBAC Contract

## Authentication
Use:
`Authorization: Bearer <token>`

## Response semantics

### 401 Unauthorized
For:
- missing authorization;
- invalid token;
- undecodable/invalid session;
- unauthenticated requests.

### 403 Forbidden
For:
- authenticated user without permission;
- invalid role scope for an operation;
- invalid department/division scope.

## Protected mutation candidates
Verify exact current routes in source before changing them. At minimum inspect:
- `PUT /api/maintenance/requests/{id}`
- `DELETE /api/maintenance/requests/{id}`
- `POST /api/optimization/run`
- `POST /api/whatif/simulate`

## Permission policy
Use the existing permission model from `backend/app/api/auth.py`.

Expected:
- Controller: approval + optimization.
- Planner: approval + optimization.
- Engineer/TRD/S&T: request submission/editing only where allowed; no system-wide approval/optimization.

Deletion must use the application's intended delete permission. Do not equate deletion with approval unless the existing policy explicitly does so.

## Department validation
For field roles:
1. identify authenticated role;
2. derive allowed department;
3. validate requested department;
4. reject unauthorized cross-department writes.

Never trust client-provided role/division for privilege escalation.

## Frontend propagation
The shared API/data service should attach the bearer token to protected mutations.

Do not place credentials/secrets in source.

## Testing contract
Cover:
- Controller allowed paths;
- Planner behavior according to policy;
- Engineer/TRD/S&T denied where restricted;
- missing token = 401;
- invalid token = 401;
- forged role/division payload cannot bypass RBAC;
- allowed field-role submission works;
- full regression remains green.
