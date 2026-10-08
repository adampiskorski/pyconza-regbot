"""Fakes for the external services that regbot talks to.

SimCord fakes Discord itself; these fakes cover everything else: Google
Sheets, YouTube, Quicket and Wafer. They are deliberately small and explicit
so that tests read as scenarios, not framework code.
"""

import httpx
from gspread import Cell


class FakeWorksheet:
    """In-memory stand-in for the gspread worksheet used by sheets.py."""

    def __init__(self, rows=None):
        self.rows = [list(row) for row in rows or []]

    async def get_all_values(self):
        return [list(row) for row in self.rows]

    async def findall(self, query):
        return [
            Cell(row_number, column_number, value)
            for row_number, row in enumerate(self.rows, start=1)
            for column_number, value in enumerate(row, start=1)
            if value == query
        ]

    async def append_row(self, row):
        self.rows.append(list(row))

    async def update_cells(self, cells):
        for cell in cells:
            while len(self.rows) < cell.row:
                self.rows.append([])
            row = self.rows[cell.row - 1]
            while len(row) < cell.col:
                row.append("")
            row[cell.col - 1] = cell.value


def fake_google_sheets(monkeypatch, *, registrations=None, quiz=None):
    """Point `sheets.get_worksheet` at the given fake worksheets."""
    import regbot.sheets as sheets

    async def get_worksheet(sheet_id, worksheet):
        if sheet_id == sheets.SHEET_ID:
            return registrations
        if sheet_id == sheets.QUIZ_SHEET_ID:
            return quiz
        raise AssertionError(f"Unexpected sheet requested: {sheet_id}")

    monkeypatch.setattr(sheets, "get_worksheet", get_worksheet)


class FakeYouTube:
    """Stand-in for the YouTube API resource, recording live chat inserts."""

    def __init__(self):
        self.inserted_messages = []
        self.error = None

    def liveChatMessages(self):
        return self

    def insert(self, part, body):
        youtube = self

        class Request:
            def execute(self):
                if youtube.error is not None:
                    raise youtube.error
                youtube.inserted_messages.append(body)

        return Request()


def make_http_error(reason="The live chat is disabled.", status=403):
    """A googleapiclient HttpError, like the one a rejected insert raises."""
    import json

    import httplib2
    from googleapiclient.errors import HttpError

    response = httplib2.Response({"status": str(status)})
    content = json.dumps({"error": {"message": reason}}).encode()
    return HttpError(response, content)


def serve_http(monkeypatch, handler):
    """Make all `httpx.AsyncClient` instances respond via the given handler."""
    transport = httpx.MockTransport(handler)
    real_client = httpx.AsyncClient
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda *args, **kwargs: real_client(*args, transport=transport, **kwargs),
    )


async def do_nothing(*args, **kwargs):
    """A no-op stand-in for async cache-refresh functions in tasks tests."""
