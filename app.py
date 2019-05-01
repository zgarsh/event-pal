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
    owner = db.Column(db.Integer, nullable=False)
    status = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(80))
    location = db.Column(db.String(80))
    time = db.Column(db.String(80))


### Event statuses:
# 0: no info - create new event and populate 'name'
# 1: has name, needs location - populate 'location'
# 2: has name and location, needs time - populate 'time'
# 3: completed event


def choose_action(request):
    """receives request and decides what to do next"""

    fullMessage = request.form['Body']

    # Get all events for that user
    thisUsersEvents = db.session.query(Event).filter_by(owner=1).all()

    # Determine if any of user's events has status <3. If yes, prompt them to complete it
    # ASSUMPTION: only one event per user can have status <3 at a time
    for i in range(len(thisUsersEvents)):
        if thisUsersEvents[i].status == 0:
            event_id = thisUsersEvents[i].id
            responseText = give_event_name(event_id, request)

        elif thisUsersEvents[i].status == 1:
            event_id = thisUsersEvents[i].id
            responseText = give_event_location(event_id, request)

        elif thisUsersEvents[i].status == 2:
            event_id = thisUsersEvents[i].id
            responseText = give_event_time(event_id, request)

    if fullMessage == 'Create new event':
        responseText = create_event(request)

    return responseText


def create_event(request):
    """creates new nameless event given request object"""

    # TODO: owner can't always be 1 - need to create users and match based on phone number
    event = Event(status=0, owner=1)
    db.session.add(event)
    db.session.commit()
    print('created new event:', event.name)

    responseText = "Ok! What's a good title for the event? Say something like 'Abby's quincinera'"

    return responseText

def give_event_name(event_id, request):
    """names event referencing request and returns response text"""

    event = db.session.query(Event).filter_by(id=event_id).one()
    event.name = request.form['Body']
    event.status = 1
    db.session.commit()

    responseText = "Alright - We'll call it " + event.name + ". Where will " + event.name + " take place?"

    return responseText

def give_event_location(event_id, request):
    """add event location by referencing request and return response text"""

    event = db.session.query(Event).filter_by(id=event_id).one()
    event.location = request.form['Body']
    event.status = 2
    db.session.commit()

    responseText = "Ok. So " + event.name + " will take place at " + event.location + ". What date and time?"

    return responseText

def give_event_time(event_id, request):
    """add event location by referencing request and return response text"""

    event = db.session.query(Event).filter_by(id=event_id).one()
    event.time = request.form['Body']
    event.status = 3
    db.session.commit()

    responseText = "Perfect. " + event.name + " at " + event.location + " at " + event.time + "."

    return responseText

@app.route("/sms", methods=['GET', 'POST'])
def sms_reply():
    message_body = request.form['Body']

    # responseText = create_event(request)
    responseText = choose_action(request)

    resp = MessagingResponse()
    resp.message(responseText)

    return str(resp)


if __name__ == "__main__":
    app.run(debug=True)
