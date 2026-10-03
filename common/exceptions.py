class BusinessError(Exception):
    """业务异常，携带用户可读消息。"""

    def __init__(self, message: str, code: str = "business_error"):
        self.message = message
        self.code = code
        super().__init__(message)
