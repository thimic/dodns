#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import traceback
import uvloop

from aiohttp.client import ClientSession
from concurrent.futures import ThreadPoolExecutor

import asyncclick as click

from dataclasses import dataclass
from typing import List

from digitalocean import Manager

from dodns.external_ip import IPChecker, PROVIDERS


asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


@dataclass(frozen=True)
class Record:

    name: str
    type: str = 'A'
    ttl: int = 3600


def update_records(records: List[Record], ipv4: str):
    manager = Manager()
    domains = manager.get_all_domains()
    for record in records:
        assert record.ttl >= 30, 'Unable to set a ttl lower than 30.'
        assert record.type == 'A', 'Only A records (IPv4) are currently supported.'
        domain = None
        sub_domain = None
        for domain in domains:
            if not record.name.endswith(domain.name):
                continue
            sub_domain_raw, _ = record.name.split(domain.name)
            if sub_domain_raw:
                sub_domain = sub_domain_raw.strip('.')
            else:
                sub_domain = '@'
            break
        if not sub_domain:
            raise ValueError(
                f'Unable to find find registered domain name for record '
                f'{record!r}'
            )
        do_records = domain.get_records()
        do_records_filtered = [
            r for r in do_records if r.name == sub_domain and r.type == record.type
        ]
        if not do_records_filtered:
            raise ValueError(
                f'Unable to find record {sub_domain!r} for domain '
                f'{domain!r}'
            )
        do_record = do_records_filtered[0]
        if do_record.data == ipv4 and do_record.ttl == record.ttl:
            click.echo(f'Record {record.name!r} is up to date. Skipping update.')
            return
        do_record.data = ipv4
        do_record.ttl = record.ttl
        do_record.save()
        click.echo(f'Updated {record.name!r} with ip {ipv4} and ttl {record.ttl}')


async def in_thread(executor, func, *args):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, func, *args)


@click.command()
@click.option(
    '-r',
    '--record',
    'raw_records',
    multiple=True,
    help='Digital Ocean domain record to update'
)
@click.option(
    '-t',
    '--ttl',
    type=int,
    default=3600,
    show_default=True,
    help='Record time to live in seconds. Minimum 30.'
)
async def main(raw_records: List[str], ttl=30):
    records = [Record(r, ttl=ttl) for r in raw_records]
    async with ClientSession() as session:
        with ThreadPoolExecutor(max_workers=2) as executor:
            ip_checker = IPChecker(session, PROVIDERS)
            while True:
                try:
                    ip = await ip_checker.get()
                    await in_thread(executor, update_records, records, ip)
                    await asyncio.sleep(30)
                except Exception:
                    traceback.print_exc()
                    continue


if __name__ == '__main__':
    main(_anyio_backend='asyncio')
