# event-pal
Eventpal is your own personal assistant for coordinating events with your friends. Want to go to dinner last minute but aren't in the mood to go alone? Ask eventpal to send a message to 3, 8, or all of your friends to let them know your plans. Eventpal will send an invite, handle RSVPs, and let you send updates to only confirmed attendees!

### DB setup
delete chatterdb.db and then use python shell to:
1. `from app import db`
1. `db.create_all()`

### To run:
1. `flask run` in this directory
1. `ngrok http 5000` in this directory and copy 'forwarding' URL
1. go to twilio: https://www.twilio.com/console/phone-numbers/incoming
1. click on phone number and scroll to 'messaging - a message comes in'
1. paste forwarding URL from ngrok with '/sms' at the end

### DB tables
user|event
----|-----
id|id
creator|owner
status|status
name|name
phone|location
||time


### TODO
* how to store user/friend/invitees relationship
* should all users' names be relative to their creator? ie I could appear multiple times in the User table but be referenced by different names for different other users
* alternatively, prompt new user to name themselves when they are first added. Could still have nickname mapping elsewhere
* alternatively, create unique usernames
