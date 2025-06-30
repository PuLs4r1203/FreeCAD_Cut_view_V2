# -*- coding: utf-8 -*-
"""
A040_create_cubes Macro for FreeCAD
===================================

This macro is a helper function for the Cutviews workflow in FreeCAD. 
It creates a rectangular cut cube (as a PartDesign::Body with a centered rectangle sketch and pad) for 
each link in the selected cutview group (e.g., selected letter = F --> 'Cut_F' group). 
The cubes are created on the selected plane and grouped accordingly.

Features:
---------
- Creates a new PartDesign::Body for each link in the selected cutview group.
- Adds a centered rectangle sketch on the selected plane.
- Pads (extrudes) the rectangle to form a cube of the specified size.
- Adds the new cube body to the corresponding cutview group.
- Provides user feedback via FreeCAD message boxes and the console.

Usage:
------
This function is intended to be called from a GUI panel (such as the Cutviews macro panel). 
It expects the panel object to have 'selected_plane', 'letter_combo', and 'cube_size' attributes.

Dependencies:
-------------
- FreeCAD 1.1.0dev
- PySide (Qt for Python)
- Part, Sketcher workbenches

License:
--------
MIT License

Copyright (c) 2025 PuLs4r

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtGui
import Part
import Sketcher

def create_rectangle_sketch(doc, plane, cube_front_label, is_plane=True, force_letter=None, rect_size=500):
    """Create a section view with a centered rectangle on the given plane."""
    # Validate input
    if not plane:
        QtGui.QMessageBox.critical(None, "Error", "No plane selected!")
        return
    if not doc:
        QtGui.QMessageBox.critical(None, "Error", "No active document!")
        return
    try:
        # Create a new body for the cut cube
        body_front = doc.addObject('PartDesign::Body', cube_front_label)
        doc.recompute()
        # Create a centered rectangle sketch on the plane
        sketch = doc.addObject('Sketcher::SketchObject', 'CenteredRectangle')
        body_front.addObject(sketch)
        size = rect_size
        half = size / 2
        points = [App.Vector(-half, -half, 0), App.Vector(half, -half, 0), App.Vector(half, half, 0), App.Vector(-half, half, 0)]
        lines = [sketch.addGeometry(Part.LineSegment(points[i], points[(i+1)%4])) for i in range(4)]
        constraints = [
            ('Coincident', lines[0], 2, lines[1], 1),
            ('Coincident', lines[1], 2, lines[2], 1),
            ('Coincident', lines[2], 2, lines[3], 1),
            ('Coincident', lines[3], 2, lines[0], 1),
            ('Horizontal', lines[0]),
            ('Horizontal', lines[2]),
            ('Vertical', lines[1]),
            ('Vertical', lines[3]),
        ]
        for c in constraints:
            sketch.addConstraint(Sketcher.Constraint(*c))
        sketch.addConstraint(Sketcher.Constraint('DistanceX', lines[0], 1, lines[0], 2, size))
        sketch.addConstraint(Sketcher.Constraint('DistanceY', lines[1], 1, lines[1], 2, size))
        sketch.MapMode = 'FlatFace'
        sketch.AttachmentSupport = [(plane, '')]
        sketch.AttachmentOffset = App.Placement(App.Vector(0, 0, 0), App.Rotation())
        doc.recompute()
        # Pad (extrude) the rectangle to create the cube
        pad = body_front.newObject('PartDesign::Pad', 'Pad')
        pad.Profile = sketch
        pad.Length = size
        pad.Reversed = False
        pad.ViewObject.ShapeColor = (1.0, 0.5, 0.5)
        pad.ViewObject.Transparency = 70
        doc.recompute()
        doc.commitTransaction()
    except Exception as e:
        # Abort if rectangle creation fails
        App.Console.PrintError(f"Failed to create rectangle: {str(e)}\n")
        doc.abortTransaction()
        if App.GuiUp:
            QtGui.QMessageBox.critical(None, "Error", f"Failed to create rectangle:\n{str(e)}")
        return

def A040_create_cubes(panel):
    doc = App.ActiveDocument
    if not doc:
        QtGui.QMessageBox.critical(None, "Error", "No active document found!")
        return
    plane = getattr(panel, 'selected_plane', None)
    if not plane:
        QtGui.QMessageBox.critical(None, "Error", "Please select a plane.")
        return
    letter = panel.letter_combo.currentText()
    size = panel.cube_size  # Use property instead of .value()
    # Find the main group
    all_group = None
    for obj in doc.Objects:
        if getattr(obj, 'TypeId', '') == 'App::DocumentObjectGroup' and obj.Name == 'All_Cutviews':
            all_group = obj
            break
    if not all_group:
        group_names = [obj.Name for obj in doc.Objects if getattr(obj, 'TypeId', '') == 'App::DocumentObjectGroup']
        App.Console.PrintError(f"Group 'All_Cutviews' not found!\nExisting groups: {group_names}\n")
        QtGui.QMessageBox.critical(None, "Error", "Group 'All_Cutviews' not found!")
        return
    # Find the subgroup Cut_[Letter]
    group_name = f"Cut_{letter}"
    group = None
    for obj in all_group.Group:
        if getattr(obj, 'TypeId', '') == 'App::DocumentObjectGroup' and obj.Name == group_name:
            group = obj
            break
    if not group:
        QtGui.QMessageBox.critical(None, "Error", f"Group '{group_name}' not found in 'All_Cutviews'!")
        return
    # Count links
    links = [o for o in group.Group if getattr(o, 'TypeId', '') == 'App::Link']
    count = len(links)
    if count == 0:
        QtGui.QMessageBox.critical(None, "Error", f"No links found in group '{group_name}'!")
        return
    for i in range(count):
        cube_label = f"{letter}{i+1:03d}_Cutcube"
        before_objs = set(doc.Objects)
        create_rectangle_sketch(doc, plane, cube_label, is_plane=True, force_letter=letter, rect_size=size)
        after_objs = set(doc.Objects)
        new_objs = after_objs - before_objs
        for obj in new_objs:
            if getattr(obj, 'TypeId', '') == 'PartDesign::Body':
                group.addObject(obj)