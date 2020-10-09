from asyncio import sleep
from typing import Optional, Set
from urllib.parse import urljoin
from datetime import datetime

import httpx
from ics import Calendar, Event
from pytz import utc

from regbot.helpers import get_str_env

USERNAME = get_str_env("WAFER_USERNAME")
PASSWORD = get_str_env("WAFER_PASSWORD")
BASE_URL = get_str_env("WAFER_BASE_URL")
TICKETS_URL = get_str_env("WAFER_TICKETS_ENDPOINT")
TALKS_URL = get_str_env("WAFER_TALKS_ENDPOINT")
ICS_ENDPOINT = get_str_env("WAFER_ICS_ENDPOINT")


SPEAKERS_TICKETS: Set[str] = set()
EVENTS_CACHE: set = set()
ANNOUNCED_EVENT_NAMES: Set[str] = set()


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
                    SPEAKERS_TICKETS.add(str(result["barcode"]))
            next_url = d["next"]
            if next_url is not None:
                await sleep(
                    1.5
                )  # PyConZA is prone to network errors if not rate limiting


async def is_barcode_belong_to_speaker(barcode: str) -> bool:
    """Check if the given barcode is of a ticket owned by a speaker."""
    return barcode in SPEAKERS_TICKETS


async def update_calendar_cache() -> None:
    """Update the ICal events cache from wafer."""
    ical_url = urljoin(BASE_URL, ICS_ENDPOINT)
    async with httpx.AsyncClient() as client:
        r = await client.get(ical_url)
        c = Calendar(r.text)
    global EVENTS_CACHE
    EVENTS_CACHE = {e for e in c.events if "break" not in e.name.lower()}


async def mark_as_announced(event: Event) -> None:
    """Cache the event name, in order to mark it as done."""
    global ANNOUNCED_EVENT_NAMES
    ANNOUNCED_EVENT_NAMES.add(event.name)


async def all_upcoming_events(minutes: Optional[int] = None) -> Set[Event]:
    """All upcoming events that have yet to be announced. If minutes are given, then it
    will only mention the events comming up in the given number of minutes.
    """
    events = set()
    now = datetime.utcnow().replace(tzinfo=utc)
    for event in EVENTS_CACHE:
        diff = (event.begin - now).total_seconds()
        diff_minutes = round(diff / 60)
        if event.name not in ANNOUNCED_EVENT_NAMES and diff > 0:
            if minutes:
                if diff_minutes <= minutes:
                    events.add(event)
            else:
                events.add(event)
    return events
