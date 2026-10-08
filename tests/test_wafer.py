"""Unit tests for the Wafer caches: speakers, calendar events, announcements."""

import arrow
import httpx
import pytest
from ics import Event

import regbot.wafer as wafer
from regbot.wafer import (
    all_upcoming_events,
    is_barcode_belong_to_speaker,
    mark_as_announced,
    update_calendar_cache,
    update_speakers_cache,
)

from .fakes import serve_http


@pytest.fixture(autouse=True)
def _no_rate_limit_sleep(monkeypatch):
    """Skip the rate-limiting sleeps so the tests stay fast."""

    async def no_sleep(seconds):
        pass

    monkeypatch.setattr(wafer, "sleep", no_sleep)


def talks_page(results, next_url=None):
    return httpx.Response(200, json={"results": results, "next": next_url})


def serve_wafer(monkeypatch, pages):
    """Fake the Wafer API, serving the given responses keyed by full URL."""

    def handler(request):
        return pages[str(request.url)]

    serve_http(monkeypatch, handler)


class TestUpdateSpeakersCache:
    async def test_collects_barcodes_of_talk_authors_across_pages(self, monkeypatch):
        serve_wafer(
            monkeypatch,
            {
                "https://wafer.example.com/api/talks/": talks_page(
                    [{"authors": [1, 2]}],
                    next_url="https://wafer.example.com/api/talks/?page=2",
                ),
                "https://wafer.example.com/api/talks/?page=2": talks_page(
                    [{"authors": [3]}]
                ),
                "https://wafer.example.com/api/tickets/": talks_page(
                    [
                        {"user": 1, "barcode": 111},  # speaker
                        {"user": 3, "barcode": 222},  # speaker
                        {"user": 99, "barcode": 333},  # not a speaker
                    ]
                ),
            },
        )

        await update_speakers_cache()

        assert {"111", "222"} == wafer.SPEAKERS_TICKETS

    async def test_speaker_barcode_lookup(self, monkeypatch):
        wafer.SPEAKERS_TICKETS.add("111")

        assert await is_barcode_belong_to_speaker("111") is True
        assert await is_barcode_belong_to_speaker("999") is False


SCHEDULE = """\
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//pyconza//schedule//EN
BEGIN:VEVENT
SUMMARY:Opening Ceremony
DTSTART:20261009T070000Z
DTEND:20261009T073000Z
UID:opening
END:VEVENT
BEGIN:VEVENT
SUMMARY:Lunch Break
DTSTART:20261009T110000Z
DTEND:20261009T120000Z
UID:lunch
END:VEVENT
END:VCALENDAR
"""


class TestUpdateCalendarCache:
    async def test_events_are_cached_and_breaks_are_filtered_out(self, monkeypatch):
        serve_http(monkeypatch, lambda request: httpx.Response(200, text=SCHEDULE))

        await update_calendar_cache()

        assert {event.name for event in wafer.EVENTS_CACHE} == {"Opening Ceremony"}


def upcoming_event(name="Opening Ceremony", **shift):
    """An event beginning some time from now (default: 4 minutes)."""
    return Event(name=name, begin=arrow.utcnow().shift(**{"minutes": 4, **shift}))


class TestAllUpcomingEvents:
    async def test_returns_events_within_the_given_window(self, monkeypatch):
        in_window = upcoming_event("In Window", minutes=3)
        beyond_window = upcoming_event("Beyond Window", minutes=30)
        wafer.EVENTS_CACHE.update({in_window, beyond_window})

        events = await all_upcoming_events(minutes=5)

        assert {event.name for event in events} == {"In Window"}

    async def test_past_events_are_not_announced(self, monkeypatch):
        wafer.EVENTS_CACHE.add(upcoming_event("Long Past", minutes=-60))

        assert await all_upcoming_events(minutes=5) == set()

    async def test_already_announced_events_are_not_announced_again(self, monkeypatch):
        event = upcoming_event()
        wafer.EVENTS_CACHE.add(event)

        await mark_as_announced(event)

        assert await all_upcoming_events(minutes=5) == set()
