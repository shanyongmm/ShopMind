import logging
from typing import Any

import requests

from ..core.config import get_settings


logger = logging.getLogger(__name__)


class JavaApiError(RuntimeError):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class JavaApiClient:
    def __init__(
        self,
        base_url: str | None = None,
        timeout: float | None = None,
        token: str | None = None,
        session: requests.Session | None = None,
    ):
        settings = get_settings()
        self.base_url = (base_url or settings.java_api_base_url).rstrip("/")
        self.timeout = timeout or settings.java_api_timeout
        self.session = session or requests.Session()

        self.session.headers.update({"Accept": "application/json"})
        api_token = token if token is not None else settings.java_api_token
        if api_token:
            self.session.headers.update({"Authorization": f"Bearer {api_token}"})

    def _url(self, path: str) -> str:
        return f"{self.base_url}/{path.lstrip('/')}"

    def request(self, method: str, path: str, **kwargs: Any) -> Any:
        url = self._url(path)
        try:
            response = self.session.request(method, url, timeout=self.timeout, **kwargs)
            response.raise_for_status()
        except requests.Timeout as exc:
            logger.warning("java api timeout method=%s url=%s", method, url)
            raise JavaApiError(f"Java interface request timed out: {method} {url}") from exc
        except requests.RequestException as exc:
            status_code = exc.response.status_code if exc.response is not None else None
            logger.exception("java api request failed method=%s url=%s status=%s", method, url, status_code)
            raise JavaApiError(
                f"Java interface request failed: {method} {url}; reason={exc}",
                status_code=status_code,
            ) from exc

        try:
            payload = response.json()
        except ValueError as exc:
            logger.exception("java api returned non-json response method=%s url=%s", method, url)
            raise JavaApiError("Java interface returned non-json data", status_code=response.status_code) from exc

        logger.info("java api request succeeded method=%s url=%s status=%s", method, url, response.status_code)
        return payload

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        return self.request("GET", path, params=params)

    def post(self, path: str, data: dict[str, Any] | None = None) -> Any:
        return self.request("POST", path, json=data)

    def list_top_products(self, limit: int = 5) -> Any:
        return self.get("/api/agent/product/hot", params={"limit": limit})

    def list_sales_top_products(self, limit: int = 10, params: dict[str, Any] | None = None) -> Any:
        query_params = {"limit": limit}
        if params:
            query_params.update(params)
        return self.get("/api/agent/sales/top-products", params=query_params)

    def list_products(self) -> Any:
        return self.get("/api/agent/product/list")

    def get_product_by_id(self, product_id: int) -> Any:
        return self.get(f"/api/agent/product/{product_id}")

    def get_database_data(self, params: dict[str, Any] | None = None) -> Any:
        return self.get("/api/agent/product/list", params=params)

    def search_products(self, keyword: str) -> Any:
        return self.get("/api/agent/product/list")

    def recommend_products(self, keyword: str | None = None, limit: int = 10) -> Any:
        params: dict[str, Any] = {"limit": limit}
        if keyword:
            params["keyword"] = keyword
        return self.get("/api/agent/product/recommended", params=params)

    def get_order_by_id(self, order_id: int) -> Any:
        return self.get(f"/api/agent/order/{order_id}")

    def get_user_orders(self, user_id: int) -> Any:
        return self.get(f"/api/agent/order/user/{user_id}")

    def get_recent_order_stats(self, days: int = 7) -> Any:
        return self.get("/api/agent/order/stats/recent", params={"days": days})

    def get_sales_summary(self, params: dict[str, Any] | None = None) -> Any:
        return self.get("/api/agent/sales/summary", params=params)

    def get_daily_sales(self, params: dict[str, Any] | None = None) -> Any:
        return self.get("/api/agent/sales/daily", params=params)

    def get_recent_paid_orders(self, limit: int = 10) -> Any:
        return self.get("/api/agent/sales/recent-orders", params={"limit": limit})

    def get_recent_product_refund_rates(self, days: int = 30, limit: int = 10) -> Any:
        return self.get("/api/agent/after-sale/refund-rate/products/recent", params={"days": days, "limit": limit})

    def get_recent_category_refund_rates(self, days: int = 30, limit: int = 10) -> Any:
        return self.get("/api/agent/after-sale/refund-rate/categories/recent", params={"days": days, "limit": limit})
