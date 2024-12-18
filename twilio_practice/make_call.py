import os
from dotenv import load_dotenv
load_dotenv()
from twilio.rest import Client

account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")

client = Client(account_sid, auth_token)

call = client.calls.create(
    url="http://demo.twilio.com/docs/classic.mp3",
    to=os.getenv("MY_PHONE_NUM"),
    from_=os.getenv('TWILIO_PHONE_NUM'),
)

print(call.sid)



