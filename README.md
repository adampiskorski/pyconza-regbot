# PyConZA Discord Registration Bot

Developed for PyConZA 2020, in order to allow users to self register.

Has several commands, but the core one is register (called with `!register` and your Quicket ticket barcode number).
It fetches the guest list from quicket, and sets the appropriate roles and changes the nickname (if it has sufficient permission) of the user.

## Environment

Set the following environmental variables

- EVENT_NAME: The name of the conference

- DISCORD_TOKEN: Your discord bot token from the [Discord developer portal](https://discord.com/developers/applications) (this bot should already be added to the discord server).
- DISCORD_LOG_CHANNEL_ID: The discord channel where bot log messages (errors and successes) will be sent to.
- DISCORD_HELPDESK_CHANNEL_ID: The help desk channel
- DISCORD_WELCOME_CHANNEL_ID: The channel used for greetings
- DISCORD_ANNOUNCEMENT_CHANNEL_ID: The channel that calendar announcements are made in
- DISCORD_ANNOUNCEMENT_STAGING_CHANNEL_ID: The channel that the bot will monitor for manual announcements to re-post
- DISCORD_GUILD_ID: The conference's discord server ID (yes, one conference server at a time)
- DISCORD_REGISTERED_ROLE_NAME: The name of the attendee role
- DISCORD_REGISTRATION_ROLE: The name of the registration role
- DISCORD_ORGANIZER_ROLE: The name of the organizer role
- DISCORD_SPEAKER_ROLE: The name of the speaker role
- DISCORD_SPONSOR_PATRON_ROLE: The name of the patron sponsor role
- DISCORD_SPONSOR_SILVER_ROLE: The name of the silver sponsor role
- DISCORD_SPONSOR_GOLD_ROLE: The name of the gold sponsor role

- QUICKET_USER_TOKEN: The [user token](https://www.quicket.co.za/account/users/apikeys.aspx) (from personal profile) for Quicket. It needs to be of the user which created the Quicket event in order to have sufficient permissions to access the guest list endpoint.
- QUICKET_API_KEY: The API key from Quicket's [developer portal](https://developer.quicket.co.za/)
- QUICKET_CACHE_EXPIRE_MINUTES: How often to call the Quicket guest list endpoint for updated Ticket information.
- QUICKET_EVENT_ID: The conference's Quicket event ID.

Google sheets is used for state management. The following environmental variables represent the unique following keys of a Google service account json key file:

- GOOGLE_PROJECT_ID: `project_id`
- GOOGLE_PRIVATE_KEY_ID: `private_key_id`
- GOOGLE_PRIVATE_KEY: `private_key`
- GOOGLE_CLIENT_EMAIL: `client_email`
- GOOGLE_CLIENT_ID: `client_id`
- GOOGLE_CLIENT_X509_CERT_URL: `client_x509_cert_url`

In order to take certain actions on YouTube, you need a valid Google client oAuth authentication from one user who has the desired permissions:

- GOOGLE_OAUTH_CLIENT_ID: Client ID for oAuth flow
- GOOGLE_OAUTH_CLIENT_SECRET: Secret for oAuth flow

- GOOGLE_SHEET_ID: The ID of the spread sheet to use for state management.
- GOOGLE_SHEET_WORKSHEET_NAME: The human readable name of the specific sheet to use.

For use with the PyConZA site and wafer:

- WAFER_USERNAME: The username to sign on with.
- WAFER_PASSWORD: The password to sing on with.
- WAFER_BASE_URL: The base URL of the Wafer site.
- WAFER_TICKETS_ENDPOINT: The endpoint URL of the tickets API.
- WAFER_TALKS_ENDPOINT: The endpoint URL of the talks API.
- WAFER_CACHE_EXPIRE_MINUTES: How often to call the Wafer tickets and talks endpoints for an updated speakers list.
- WAFER_ICS_ENDPOINT: The ICal endpoint for calendar information.

- YOUTUBE_KEY: The API key created to access the YouTube Data API V3
- DISCORD_YOUTUBE_CATEGORY: The discord channel category to put YouTube video channels
- YOUTUBE_PLAYLIST: The ID of the YouTube playlist to check for videos to put into Discord.

Feature flags that turns certain features on or off. Note that some features, like registration, requires Wafer and Quicket Sync:

- FEATURE_REGISTRATION: Chat commands and events for registration
- FEATURE_WAFER_SYNC: The regular syncing of data with Wafer
- FEATURE_QUICKET_SYNC: The regular syncing of data with Quicket
- FEATURE_YOUTUBE: For syncing YouTube channels
- FEATURE_REPOST_ANNOUNCE: For re-posting message as a bot in the announcements channel

## Run

Using [poetry](https://python-poetry.org/)

> `poetry install --no-dev`

Then activate the virtualenv with

> `poetry shell`

Then start the server with

> `python -m regbot`

## Development

Install dev dependencies with

> `poetry install`

Configure [pre-commit](https://pre-commit.com/) with

> `pre-commit install`
