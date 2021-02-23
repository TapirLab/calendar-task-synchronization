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
"""
from datetime import datetime
import synchronization as sync

def main(parameters):
    """Synchronizes OpenProject tasks with Google Calendar.

    The main function executes the synchronization task. Its parameters are given
    as a dictionary to ease calls. Each of the parameters should be defined
    except the `sheet_id` parameter if `save_logs` is `False`.

    Args:
        parameters: required parameters to complete synchronization
            {
            'path_to_secret_file': secret key file of Google Service Account,
            'SCOPES': field of permissions to authorize,
            'calendar_id': the id of the Google Calendar,
            'openproject_api_url': 'your_open_project_url' + '/api/v3',
            'openproject_api_key': key to access OpenProject API,
            'project_name': name of your OpenProject Project,
            'save_logs': whether you want to sync logs to sheet or not,
            'sheet_id': Google Sheet id, if 'save_logs' false, can be an empty string
            }
    """
    # Google Calendar and Sheets API Configurations
    # Path to service account credentials json file
    secret_file = parameters['path_to_secret_file']
    # Scopes to create API services
    scopes = parameters['SCOPES']
    # Calendar ID
    calendar_id = parameters['calendar_id']

    # OpenProject API configurations, session authorization and reading
    url = parameters['openproject_api_url']
    api_key = parameters['openproject_api_key']
    project_name = parameters['project_name'] # Name of your project as it is seen on OpenProject

    # Read and parse work packages from OpenProject
    # Initilize and Authorize OpenProject session
    session = sync.openproject_session(api_key)

    # Get project ID
    projects = sync.get_projects_and_ids(session, url)
    project_id = projects[project_name]

    # Read work packages in json structre
    all_work_packages = sync.read_workpackages(session, url, project_id=project_id)
    # Parse work packages into predetermined structure
    parsed_wps, op_err = sync.parse_workpackages(all_work_packages)

    # Load service account credentials
    credentials = sync.load_credentials(secret_file, scopes)
    # create calendar service
    calendar_service = sync.google_calendar_service(credentials)
    # Read events from calendar
    all_events = sync.read_events(calendar_service, calendar_id)
    # Parse events
    parsed_events, gc_err = sync.parse_events(all_events)
    # SYNCHRONIZE!
    wps, errors = sync.synchronize_wps(parsed_wps,
                                       parsed_events,
                                       calendar_service,
                                       calendar_id)

    if parameters['save_logs']:
        # Create sheet service
        sheet_id = parameters['sheet_id']
        sheet_service = sync.google_sheet_service(credentials)
        # save logs
        sync.save_logs(wps, errors, sheet_service, sheet_id)

    print('Synchronization has been completed at %s!' %datetime.today().isoformat())


if __name__ == "__main__":

    # Before synchronization, you have to add your service account to your
    # calendar and sheet as an editor. If you do not add your account as an editor
    # authorization can not be performed.
    # If you do not want to save package logs, set 'save_logs=False'
    # If 'save_logs' is false, you do not need to provide sheet id.
    # Required parameters to synchronize OpenProject with Google Calendar.
    required_parameters = {
        'path_to_secret_file': 'path_to_your_servis_accountsecret_file',
        'SCOPES': ['https://www.googleapis.com/auth/calendar',
                   'https://www.googleapis.com/auth/spreadsheets'],
        'calendar_id': 'your_google_calendar_id',
        'openproject_api_url': 'your_open_project_url' + '/api/v3/',
        'openproject_api_key': 'your_open_project_api_key',
        'project_name': 'your_projet_name',
        'save_logs': False,
        'sheet_id': 'your_google_sheet_id'
        }

    main(required_parameters)
