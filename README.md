# PyConZA Discord Registration Bot

Developed for PyConZA 2020, in order to allow users to self register.

Has several commands, but the core one is register (called with `!register` and your Quicket ticket barcode number).
It fetches the guest list from quicket, and sets the appropriate roles and changes the nickname (if it has sufficient permission) of the user.

## Environment

Set the following environmental variables

* EVENT_NAME: The name of the conference

* DISCORD_TOKEN: Your discord bot token from the [Discord developer portal](https://discord.com/developers/applications) (this bot should already be added to the discord server).
* DISCORD_LOG_CHANNEL_ID: The discord channel where bot log messages (errors and successes) will be sent to.
* DISCORD_HELPDESK_CHANNEL_ID: The helpdesk channel
* DISCORD_GUILD_ID: The conference's discord server ID (yes, one conference server at a time)
* DISCORD_REGISTERED_ROLE_NAME: The name of the attendee role
* DISCORD_REGISTRATION_ROLE: The name of the registration role
* DISCORD_ORGANIZER_ROLE: The name of the organizer role

* QUICKET_USER_TOKEN: The [user token](https://www.quicket.co.za/account/users/apikeys.aspx) (from personal profile) for Quicket. It needs to be of the user which created the Quicket event in order to have sufficient permissions to access the guest list endpoint.
* QUICKET_API_KEY: The API key from Quicket's [developer portal](https://developer.quicket.co.za/)
* QUICKET_CACHE_EXPIRE_MINUTES: How often to call the Quicket guest list endpoint for updated Ticket information.
* QUICKET_EVENT_ID: The conference's Quicket event ID.

## Run

Using [poetry](https://python-poetry.org/)
> `poetry install`

Then activate the virtualenv with
> `poetry shell`

Then start the server with
> `python -m regbot`

## Development

Install dev dependencies with
> `poetry install --dev`

Configure [pre-commit](https://pre-commit.com/) with
> `pre-commit install`
