from http import HTTPStatus
import functools
import time
import logging

from prometheus_client import Histogram, Summary

# Initialize logger
logger = logging.getLogger(__name__)

# Define Prometheus metrics
INTEGRATION_HANDLER_QUERY_TIME = Summary(
    'mindsdb_integration_handler_query_seconds',
    'How long integration handlers take to answer queries',
    ('integration', 'response_type')
)

INTEGRATION_HANDLER_RESPONSE_SIZE = Summary(
    'mindsdb_integration_handler_response_size',
    'How many rows are returned by an integration handler query',
    ('integration', 'response_type')
)

REST_API_LATENCY = Histogram(
    'mindsdb_rest_api_latency_seconds',
    'How long REST API requests take to complete, grouped by method, endpoint, and status',
    ('method', 'endpoint', 'status')
)


def api_endpoint_metrics(method: str, uri: str):
    def decorator_metrics(endpoint_func):
        @functools.wraps(endpoint_func)
        def wrapper_metrics(*args, **kwargs):
            start_time = time.perf_counter()
            try:
                response = endpoint_func(*args, **kwargs)
                status = response.status_code if hasattr(response, 'status_code') else HTTPStatus.OK.value
                return response
            except Exception as e:
                logger.error(f"Exception occurred in {endpoint_func.__name__}: {e}")
                status = HTTPStatus.INTERNAL_SERVER_ERROR.value
                raise e
            finally:
                elapsed_time = time.perf_counter() - start_time
                api_latency_with_labels = REST_API_LATENCY.labels(method, uri, status)
                api_latency_with_labels.observe(elapsed_time)
                logger.debug(f"Request to {uri} with method {method} took {elapsed_time:.4f} seconds and resulted in status {status}")
        return wrapper_metrics
    return decorator_metrics
    
