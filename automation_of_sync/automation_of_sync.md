---
author: Tapir Lab.
title: Automation of Calendar Sync.
date: December 2020  
---

# Automation on Windows
## Steps:
1. Click start and type **Task Scheduler** and run **Task Scheduler**,
2. Go to **Action > Import Task...** and import **Synchronize.xml**,
3. Go to the **Actions** tab, select the listed action, and click the edit button on the bottom,
4. Click browse and select the **run_main.vbs**,
1. Then copy the full path of **run_main.vbs** and paste it to **Start in (optional)** section,
1. Click **ok** and, run the task manually until you configure it correctly.

## If Import Doesn't Work
1. Click start and type **Task Scheduler** and run **Task Scheduler**,
2. Go to **Action** tab and click on  **Create Task...**,
3. In the **General** tab, give a name to your task and enable **Run with highest privileges**,
4. In the **Trigger** tab, click **New...** and choose the appropriate trigger for you,
    * **Repeat Task Every:** option should be configured to run code periodically.
    * **for a duration of:** can be configured to **Indefinitely** to run while your computer is on.
5. In **Actions** tab, click **New...** and choose **Start a Program** as action,
    * **Browse** to where **run_main.vbs** file is located and choose **run_main.vbs** to execute batch in background.
    * Give path of the repository to **Start in (optional):** in order to correctly set paths when the script is executed.
6. Choose appropriate **conditions** and **setting** for you.
7. Save by clicking **OK** and test your task by running on demand.
8. For more information: [Microsoft Task Scheduler](https://docs.microsoft.com/en-us/windows/win32/taskschd/task-scheduler-start-page)

# Automation on Linux
## Steps:
1. Install crontab if you don't have it,
2. Go to **automation_of_sync** folder,
3. Change the paths in both **synchronization.sh** and **example_crontab.txt**,
4. **example_crontab.txt** can be directly imported but it overwrites existing. Be careful!
    * Backup your existing `crontab` by `crontab -l >> backup.txt`
5. Execute the following command in the **atuomation_of_sync** folder to add the task,
    * `crontab example_crontab.txt`,
    * Check whether it is imported or not by `crontab -l`,
6. Do not forget to update and check paths!
7. Default `crontab` entry executes `main.py` at every 10 minutes.
8. After each execution it adds output to the **test.log** file in the main directory.
10. **Note:** `synchronization.sh` may require permission to execution.
    * `sudo chmod +x synchronization.sh`  provides required permission.