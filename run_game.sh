# set game language (en or de)
if [ "$1" ]; then
    export GAME_LANGUAGE=$1
fi
# redirecting stderr to dev/null to get rid of "+[IMKClient subclass]: chose IMKClient_Modern" messages
python main.py
#2> /dev/null
