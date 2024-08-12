from __future__ import absolute_import

import json
import os
import re
from unittest.mock import Mock

import elasticapm
import elasticapm.instrumentation.control
from elasticapm.conf import constants
from elasticapm.contrib.asyncio.traces import set_context
from elasticapm.contrib.starlette import ElasticAPM, make_apm_client
from elasticapm.contrib.starlette.utils import get_body, get_data_from_request
from elasticapm.utils.disttracing import TraceParent
from starlette.requests import Request

from configs.app_config import settings


class CustomElasticAPM(ElasticAPM):

    async def _request_started(self, request: Request):
        """Captures the begin of the request processing to APM.

        Args:
            request (Request)
        """
        # When we consume the body, we replace the streaming mechanism with
        # a mocked version -- this workaround came from
        # https://github.com/encode/starlette/issues/495#issuecomment-513138055
        # and we call the workaround here to make sure that regardless of
        # `capture_body` settings, we will have access to the body if we need it.
        if self.client.config.capture_body != "off":
            await get_body(request)

        if not self.client.should_ignore_url(request.url.path):
            trace_parent = TraceParent.from_headers(dict(request.headers))
            self.client.begin_transaction("request", trace_parent=trace_parent)

            await set_context(
                lambda: get_data_from_request(
                    request, self.client.config, constants.TRANSACTION
                ),
                "request",
            )
            body = await request.body()
            body = body.decode("utf-8")
            if body:
                body = json.loads(body)
                if body.get("query"):
                    transaction_name = parse_query(body["query"])
                else:
                    transaction_name = self.get_route_name(request) or request.url.path
            else:
                transaction_name = self.get_route_name(request) or request.url.path
            elasticapm.set_transaction_name(
                "{} {}".format(request.method, transaction_name), override=False
            )


def parse_query(query):
    query_name = re.search(r"query\s+(\w+)", query).group(1)
    matches = re.findall(r"(\w+)\(.*\)\s*{\s*[^}]+\s*}", query)
    return query_name + ": " + " ".join(matches)


def get_apm_client():
    if settings.DEBUG:
        return Mock()
    apm_config = {
        "SERVICE_NAME": "chain-explorer",
        "SERVER_URL": os.environ.get("APM_SERVER_URL", "http://localhost:8200"),
        "ENABLED": True,
        "RECORDING": True,
        "CAPTURE_HEADERS": True,
        "LOG_LEVEL": "INFO",
        "ENVIRONMENT": os.environ.get("ENVIRONMENT", "dev"),
        "CAPTURE_BODY": "all",
    }
    client = make_apm_client(apm_config)
    return client


apm_client = get_apm_client()
