# Pydew Valley (Clear Code) Mod at the University of Zurich

## About project
We are modifying Pydew Valley (Clear Code) in Python and Pygame so that we can use it for an experimental study in psychology at the University of Zurich.\
In the experimental study, we investigate social influence on the adoption of health behaviors.\
The due date for the game is September 1, 2024.

## Tasklist and game levels
A detailed tasklist can be found in this GitHub project: https://github.com/users/sloukit/projects/1. \
You find more details on the game levels here: https://docs.google.com/spreadsheets/d/1NAssjrPN4mv3kBC3e5YmJcYkJZLU7450cFR9EhCbfgE/edit?gid=374591304#gid=374591304. \
If you are interested in collaborating with us on this project, please contact me at s.kittelberger[at]psychologie.uzh.ch.

## Run project locally
```bash
git clone https://github.com/sloukit/pydew-valley-uzh.git
pip install pygame-ce
cd pydew-valley-uzh-main
python3 main.py
```

## Resources
This game builts on a Clear Code tutorial: \
https://www.youtube.com/watch?v=T4IX36sP_0c&ab_channel=ClearCode \

We use assets from Sprout Lands (basic and premium version): \
https://cupnooble.itch.io/sprout-lands-asset-pack 

## Discord
Project server:      https://discord.gg/SuthU2qKaZ \
Pygame(-ce) server:  https://discord.gg/pygame \
Clear Code server:   https://discord.gg/Z2C3vnrxef \
Sprout Lands server: https://discord.gg/eTvqPnCRds 

## More information from the creator
Stardew Valley clone made in Pygame-ce. Created by Christian Koch / Clear code. 
The code for this project is in the public domain (Creative commons 0) you can use it for any purpose, including commercial ones, without permission. Attributions are not necessary but would be appreciated. 

This code is intended for a community project and is intended to be expanded. 

**To add additional characters**<br>
All the imports happen in the load_assets in main.py and the character_importer method imports the content of images/characters. The name of the subfolder will be a key in the dictionary 
and the files within that subfolder should be tileset images with each tile being 48x48. Each of these images will be stored in a sub dictionary attached to the subfolder key; the first row    
should be the up animation, the second one the down animation and the third row the left aimation; animations for the right side will be a flipped copy of the left side. 
If you want to add more character animations just check out the rabbit folder in characters to understand how it works. 

In sprites.py there is a Player class that currently controls the rabbit in the game you could inherit from that and overwrite methods or use the Entity class as a parent and add more to it. 
(The Player class currently has too many methods, quite a few of those could be stored in Entity to make the whole setup more flexible) 

**Adding to the tileset**<br>
The level was created in Tiled (mapeditor.org). The layers are fairly self-explanatory (or at least I hope they are). Add more things as needed and then expand the setup method in the Level class to import it. 
The graphics folders contain a few more graphics that could be used to decorate the map. 

**Extracting data**<br>
in the Level class there is an apply_tool method that lets an entity interact with the world (i.e. use a tool or plant a seed); if you want to measure what's going on in the game this should be a good starting point. 

**Additional code**<br>
Please note that Python 3.12 or above is required to run the project, due to it using some new Python features unavailable in previous versions.
Notably, newest features in type-checking requiring a new keyword only available in 3.12 or above might be used some time in the future, so if you have a lower version of Python,
make sure you upgrade to 3.12 before contributing to the project.
