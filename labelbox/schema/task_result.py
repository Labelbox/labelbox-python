from typing import Dict, List


class BulkTaskResult:
    status: str = None
    success: List[Dict[str, str]] = None
    errors: Dict[str, List[str]] = None

    def __init__(self, status, success, errors):
        self.status = status
        self.success = success
        self.errors = errors

    def __repr__(self) -> str:
        return  f"BulkTaskResult(status={self.status}," \
                f"success={self.success}," \
                f"errors={self.errors})"