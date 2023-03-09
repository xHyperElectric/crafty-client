import requests
from urllib.parse import urljoin

from crafty_client.static.exceptions import *
from crafty_client.static.routes import APIRoutes


class CraftyWeb:

    def __init__(self, url, api_token, verify_ssl=False):
        """ The main class for communicating with the Crafty Web API"""
        self.url = url
        self.token = api_token
        self.verify_ssl = verify_ssl
        self.headers = {'Authorization': f'Bearer {self.token}', 'Content-Type': 'application/json'}

    # TODO: Verify all these errors still exist (mostly copied from API V1)
    def _check_errors(self, response_dict):
        if response_dict['error'] == 'INCORRECT_CREDENTIALS':
            raise IncorrectCredentials()
        elif response_dict['error'] == 'SER_NOT_RUNNING':
            raise ServerNotRunning()
        elif response_dict['error'] == 'NO_COMMAND':
            raise MissingParameters("Your request is missing essential parameters or they are invalid")
        elif response_dict['error'] == 'SER_RUNNING':
            raise ServerAlreadyRunning()
        elif response_dict['error'] == 'NOT_AUTHORIZED':
            raise AccessDenied()
        elif response_dict['error'] == 'ACCESS_DENIED':
            print(f'Access Denied')
            raise AccessDenied(response_dict['info'])
        elif response_dict['error'] == 'NOT_ALLOWED':
            raise NotAllowed(response_dict['info'])
        elif response_dict['error'] == 'NOT_FOUND':
            raise ServerNotFound(response_dict['info'])
        # Add elif response_dict['error'] == 'INVALID_JSON_SCHEMA':
        else:
            pass

    def _make_request(self, method, api_route, params=None, data=None):
        endpoint = urljoin(self.url, api_route)

        with requests.request(method, endpoint, 
                              verify=self.verify_ssl, headers=self.headers, params=params, json=data) as route:
            print(f'Debug: \n{route.text}')
            response_dict = route.json()
            print(response_dict)

            status = response_dict.get('status', None)
            data = response_dict.get('data', None)
            error = response_dict.get('error', None)
            info = response_dict.get('info', None) or response_dict.get('error_data', None)

            self._check_errors({'status': status, 'data': data, 'error': error, 'info': info})
            return {'status': status, 'data': data, 'error': error, 'info': info}

    def get_token(self, username, password=None, password_path=None):
        """
        Logs into the Crafty Controller and returns a token for the specified user.

        :param username: The username for the user to log in.
        :type username: str
        :param password: The password for the user. Either `password` or `password_path` must be specified.
        :type password: str, optional
        :param password_path: The path to a file containing the user's password. Either `password` or `password_path`
            must be specified.
        :type password_path: str, optional
        :return: The token generated by the Crafty Controller upon successful login.
        :rtype: str
        :raises ValueError: If neither `password` nor `password_path` are specified.
        :raises IncorrectCredentials: If the username or password are incorrect.
        """

        self.headers = None

        if password_path:
            with open(password_path, 'rb') as file:
                password = file.read()
        if password is None and password_path is None:
            raise ValueError('Must either have a password or path to the file where a password is saved')

        data = {
            'username': username,
            'password': password
        }

        response = self._make_request('POST', APIRoutes.LOGIN_URL, data=data)

        if response.get('data') is not None:
            try:
                return response['data']['token']
            except TypeError as e:
                if 'NoneType' in str(e) and response.get('error') == 'INCORRECT_CREDENTIALS':
                    raise IncorrectCredentials("Incorrect username or password. Please try again.")
                raise e
        elif response.get('error') == 'INCORRECT_CREDENTIALS':
            raise IncorrectCredentials("Incorrect username or password. Please try again.")
        else:
            raise Exception('Debug This')

    def log_out(self):
        """
        Logs out the current user by invalidating all of their authentication tokens.

        :return: A dictionary containing the response from the server.
        :rtype: dict
        """

        url = f'{APIRoutes.AUTH_URL}/invalidate_tokens'
        response = self._make_request('POST', url)

        if response['status'] == 'ok':
            print('Successfully logged out user')
            return response
        elif response['status'] == 'error':
            self._check_errors(response)
        else:
            raise Exception('Debug This')

    # Role Functions

    def get_all_roles(self):
        """
        Retrieves a list of all roles.

        :return: A list containing dictionaries, with each dictionary representing a role.
        :rtype: list[dict]
        """

        return self._make_request('GET', APIRoutes.ROLES_URL)['data']

    def create_role(self, name, server_ids, permissions):
        """
        Create a new role.

        :param name: The name of the new role.
        :type name: str
        :param server_ids: A list of server IDs that the role will apply to. If only one ID is given, it does not need
            to be a list.
        :type server_ids: list[int] | int
        :param permissions: A string of eight binary digits representing permissions for commands, terminal, logs,
            schedule, backup, files, config, and players. A value of 1 indicates permission is granted, while 0
            indicates it is denied. For example, the string '101110010' would grant permissions for commands, logs,
            schedule, files, and players, but deny permissions for terminal, backup, and config.
        :type permissions: str | int
        :return: A dictionary containing the response from the server.
        :rtype: dict
        """
        if isinstance(server_ids, (int, str)):
            server_ids = [server_ids]
        elif isinstance(server_ids, list):
            pass
        else:
            raise TypeError(f'"server_ids" must be of type list[int], instead received type {type(server_ids)}')

        servers = [
            {'server_id': int(server_id), 'permissions': str(permissions)} for server_id in server_ids]
        data = {
            'name': name,
            'servers': servers
        }

        return self._make_request('POST', APIRoutes.ROLES_URL, data=data)

    def get_role(self, role_id):
        """
        Retrieves information about the role corresponding to the given role ID.

        :param role_id: The ID of the role to retrieve.
        :type role_id: int | str
        :return: A dictionary containing information about the role.
        :rtype: dict
        """

        if not isinstance(role_id, (int, str)):
            raise TypeError(f'Expected "role_id" to be of type int or str, but got {type(role_id)} instead')

        url = f'{APIRoutes.ROLES_URL}/{role_id}'
        return self._make_request('GET', url)['data']

    def get_roles_servers(self, role_id):
        """
        Retrieve a list of all servers that the role corresponding to the given role ID has access to.

        :param role_id: The ID of the role to retrieve servers for.
        :type role_id: int | str
        :return: A list containing dictionaries, where each dictionary represents a server that the role has access to
            along with its respective permissions.
        :rtype: list[dict]
        """

        if not isinstance(role_id, (int, str)):
            raise TypeError(f'Expected "role_id" to be of type int or str, but got {type(role_id)} instead')

        url = f'{APIRoutes.ROLES_URL}/{role_id}/servers'
        return self._make_request('GET', url)['data']

    def get_role_users(self, role_id):
        """
        Retrieves a list of user IDs with access to the role corresponding to the given role ID.

        :param role_id: The ID of the role to retrieve users for (can be either an int or a str).
        :type role_id: int | str
        :return: A list of user IDs that have access to the role
        :rtype: list[int]
        """

        if not isinstance(role_id, (int, str)):
            raise TypeError(f'Expected "role_id" to be of type int or str, but got {type(role_id)} instead')

        url = f'{APIRoutes.ROLES_URL}/{role_id}/users'
        return self._make_request('GET', url)['data']

    def delete_role(self, role_id):
        """
        Deletes the role corresponding to the given role ID.

        :param role_id: The ID of the role to be deleted.
        :type role_id: int | str
        :return: A dictionary containing the response from the server.
        :rtype: dict
        :raises AccessDenied: If the user does not have permission to delete roles. (Superuser required)
        """

        if not isinstance(role_id, (int, str)):
            raise TypeError(f'Expected "role_id" to be of type int or str, but got {type(role_id)} instead')

        url = f'{APIRoutes.ROLES_URL}/{role_id}'
        response = self._make_request('DELETE', url)
        if response['status'] == 'ok':
            print(f'Successfully Removed Role with role ID: {role_id}')
        return response

    def modify_role(self, role_id, name=None, server_ids=None, permissions=None):
        """
        Modifies the properties of the role corresponding to the given role ID.

        :param role_id: The ID of the role to modify.
        :type role_id: int | str
        :param name: The new name for the role, default is None.
        :type name: str, optional
        :param server_ids: A list of server IDs to modify role permissions for (role must have access to the servers),
            default is None. If modifying server permissions, both 'server_ids' and 'permissions' must be fulfilled.
        :type server_ids: list[int] | int, optional
        :param permissions: A binary string or list of binary strings that represent the role's permissions for
            commands, terminal, logs, schedule, backup, files, config, and players respectively. The string(s)
            can either represent the permissions to be set for every server or the permissions for each server
            individually, depending on whether server_ids is a single ID or a list of IDs. If permissions is a single
            string, it will be applied to all servers specified in server_ids. If permissions is a list of strings,
            it must be of the same length as server_ids and each string will be applied to the corresponding server.
            Default is None.
        :type permissions: list[str] | str, optional
        :return: A dictionary containing the response from the server.
        :rtype: dict
        :raises ValueError: If either server_ids or permissions is None while the other is not.
        :raises ValueError: If server_ids and permissions do not have the same length if they are both lists
        :raises AccessDenied: If the user does not have the necessary permissions to modify the role.
        """

        if not isinstance(role_id, (int, str)):
            raise TypeError(f'Expected "role_id" to be of type int or str, but got {type(role_id)} instead')
        if not isinstance(name, str) and name is not None:
            raise TypeError(f"'name' must be of type string, instead was of type {type(name)}")
        if (server_ids is None and permissions is not None) or (server_ids is not None and permissions is None):
            raise ValueError("Both 'server_ids' and 'permissions' must be either provided or None.")
        elif server_ids is not None and permissions is not None:
            if isinstance(server_ids, int):
                server_ids = [server_ids]
            elif not isinstance(server_ids, list):
                raise TypeError(f"'server_ids' must either be of type int or a list of int instead was of type "
                                f"{type(server_ids)}")
            if isinstance(permissions, str):
                permissions = [permissions] * len(server_ids)
            elif isinstance(permissions, int):
                permissions = str(permissions)
            elif not isinstance(permissions, (str, list)):
                raise TypeError(f"'permissions' must either be of type str or a list of str instead was of type "
                                f"{type(permissions)}")
            elif len(permissions) != len(server_ids):
                raise ValueError(
                    '''If 'server_ids' and 'permissions' are both provided as lists, they must have the same length.
                        Otherwise permissions can be a single string if the role should have the same permissions for
                        all servers.''')

        url = f'{APIRoutes.ROLES_URL}/{role_id}'
        data = {}
        if name is not None:
            data['name'] = name
        if server_ids is not None:
            data['servers'] = []
            for i in range(len(server_ids)):
                server_dict = {'id': server_ids[i], 'permissions': permissions[i]}
                data['servers'].append(server_dict)

        return self._make_request('PATCH', url, data=data)

    # Server Functions

    def get_all_servers(self):
        """
        Retrieves a list of all servers.

        :return: A list of dictionaries, where each dictionary represents a server and its properties.
        :rtype: list[dict]
        :raises AccessDenied: If the user does not have the necessary permissions to retrieve server information.
        """

        return self._make_request('GET', APIRoutes.SERVERS_URL)['data']

    # Create a Server
    # TODO: Fix this Mess
    # def create_server(self, name, create_type, version, server_type, mem_min, mem_max,
    #                   server_properties_port=25565, port=25565, host="127.0.0.1",
    #                   monitoring_type=None, motd='', ip=None, path='', extra=None):
    #     if create_type == 'minecraft_bedrock' and port == 25565:
    #         port = 19132
    #     if monitoring_type is None: monitoring_type=create_type
    #     data = {
    #         "name": name,
    #         "monitoring_type": monitoring_type,
    #         f"{monitoring_type}_monitoring_data": {
    #             "host": host,
    #             "port": port
    #         },
    #         "create_type": create_type,
    #
    #     }
    #     if create_type == 'download_jar':
    #         f'{type}'
    #         data['download_jar_create_data']: {
    #             "type": server_type,
    #             "version": version,
    #             "mem_min": mem_min,
    #             "mem_max": mem_max,
    #             "server_properties_port": server_properties_port,
    #             "agree_to_eula": True
    #         }
    #     elif create_type == 'import_server':
    #         data['import_server_create_data']: {
    #             'existing_server_path': path,
    #             'command': command
    #         }
    #     return self._make_request('POST', APIRoutes.SERVERS_URL, data=data)

    def get_server(self, server_id):
        """
        Retrieves information about the server corresponding to the specified server ID.

        :param server_id: The ID of the server to retrieve information for.
        :type server_id: int | str
        :return: A dictionary containing information about the server.
        :rtype: dict
        :raises AccessDenied: If the user does not have permission to access the specified server.
        """

        if not isinstance(server_id, (int, str)):
            raise TypeError(f'Expected "server_id" to be of type int or str, but got {type(server_id)} instead')

        url = f'{APIRoutes.SERVERS_URL}/{server_id}'
        return self._make_request('GET', url)['data']

    def delete_server(self, server_id):
        """
        Deletes the server corresponding to the specified server ID.

        :param server_id: The ID of the server to be deleted.
        :type server_id: int | str
        :return: A message confirming the deletion of the server.
        :rtype: str
        :raises ServerNotFound: If the server with the specified ID does not exist.
        :raises AccessDenied: If the user does not have the necessary permissions to delete the server.
        """

        if not isinstance(server_id, (int, str)):
            raise TypeError(f'Expected "server_id" to be of type int or str, but got {type(server_id)} instead')

        url = f'{APIRoutes.SERVERS_URL}/{server_id}'
        response = self._make_request('DELETE', url)
        if response['status'] == 'ok':
            print(f'Successfully Removed Server with server ID: {server_id}')
        return response

    # TODO: Fix this docstring
    def modify_server(self, server_id, data):
        """
        Modify a server with the given server_id using the specified data.

        Args:
            server_id (int): The ID of the server to modify.
            data (dict): A dictionary of changes to make to the server. Possible keys include:
                - server_name (str): The name of the server.
                - path (str): The path to the server files.
                - backup_path (str): The path to the backup files.
                - executable (str): The name of the server executable.
                - log_path (str): The path to the server logs.
                - execution_command (str): The command to start the server.
                - auto_start (bool): Whether the server should start automatically.
                - auto_start_delay (int): The delay (in seconds) before automatic startup.
                - crash_detection (bool): Whether to detect server crashes.
                - stop_command (str): The command to stop the server.
                - executable_update_url (str): The URL to update the server executable.
                - server_ip (str): The IP address of the server.
                - server_port (int): The port of the server.
                - logs_delete_after (int): The number of days to keep server logs.
                - type (str): The type of server (e.g. 'minecraft_java', 'minecraft_bedrock', etc.).
                - show_status (bool): Whether to show the server status in the dashboard.
                - shutdown_timeout (int): The number of seconds to wait before shutting down the server.
        """

        if not isinstance(server_id, (int, str)):
            raise TypeError(f'Expected "server_id" to be of type int or str, but got {type(server_id)} instead')

        url = f"{APIRoutes.SERVERS_URL}/{server_id}"
        valid_keys = ['server_name', 'path', 'backup_path', 'executable', 'log_path', 'execution_command', 'auto_start',
                      'auto_start_delay', 'crash_detection', 'stop_command', 'executable_update_url', 'server_ip',
                      'server_port', 'logs_delete_after', 'type', 'show_status', 'shutdown_timeout']
        payload = {key: data[key] for key in valid_keys if key in data}
        return self._make_request('PATCH', url, data=payload)

    def send_server_action(self, server_id, action):
        """
        Sends an action to the server corresponding to the specified server ID.

        :param server_id: The ID of the server to send the action to.
        :type server_id: int | str
        :param action: The action to send to the server. Valid actions are: clone_server, start_server, stop_server,
        restart_server, kill_server, backup_server, update_executable.
        :type action: str
        :return: A dictionary containing the response from the server.
        :rtype: dict
        :raises ValueError: If the action is not a valid action. Valid actions are: clone_server, start_server,
        stop_server, restart_server, kill_server, backup_server, update_executable.
        """

        valid_actions = ['clone_server', 'start_server', 'stop_server', 'restart_server', 'kill_server',
                         'backup_server', 'update_executable']
        if action not in valid_actions:
            raise ValueError(f'Invalid action "{action}". Valid actions are: {", ".join(valid_actions)}')
        if not isinstance(server_id, (int, str)):
            raise TypeError(f'Expected "server_id" to be of type int or str, but got {type(server_id)} instead')

        url = f'{APIRoutes.SERVERS_URL}/{server_id}/action/{action}'
        return self._make_request('POST', url)

    # TODO: Test this command
    def STDIn_command(self, server_id, data):

        if not isinstance(server_id, (int, str)):
            raise TypeError(f'Expected "server_id" to be of type int or str, but got {type(server_id)} instead')

        url = f'{APIRoutes.SERVERS_URL}/{server_id}/stdin'
        return self._make_request('POST', url, data=data)

    def get_server_logs(self, server_id, file=False, colors=False, raw=False, html=False):
        """
        Retrieves the logs for the server corresponding to the specified server ID.

        :param server_id: The ID of the server to retrieve logs for.
        :type server_id: int | str
        :param file: If True, the logs will be read from the log file instead of stdout, default is False.
        :type file: bool, optional
        :param colors: If True, HTML coloring will be added to the log output, default is False.
        :type colors: bool, optional
        :param raw: If True, ANSI stripping will be disabled, default is False.
        :type raw: bool, optional
        :param html: If True, HTML formatted logs will be returned, default is False.
        :type html: bool, optional
        :return: A dictionary containing the server logs.
        :rtype: dict
        :raises AccessDenied: If the user does not have permission to access server logs.
        """

        if not isinstance(server_id, (int, str)):
            raise TypeError(f'Expected "server_id" to be of type int or str, but got {type(server_id)} instead')

        logs_url = f'{APIRoutes.SERVERS_URL}/{server_id}/logs'

        # Modifies the url to include the optional parameters
        params = {k: v for k, v in [('file', file), ('colors', colors), ('raw', raw), ('html', html)] if v}
        url_params = '&'.join([f'{key}={value}' for key, value in params.items()])
        url = f"{logs_url}?{url_params}" if params else logs_url

        return self._make_request('GET', url)['data']

    def get_server_public_data(self, server_id):
        """
        Retrieves the public data for the server corresponding to the specified server ID.

        :param server_id: The ID of the server to retrieve public data for.
        :type server_id: int | str
        :return: A dictionary containing the public data for the server, including its name, description, server ID,
                 creation date, and server type (e.g. minecraft-java).
        :rtype: dict
        """

        if not isinstance(server_id, (int, str)):
            raise TypeError(f'Expected "server_id" to be of type int or str, but got {type(server_id)} instead')

        url = f'{APIRoutes.SERVERS_URL}/{server_id}/public'
        return self._make_request('GET', url)['data']

    def get_server_stats(self, server_id):
        """
        Retrieves statistics for the server corresponding to the specified server ID.

        :param server_id: The ID of the server to retrieve statistics for.
        :type server_id: int | str
        :return: A dictionary containing the statistics for the server.
        :rtype: dict
        """

        if not isinstance(server_id, (int, str)):
            raise TypeError(f'Expected "server_id" to be of type int or str, but got {type(server_id)} instead')

        url = f'{APIRoutes.SERVERS_URL}/{server_id}/stats'
        return self._make_request('GET', url)['data']

    # TODO: Seemingly Broken
    def get_server_users(self, server_id):
        """
        Retrieves all the users with access to the server corresponding to the specified server ID.

        :param server_id: The ID of the server to retrieve users for.
        :type server_id: int | str
        :return: A dictionary mapping user IDs to usernames.
        :rtype: dict
        """

        if not isinstance(server_id, (int, str)):
            raise TypeError(f'Expected "server_id" to be of type int or str, but got {type(server_id)} instead')

        url = f'{APIRoutes.SERVERS_URL}/{server_id}/users'

        # TODO: Add this:
        # users = self._make_request('GET', url)['data']
        #
        # user_dict = {}
        # for user in users:
        #     user_data = self.get_user(user)
        #     user_dict[user_data['id']] = user_data['username']
        #
        # return user_dict

        return self._make_request('GET', url)['data']

    # TODO: Complete this and the next
    def create_schedule(self, server_id, data):

        if not isinstance(server_id, (int, str)):
            raise TypeError(f'Expected "server_id" to be of type int or str, but got {type(server_id)} instead')

        url = f'{APIRoutes.SERVERS_URL}/{server_id}/tasks'
        return self._make_request('POST', url, data=data)

    def modify_schedule(self, server_id, task_id, data):

        for arg, arg_name in [(server_id, 'server_id'), (task_id, 'task_id')]:
            if not isinstance(arg, (int, str)):
                raise TypeError(f'Expected "{arg_name}" to be of type int or str, but got {type(arg)} instead')

        url = f'{APIRoutes.SERVERS_URL}/{server_id}/tasks/{task_id}'
        return self._make_request('PATCH', url, data=data)

    def remove_schedule(self, server_id, task_id):
        """
        Removes a scheduled task from the server corresponding to the specified server ID.

        :param server_id: The ID of the server to remove the scheduled task from.
        :type server_id: int | str
        :param task_id: The ID of the scheduled task to remove.
        :type task_id: int | str
        :return: A dictionary containing the response from the server.
        :rtype: dict
        """

        for arg, arg_name in [(server_id, 'server_id'), (task_id, 'task_id')]:
            if not isinstance(arg, (int, str)):
                raise TypeError(f'Expected "{arg_name}" to be of type int or str, but got {type(arg)} instead')

        url = f'{APIRoutes.SERVERS_URL}/{server_id}/tasks/{task_id}'
        response = self._make_request('DELETE', url)
        if response['status'] == 'ok':
            print(f'Successfully Removed Schedule with task ID: {task_id}')
        return response

    # User Functions

    def get_all_users(self):
        """
        Retrieves a list of all users in the system.

        :return: A list of dictionaries, each containing information about a user.
        :rtype: list
        """

        return self._make_request('GET', APIRoutes.USERS_URL)['data']

    # TODO: Complete this (Mostly Done) (Check for types)
    def create_user(self, username, password, email=None, enabled=True, hints=True, lang='en_US', roles=None,
                    superuser=False):
        """
        Create a new user in the Crafty system.

        :param username: The username for the new user (required).
        :type username: str
        :param password: The password for the new user (required).
        :type password: str
        :param email: The email address for the new user. Defaults to None.
        :type email: str
        :param enabled: Whether the new user is enabled. Defaults to True.
        :type enabled: bool
        :param hints: Whether hints are enabled for the new user. Defaults to True.
        :type hints: bool
        :param lang: The language for the new user. Defaults to 'en_US'.
        :type lang: str
        :param roles: A list of 'role_ids' for the new user.
        :type roles: list[int] | int
        :param superuser: Whether the new user is a superuser. Defaults to False.
        :type superuser: bool
        :return: A dictionary containing the newly created user's id number (user_id).
        :rtype: dict
        :raises: ValueError if 'roles' contains an invalid role.
        """

        if roles is not None:
            roles_list = self.get_all_roles()
            valid_roles = [str(role['role_id']) for role in roles_list or []]

            roles = [str(role) for role in roles or []]
            invalid_roles = [role for role in roles if role not in valid_roles]
            if invalid_roles:
                raise ValueError(f"Invalid role(s): {', '.join(invalid_roles)}. Valid role(s): "
                                 f"{', '.join(valid_roles)}.")

        data = {
            'username': username,
            'password': password,
            'email': email,
            'enabled': enabled,
            'hints': hints,
            'lang': lang,
            'roles': roles,
            'superuser': superuser,
        }

        data = {key: value for key, value in data.items() if value is not None}
        return self._make_request('POST', APIRoutes.USERS_URL, data=data)

    def get_user(self, user_id):
        """
        Retrieves the user corresponding to the specified user ID.

        :param user_id: The ID number of the user to retrieve.
        :type user_id: int | str
        :return: A dictionary containing the details of the retrieved user.
        :rtype: dict
        """

        if not isinstance(user_id, (int, str)):
            raise TypeError(f'Expected "user_id" to be of type int or str, but got {type(user_id)} instead')

        url = f'{APIRoutes.USERS_URL}/{user_id}'
        return self._make_request('GET', url)['data']

    def delete_user(self, user_id):
        """
        Delete the user corresponding to the specified user ID.

        :param user_id: The ID number of the user to be deleted.
        :type user_id: int | str
        :return: A dictionary containing the response from the server.
        :rtype: dict
        """

        if not isinstance(user_id, (int, str)):
            raise TypeError(f'Expected "user_id" to be of type int or str, but got {type(user_id)} instead')

        url = f'{APIRoutes.USERS_URL}/{user_id}'
        response = self._make_request('DELETE', url)
        if response['status'] == 'ok':
            print(f'Successfully Removed User with user ID: {user_id}')
        return response

    def modify_user(self, user_id, username=None, password=None, email=None, enabled=None, superuser=None, lang=None,
                    hints=None, roles=None, permissions=None):
        """
        Modifies the properties of the user corresponding to the given user ID.

        :param user_id: The ID of the user to modify.
        :type user_id: int | str
        :param username: The new username for the user, default is None.
        :type username: str, optional
        :param password: The new password for the user, default is None.
        :type password: str, optional
        :param email: The new email for the user, default is None.
        :type email: str, optional
        :param enabled: Whether the user is enabled or disabled, default is None.
        :type enabled: bool, optional
        :param superuser: Whether the user has superuser privileges, default is None.
        :type superuser: bool, optional
        :param lang: The new language preference for the user, default is None.
        :type lang: str, optional
        :param hints: Whether the user wants to receive hints or not, default is None.
        :type hints: bool, optional
        :param roles: A list of role IDs to assign to the user, default is None.
        :type roles: list[int] | int, optional
        :param permissions: A dictionary containing the parameters: enabled (bool), name (str), and quantity (int). Name
            should be a three character string for the permissions of 'SERVER_CREATION', 'USER_CONFIG', and
            'ROLES_CONFIG' respectively.
        :type permissions: dict, optional
        :return: A dictionary containing the response from the server.
        :rtype: dict
        :raises AccessDenied: If the user does not have the necessary permissions to modify the user.
        """

        if not isinstance(user_id, (int, str)):
            raise TypeError(f'Expected "user_id" to be of type int or str, but got {type(user_id)} instead')
        if username is not None and not isinstance(username, str):
            raise TypeError(f"Expected 'username' to be of type str, but got {type(username)} instead")
        if password is not None and not isinstance(password, str):
            raise TypeError(f"Expected 'password' to be of type str, but got {type(password)} instead")
        if email is not None and not isinstance(email, str):
            raise TypeError(f"Expected 'email' to be of type str, but got {type(email)} instead")
        if enabled is not None and not isinstance(enabled, bool):
            raise TypeError(f"Expected 'enabled' to be of type bool, but got {type(enabled)} instead")
        if superuser is not None and not isinstance(superuser, bool):
            raise TypeError(f"Expected 'superuser' to be of type bool, but got {type(superuser)} instead")
        if lang is not None and not isinstance(lang, str):
            raise TypeError(f"Expected 'lang' to be of type str, but got {type(lang)} instead")
        if hints is not None and not isinstance(hints, bool):
            raise TypeError(f"Expected 'hints' to be of type bool, but got {type(hints)} instead")
        if roles is not None:
            if isinstance(roles, (int, str)):
                roles = [roles]
            if not isinstance(roles, (int, str, list)):
                raise TypeError(f"Expected 'roles' to be of type list[int], but got {type(roles)} instead")
            roles = [str(role) for role in roles]
        if permissions is not None:
            if not isinstance(permissions, dict):
                raise TypeError(f"Expected 'permissions' to be of type dict, but got {type(permissions)} instead")
            if 'enabled' not in permissions or 'name' not in permissions or 'quantity' not in permissions:
                raise ValueError("permissions dictionary must contain 'enabled', 'name', and 'quantity' keys")
            if not isinstance(permissions["enabled"], bool):
                raise TypeError("The 'enabled' key in the permissions dictionary must be a boolean.")
            if not isinstance(permissions["name"], str):
                raise TypeError("The 'name' key in the permissions dictionary must be a string.")
            if not isinstance(permissions["quantity"], int):
                raise TypeError("The 'quantity' key in the permissions dictionary must be an integer.")

        data = {
            'username': username,
            'password': password,
            'email': email,
            'enabled': enabled,
            'superuser': superuser,
            'lang': lang,
            'hints': hints,
            'roles': roles,
            'permissions': permissions,
        }
        data = {key: value for key, value in data.items() if value is not None}

        url = f'{APIRoutes.USERS_URL}/{user_id}'
        return self._make_request('PATCH', url, data=data)

    def get_user_crafty_permissions(self, user_id):
        """
        Get the Crafty permissions for the user corresponding to the specified user ID.

        :param user_id: The ID of the user to retrieve permissions for.
        :type user_id: int | str
        :return: A dictionary containing the user's Crafty permissions.
        :rtype: dict
        """

        if not isinstance(user_id, (int, str)):
            raise TypeError(f'Expected "user_id" to be of type int or str, but got {type(user_id)} instead')

        url = f'{APIRoutes.USERS_URL}/{user_id}/permissions'
        return self._make_request('GET', url)['data']

    def get_user_profile_picture(self, user_id):
        """
        Retrieve the profile picture for the user corresponding to the specified user ID.

        :param user_id: The user ID of the user to retrieve the profile picture for.
        :type user_id: int | str
        :return: A link to the profile picture of the user corresponding to the specified user ID.
        :rtype: str
        """

        if not isinstance(user_id, (int, str)):
            raise TypeError(f'Expected "user_id" to be of type int or str, but got {type(user_id)} instead')

        url = f'{APIRoutes.USERS_URL}/{user_id}/pfp'
        return self._make_request('GET', url)['data']

    def get_user_public_data(self, user_id):
        """
        Retrieve the public data for the user corresponding to the specified user ID.

        :param user_id: The user ID of the user to retrieve the public data for.
        :type user_id: int or str
        :return: A dictionary containing the public data of the requested user.
        :rtype: dict
        """

        url = f'{APIRoutes.USERS_URL}/{user_id}/public'
        return self._make_request('GET', url)['data']

    # Test Functions

    # TODO: Delete this
    def test_foo(self, method, url, data=None):
        return self._make_request(method, url, data=data)

    # TODO: Add in default schema values with 'https://json-schema-faker.js.org/'
    def json_schema(self, schema):
        """
        Retrieves a JSON schema for a given endpoint.

        :param schema: A string representing the schema to retrieve.
                       Must be one of ['login', 'modify_role', 'create_role', 'server_patch', 'new_server',
                       'user_patch', 'new_user'].
        :return: A dictionary representing the JSON schema for the given endpoint.
        :raises ValueError: If the input `schema` is not a valid option.
        :raises TypeError: If the input 'schema' is not a string.
        """

        valid_schemas = ['login', 'modify_role', 'create_role', 'server_patch', 'new_server', 'user_patch', 'new_user',
                         'new_task', 'patch_task']

        if not isinstance(schema, str):
            raise TypeError(f"Expected `schema` to be a string, but got {type(schema)}")

        if schema not in valid_schemas:
            raise ValueError(f"Invalid schema. Must be one of the following: {valid_schemas}")

        url = f'{APIRoutes.SCHEMA_URL}/{schema}'
        return self._make_request('GET', url)
