import logging
import re
from functools import lru_cache
from typing import Any

from ..clients.java_api import JavaApiClient, JavaApiError
from .order import get_order_service


logger = logging.getLogger(__name__)


class AfterSalesService:
    def __init__(self, java_api: JavaApiClient | None = None):
        self.java_api = java_api or JavaApiClient()

    def get_after_sales_status(self, order_id: str | int) -> dict[str, Any]:
        order_result = get_order_service().get_order_detail(order_id)
        if not order_result.get("success"):
            order_result["action"] = "after_sales_status"
            return order_result

        order = order_result.get("data") or {}
        status = order.get("status")
        order_result["action"] = "after_sales_status"
        order_result["data"] = {
            "orderId": order.get("id"),
            "orderNo": order.get("orderNo"),
            "orderStatus": status,
            "cancelReason": order.get("cancelReason"),
            "cancelTime": order.get("cancelTime"),
            "hasAfterSalesEndpoint": False,
            "message": self._status_message(status),
            "order": order,
        }
        return order_result

    def get_recent_product_refund_rates(self, days: int = 30, limit: int = 10) -> dict[str, Any]:
        normalized_days = self._bounded_int(days, 1, 365, 30)
        normalized_limit = self._bounded_int(limit, 1, 50, 10)
        result = self._call_java(
            "recent_product_refund_rates",
            self.java_api.get_recent_product_refund_rates,
            normalized_days,
            normalized_limit,
        )
        if result.get("success"):
            result["data"] = self._enrich_refund_payload(result.get("data"), normalized_days, normalized_limit)
        return result

    def get_recent_category_refund_rates(self, days: int = 30, limit: int = 10) -> dict[str, Any]:
        normalized_days = self._bounded_int(days, 1, 365, 30)
        normalized_limit = self._bounded_int(limit, 1, 50, 10)
        result = self._call_java(
            "recent_category_refund_rates",
            self.java_api.get_recent_category_refund_rates,
            normalized_days,
            normalized_limit,
        )
        if result.get("success"):
            result["data"] = self._enrich_refund_payload(result.get("data"), normalized_days, normalized_limit)
        return result

    def create_after_sales_request(self, request_summary: str) -> dict[str, Any]:
        order_id = self._extract_order_id(request_summary)
        order_reference: dict[str, Any] | None = None
        if order_id is not None:
            order_reference = get_order_service().get_order_status(order_id)

        return {
            "success": False,
            "source": "java_api",
            "action": "create_after_sales_request",
            "message": "Java has not exposed an after-sales creation endpoint yet.",
            "data": {
                "requestSummary": request_summary,
                "extractedOrderId": order_id,
                "orderReference": order_reference,
                "nextRequiredJavaEndpoint": "POST /api/agent/after-sales",
            },
        }

    def _call_java(self, action: str, func, *args: Any) -> dict[str, Any]:
        try:
            payload = func(*args)
        except JavaApiError as exc:
            logger.warning("after-sales service java call failed action=%s status=%s error=%s", action, exc.status_code, exc)
            return self._error(action, str(exc), status_code=exc.status_code)
        except Exception as exc:
            logger.exception("after-sales service unexpected failure action=%s", action)
            return self._error(action, "After-sales service failed unexpectedly.", error=str(exc))

        return {
            "success": True,
            "source": "java_api",
            "action": action,
            "data": payload,
        }

    @staticmethod
    def _extract_order_id(text: str) -> int | None:
        match = re.search(r"\d+", text or "")
        if not match:
            return None
        value = int(match.group())
        return value if value > 0 else None

    @staticmethod
    def _bounded_int(value: Any, minimum: int, maximum: int, default: int) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return default
        return max(minimum, min(maximum, parsed))

    @staticmethod
    def _enrich_refund_payload(payload: Any, days: int, limit: int) -> dict[str, Any]:
        if isinstance(payload, dict):
            enriched = dict(payload)
        else:
            enriched = {"records": payload if isinstance(payload, list) else []}

        records = enriched.get("records") if isinstance(enriched.get("records"), list) else []
        enriched["days"] = enriched.get("days", days)
        enriched["limit"] = limit
        enriched["topRecord"] = records[0] if records else None
        enriched["topRefundRate"] = records[0].get("refundRate") if records and isinstance(records[0], dict) else None
        return enriched

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

    @staticmethod
    def _status_message(status: Any) -> str:
        try:
            parsed = int(status)
        except (TypeError, ValueError):
            return "Unable to derive after-sales status from this order."

        if parsed in (4, 5):
            return "The order is already cancelled or closed; use cancelReason/cancelTime as the current reference."
        if parsed in (0, 1):
            return "No dedicated after-sales record is exposed. The order may still be handled through payment/shipment cancellation flow."
        if parsed in (2, 3):
            return "No dedicated after-sales record is exposed. Only order shipment/completion data is currently available."
        return "No dedicated after-sales record is exposed for this order status."


@lru_cache
def get_after_sales_service() -> AfterSalesService:
    return AfterSalesService()
