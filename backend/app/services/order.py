import logging
from functools import lru_cache
from typing import Any

from ..clients.java_api import JavaApiClient, JavaApiError


logger = logging.getLogger(__name__)


ORDER_STATUS_LABELS = {
    0: "pending_payment",
    1: "pending_shipment",
    2: "pending_receipt",
    3: "completed",
    4: "cancelled",
    5: "closed",
}


class OrderService:
    def __init__(self, java_api: JavaApiClient | None = None):
        self.java_api = java_api or JavaApiClient()

    def get_order_detail(self, order_id: str | int) -> dict[str, Any]:
        parsed_order_id = self._positive_int(order_id)
        if parsed_order_id is None:
            return self._error("order_detail", "Please provide a valid positive order id.")
        return self._call_java("order_detail", self.java_api.get_order_by_id, parsed_order_id)

    def get_order_status(self, order_id: str | int) -> dict[str, Any]:
        result = self.get_order_detail(order_id)
        if not result.get("success"):
            result["action"] = "order_status"
            return result

        order = result.get("data") or {}
        result["action"] = "order_status"
        result["data"] = {
            "orderId": order.get("id"),
            "orderNo": order.get("orderNo"),
            "status": order.get("status"),
            "statusText": self._status_text(order.get("status")),
            "payTime": order.get("payTime"),
            "shipTime": order.get("shipTime"),
            "receiveTime": order.get("receiveTime"),
            "completeTime": order.get("completeTime"),
            "cancelTime": order.get("cancelTime"),
            "closeTime": order.get("closeTime"),
            "cancelReason": order.get("cancelReason"),
        }
        return result

    def get_logistics_info(self, order_id: str | int) -> dict[str, Any]:
        result = self.get_order_detail(order_id)
        if not result.get("success"):
            result["action"] = "logistics_info"
            return result

        order = result.get("data") or {}
        result["action"] = "logistics_info"
        result["data"] = {
            "orderId": order.get("id"),
            "orderNo": order.get("orderNo"),
            "status": order.get("status"),
            "statusText": self._status_text(order.get("status")),
            "shipTime": order.get("shipTime"),
            "receiveTime": order.get("receiveTime"),
            "receiver": {
                "name": order.get("receiverName"),
                "phone": order.get("receiverPhone"),
                "province": order.get("receiverProvince"),
                "city": order.get("receiverCity"),
                "district": order.get("receiverDistrict"),
                "detailAddress": order.get("receiverDetailAddress"),
            },
            "tracking": None,
            "message": "Java order API exposes shipment time and receiver address, but no carrier tracking number yet.",
        }
        return result

    def get_recent_order_stats(self, days: int = 7) -> dict[str, Any]:
        normalized_days = self._bounded_int(days, 1, 365, 7)
        result = self._call_java("recent_order_stats", self.java_api.get_recent_order_stats, normalized_days)
        if not result.get("success"):
            return result

        stats = result.get("data") or {}
        result["data"] = {
            "days": stats.get("days", normalized_days),
            "startDate": stats.get("startDate"),
            "endDate": stats.get("endDate"),
            "orderCount": stats.get("orderCount", 0),
            "totalOrderAmount": stats.get("totalOrderAmount", 0),
            "paidOrderCount": stats.get("paidOrderCount", 0),
            "transactionAmount": stats.get("transactionAmount", 0),
            "averageTransactionAmount": stats.get("averageTransactionAmount", 0),
            "hasOrders": stats.get("hasOrders", False),
            "hasPaidOrders": stats.get("hasPaidOrders", False),
        }
        return result

    def _call_java(self, action: str, func, *args: Any) -> dict[str, Any]:
        try:
            payload = func(*args)
        except JavaApiError as exc:
            logger.warning("order service java call failed action=%s status=%s error=%s", action, exc.status_code, exc)
            return self._error(action, str(exc), status_code=exc.status_code)
        except Exception as exc:
            logger.exception("order service unexpected failure action=%s", action)
            return self._error(action, "Order service failed unexpectedly.", error=str(exc))

        return {
            "success": True,
            "source": "java_api",
            "action": action,
            "data": payload,
        }

    @staticmethod
    def _positive_int(value: str | int) -> int | None:
        try:
            parsed = int(str(value).strip())
        except (TypeError, ValueError):
            return None
        return parsed if parsed > 0 else None

    @staticmethod
    def _status_text(status: Any) -> str:
        try:
            return ORDER_STATUS_LABELS.get(int(status), "unknown")
        except (TypeError, ValueError):
            return "unknown"

    @staticmethod
    def _bounded_int(value: Any, minimum: int, maximum: int, default: int) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return default
        return max(minimum, min(maximum, parsed))

    @staticmethod
    def _error(
        action: str,
        message: str,
        status_code: int | None = None,
        error: str | None = None,
    ) -> dict[str, Any]:
        result: dict[str, Any] = {
            "success": False,
            "source": "java_api",
            "action": action,
            "message": message,
            "data": None,
        }
        if status_code is not None:
            result["status_code"] = status_code
        if error:
            result["error"] = error
        return result


@lru_cache
def get_order_service() -> OrderService:
    return OrderService()
