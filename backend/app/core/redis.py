
import redis.asyncio as aioredis

from app.config import settings
from app.core.logging import logger


class RedisManager:
    """Singleton-like manager for the async Redis client."""

    def __init__(self) -> None:
        self.redis_url = settings.REDIS_URL
        self._client: aioredis.Redis | None = None

    def get_client(self) -> aioredis.Redis:
        """Returns or creates the active Redis client instance."""
        if self._client is None:
            logger.info("Initializing async Redis client", url=self.redis_url)
            self._client = aioredis.Redis.from_url(
                self.redis_url, decode_responses=True, socket_timeout=5.0
            )
        return self._client

    async def ping(self) -> bool:
        """Pings the Redis server to verify the connection is alive."""
        try:
            client = self.get_client()
            return await client.ping()
        except Exception as e:
            logger.error("Failed to ping Redis server", error=str(e))
            return False

    async def close(self) -> None:
        """Closes the Redis connection pool."""
        if self._client is not None:
            logger.info("Closing async Redis client")
            await self._client.close()
            self._client = None


# Singleton instance
redis_manager = RedisManager()
