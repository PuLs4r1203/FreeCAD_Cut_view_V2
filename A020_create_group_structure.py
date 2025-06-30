# -*- coding: utf-8 -*-
"""
A020_create_group_structure Macro for FreeCAD
============================================

This macro is a helper function for the Cutviews workflow in FreeCAD. 
It creates and manages the group structure for organizing cut views within the active document. 
The macro ensures that a main group ('All_Cutviews----------------') exists, and then creates a 
subgroup for the selected cutview letter (e.g., selected Letter = F --> 'Cut_F' group).

Features:
---------
- Ensures the existence of a main group for all cutviews.
- Creates a subgroup for the selected cutview letter if it does not already exist.
- Adds the new subgroup to the main group.
- Provides user feedback via the FreeCAD console and message boxes.

Usage:
------
This function is intended to be called from a GUI panel (such as the Cutviews macro panel). 
It expects the panel object to have a 'selected_letter' attribute containing the cutview letter (A-Z).

Dependencies:
-------------
- FreeCAD 1.1.0dev
- PySide (Qt for Python)

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

def A020_create_group_structure(panel):
    doc = App.ActiveDocument
    if not doc:
        QtGui.QMessageBox.critical(None, "Error", "No active document found!")
        return
    # Check for existing group with label
    group_label = "All_Cutviews----------------"
    for obj in doc.Objects:
        if obj.TypeId == 'App::DocumentObjectGroup' and obj.Label == group_label:
            all_cutviews_group = obj
            break
    else:
        # Create group if not found
        all_cutviews_group = doc.addObject("App::DocumentObjectGroup", "All_Cutviews")
        all_cutviews_group.Label = group_label
        App.Console.PrintMessage("All_Cutviews group has been created!\n")
        doc.recompute()

    # Get selected letter from panel (assume panel.selected_letter exists)
    cut_letter = getattr(panel, 'selected_letter', None)
    if isinstance(cut_letter, str):
        cut_letter = cut_letter.strip()
    if not cut_letter or not isinstance(cut_letter, str) or len(cut_letter) != 1:
        App.Console.PrintError(f"No valid cutview letter selected! (Value: {cut_letter})\n")
        return
    cut_group_label = f"Cut_{cut_letter}"
    # Check if group with this label exists in All_Cutviews group
    for obj in all_cutviews_group.Group:
        if obj.TypeId == 'App::DocumentObjectGroup' and obj.Label == cut_group_label:
            App.Console.PrintMessage(f"{cut_group_label} already exists!\n")
            return
    # Create Cut_[Letter] group
    cut_group = doc.addObject("App::DocumentObjectGroup", cut_group_label)
    cut_group.Label = cut_group_label
    all_cutviews_group.addObject(cut_group)
    App.Console.PrintMessage(f"{cut_group_label} has been created!\n")
    doc.recompute()

