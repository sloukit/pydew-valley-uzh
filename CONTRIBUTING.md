### To add additional characters
All the imports happen in the load_assets in main.py and the character_importer method imports the content of images/characters. The name of the subfolder will be a key in the dictionary
and the files within that subfolder should be tileset images with each tile being 48x48. Each of these images will be stored in a sub dictionary attached to the subfolder key; the first row
should be the up animation, the second one the down animation and the third row the left aimation; animations for the right side will be a flipped copy of the left side.
If you want to add more character animations just check out the rabbit folder in characters to understand how it works.

In sprites.py there is a Player class that currently controls the rabbit in the game you could inherit from that and overwrite methods or use the Entity class as a parent and add more to it.
(The Player class currently has too many methods, quite a few of those could be stored in Entity to make the whole setup more flexible)

### Adding to the tileset
The level was created in Tiled (mapeditor.org). The layers are fairly self-explanatory (or at least I hope they are). Add more things as needed and then expand the setup method in the Level class to import it.
The graphics folders contain a few more graphics that could be used to decorate the map.

**Collisions**<br>
If you would like to add custom collisions to a new object that you have created, feel free to add them in Tiled's tile collision editor.
To do this, simply open the corresponding tileset and click on the tile you want to edit. In the window on the right, you can then insert a rectangle that will then be used as hitbox for the object.
<br>
(If you don't see the Tile Collision Editor, open it under `View -> Views and Toolbars -> Tile Collision Editor` while in the tileset overview)

### Extracting data
in the Level class there is an apply_tool method that lets an entity interact with the world (i.e. use a tool or plant a seed); if you want to measure what's going on in the game this should be a good starting point.

### Additional code
Please note that Python 3.12 or above is required to run the project, due to it using some new Python features unavailable in previous versions.
Notably, newest features in type-checking requiring a new keyword only available in 3.12 or above might be used some time in the future, so if you have a lower version of Python,
make sure you upgrade to 3.12 before contributing to the project.
