from datetime import datetime

from discord import User
from google.oauth2.service_account import Credentials
from gspread.exceptions import CellNotFound
import gspread_asyncio
from gspread_asyncio import AsyncioGspreadWorksheet

from regbot.helpers import get_str_env, log
from regbot.quicket import Ticket

SERVICE_ACCOUNT = dict(
    type="service_account",
    project_id=get_str_env("GOOGLE_PROJECT_ID"),
    private_key_id=get_str_env("GOOGLE_PRIVATE_KEY_ID"),
    private_key=get_str_env("GOOGLE_PRIVATE_KEY").replace("\\n", "\n"),
    client_email=get_str_env("GOOGLE_CLIENT_EMAIL"),
    client_id=get_str_env("GOOGLE_CLIENT_ID"),
    auth_uri="https://accounts.google.com/o/oauth2/auth",
    token_uri="https://oauth2.googleapis.com/token",
    auth_provider_x509_cert_url="https://www.googleapis.com/oauth2/v1/certs",
    client_x509_cert_url=get_str_env("GOOGLE_CLIENT_X509_CERT_URL"),
)
SHEET_ID = get_str_env("GOOGLE_SHEET_ID")
WORKSHEET = get_str_env("GOOGLE_SHEET_WORKSHEET_NAME")
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive",
]


def get_creds() -> Credentials:
    """Get the Google credentials needed to access the Google sheet"""
    return Credentials.from_service_account_info(SERVICE_ACCOUNT, scopes=SCOPES)


client_manager = gspread_asyncio.AsyncioGspreadClientManager(get_creds)


async def get_worksheet() -> AsyncioGspreadWorksheet:
    """Get the gspread worksheet used to store state of ticket registration"""
    client = await client_manager.authorize()
    sheet = await client.open_by_key(SHEET_ID)
    return await sheet.worksheet(WORKSHEET)


async def is_ticket_used(ticket: Ticket) -> bool:
    """Check if the given ticket exists (was registered) in the sheet"""
    work_sheet = await get_worksheet()
    try:
        await work_sheet.find(ticket.barcode)
        return True
    except CellNotFound:
        return False


async def register_ticket(ticket: Ticket, member: User) -> bool:
    """Registers the user to the ticket by appending a row with the relevant information
    to the work sheet
    """
    work_sheet = await get_worksheet()
    row = (
        ticket.barcode,
        ticket.full_name,
        member.name,
        str(member.id),
        str(datetime.now()),
    )
    await work_sheet.append_row(row)
    await log(f"Registering row to sheet: {row}")
    return True
