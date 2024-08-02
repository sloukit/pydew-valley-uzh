"""Non-main script src for the game."""

# This file exists only so Python recognises the src folder as a package to be able to run the game from the main file.
# If it doesn't exist, the game will not be able to import anything from the src folder as a module
# because Python won't recognise it as a package.

# In addition, since the src folder is a package, every file in here will need to have dots before the name of another file
# in the same folder for the imports to work, like so:

# from .settings import *
# instead of :
# from settings import *
