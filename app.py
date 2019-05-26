import os
from flask import Flask, request, redirect
from flask_sqlalchemy import SQLAlchemy
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
# new:
# from flask_heroku import Heroku


# client for sending SMS that aren't responses (inviting guests)

# from secrets import twilio_account_sid, twilio_auth_token, twilio_number
# change line above to use environment variables instead
twilio_account_sid = os.environ['TWILIO_ACCOUNT_SID']
twilio_auth_token = os.environ['TWILIO_AUTH_TOKEN']
twilio_number = os.environ['TWILIO_NUMBER']

client = Client(twilio_account_sid, twilio_auth_token)

# Connect to heroku postgres DB
# DATABASE_URL = os.environ['DATABASE_URL']


# project_dir = os.path.dirname(os.path.abspath(__file__))
# database_file = "sqlite:///{}".format(os.path.join(project_dir, "chatterdb.db"))

app = Flask(__name__)
# app.config["SQLALCHEMY_DATABASE_URI"] = database_file

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# new:
# heroku = Heroku(app) #commenting this out but I feel like I need this maybe

db = SQLAlchemy(app)

# sample
def send_sms():

    body = "Thank you for subscribing to CAT FACTS! Did you know that There are over 500 million domestic cats in the world???"

    to = '+16505552948',
    client.messages.create(
        to,
        from_=twilio_number,
        body=body)


#############################

# Oops - I probably should have used twilio cookies instead of tracking conversation status
# - see info here: https://www.twilio.com/blog/2014/07/the-definitive-guide-to-sms-conversation-tracking.html
# also see this text survey tutorial: https://www.twilio.com/docs/voice/tutorials/automated-survey-python-flask

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
    creator = db.Column(db.Integer, nullable=False)
    status = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(80))
    phone = db.Column(db.String(80))

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    location = db.Column(db.String(80))
    time = db.Column(db.String(80))
    owner = db.Column(db.Integer, nullable=False)
    status = db.Column(db.Integer, nullable=False)

class Attendees(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'))
    status = db.Column(db.Integer, nullable = False, default=0)

class Friends(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    users_friend_id = db.Column(db.Integer, db.ForeignKey('user.id'))


### Event statuses:
# 0: no info - create new event and populate 'name'
# 1: has name, needs location - populate 'location'
# 2: has name and location, needs time - populate 'time'
# 3: needs invitees
# 4: completed event

### Attendance statuses:
# 0: invited
# 1: confirmed
# 2: maybe
# 3: declined


def choose_action_host(request):
    """receives request and decides what to do next"""

    # print(request.values)
    # print(request.values['From'])

    fullMessage = request.form['Body']
    responseText = 'Hello'

    thisUsersID = db.session.query(User).filter_by(phone=request.values['From']).one().id

    thisUsersEvents = db.session.query(Event).filter_by(owner=thisUsersID).all()
    thisUsersUsers = db.session.query(User).filter_by(creator=thisUsersID).all()

    # Determine if any of user's events has status <4. If yes, prompt them to complete it
    # ASSUMPTION: only one event per user can have status <4 at a time
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

        elif thisUsersEvents[i].status == 3:
            event_id = thisUsersEvents[i].id
            responseText = give_event_attendees(event_id, request)

    # Determine if user is creating a new user (if user table has entry with
    # this user as a creator and status <2)
    for i in range(len(thisUsersUsers)):
        if thisUsersUsers[i].status == 0:
            user_in_prog = thisUsersUsers[i].id
            responseText = give_user_name(user_in_prog, request)

        elif thisUsersUsers[i].status == 1:
            user_in_prog = thisUsersUsers[i].id
            responseText = give_user_phone(user_in_prog, request)

    # If no in-progress events or users, determine if user is trying to create event or user
    if fullMessage.lower() in ['create new event', 'new event', 'create event']:
        responseText = create_event(request)

    if fullMessage.lower() in ['add user', 'create user', 'new user', 'add new user', 'create new user']:
        responseText = create_user(request)

    if fullMessage.lower().startswith('send invites'):
        parsedmessage = fullMessage.split(',')
        if len(parsedmessage) < 3:
            responseText = "Please reply with 'send invites', <event id>, <your message>"
            return responseText
        try:
            event = db.session.query(Event).filter_by(id=parsedmessage[1]).one()
        except:
            responseText = "Please give a valid event ID"
            return responseText

        event_id = event.id
        host_message = parsedmessage[2]

        send_invites(event_id, host_message)

        responseText = 'Trying to send invites for event ' + str(event_id)

        return responseText

    return responseText

def choose_action_guest(request):
    """receives request and decides what to do next"""

    fullMessage = request.form['Body']
    responseText = 'Hello'

    # TODO: how to handle duplicate entries for this and for normal create user flow
    if fullMessage.lower().startswith('secretpassword'):
        parsedmessage = fullMessage.split()
        if len(parsedmessage) > 1:
            newname = ' '.join(parsedmessage[1:])
        else:
            newname = 'secret spy'
        newphone = request.values['From']
        user = User(status=0, creator=0, name=newname, phone=newphone)
        db.session.add(user)
        db.session.commit()
        print('created new user', newname, newphone)
        responseText = "shhhhh. you've been added but don't tell anyone"
        return responseText

    # See if that user has been added
    try:
        # if they are already signed up, get ID
        thisUsersID = db.session.query(User).filter_by(phone=request.values['From']).one().id
    except:
        # user is not registered
        responseText = 'Please ask Zach to add you as a user!'
        return responseText

    return responseText

def create_event(request):
    """creates new nameless event given request object"""

    requestor_phone = request.values['From']
    requestor_id = db.session.query(User).filter_by(phone=requestor_phone).one().id

    if requestor_id == 1:
        event = Event(status=0, owner=1)
        db.session.add(event)
        db.session.commit()
        print('created new event')

        responseText = "Ok! What's a good title for the event? Say something like 'Abby's quincinera'"

    else:
        responseText = "Please ask Zach to help add an event :)"

    return responseText


def give_event_name(event_id, request):
    """names event referencing request and returns response text"""

    event = db.session.query(Event).filter_by(id=event_id).one()
    event.name = request.form['Body']
    event.status = 1
    db.session.commit()
    # print('gave event #', event.id ' name: ', event.name)

    responseText = "Alright - We'll call it " + event.name + ". Where will " + event.name + " take place?"

    return responseText


def give_event_location(event_id, request):
    """add event location by referencing request and return response text"""

    event = db.session.query(Event).filter_by(id=event_id).one()
    event.location = request.form['Body']
    event.status = 2
    db.session.commit()
    # print('gave event #' + event.id ' location:' + event.location)

    responseText = "Ok. So " + event.name + " will take place at " + event.location + ". What date and time?"

    return responseText


def give_event_time(event_id, request):
    """add event location by referencing request and return response text"""

    event = db.session.query(Event).filter_by(id=event_id).one()
    event.time = request.form['Body']
    event.status = 3
    db.session.commit()
    # print('gave event #' + event.id ' time:' + event.time)

    responseText = "Perfect. " + event.name + " at " + event.location + " at " + event.time + ". Who should I invite? send user IDs separated by a comma or say 'everyone'."

    return responseText


def give_event_attendees(event_id, request):
    """add event attendees by referencing request and return response text"""

    responseText = ''

    attendeetext = request.form['Body']
    # if text is 'everyone' invite all of that user's friends
    if attendeetext.lower() == 'everyone':
        attendeelist = []
        this_user_phone = request.values['From']
        this_user_id = db.session.query(User).filter_by(phone=this_user_phone).one().id
        thisUsersFriends = db.session.query(Friends).filter_by(user_id=this_user_id).all()
        for i in thisUsersFriends:
            attendeelist.append(i.users_friend_id)
    else:
        attendeelist = attendeetext.split(',')
        for i in attendeelist:
            i = int(''.join(c for c in i if c.isdigit()))
    successfullyadded = []
    couldnotadd =[]
    for i in attendeelist:
        user_exists = db.session.query(User.id).filter_by(id=i).scalar() is not None
        if user_exists:
            thisattendee = i #int(i)
            relationship = Attendees(status=0, user_id=thisattendee, event_id=event_id)
            db.session.add(relationship)
            db.session.commit()
            successfullyadded.append(str(thisattendee))
        else:
            couldnotadd.append(i)

    # update event status to 4
    event = db.session.query(Event).filter_by(id=event_id).one()
    event.status = 4
    db.session.commit()
    if successfullyadded:
        responseText += 'Added users: ' + ', '.join(successfullyadded)
    if successfullyadded and couldnotadd:
        responseText += '\n'
    if couldnotadd:
        responseText += 'Could not add: ' + ', '.join(couldnotadd)
    responseText += "\nTo send invites, reply: \n'send invites, <event ID>, <message to invitees>.'"
    responseText += "\nThis event's ID is: " + str(event_id)
    return responseText


def create_user(request):
    """create new user given request"""

    requestor_phone = request.values['From']
    requestor_id = db.session.query(User).filter_by(phone=requestor_phone).one().id

    if requestor_id == 1:
        user = User(status=0, creator=1)
        db.session.add(user)
        db.session.commit()
        print('created new user')

        responseText = "Ok I'll add a new user. What is their name?"

    else:
        responseText = "Please ask Zach to help add a new user :)"

    return responseText


def give_user_name(user_id, request):
    """provide users name given user ID and request object"""

    user = db.session.query(User).filter_by(id=user_id).one()
    user.name = request.form['Body']
    user.status = 1
    db.session.commit()

    responseText = "Created new user named " + user.name + ". What's their number?"

    return responseText


def give_user_phone(user_id, request):
    """provide users phone number gievn user ID and request object"""

    # assign phone number and increment new user's status
    user = db.session.query(User).filter_by(id=user_id).one()
    user.phone = request.form['Body']
    user.status = 2

    # if user is adding someone else, add that person as their friend
    this_user_phone = request.values['From']
    this_user_id = db.session.query(User).filter_by(phone=this_user_phone).one().id
    if this_user_id != user_id:
        friendship = Friends(user_id=1, users_friend_id=user_id)
        db.session.add(friendship)

    db.session.commit()

    responseText = "Created new user named " + user.name + " with phone number: " + str(user.phone)

    return responseText


def send_invites(event_id, host_message):
    """send invites to everyone invited to event and returns nothing"""

    invitees = db.session.query(Attendees).filter_by(event_id=event_id).all()
    event = db.session.query(Event).filter_by(id=event_id).one()

    for invitee in invitees:

        inviteephone = db.session.query(User).filter_by(id=invitee.user_id).one().phone

        body = "Hello! I am a bot helping Zach to coordinate an event. Are you interested in going to this event? \n"
        body += event.name + "\n"
        body += event.location + "\n"
        body += event.time + "\n \n"
        body += "Zach's message: " + host_message + "\n \n"
        body += "(you can reply 'STOP' to never be invited to another event)"

        print('trying to send message:', body, 'to', inviteephone)

        client.messages.create(
            inviteephone,
            from_=twilio_number,
            body=body)

    pass


@app.route("/sms", methods=['GET', 'POST'])
def sms_reply():
    print('message from:', request.values['From'])

    message_body = request.form['Body']
    print('message:', message_body)

    user = db.session.query(User).filter_by(phone = request.values['From']).one()

    if user.id == 1:
        # user is me
        responseText = choose_action_host(request)
        print('response to Zach:', responseText)
    else:
        # user is someone else
        responseText = choose_action_guest(request)
        print('response to someone else:', responseText)

    resp = MessagingResponse()
    resp.message(responseText)

    return str(resp)


if __name__ == "__main__":
    app.run(debug=True)
