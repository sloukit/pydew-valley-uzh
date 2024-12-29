# How to add translations to new Python file
# add this import
# `from src.support import get_translated_string as _`
# replace strings that needs to be translated from this:
# `print("This is hardcoded messages")`
# to this:
# `print(_("This is hardcoded messages"))`
# next run this script with python file name as parameter:
# `./extract_translations.sh src/screens/inventory.py`
#
# this script will extract new or changed strings from python file and add them to data/translations/en.txt (de.txt, etc.),
# but it won't remove from data/translations/en.tx if a string is removed from original source python file.

if [[ -z "$1" ]]
then
    echo usage: $0 script.py
    exit 1
fi

echo ""
python -m rich.rule "[blue]Extracting strings"

# this is not the intended way of using gettext/xgettext, but it's simpler and suits the purpose
xgettext -d base -o data/translations/temp_file.pot $1

# cat data/translations/temp_file.pot

cat data/translations/temp_file.pot | grep msgid | awk -F '"' '{print $2}' > data/translations/extracted_strings.txt

# cat data/translations/extracted_strings.txt

python -m tools.extract_translations "$1"

# clean up
rm data/translations/temp_file.pot
rm data/translations/extracted_strings.txt
