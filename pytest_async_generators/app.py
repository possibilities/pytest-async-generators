import strawberry
import typing
import asyncio
from aiohttp import web
from strawberry.aiohttp.views import GraphQLView


@strawberry.type
class Count:
    count: int


def get_count(root) -> Count:
    return Count(count=222)


@strawberry.type
class Query:
    foo: Count = strawberry.field(resolver=get_count)


@strawberry.type
class Subscription:
    @strawberry.subscription
    async def count(self, target: int = 100) -> typing.AsyncGenerator[int, None]:
        for i in range(target):
            yield i
            await asyncio.sleep(0.5)


def create_app() -> web.Application:
    app = web.Application()

    app.router.add_route(
        "*",
        "/graphql",
        handler=GraphQLView(
            schema=strawberry.Schema(
                query=Query,
                subscription=Subscription,
            ),
            graphiql=True,
        ),
    )

    return app
