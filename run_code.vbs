Set WshShell = CreateObject("WScript.Shell") 
WshShell.Run chr(34) & ".\automation_of_sync\synchronization.bat" & Chr(34), 0
Set WshShell = Nothing