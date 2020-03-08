#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio

from aiohttp.client import ClientSession

from typing import List, Optional

from dataclasses import dataclass


@dataclass(frozen=True)
class IPv4Provider:

    endpoint: str
    key_path: str


class GoogleWifi(IPv4Provider):

    endpoint = 'http://onhub.here/api/v1/status'
    key_path = 'wan.localIpAddress'


class AmazonAWS(IPv4Provider):

    endpoint = 'https://checkip.amazonaws.com'
    key_path = ''


class IPEcho(IPv4Provider):

    endpoint = 'http://ipecho.net/plain'
    key_path = ''


class IPInfo(IPv4Provider):

    endpoint = 'http://ipinfo.io/ip'
    key_path = ''


class IPify(IPv4Provider):

    endpoint = 'https://api.ipify.org'
    key_path = ''


PROVIDERS = [
    GoogleWifi,
    AmazonAWS,
    IPEcho,
    IPInfo,
    IPify
]


class IPChecker:

    def __init__(self, session: ClientSession, providers: List[IPv4Provider]):
        self._session = session
        self._providers: List[IPv4Provider] = providers

    def register_provider(self, provider: IPv4Provider, index: Optional[int] = None):
        if index is None:
            index = len(self._providers) + 1
        self._providers.insert(index, provider)

    async def get(self) -> Optional[str]:
        for provider in self._providers:
            try:
                ip = await self._check_ip(provider)
            except ConnectionError:
                continue
            except Exception:
                continue
            return ip

    async def _check_ip(self, provider: IPv4Provider) -> str:
        response = await self._session.get(provider.endpoint)
        if not response:
            raise ConnectionError(
                f'Unable to connect to {provider.endpoint}: '
                f'{response.status} {response.reason}'
            )
        if provider.key_path:
            data = await response.json()
            keys = provider.key_path.split('.')
            value = data
            for key in keys:
                value = value.get(key)
        else:
            value = await response.read()
        return value


async def main():
    async with ClientSession() as session:
        checker = IPChecker(session, PROVIDERS)
        ip = await checker.get()
        print(ip)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

