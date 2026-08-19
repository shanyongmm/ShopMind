import logging
from functools import lru_cache
from typing import Any

from ..clients.java_api import JavaApiClient, JavaApiError


logger = logging.getLogger(__name__)


class ProductService:
    def __init__(self, java_api: JavaApiClient | None = None):
        self.java_api = java_api or JavaApiClient()

    def list_top_products(self, limit: int = 5) -> dict[str, Any]:
        return self._call_java("hot_products", self.java_api.list_top_products, max(1, limit))

    def search_products(self, keyword: str) -> dict[str, Any]:
        keyword = keyword.strip()
        if not keyword:
            return self._error("product_search", "Please provide a product keyword.")
        if keyword.isdigit():
            return self._call_java("product_detail", self.java_api.get_product_by_id, int(keyword))

        products_result = self._call_java("product_search", self.java_api.list_products)
        if not products_result.get("success"):
            return products_result

        products = self._as_list(products_result.get("data"))
        matched_products = [product for product in products if self._matches_product(product, keyword)]
        products_result["data"] = {
            "keyword": keyword,
            "count": len(matched_products),
            "items": matched_products[:10],
        }
        return products_result

    def recommend_products(self, requirement: str, limit: int = 10) -> dict[str, Any]:
        requirement = requirement.strip()
        if not requirement:
            return self._error("product_recommendations", "Please provide a product requirement.")
        products_result = self._call_java(
            "product_recommendations",
            self.java_api.recommend_products,
            requirement,
            max(1, limit),
        )
        if not products_result.get("success"):
            return products_result

        products = self._as_list(products_result.get("data"))
        products_result["data"] = {
            "requirement": requirement,
            "count": len(products),
            "items": products,
        }
        return products_result

    def _call_java(self, action: str, func, *args: Any) -> dict[str, Any]:
        try:
            payload = func(*args)
        except JavaApiError as exc:
            logger.warning("product service java call failed action=%s status=%s error=%s", action, exc.status_code, exc)
            return self._error(action, str(exc), status_code=exc.status_code)
        except Exception as exc:
            logger.exception("product service unexpected failure action=%s", action)
            return self._error(action, "Product service failed unexpectedly.", error=str(exc))

        return {
            "success": True,
            "source": "java_api",
            "action": action,
            "data": payload,
        }

    @staticmethod
    def _as_list(payload: Any) -> list[dict[str, Any]]:
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        if isinstance(payload, dict) and isinstance(payload.get("records"), list):
            return [item for item in payload["records"] if isinstance(item, dict)]
        if isinstance(payload, dict) and isinstance(payload.get("items"), list):
            return [item for item in payload["items"] if isinstance(item, dict)]
        return []

    @staticmethod
    def _matches_product(product: dict[str, Any], keyword: str) -> bool:
        haystack = " ".join(
            str(product.get(field) or "")
            for field in ("id", "categoryId", "name", "sku", "description")
        ).lower()
        tokens = [token for token in keyword.lower().replace(",", " ").split() if token]
        if not tokens:
            tokens = [keyword.lower()]
        return any(token in haystack for token in tokens)

    @staticmethod
    def _to_int(value: Any) -> int:
        try:
            return int(value or 0)
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _to_float(value: Any) -> float:
        try:
            return float(value or 0)
        except (TypeError, ValueError):
            return 0.0

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
def get_product_service() -> ProductService:
    return ProductService()
