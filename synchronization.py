#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This program synchronizes OpenProject tasks with Google Calendar.
Each work package created as a "task" on OpenProject will be represented as an
event on Google Calendar where "dueHour" of the task is the start of the event.
Synchronization requires a common structure between `tasks` and `events`. Thus,
not every information on the work packages is included in event creation.
Following parameters will be required to create an event, the rest is discarded:
ID, subject, description, parental relation, assignee, last update date, due date,
and "dueHour". "dueHour" parameter should be located at the end of the description
in the form of "dueHour=HH:MM:SS" where H is hour, M is minute, and S is second.
If the task starts with three exclamations (!) marks, it will not be synchronized.

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% Google Calendar Task Synchronization Script for Open Project
%% -------------------
%% $Author: Halil Said Cankurtaran$,
%% $Date: January 10th, 2020$,
%% $Revision: 1.0$
%% $Tapir Lab.$
%% $Copyright: Tapir Lab.$
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

Known Issues:
    1. If the due date is not given, the due hour does not have any importance.
       Event is directly created on the creation time.
    2. Event creation based on creation time is w.r.t. GMT +0, this is because
    of the OpenProject configurations. It might be changed or 3 hours added
    3. If the due date is given but the due hour is not given, then it can not sync.
    4. General Exception is used to create logs. Google Styleguide also
    recommends this approach.
    5. Sheet may end up with "The read operation timed out" if the sheet exceeds
    a certain number of logs. This problem occurs when 918th synchronization
    has been performed. Thus, the sheet should be cleaned periodically.
    6. All the tasks should be listed in one page on OpenProject.
"""
import json
from datetime import datetime, timedelta
import requests
from google.oauth2 import service_account
from googleapiclient.discovery import build


# Allowed length of task name for OpenProject = 255
# Allowed length of event name for Google Calendar = unknown.
# Event name for Google Calendar can be longer than 255
# Created token expires in 60 min
def get_projects_and_ids(session, url):
    """Reads projects from OpenProject and returns project names and ids"""

    read_url = json.loads(session.get(url+"projects/").content.decode('utf-8'))
    raw_projects = read_url['_embedded']['elements']
    parsed_projects = {elem['name']:elem['id'] for elem in raw_projects}

    return parsed_projects


def load_credentials(secret_file_path, scopes):
    """Loads credentials if secret_file_path is correct.

    Loads credentials of service_account added both calendar and sheet

    Args:
        secret_file_path: path to json credentials file of service account
        SCOPES: scopes to authorize credential. (calendar/sheet)

    Returns:
        credentials: google.oauth2.service_account.Credentials object

    Raises:
        Exception: Possibly a "FileNotFoundError", but might be connection err.
    """
    try:
        credentials = service_account.Credentials.from_service_account_file(
            secret_file_path, scopes=scopes)
        return credentials
    except Exception as error:
        raise error


def google_calendar_service(credentials):
    """Creates service for Google Calendar based on given credentials."""
    try:
        service = build('calendar', 'v3', credentials=credentials)
    except Exception as error:
        raise error

    return service


def google_sheet_service(credentials):
    """Creates service for Google Calendar based on given credentials."""
    try:
        service = build('sheets', 'v4', credentials=credentials)
    except Exception as error:
        raise error

    return service


def openproject_session(api_key):
    """Create a session with given api key"""
    session = requests.sessions.Session()  # Session to OpenProject
    session.auth = requests.auth.HTTPBasicAuth('apikey', api_key)  # Authorization

    return session


def read_workpackages(session, url, project_id):
    """Reads work packages from OpenProject and return as json"""
    api_url = url + "projects/{}/work_packages".format(project_id)
    workpackages = json.loads(session.get(api_url).content.decode('utf-8'))

    return workpackages


def parse_workpackages(workpackages):
    """Parses read workpackages into a structured dictionary element.

    Shapes work packages into a standard structure to use in the event creation
    There might be ignored information. Minimum working example only needs
    title, date, and time. If there happens any error during parsing,
    that work package will be added to the `err` list.
    Only the following parameters will be parsed to create an event, the rest
    is discarded: ID, subject, description, parental relation, assignee,
    last update date, due date, and "dueHour". "dueHour" parameter should be
    located at the end of the description in the form of "dueHour=HH:MM:SS"
    where H is hour, M is minute, and S is second. If the task starts with three
    exclamations (!) marks, it will not be synchronized.

    Args:
        workpackages: all workpackages returned from read_workpackages() func.

    Returns:
        parsed_wps: a dictionary of structured workpackages. Key is wp ID.
        err: a list of could not structured workpackages with Exception info
    """
    parsed_wps = {}
    err = []
    for elem in workpackages['_embedded']['elements']:
        # If description returns None, it will not be synfchronized
        # Packages starting with "!!!" line will not be synchronized
        if elem['description']['raw'] is None or \
            elem['description']['raw'].split('\n')[0] == '!!!':
            pass # Do not synchronize this package to Calendar
        else:
            try:
                tmp = {}
                tmp['wp_id'] = elem['id']  # Read work package ID
                tmp['subject'] = elem['subject'].strip()  # Read work package subject
                tmp['description'] = elem['description']['html']  # Save description

                if elem['_links']['parent']['href']:  # If there is a parent
                    tmp['parent'] = elem['_links']['parent']['href'].split('/')[-1] \
                        + ":" + elem['_links']['parent']['title']
                else:
                    tmp['parent'] = "No parent"

                if elem['_links']['assignee']['href']:  # There might not be an assignee
                    tmp['assignee'] = elem['_links']['assignee']['title'] # if there is
                else:
                    tmp['assignee'] = 'Not assigned to anyone'  # if there is not

                if elem['dueDate']:  # Assumes due hour is specified
                    tmp['due_date'] = elem['dueDate']  # if specified
                    tmp['due_hour'] = elem['description']['raw'].split('\n')[-1].split('=')[-1].strip()
                else:  # dueHour has no effect on time even if it is specified
                    tmp['due_date'] = elem['createdAt'].split('T')[0]  # create date
                    tmp['due_hour'] = elem['createdAt'].split('T')[-1][:-1]  # create time

                tmp['updated_at'] = elem['updatedAt']
                parsed_wps[elem['id']] = tmp
            except Exception as error:
                err.append([elem, error])

    return parsed_wps, err


def read_events(service, calendar_id, time='2020-10-11T00:00:00Z'):
    """Reads and returns all events on the calendar after the specified time
    Bug: What happens if this function returns nothing and raises an exception?
    """
    try:
        events_result = service.events().list(calendarId=calendar_id, timeMin=time).execute()
        events = events_result.get('items', [])
        return events
    except Exception as error:
        print(error)

def parse_events(events):
    """Parses events based on the structure used to create events.

    In order to check its content and situation, each event must be parsed
    into a predefined structure.

    Args:
        events: all events returned from read_events() func.

    Returns:
        parsed_events: a dictionary of structured events. Key is wp ID.
        err: a list of could not structured events with Exception info
    """
    parsed_events = {}
    err = []
    for elem in events:
        try:
            tmp = {}
            tmp['event_id'] = elem['id']  # ID required in deletion and update
            summary = elem['summary'].split(':')  # Split title of event
            tmp['wp_id'] = summary[0]  # Workpackage ID on Openproject
            tmp['subject'] = summary[-1]  # Workpackage subject on OpenProject
            description = elem['description'].split('\n')  # Split description
            tmp['assignee'] = description[-2]  # Assigne on OpenProject
            tmp['updated_at'] = description[-1]  # Update time of wp saved on Calendar
            due = elem['end']['dateTime'].split('T')  # Split dueDate to date, time
            tmp['due_date'] = due[0]  # DueDate of created event
            tmp['due_hour'] = due[1]  # DueHour of created event
            parsed_events[int(tmp['wp_id'])] = tmp  # Save to parsed_events dic.
        except Exception as error:
            err.append([elem, error])  # If a parsin error occurs, save to err list

    return parsed_events, err


def wp_to_event(work_package):
    """Converts workpackage to required event structure of Google Calendar

    Google API requires a body to create, update, and delete events.
    This function constructs the required body based on work package information.
    Followings will be included in the body of the event: ID, subject, description,
    parental relation, assignee, last update date, due date, and "dueHour".
    "dueHour" parameter should be located at the end of the description in the
    form of "dueHour=HH:MM:SS" where H is hour, M is minute, and S is second.
    Note: Seperation oh H, M, and S must be done via `colon` (:) mark.

    Args:
        work_pakcage: Parsed work package

    Returns:
        event: An event body to use in API calls"""
    wp = work_package
    event_start = str_to_date(wp['due_date'], wp['due_hour']) # Start datetime
    event_finish = event_start + timedelta(hours=1) # Finish datetime
    # Description includes, description, parental relation, assignee and last update datetime
    # Description is saved in HTML formant. It includes </p> at the end.
    # Thus there is no line breaking after description. However, if one uses
    # raw format, line braking should be added between description and parent
    description = wp['description'] + "Parent=" + wp['parent'] + "\n"\
                  + wp['assignee'] + "\n" + wp['updated_at']

    event = {'summary': str(wp['wp_id']) + ':' + wp['subject'],
             'description': description,
             'start': {'dateTime': event_start.astimezone().isoformat()},
             'end': {'dateTime': event_finish.astimezone().isoformat()},
             'reminders': {
                 'useDefault': False,
                 'overrides': [
                     {'method': 'popup', 'minutes': 24 * 60},
                     {'method': 'popup', 'minutes': 30},
                     ],
                 },
             }

    return event


def str_to_date(date, hour):
    """Converts str type date and hour to datetime object

    Datetime object provides operations. This package converts the datetime string
    into a datetime object to get the correct dueDate and dueHour. All dates should
    be in `isoformat`.

    Args:
        date: YYYY-MM-DD,  Y=Year, M=Month, D=Day, formatted date string
        hour: HH:MM:SS, H=Hour, M=Minute, S=Seconds, formatted hour string

    Returns:
        date_time_obj: a datetime.datetime object
    """
    due_date = [int(x) for x in date.split('-')]
    due_hour = [int(x) for x in hour.split(':')]
    # Year, month, day, hour, minute, seconds
    date_time_obj = datetime(due_date[0], due_date[1], due_date[2],
                             due_hour[0], due_hour[1], due_hour[2])

    return date_time_obj


def to_create(work_package, service, calendar_id):
    """Creates an event for work package via service on specifiedcalendar_id

    Google API enables configuration of events via a service built with
    Google Calendar API ['https://www.googleapis.com/auth/calendar'] scope.
    This function creates an event on the calendar specified  with `calendar_id`;
    based on given work package (wp), by using previously built service which
    includes Google Calendar API scope.

    Args:
        work_package: One of the elements of parsed workpackages
        service: Google API service built with Calendar scope
        calendar_id: Calendar ID of Google Calendar

    Returns:
        str(e): If an error occurs during the process, it will be returned.

    ToDo: Return a value for success insted of printing
    """
    wp = work_package
    event = wp_to_event(wp)
    try:
        response = service.events().insert(calendarId=calendar_id,
                                           body=event).execute()
        print('Event %s created at: %s' %(event['summary'],
                                          response.get('htmlLink')))
    except Exception as error:
        return str(error)


def to_delete(parsed_event, service, calendar_id):
    """Deletes given parsed_event from calendar using previously built service.

    Google API enables configuration of events via a service built with
    Google Calendar API ['https://www.googleapis.com/auth/calendar'] scope.
    This function deletes an event on the calendar specified  with `event_id`;
    based on a given event (parsed_event), by using previously built service
    which includes Google Calendar API scope.

    Args:
        parsed_event: One of the elements of parsed_events
        service: Google API service built with Calendar scope
        calendar_id: Calendar ID of Google Calendar

    Returns:
        str(e): If an error occurs during the process, it will be returned.

    ToDo: Return a value for success insted of printing
    """
    event_id = parsed_event['event_id']
    subject = parsed_event['subject']
    try:
        service.events().delete(calendarId=calendar_id,
                                eventId=event_id).execute()
        print('Work Package: {} has been deleted'.format(subject))
    except Exception as error:
        return str(error)


def may_update(work_package, parsed_event, service, calendar_id):
    """Updates wp on calendar if there is an update.

    Google API enables configuration of events via a service built with
    Google Calendar API ['https://www.googleapis.com/auth/calendar'] scope.
    This function updates an event on the calendar specified  with `event_id`;
    based on a given event (parsed_event), by using previously built service
    which includes Google Calendar API scope if there is any update.

    Args:
        work_package: One of the elements of parsed workpackages
        parsed_event: One of the elements of parsed_events
        service: Google API service built with Calendar scope
        calendar_id: Calendar ID of Google Calendar

    Returns:
        str(e): If an error occurs during the process, it will be returned.

    ToDo: Return a value for success insted of printing
    """
    wp = work_package
    if wp['updated_at'] != parsed_event['updated_at']:
        tmp = wp_to_event(wp)
        event_id = parsed_event['event_id']
        try:
            updated_event = service.events().update(calendarId=calendar_id,
                                                    eventId=event_id,
                                                    body=tmp).execute()
            print('Event %s has been updated' % updated_event['summary'])
        except Exception as error:
            return str(error)


def synchronize_wps(parsed_wps, parsed_events, service, calendar_id):
    """Synchronizes OpenProject work pacakges with Google Calendar events

    After loading and parsing all work packages and events, this function is
    called to synchronize events on Google Calendar. For each work package
    there are three possible actions: (i) It should be created, (ii) It is
    already created but its content requires an update, and (iii) work package is
    closed or deleted, so it should be removed from the calendar.

    Args:
        parsed_wps: a dictionary of structured workpackages. Key is wp ID.
        parsed_events: a dictionary of structured events. Key is wp ID.
        service: Authorized Google Calendar API service
        calendar_id: Id of the Calendar which workpackages are synchronized.

    Returns:
        wp_ids: classified wp_ids as create, delete or update
        err: Faced errors during creation, deletion or update
    """
    wps_on_openproject = set(parsed_wps.keys())
    wps_on_calendar = set(parsed_events.keys())
    # Decide which packages to create, to delete and may update
    to_create_set = wps_on_openproject.difference(wps_on_calendar)
    to_delete_set = wps_on_calendar.difference(wps_on_openproject)
    may_update_set = wps_on_calendar.intersection(wps_on_openproject)
    to_create_err, to_delete_err, may_update_err = [], [], []

    # Iterate over each work_package
    for wp_id in to_create_set:
        err = to_create(parsed_wps[wp_id], service, calendar_id)
        to_create_err.append(err)

    for wp_id in to_delete_set:
        err = to_delete(parsed_events[wp_id], service, calendar_id)
        to_delete_err.append(err)

    for wp_id in may_update_set:
        work_package, event = parsed_wps[wp_id], parsed_events[wp_id]
        err = may_update(work_package, event, service, calendar_id)
        may_update_err.append(err)

    wp_ids = [to_create_set, to_delete_set, may_update_set]
    error = [to_create_err, to_delete_err, may_update_err]

    return [wp_ids, error]


def save_logs(wps, errors, sheet_service, sheet_id):
    """Saves work package and error logs and to a Google Sheet.

    Action and error logs are saved to a Google Sheet since this code will be
    executed on a remote server. This function does not cover all the errors,
    for instance, authorization and service errors are neglected.

    Args:
        wps: a dictionary of ids of structured workpackages.
        errors: raised errors from calendar operations. If no error Nonetype
        sheet_service: Authorized Google Sheet API service
        sheet_id: Id of the sheet in which logs are saved.
    """
    # Error logs
    range_name = 'errors'
    # Parse errors and insert where the error occured
    to_create_errors = [str(elem) for elem in errors[0]]
    to_create_errors.insert(0, 'to_create_errors')

    to_delete_errors = [str(elem) for elem in errors[1]]
    to_delete_errors.insert(0, 'to_delete_errors')

    may_update_errors = [str(elem) for elem in errors[2]]
    may_update_errors.insert(0, 'may_update_errors')

    log_time = [datetime.now().isoformat()]
    values = [log_time, to_create_errors, to_delete_errors, may_update_errors]
    data = {'values': values}

    # Append into errors page of sheet
    sheet_service.spreadsheets().values().append(spreadsheetId=sheet_id,
                                                 valueInputOption='USER_ENTERED',
                                                 range=range_name,
                                                 body=data).execute()

    # Parse actions and insert where the action has taken
    range_name = 'actions'
    to_create = [str(elem) for elem in wps[0]]
    to_create.insert(0, 'to_create')

    to_delete = [str(elem) for elem in wps[1]]
    to_delete.insert(0, 'to_delete')

    may_update = [str(elem) for elem in wps[2]]
    may_update.insert(0, 'may_update')

    values = [log_time, to_create, to_delete, may_update]
    data = {'values': values,}

    # Append into actions page of sheet
    sheet_service.spreadsheets().values().append(spreadsheetId=sheet_id,
                                                 valueInputOption='USER_ENTERED',
                                                 range=range_name,
                                                 body=data).execute()
