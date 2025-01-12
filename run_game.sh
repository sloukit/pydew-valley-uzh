# set game language (en or de)
if [ "de" ]; then
    export GAME_LANGUAGE=de
fi
# redirecting stderr to dev/null to get rid of "+[IMKClient subclass]: chose IMKClient_Modern" messages
python main.py
#2> /dev/null
