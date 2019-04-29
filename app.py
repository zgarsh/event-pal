import os
from flask import Flask, request, redirect
from twilio.twiml.messaging_response import MessagingResponse

from flask_sqlalchemy import SQLAlchemy

project_dir = os.path.dirname(os.path.abspath(__file__))
database_file = "sqlite:///{}".format(os.path.join(project_dir, "chatterdb.db"))

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = database_file

db = SQLAlchemy(app)

# tutorial for flask/twilio app: https://www.twilio.com/blog/build-smart-auto-response-bot-python-flask-twilio-sms-cleverbot
# tutorial for DB stuff: https://www.codementor.io/garethdwyer/building-a-crud-application-with-flask-and-sqlalchemy-dm3wv7yu2

############# DB SETUP ####################
# delete chatterdb.db and then use python shell to:
# from app import db
# db.create_all()

############# TO RUN: ####################
# `flask run` in this directory
# `ngrok http 5000` in this directory and copy 'forwarding' URL
# go to twilio: https://www.twilio.com/console/phone-numbers/incoming
# click on phone number and scroll to 'messaging - a message comes in'
# paste forwarding URL from ngrok with '/sms' at the end

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    info = db.Column(db.String(80), nullable=False)


### Create event flow:
# User: i want to create a new event
# chatterbot: Ok! What's a good title for the event? Say something like 'Abby's quincinera'
# U: Victor's Birthday
# C: Alright - we'll call it 'Victor's Birthday'?
# U: Yes
# C: I created a new event called 'Victor's Birthday'.

def choose_action(message):
    """receives full message and decides what to do next"""

def create_event(request):
    """creates new event called eventName"""

    eventName = request.form['Body']

    event = Event(info=eventName)
    db.session.add(event)
    db.session.commit()
    print('created new event:', eventName)


    responseText = 'created event: ' + eventName

    return responseText


@app.route("/sms", methods=['GET', 'POST'])
def sms_reply():
    message_body = request.form['Body']

    responseText = create_event(request)

    resp = MessagingResponse()
    resp.message(responseText)

    return str(resp)


if __name__ == "__main__":
    app.run(debug=True)
