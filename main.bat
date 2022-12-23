@echo off

REM https://stackoverflow.com/questions/764631/how-to-hide-console-window-in-python
REM https://superuser.com/questions/140047/how-to-run-a-batch-file-without-launching-a-command-window

REM START /B /MIN .\venv\Scripts\pythonw.exe ".\main.py"

.\venv\Scripts\python.exe ".\main.py"

@echo on
