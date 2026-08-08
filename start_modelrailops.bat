@echo off

echo Starting Model Railroad Operations...

cd /d "%~dp0"

echo Current folder:
cd

echo Activating virtual environment...

call .venv-1\Scripts\activate

echo Python location:
where python

echo Starting application...

python -m modelrailroadops

echo Application ended.

pause