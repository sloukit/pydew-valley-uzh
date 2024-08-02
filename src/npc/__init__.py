"""
src.npc
This module groups everything related to AI-controlled Entities.

Before initialising any Entity, this module should first be set up by calling
setup.AIData.setup. This ensures that all behaviour trees shared between
Entities of the same type are properly initialised, and that variables
necessary for AI pathfinding are created.

If you need to reference any specific entity type, you are encouraged to do so
using their respective base classes, located in src.npc.bases, to avoid having
problems with circular imports.
"""
