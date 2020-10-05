from asyncio import sleep
from typing import Set
from urllib.parse import urljoin

import httpx

from regbot.helpers import get_str_env

USERNAME = get_str_env("WAFER_USERNAME")
PASSWORD = get_str_env("WAFER_PASSWORD")
BASE_URL = get_str_env("WAFER_BASE_URL")
TICKETS_URL = get_str_env("WAFER_TICKETS_ENDPOINT")
TALKS_URL = get_str_env("WAFER_TALKS_ENDPOINT")


SPEAKERS_TICKETS: Set[str] = set()


async def update_speakers_cache() -> None:
    """Update the speakers cache from Wafer"""
    async with httpx.AsyncClient() as client:
        speakers_uids: Set[int] = set()

        next_url = urljoin(BASE_URL, TALKS_URL)
        while next_url is not None:
            r = await client.get(next_url, auth=(USERNAME, PASSWORD))
            d = r.json()
            for result in d["results"]:
                speakers_uids = speakers_uids.union(set(result["authors"]))
            next_url = d["next"]
            if next_url is not None:
                await sleep(
                    1.5
                )  # PyConZA is prone to network errors if not rate limiting

        await sleep(1.5)  # PyConZA is prone to network errors if not rate limiting
        next_url = urljoin(BASE_URL, TICKETS_URL)
        while next_url is not None:
            r = await client.get(next_url, auth=(USERNAME, PASSWORD))
            d = r.json()
            for result in d["results"]:
                if result["user"] in speakers_uids:
                    SPEAKERS_TICKETS.add(result["barcode"])
            next_url = d["next"]
            if next_url is not None:
                await sleep(
                    1.5
                )  # PyConZA is prone to network errors if not rate limiting


async def is_barcode_belong_to_speaker(barcode: str) -> bool:
    """Check if the given barcode is of a ticket owned by a speaker."""
    return barcode in SPEAKERS_TICKETS
