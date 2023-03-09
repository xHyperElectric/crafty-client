class APIRoutes(object):
    BASE_URL = '/api/v2'
    ROLES_URL = f'{BASE_URL}/roles'
    SERVERS_URL = f'{BASE_URL}/servers'
    USERS_URL = f'{BASE_URL}/users'
    AUTH_URL = f'{BASE_URL}/auth'
    LOGIN_URL = f'{AUTH_URL}/login'
    SCHEMA_URL = f'{BASE_URL}/jsonschema'
