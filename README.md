Import Rig
==========

The usual way to import a rig from another file to current scene is:

 1. Link in the rig's group,
 2. Create proxy for the armature object in it,
 3. Append the script accompanying the rig,
 4. Open Text Editor space,
 5. Open and execute the script, so the rig's UI show up,
 6. And finally, with the proxy active, change to Pose Mode.

May not look like much, but it's so tedious! So I create this Blender addon to automate most of the steps above. Just link in the group, and you're ready to go.
