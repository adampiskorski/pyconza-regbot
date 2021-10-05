import google_auth_oauthlib.flow
import googleapiclient.discovery
import pickle

from google.auth.transport.requests import AuthorizedSession, Request
from google.oauth2.service_account import Credentials
from regbot.helpers import get_str_env

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
CLIENT_ID = get_str_env("GOOGLE_OAUTH_CLIENT_ID")
CLIENT_SECRET = get_str_env("GOOGLE_OAUTH_CLIENT_SECRET")

YOUTUBE_SCOPES = [
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtubepartner",
]
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive",
] + YOUTUBE_SCOPES

CLIENT_CREDENTIALS_CACHE = None
CLIENT_CREDENTIALS_PICKLE_FILE = ".google_client_credentials"


def get_creds() -> Credentials:
    """Get the Google credentials needed to access Google APIs"""
    return Credentials.from_service_account_info(SERVICE_ACCOUNT, scopes=SCOPES)


def get_session(creds: Credentials) -> AuthorizedSession:
    """Create an authorized Google session"""
    return AuthorizedSession(creds)


def get_bearer_token_dict() -> dict:
    """Get the dictionary representation of the oAuth 2 bearer token, for use in request
    headers.
    """
    creds = get_creds()
    creds.refresh(Request(get_session(creds)))
    return {"Authorization": f"Bearer {creds.token}"}


def get_client_credentials():
    """Uses client oAuth 2 flow to get client credentials"""
    global CLIENT_CREDENTIALS_CACHE
    if CLIENT_CREDENTIALS_CACHE is None:
        try:
            with open(CLIENT_CREDENTIALS_PICKLE_FILE, "rb") as handle:
                CLIENT_CREDENTIALS_CACHE = pickle.load(handle)
        except FileNotFoundError:
            pass
    if CLIENT_CREDENTIALS_CACHE is not None:
        return CLIENT_CREDENTIALS_CACHE

    client_config = {
        "web": {
            "client_id": CLIENT_ID,
            "project_id": "pyconza",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": CLIENT_SECRET,
        }
    }
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_config(
        client_config, scopes=YOUTUBE_SCOPES
    )
    creds = flow.run_console()
    CLIENT_CREDENTIALS_CACHE = creds
    with open(CLIENT_CREDENTIALS_PICKLE_FILE, "wb") as handle:
        pickle.dump(creds, handle)
    return creds


def get_youtube():
    """Returns an authenticated YouTube resource"""
    credentials = get_client_credentials()
    return googleapiclient.discovery.build("youtube", "v3", credentials=credentials)
