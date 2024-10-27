import os
import time
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from dotenv import load_dotenv
from mailjet_rest import Client
import hashlib
# Load env vars
load_dotenv()
#Load Creds from service account json
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
SERVICE_ACCOUNT_JSON = os.getenv('SERVICE_ACCOUNT_JSON')
creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_JSON, scopes = SCOPES)

#Reference to the FirstScoop Spreadsheet
SPREADSHEET_ID = '1ybM3GNZJKzekmBI2CpSgtpsw75-bvanjXWMZdO1nq8s'
SHEET_RANGE = 'Form Responses 1!B2:B'
print(f"Spreadsheet ID: {SPREADSHEET_ID}")
print(f"Sheet Range: {SHEET_RANGE}")
#Call Sheets API
service = build('sheets', 'v4', credentials=creds)
sheet = service.spreadsheets()

result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=SHEET_RANGE).execute()
values = result.get('values', [])
subscribers = []
if values == []:
    print("No data found.")
else: 
    for row in values:
        email = row[0]
        subscribers.append({'Email': email})
# Load the created HTML content     
with open("daily_menu.html", "r") as f:
    html_content = f.read()

def hash_email(email):
    return hashlib.sha256(email.encode()).hexdigest()

# Function to create unsubscribe link 
def create_unsubscribe_url(email):
    hashed_email = hash_email(email)
    return f"https://first-scoop.vercel.app/unsubscribe?hash={hashed_email}"

mailjet = Client(auth=(os.getenv('api_key'), os.getenv('secret_key')), version ='v3.1')
#SEND BULK EMAILs
for i in range(len(subscribers)):
    subscriber = subscribers[i]
    unsubscribe_url = create_unsubscribe_url(subscriber['Email'])
    final_html = html_content.replace('{{unsubscribe_url}}', unsubscribe_url)
    data = {
        'Messages': [
        {
            "From": {
            "Email": "le022@gannon.edu",
            "Name": "Le, Tan Phuc"
            },
            "To": [
            {
                "Email": subscriber['Email'],
                "Name": subscriber['Email']
            }
            ],
            "Subject": "Bayer Menu",
            "TextPart": "HI, everyone",
            "HTMLPart": final_html
        }
        ]
    }
    result = mailjet.send.create(data=data)
    print(result.status_code)
    print(result.json())
    if i < len(subscribers) - 1:
        time.sleep(3)
 
