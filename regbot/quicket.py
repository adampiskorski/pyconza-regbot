from dataclasses import dataclass
from typing import Dict, Optional
from urllib.parse import urljoin

import httpx

from regbot.helpers import get_int_env, get_str_env, log

USER_TOKEN = get_str_env("QUICKET_USER_TOKEN")
API_KEY = get_str_env("QUICKET_API_KEY")
CACHE_EXPIRE_MINUTES = get_int_env("QUICKET_CACHE_EXPIRE_MINUTES")
EVENT_ID = get_int_env("QUICKET_EVENT_ID")


QUICKET_BASE_URL = "https://api.quicket.co.za"


@dataclass
class Ticket:
    """A partial representation of the TicketInformation object from Quicket"""

    barcode: str
    valid: bool
    first_name: str
    surname: str
    type: str

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.surname}"


TICKETS: Dict[str, Ticket] = {}


async def update_ticket_cache() -> None:
    """Update the global TICKETS cache dictionary from Quicket"""
    async with httpx.AsyncClient() as client:
        url = urljoin(QUICKET_BASE_URL, f"api/events/{EVENT_ID}/guests")
        r = await client.get(
            url,
            params={"api_key": API_KEY},
            headers={"usertoken": USER_TOKEN},
        )

        global TICKETS
        TICKETS = {}

        for result in r.json()["results"]:
            info = result["TicketInformation"]
            ticket = Ticket(
                barcode=str(info["Ticket Barcode"]),
                valid=bool(info["Valid"]),
                first_name=str(info["First name"]),
                surname=str(info["Surname"]),
                type=str(info["Ticket Type"]),
            )
            if ticket.barcode in TICKETS:
                await log(
                    f"A duplicate barcode {ticket.barcode} was found and the record "
                    f"replaced! {TICKETS[ticket.barcode].full_name} was replaced by "
                    f"{ticket.full_name}."
                )
            TICKETS[ticket.barcode] = ticket


async def get_ticket_by_barcode(barcode: str) -> Optional[Ticket]:
    """Query the Quicket guest list for the event or pull for cache if it's still
    fresh.
    """
    return TICKETS.get(barcode)
