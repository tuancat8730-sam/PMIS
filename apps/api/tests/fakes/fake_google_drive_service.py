from typing import Any


class _Request:
    def __init__(self, service: "FakeGoogleDriveService", params: dict[str, Any]) -> None:
        self._service = service
        self._params = params

    def execute(self) -> dict[str, Any]:
        return self._service.next_response(self._params)


class _FilesResource:
    def __init__(self, service: "FakeGoogleDriveService") -> None:
        self._service = service

    def list(self, **params: Any) -> _Request:
        return _Request(self._service, params)

    def create(self, **params: Any) -> _Request:
        return _Request(self._service, params)

    def update(self, **params: Any) -> _Request:
        return _Request(self._service, params)


class FakeGoogleDriveService:
    """Thay thế service `googleapiclient`: trả lần lượt phản hồi, ném lỗi nếu gặp Exception."""

    def __init__(self, responses: list[dict[str, Any] | Exception]) -> None:
        self._responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    def files(self) -> _FilesResource:
        return _FilesResource(self)

    def next_response(self, params: dict[str, Any]) -> dict[str, Any]:
        self.calls.append(params)
        response = self._responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response
