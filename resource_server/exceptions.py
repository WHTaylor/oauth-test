from http import HTTPStatus

class AuthException(Exception):
    def __init__(self,
                 status_code=HTTPStatus.UNAUTHORIZED.value,
                 error='',
                 description='',
                 bearer='example'):
        self.status_code = status_code
        self.message = "Valid bearer token must be supplied"
        self.bearer = bearer
        self.error = error
        self.description = description

    def to_dict(self):
        return {'message': self.message}

    def to_header_string(self):
        error = f'error="{self.error}"' if self.error else "" 
        description =  f"error_description={self.description}" if self.description else ""
        return ", ".join([f'realm="{self.bearer}"', error, description])


class InvalidToken(AuthException):
    def __init__(self, description='', bearer='example'):
        super().__init__(error='invalid_token', description=description, bearer=bearer)


class InsufficientScope(AuthException):
    def __init__(self, description='', bearer='example'):
        super().__init__(status_code=HTTPStatus.FORBIDDEN.value, error='insufficient_scope', description=description, bearer=bearer)
