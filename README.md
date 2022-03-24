# Climbing Gym Notifier
This is a personal project to make it easier to get spots at the climbing gym when they're all full. It is built/tested using Python 3.8

### Chat Bot
The chat bot runs as a Flask app using app.py as the entry point. A Twilio account/phone number is needed to send and receive messages, the SID, auth token, and phone number for this account should go in constants.py. Then in Twilio, set the SMS webhook to be the url of the Flask app. To initialize the database, edit db_setup.py with legitimate admin user information, and then run it from the base directory:
<pre><code>python persistence/db_setup.py</pre></code>



### Notifier
To run the notifier, simply execute the main loop in a terminal like so:
<pre><code>python climbing-notifier-main.py</code></pre>
