# -*- coding: utf-8 -*-
"""
数据源异常定义

定义数据源层相关异常类。
"""


class DataSourceError(Exception):
    """数据源基础异常"""

    def __init__(self, message: str, source: str = "unknown") -> None:
        self.source = source
        self.message = message
        super().__init__(f"[{source}] {message}")


class JuejinAuthError(DataSourceError):
    """
    掘金认证异常

    Token无效或过期时抛出。
    """

    def __init__(self, message: str = "认证失败，请检查Token是否正确") -> None:
        super().__init__(message, source="juejin")


class JuejinAPIError(DataSourceError):
    """
    掘金API调用异常

    API返回错误或网络异常时抛出。
    """

    def __init__(self, message: str, error_code: int | None = None) -> None:
        self.error_code = error_code
        detail = f"{message} (错误码: {error_code})" if error_code else message
        super().__init__(detail, source="juejin")


class JuejinRateLimitError(DataSourceError):
    """
    掘金请求频率限制异常

    触发API频率限制时抛出。
    """

    def __init__(self, retry_after: int | None = None) -> None:
        self.retry_after = retry_after
        msg = "请求频率超限"
        if retry_after:
            msg += f"，{retry_after}秒后重试"
        super().__init__(msg, source="juejin")
