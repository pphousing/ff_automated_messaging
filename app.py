from flask import Flask, render_template, request
import pandas as pd
import os
from google.oauth2.credentials import Credentials
import gspread
from google.auth.transport.requests import Request
import googlemaps
from dotenv import load_dotenv
from googleapiclient.discovery import build
import base64
from email.mime.text import MIMEText
import json
from flask import session
from io import StringIO
import re
import requests
from math import radians, sin, cos, sqrt, atan2

# Load environment variables from .env file
load_dotenv()
print("GOOGLE_MAPS_API_KEY:", os.environ.get("GOOGLE_MAPS_API_KEY"))

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY')  # <-- Add this line



def send_text(phone_num, message, first_name):
    url = "https://api.openphone.com/v1/messages"
    headers={
        "Authorization": os.environ.get("AUTHORIZATION"),
        "Content-Type":"application/json"
    }
    first_name = first_name.title()
    if first_name =='Charlie':
        payload = {
            "content": message,
            "from": "PNvnUZwoP3",
            "to":[phone_num],
            "userId":"USMZbFI72a"
        }
    elif first_name == 'Mahmoud':
        payload = {
        "content": message,
        "from": "PNaOHVFQas",
        "to":[phone_num],
        "userId":"UStOusLc0x"
    }
    elif first_name == 'Ahmed':
        payload = {
        "content": message,
        "from":  'PNVYQxBEmb',
        "to":[phone_num],
        "userId":'USNNA3aaH3'
    }
    elif first_name == 'Mohamed':
        payload = {
        "content": message,
        "from":  'PNecGwld3E',
        "to":[phone_num],
        "userId":'USkdRcH9dR'
    }
    response = requests.post(url,headers=headers, json = payload)
    return response

def extract_10_digit_number(phone_str):
    # Find all digits
    digits = re.findall(r'\d', phone_str)
    # Join and extract the last 10 digits (in case it includes country code)
    return '+1' + ''.join(digits)[-10:]


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", filters=json.dumps({}), phone_status_html=None, email_status_html=None)




@app.route('/send_messages', methods=['POST'])
def send_messages():
    filters = json.loads(request.form['filters'])

    # Get all 20 rows (lists)
    ff_links = [x.strip().split('?')[0] for x in request.form.getlist('ff_links[]')]
    ll_names = [x.strip() for x in request.form.getlist('ll_names[]')]
    cities   = [x.strip() for x in request.form.getlist('cities[]')]
    pns      = [x.strip() for x in request.form.getlist('ll_pns[]')]

    adults = int(request.form['adults'])
    kids   = int(request.form['kids'])
    los    = int(request.form['stay_length'])
    pets   = int(request.form['pets'])
    dogs   = int(request.form['dogs'])
    cats   = int(request.form['cats'])
    info   = str(request.form.get('info', '')).strip()
    first_name = str(request.form['first_name']).strip()

    # Combine rows and keep only rows with at least one meaningful field
    rows = []
    for link, name, pn, city in zip(ff_links, ll_names, pns, cities):
        if any([link, name, pn, city]):  # at least something entered
            rows.append({"link": link, "name": name, "pn": pn, "city": city})

    # Require at least 1 row
    if len(rows) == 0:
        return render_template(
            "index.html",
            filters=json.dumps(filters),
            results_html="<div class='alert alert-danger'>Please fill out at least 1 row (FF Link / Name / Phone / City).</div>"
        )

    results = []

    for r in rows:
        # Optional: enforce minimum required fields for sending
        if not r["pn"] or not r["name"] or not r["city"] or not r["link"]:
            results.append({
                "channel": "OpenPhone SMS",
                "recipient": f'{r["name"] or "Unknown"} ({r["pn"] or "No phone"})',
                "status": "Skipped: missing FF link, name, phone, or city"
            })
            continue

        phone = extract_10_digit_number(r["pn"])
        if not phone or len(phone) != 12:  # "+1" + 10 digits
            results.append({
                "channel": "OpenPhone SMS",
                "recipient": f'{r["name"]} ({r["pn"]})',
                "status": "Skipped: invalid phone number"
            })
            continue

        txt = (
            f"Hi {r['name']}! My name is {first_name} and I saw your "
            f"{r['city']} Furnished Finder listing ({r['link']}) and was wondering if it "
            f"was still available? I’m with Paradise Point Housing "
            f"(https://www.paradisepointhousing.com), and I’m working with an "
            f"insurance company to help place a displaced family in your area.\n\n"
        )

        if info:
            txt += f"{info}\n\n"

        txt += (
            f"This claim is for {adults} adults, {kids} kids, and {pets} pets "
            f"({dogs} dogs and {cats} cats) looking for a {los}-month stay to start. Target start date is typically within 5-10 days "
        )

        resp = send_text(phone, txt, first_name)

        results.append({
            "channel": "OpenPhone SMS",
            "recipient": f"{r['name']} ({r['pn']})",
            "status": resp.text
        })

    results_df = pd.DataFrame(results)
    results_html = results_df.to_html(classes="table table-bordered table-striped", index=False) if results else None

    return render_template(
        "index.html",
        filters=json.dumps(filters),
        results_html=results_html
    )
    

   





if __name__ == '__main__':
    # app.run(debug=True)
    # Use the PORT environment variable or default to 5000 for local testing
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)