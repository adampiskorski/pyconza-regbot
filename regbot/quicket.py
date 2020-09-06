from datetime import datetime, timedelta
from typing import Dict, Optional
from urllib.parse import urljoin
from dataclasses import dataclass

import httpx

from regbot.helpers import get_int_env, get_str_env, log

USER_TOKEN = get_str_env("QUICKET_USER_TOKEN")
API_KEY = get_str_env("QUICKET_API_KEY")
CACHE_EXPIRE_MINUTES = get_int_env("QUICKET_CACHE_EXPIRE_MINUTES")
EVENT_ID = get_int_env("QUICKET_EVENT_ID")


QUICKET_BASE_URL = "https://api.quicket.co.za"

LAST_QUICKET_FETCH = datetime(year=1970, month=1, day=1)


@dataclass
class Ticket:
    """A partial representation of the TicketInformation object from Quicket"""

    barcode: str
    valid: bool
    first_name: str
    surname: str

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.surname}"


TICKETS: Dict[str, Ticket] = dict()


async def update_ticket_cache() -> None:
    """Update the global TICKETS cache dictionary from Quicket"""
    async with httpx.AsyncClient() as bot:
        url = urljoin(QUICKET_BASE_URL, f"api/events/{EVENT_ID}/guests")
        r = await bot.get(
            url,
            params={"api_key": API_KEY},
            headers={"usertoken": USER_TOKEN},
        )

        global TICKETS
        TICKETS = dict()

        for result in r.json()["results"]:
            info = result["TicketInformation"]
            ticket = Ticket(
                barcode=info["Ticket Barcode"],
                valid=info["Valid"],
                first_name=info["First name"],
                surname=info["Surname"],
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
    global LAST_QUICKET_FETCH
    fetch_interval_is_expired = (
        LAST_QUICKET_FETCH + timedelta(minutes=CACHE_EXPIRE_MINUTES) < datetime.now()
    )

    if fetch_interval_is_expired:
        await log("Quicket ticket cache expired, downloading...")
        await update_ticket_cache()
        LAST_QUICKET_FETCH = datetime.now()

    return TICKETS.get(barcode)
