# Google Calendar Task Synchronization Script for OpenProject
![Tapir Lab.](http://tapirlab.com/wp-content/uploads/2020/10/tapir_logo.png)
Project management is an essential part of every research laboratory, institution, and company. However, some of the current open source solutions, such as OpenProject, lack of direct synchronization with common calendars. That means users of these open source solutions have to check each and every update on the platform itself. This kind of drawbacks eventually leads to inefficient and inadequate project management. With this repository, Tapir Lab. enables OpenProject users to synchronize their "tasks" with Google Calendar. This feature is requested by the community and its current status can be seen on the [link](https://community.openproject.com/projects/openproject/work_packages/22861/activity). Detailed explanation and examples can be seen below.   
## Description
This repository connects OpenProject with Google Calendar by use of APIs. The OpenProject API key can be created easily on the `"My account > Access token"` tab. On the other hand, in order to run this program, you have to create a Google [`service account`](https://cloud.google.com/iam/docs/service-accounts) and add this account as an editor to both Google Calendar and Google Sheet. Google Sheet is required to save logs. Logs are saved to a Google Sheet instead of a local file to ease process. `Service account` provides a better way to handle authorization. Even if you don't wan to run this script on a server, the use of `user accounts` is not recommended and supported due to several security considerations. For more information please refer to the official documents of both platforms. Some of the useful links are listed below:

* [**OpenProject API Example**](https://docs.openproject.org/api/example/#basic-auth)
* [**Google Service Accounts**](https://cloud.google.com/iam/docs/service-accounts)
* [**Creation of Service Account**](https://cloud.google.com/iam/docs/creating-managing-service-accounts)
* [**Using OAuth 2.0 to Access Google APIs**](https://developers.google.com/identity/protocols/oauth2#serviceaccount)

Following should be provided to synchronize tasks with the calendar:
1. OpenProject API key,
2. Google service account key file,
3. Project ID of the project (explained in the example),
4. Google Calendar and Sheet IDs (explained in the example),

## Prerequisites

* Python3
* Other necessary packages can be installed via `pip install -r requirements.txt`

## Folder Structure
```
OP2GC-Synchronization
|── automation_of_sync
|   |── Scripts and tutorials for automation
|── tutorial
|   |── Explanation of task creation steps
|── LICENSE
|── main.py
|── README.md
|── requirements.txt
|── run_main.vbs
|── synchronization.py
```
## Example 
Synchronization can be performed after the configuration of the `main.py` script with the correct parameters. An extensive explanation of each parameter can be found below the visualization of the process.
![Example Output](./tutorial/sync.gif)

**Required parameters:**
```python
    required_parameters = {
        'path_to_secret_file': secret key file of Google Service Account,
        'SCOPES': field of permissions to authorize,
        'calendar_id': the id of the Google Calendar,
        'openproject_api_url': 'your_open_project_url' + '/api/v3',
        'openproject_api_key': key to access OpenProject API,
        'project_name': name of your OpenProject Project,
        'save_logs': whether you want to sync logs to sheet or not,
        'sheet_id': Google Sheet id, if 'save_logs' false, can be an empty string
        }
```
* **path_to_secret_file:** is the file that includes your credentials to authorize Google APIs. For more detailed information refer to the official documentation. 
* **SCOPES:** are used to specify which applications will be authorized. In this case, calendar and sheet apps must be authorized.
* **calendar_id:** can be found under the `Integrate Calendar` section of the `settings and sharing` page of the calendar that you want to synchronize. The tests should be performed on a temporary calendar before integrating the system in order to prevent loss of information!
* **openproject_api_url:** You can access the OpenProject API by adding `/api/v3` to the end of the OpenProject URL. So the first part of the URL should be given as `https://www.myopenprojecturl.com`.
* **openproject_api_key:** API Key to authorize. Official documents should be read in order to create API Key correctly. Some useful links are provided under the `Description` section.
* **project_name:** In order to access your project, its `id` should be found. This can be done by inspecting the `https://www.myopenprojecturl.com/api/v3/projects/` page. Additionally, `get_projects_and_ids(session, url)` function is provided in `synchronization.py` to read all projects and access their ids. For example, assume that you have two projects named "Project 1" and "PROJECT2", and want to synchronize "Project 1". `get_projects_and_ids()` function returns a dictionary in the form of `projects = {'Project 1': 1, 'PROJECT2': 2}`. Then, project id can be given as `projects['Project 1']`. In order to ease the process, `project_name` is given instead of `id` as a parameter, and its corresponding `id` is found.
* **save_logs:** Logs of created, deleted, and updated packages can be saved into a Google Sheet. However, if the script fails to access Google API or OpenProject API these logs may be misleading. Thus, services and sessions should be checked whether they operate correctly or not. If you want to save task logs, specify this as `True` and provide `Sheet ID`.
* **sheet_id:** Official documentation of Google Sheet API explains how to find Google Sheet ID properly. Please visit the [link](https://developers.google.com/sheets/api/guides/concepts).

## License

The software is licensed under the MIT License.