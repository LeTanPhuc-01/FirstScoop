from flask import Flask, request, render_template
import gspread
import hashlib
from oauth2client.service_account import ServiceAccountCredentials
import os

app = Flask(__name__)

# Configure Google Sheets API/ Google Drive
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(os.environ.get("MY_LITTLE_SECRET_JSON"), scope)
client = gspread.authorize(creds)

# Open Google Sheet
sheet = client.open("FirstScoop").worksheet("Form Responses 1")

# Email hashing function
def hash_email(email):
    return hashlib.sha256(email.encode()).hexdigest()
@app.route("/unsubscribe", methods=["GET"])
def unsubscribe():
    hashed_email = request.args.get('hash')
    if not hashed_email:
        return render_template("error.html", error_detail ="Hash parameter is undefined"), 400
    # Find the email in Google Sheets
    email_values = [hash_email(e) for e in sheet.col_values(2)[1:]]
    
    try:
        if hashed_email in email_values:
            index = email_values.index(hashed_email)
            # Index + 2 because the list index starts at 1 and the first row in GG sheets is ignored (Header)
            row = index + 2
            original_email = sheet.cell(row, 2).value
            sheet.delete_rows(row)
            return render_template("success.html", original_email= f"{original_email}"), 200
        
        else:
            return render_template("error.html", error_detail ="Email not found."), 404  
    except Exception as e:
        return render_template("error.html", error_detail = f"{str(e)}"), 500        

            

if __name__ == "__main__":
    app.run(debug=True)
