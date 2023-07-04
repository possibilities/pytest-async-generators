import asyncio
import pytest
from typing import Any, AsyncGenerator, Callable
import os
import asyncio
import pytest
import pytest_asyncio
import websockets
import re
import json
import uuid
from types import TracebackType
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport
from gql.transport.websockets import WebsocketsTransport
from gql import gql, Client
from aiohttp.test_utils import TestServer
from pytest_async_generators.app import create_app
from typing import (
    Self,
    Optional,
    Coroutine,
    Type,
    Any,
    Dict,
    Callable,
    Awaitable,
    List,
    cast,
)


@pytest_asyncio.fixture
async def server(
    aiohttp_server: Callable[..., Awaitable[TestServer]],
) -> TestServer:
    return await aiohttp_server(create_app())


def _get_graphql_query_operation_name(query_string: str) -> str:
    match = re.search(r"(subscription)\s+(\w+)", query_string)
    if not match:
        raise Exception("Operation name couldn't be found for query: \n {query_string}")
    return match.group(2)


# class SubscriptionMessagesListener:
#     def __init__(self, subscription_coroutine: Coroutine) -> None:
#         self._subscription: asyncio.Task = asyncio.create_task(subscription_coroutine)

#     async def __aenter__(self: Self) -> Self:
#         await asyncio.sleep(1)
#         return self

#     async def __aexit__(
#         self,
#         exc_type: Optional[Type[BaseException]],
#         exc_val: Optional[BaseException],
#         exc_tb: Optional[TracebackType],
#     ) -> Optional[bool]:
#         pass

#     async def wait_for_messages(self: Self) -> List[Dict[str, Any]]:
#         exception = self._subscription.exception()
#         if exception:
#             raise exception
#         messages = self._subscription.result()
#         self._subscription.cancel()
#         return messages


# @pytest_asyncio.fixture
# async def subscription_messages() -> Callable:
#     def collect_messages(
#         subscription_coroutine: Coroutine,
#     ) -> SubscriptionMessagesListener:
#         return SubscriptionMessagesListener(subscription_coroutine)

#     return collect_messages


@pytest_asyncio.fixture
async def broken_client(
    broken_server: TestServer,
) -> Callable:
    transport = AIOHTTPTransport(url=f"http://localhost:{broken_server.port}/graphql")
    api_client = Client(transport=transport, fetch_schema_from_transport=True)

    async def run_api_query(
        raw_query: str, variable_values: Dict[str, Any] | None = {}
    ) -> Dict[str, Any]:
        query = gql(raw_query)
        response = await api_client.execute_async(
            query,
            variable_values=variable_values,
        )

        return next(iter(response.values()))

    return run_api_query


class EventBusWithAsyncGenerator:
    def __init__(self) -> None:
        self.queue: asyncio.Queue = asyncio.Queue()

    async def send_message(self, event: Any) -> None:
        await self.queue.put(event)

    async def to_async_generator(self) -> AsyncGenerator[Any, None]:
        while True:
            yield await self.queue.get()


@pytest.mark.asyncio
async def test_fake_generator(subscribe_to_messages: Callable) -> None:
    event_bus = EventBusWithAsyncGenerator()

    subscription = await subscribe_to_messages(event_bus.to_async_generator())

    await asyncio.sleep(0.10)
    await event_bus.send_message("first-message")
    await asyncio.sleep(0.11)
    await event_bus.send_message("second-message")
    await asyncio.sleep(0.12)
    await event_bus.send_message("third-message")

    [message_1, message_2, message_3] = await subscription.wait_for_messages()

    assert message_1 == "first-message"
    assert message_2 == "second-message"
    assert message_3 == "third-message"


async def count() -> AsyncGenerator[int, None]:
    for n in range(10):
        await asyncio.sleep(0.1)
        yield n


@pytest.mark.asyncio
async def test_realish_generator(subscribe_to_messages: Callable) -> None:
    subscription = await subscribe_to_messages(count())
    messages = await subscription.wait_for_messages()
    assert messages == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]


@pytest_asyncio.fixture
async def websocket_transport(server):
    transport = WebsocketsTransport(
        url=f"ws://localhost:{server.port}/graphql", close_timeout=0.1
    )
    yield transport
    await transport.close()


@pytest.fixture
def subscription_client(websocket_transport):
    def _subscription_client(query):
        query = gql(query)
        client = Client(
            transport=websocket_transport, fetch_schema_from_transport=False
        )
        return client.subscribe_async(query)

    return _subscription_client


@pytest.mark.asyncio
async def test_graphql_subscription(
    subscribe_to_messages: Callable, websocket_transport, subscription_client
) -> None:
    subscription = subscription_client(
        "subscription Count { count(target: 3) }",
    )

    subscribing = await subscribe_to_messages(subscription)

    messages = await subscribing.wait_for_messages()
    assert messages == [{"count": 0}, {"count": 1}, {"count": 2}]
