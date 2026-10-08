"""Unit tests for the Quicket guest-list cache."""

import httpx

import regbot.quicket as quicket
from regbot.quicket import Ticket, get_ticket_by_barcode, update_ticket_cache

from .fakes import serve_http


def guest(
    barcode,
    first_name="Ada",
    surname="Lovelace",
    ticket_type="Standard",
    valid=True,
):
    """A guest list entry as returned by the Quicket API."""
    return {
        "TicketInformation": {
            "Ticket Barcode": barcode,
            "Valid": valid,
            "First name": first_name,
            "Surname": surname,
            "Ticket Type": ticket_type,
        }
    }


def serve_guests(monkeypatch, guests):
    """Fake the Quicket guests endpoint to return the given guest entries."""
    serve_http(
        monkeypatch,
        lambda request: httpx.Response(200, json={"results": guests}),
    )


class TestTicket:
    def test_full_name_joins_first_name_and_surname(self):
        ticket = Ticket(
            barcode="1",
            valid=True,
            first_name="Ada",
            surname="Lovelace",
            type="Standard",
        )
        assert ticket.full_name == "Ada Lovelace"


class TestUpdateTicketCache:
    async def test_guest_list_is_cached_by_barcode(self, monkeypatch):
        serve_guests(monkeypatch, [guest("555777"), guest("111222", "Alan", "Turing")])

        await update_ticket_cache()

        assert set(quicket.TICKETS) == {"555777", "111222"}
        ticket = quicket.TICKETS["111222"]
        assert ticket.full_name == "Alan Turing"
        assert ticket.valid is True
        assert ticket.type == "Standard"

    async def test_duplicate_barcode_is_replaced_by_the_latest_record(self, monkeypatch):
        serve_guests(monkeypatch, [guest("555777", "Ada"), guest("555777", "Grace")])

        await update_ticket_cache()

        assert quicket.TICKETS["555777"].full_name == "Grace Lovelace"


class TestGetTicketByBarcode:
    async def test_known_barcode_returns_the_ticket(self, monkeypatch):
        serve_guests(monkeypatch, [guest("555777")])
        await update_ticket_cache()

        ticket = await get_ticket_by_barcode("555777")

        assert ticket is not None
        assert ticket.barcode == "555777"

    async def test_unknown_barcode_returns_none(self):
        assert await get_ticket_by_barcode("000000") is None
