# Nila 3D Avatar Generator

## Generate the GLB

1. Install Blender 3.6 or newer on a computer.
2. Download create_nila.py from this folder.
3. Run this command in the downloaded file's folder:

   blender --background --python create_nila.py

4. The script creates nila_avatar.glb in the same folder.
5. Upload that GLB in the Nila 3D World page's model file picker.

Alternatively, open Blender, choose the Scripting workspace, open create_nila.py and press Run Script.

## Included
- Procedural human-proportioned base avatar
- Warm skin, dark hair, midnight-blue eyes and midnight-blue outfit
- Armature with torso, head, arms, hands, legs and feet
- Starter actions named Nila_Stand, Nila_Walk and Nila_Wave

## Quality and limitations
This is a procedural prototype, not a photorealistic scanned human. Detailed anatomy, realistic hands, hair strands, clothing folds, high-resolution skin textures, blink/smile facial blendshapes and lip-sync need a dedicated modelling and rigging pass. The web viewer can play animations embedded in a GLB, but does not generate lip-sync automatically.

The generator needs Blender on a computer or cloud machine; it cannot run inside the Android browser.
