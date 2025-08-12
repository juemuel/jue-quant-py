class DataProviderError(Exception):
    def __init__(self, message="数据源错误", detail=None, status_code=500):
        self.message = message
        self.detail = detail or message
        self.status_code = status_code
        super().__init__(self.message)


class DataEmptyError(DataProviderError):
    def __init__(self, message="未找到匹配的数据", detail=None):
        super().__init__(message=message, detail=detail, status_code=204)


class DataFieldMissingError(DataProviderError):
    def __init__(self, field_name=None, source=None):
        message = f"数据源 '{source}' 返回结果中缺少必要字段: {field_name}"
        super().__init__(message=message, detail=message, status_code=500)


class DataAccessDeniedError(DataProviderError):
    def __init__(self, source=None):
        message = f"没有访问 '{source}' 数据源的权限"
        super().__init__(message=message, detail=message, status_code=403)


class InvalidParameterError(DataProviderError):
    def __init__(self, message="无效的参数"):
        super().__init__(message=message, detail=message, status_code=400)
