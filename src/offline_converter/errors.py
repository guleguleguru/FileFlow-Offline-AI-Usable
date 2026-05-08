from __future__ import annotations


class FileFlowError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        code: str = "conversion_failed",
        action: str = "请查看日志，确认输入文件和依赖组件是否可用。",
        detail: str = "",
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.action = action
        self.detail = detail

    def to_payload(self) -> dict[str, str]:
        return {
            "code": self.code,
            "message": self.message,
            "action": self.action,
            "detail": self.detail,
        }


def error_payload(exc: BaseException) -> dict[str, str]:
    if isinstance(exc, FileFlowError):
        return exc.to_payload()
    return FileFlowError(str(exc), detail=exc.__class__.__name__).to_payload()
