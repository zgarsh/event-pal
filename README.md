# event-pal

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
