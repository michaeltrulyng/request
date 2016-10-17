from apiclient import discovery
import calendar
import datetime
from datetime import timedelta
import httplib2
import json
import oauth2client
from oauth2client import client
from oauth2client import tools
import os
import time
import urllib2

from apiclient.discovery import build
from oauth2client.client import OAuth2WebServerFlow

GMAIL_SECRET_FILE = '/home/mtl/python/gmail_secret.json'
CALENDAR_SECRET_FILE = '/home/mtl/python/calendar_secret.json'
GMAIL_SCOPE = 'https://www.googleapis.com/auth/gmail.compose'
GMAIL_APPLICATION_NAME = 'Gmail API Quickstart'

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
GRANT_TYPE = 'http://oauth.net/grant_type/device/1.0'

REDIRECT_URI = 'urn:ietf:wg:oauth:2.0:oob'
REQUEST_URL = 'https://accounts.google.com/o/oauth2/device/code'
CALENDAR_NAME = 'Late Shift Calendar'
EVENT_NAME = 'AED LATE SHIFT'

QUERY = 'from:catchcan@producepro.com'
MAX_RESULTS = 15

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser( '~' )
    credential_dir = os.path.join( home_dir, '.credentials' )
    if not os.path.exists( credential_dir ):
        os.makedirs( credential_dir )
    credential_path = os.path.join( credential_dir,
                                   'gmail-python-quickstart.json' )

    store = oauth2client.file.Storage( credential_path )
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets( GMAIL_SECRET_FILE, GMAIL_SCOPE )
        flow.user_agent = GMAIL_APPLICATION_NAME
        if flags:
            credentials = tools.run_flow( flow, store, flags )
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run( flow, store )
        print( 'Storing credentials to ' + credential_path )
    return credentials

def main():

	credentials = get_credentials()
	http = credentials.authorize( httplib2.Http() )
	gmail_mailbox = discovery.build( 'gmail', 'v1', http=http )

	try:
		response = gmail_mailbox.users().messages().list( userId='me', q=QUERY, maxResults=MAX_RESULTS ).execute()
		messages = []

		if 'messages' in response:
			messages.extend( response['messages'] )

		for message in messages:
			mesg = gmail_mailbox.users().messages().get( userId='me', id=message['id'] ).execute()
			print( mesg['snippet'] + '\n' )

	except errors.HttpError, e:
		print( 'Error: ' + e )

	with open( CALENDAR_SECRET_FILE ) as client_json:
		client_data = json.load( client_json )

	flow = OAuth2WebServerFlow( client_id=client_data['client_id'],
								client_secret=client_data['client_secret'],
								scope=SCOPES,
								redirect_uri=REDIRECT_URI )

	try:
		auth_uri = flow.step1_get_authorize_url()
		print( 'Please paste this URL in your browser to authenticate this '
			'program.')
		print( "\n%s\n" % auth_uri )
		auth_code = raw_input( 'Enter the code it gives you here: ' )

		credentials = flow.step2_exchange( auth_code )

		http = httplib2.Http()
		http = credentials.authorize( http )
		service = build( 'calendar', 'v3', http=http )

		# Find first calendar matching target name
		calendar_found = 0
		page_token = None

		while (True and not calendar_found ):
			calendar_list = service.calendarList().list( pageToken=page_token ).execute()
			for calendar_list_entry in calendar_list['items']:
				if ( calendar_list_entry['summary'] != CALENDAR_NAME ):
					continue
				else:
					calendar_found = 1
					calendar_id = calendar_list_entry['id']
					break
			page_token = calendar_list.get( 'nextPageToken'  )
			if not page_token:
				break

		if calendar_id:
			service.calendars().get( calendarId=calendar_id ).execute()

			# This code is slightly different for testing purposes
			today = datetime.date.today()
			last_day = calendar.monthrange( today.year, today.month )[1]
			event_min = ( datetime.datetime( today.year, today.month, 1,
				0, 0, 0 ).isoformat( 'T' ) + 'Z' )
			event_last_day = datetime.datetime( today.year, today.month, last_day,
				0, 0, 0 )
			event_max = (( event_last_day + timedelta( days=1 )).isoformat( 'T' ) + 'Z' )

			print( 'Calendar ID: %s\n' % calendar_id )
			print( 'Time min: ' + event_min )
			print( 'Time max: ' + event_max )

			page_token = None
			while True:
				events = service.events().list( calendarId=calendar_id, timeMin=event_min, timeMax=event_max, pageToken=page_token, orderBy='updated' ).execute()
				for event in events['items']:
						event_object = service.events().get( calendarId=calendar_id, eventId=event['id'] ).execute()
						print( 'Event name: ' + event_object['summary'] )
						event_object_start = event_object['start']
						print( 'Event start: ' + event_object_start['dateTime'] )
						print( 'Event created: ' + event_object['created'] )
						for attendee in event_object['attendees']:
							print( '\tName: ' + attendee['displayName'] )
							print( '\tE-mail: ' + attendee['email'] )
				page_token = events.get( 'nextPageToken' )
				if not page_token:
					break

	except urllib2.URLError, e:
		print( 'Error: %s\n' % e )

if __name__ == '__main__':
	main()
