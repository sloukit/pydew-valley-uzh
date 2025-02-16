# set game language (en or de)
if [ "$1" ]; then
    export GAME_LANGUAGE=$1
fi
# redirecting stderr to dev/null to get rid of "+[IMKClient subclass]: chose IMKClient_Modern" messages
export USE_SERVER=true
export SERVER_URL=<YOUR_SERVER_NAME>

python main.py
#2> /dev/null
