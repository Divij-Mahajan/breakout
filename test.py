import os.path
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pandas as pd

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

SAMPLE_SPREADSHEET_ID = "1Za6UWrGZytXlPMSEKtuqsl6bXnwDu8eir6wVIDTr-nk"
SAMPLE_RANGE_NAME = "Sheet15!A2:E"

GOOGLE_TOKEN='{"token": "ya29.a0AeDClZAgYs3lAaagulHN8yFNtiYpZIwfMo2G_5eJI6BqkrWNCiSso46osXo6iu4HCwRtv5b_eU7RhMIAk-QKL5YbFFeNfHBleFfoXnBJiaoXMRD6FhiKItfNYe239JkY5Fsqy6CpXIgpTlADQhhTyWVx7_yeSJT5I1Xg-vzTaCgYKAUQSARESFQHGX2MiixoR5wtCFrZ7T8I2ixDZ1g0175", "refresh_token": "1//0gbv5KN7G-9_GCgYIARAAGBASNwF-L9IrOAgGk3NPpHLF_rwIkJR9YKGC7ofh43GikwnjjhTsl6tg3dZunkAEISl-sdZHwXLMrXw", "token_uri": "https://oauth2.googleapis.com/token", "client_id": "81011847202-3ck07eh8bklllcopc8eqljl36jpdsd7h.apps.googleusercontent.com", "client_secret": "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", "scopes": ["https://www.googleapis.com/auth/spreadsheets.readonly"], "universe_domain": "googleapis.com", "account": "", "expiry": "2024-11-17T13:22:51.688952Z"}'
GOOGLE_CREDENTIALS='{"installed":{"client_id":"81011847202-3ck07eh8bklllcopc8eqljl36jpdsd7h.apps.googleusercontent.com","project_id":"ml-agent-442012","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_secret":"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","redirect_uris":["http://localhost"]}}'

def main():
  """Shows basic usage of the Sheets API.
  Prints values from a sample spreadsheet.
  """
  print(help(InstalledAppFlow))
  creds = None
  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_info(json.loads(GOOGLE_TOKEN),SCOPES)
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_config(
          json.loads(GOOGLE_CREDENTIALS), SCOPES
      )

      creds = flow.run_local_server(port=0)
    with open("token.json", "w") as token:
      token.write(creds.to_json())

  try:
    service = build("sheets", "v4", credentials=creds)

    # Call the Sheets API
    sheet = service.spreadsheets()
    result = (
        sheet.values()
        .get(spreadsheetId=SAMPLE_SPREADSHEET_ID, range=SAMPLE_RANGE_NAME)
        .execute()
    )
    values = pd.DataFrame(result.get("values", []))
    print(values)
    

  except HttpError as err:
    print(err)


if __name__ == "__main__":
  main()