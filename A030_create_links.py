# -*- coding: utf-8 -*-
"""
A030_create_links Macro for FreeCAD
==================================

This macro is a helper function for the Cutviews workflow in FreeCAD. 
It creates App::Link objects for all solids found in the selected body or assembly and 
adds them to a group named according to the selected cutview letter (e.g., selected Letter = F --> 'Cut_F' group).

Features:
---------
- Recursively collects all solids (bodies, parts, assemblies, links) from the selected body or assembly.
- Creates a group for the cutview letter if it does not already exist.
- Creates App::Link objects for each solid and adds them to the group.
- Sets the visibility of original bodies to False after linking.
- Provides user feedback via FreeCAD message boxes and the console.

Usage:
------
This function is intended to be called from a GUI panel (such as the Cutviews macro panel). 
It expects the panel object to have 'selected_body' and 'selected_letter' attributes.

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
from PySide import QtCore, QtGui
import time  # for selection wait

def A030_create_links(panel):
    doc = App.ActiveDocument
    if not doc:
        QtGui.QMessageBox.critical(None, "Error", "No active document found!")
        return
    body = getattr(panel, 'selected_body', None)
    if not body:
        QtGui.QMessageBox.critical(None, "Error", "Please select a body.")
        return
    # Get the letter
    letter = getattr(panel, 'selected_letter', None)
    if not (isinstance(letter, str) and len(letter.strip()) == 1):
        letter = panel.letter_combo.currentText() if hasattr(panel, 'letter_combo') else 'A'
    else:
        letter = letter.strip()

    # Find or create the group
    group_name = f"Cut_{letter}"
    group = None
    for obj in doc.Objects:
        if obj.TypeId == 'App::DocumentObjectGroup' and obj.Name == group_name:
            group = obj
            break
    if not group:
        group = doc.addObject('App::DocumentObjectGroup', group_name)
        group.Label = group_name

    allowed_types = [
        'Assembly::Assembly', 
        'Assembly::AssemblyObject', 
        'App::Part',
        'Part::Body', 
        'PartDesign::Body', 
        'App::Link', 
        'App::LinkSub'
    ]
    solids = []
    def collect(obj):
        t = getattr(obj, 'TypeId', '')
        if t in allowed_types[:3]:
            for c in getattr(obj, 'OutList', []):
                collect(c)
        elif t in ['PartDesign::Body', 'Part::Body', 'Part::Feature']:
            if t != 'Part::Feature' or (getattr(obj, 'Shape', None) and obj.Shape.Solids):
                solids.append(obj)
        elif t in ['App::Link', 'App::LinkSub']:
            linked = getattr(obj, 'LinkedObject', None)
            for l in (linked if isinstance(linked, (tuple, list)) else [linked]):
                if l and getattr(l, 'TypeId', '') in ['PartDesign::Body', 'Part::Body']:
                    solids.append(obj)
                    break
    collect(body)
    if not solids:
        QtGui.QMessageBox.critical(None, "Error", "No solids found in the selected body or assembly.")
        return
    for idx, obj in enumerate(solids):
        Gui.Selection.clearSelection()
        Gui.Selection.addSelection(obj)
        if getattr(obj, 'TypeId', '') in ['PartDesign::Body', 'Part::Body']:
            Gui.runCommand('Std_LinkMake', 0)
            obj.ViewObject.Visibility = False
        else:
            Gui.runCommand('Std_LinkMakeRelative', 0)
        sub_link = doc.ActiveObject
        if sub_link and getattr(sub_link, 'TypeId', '') == 'App::Link':
            sub_link.Label = f'{letter}{idx+1:03d}_Link_{obj.Label}'
            # Add the link to the group
            group.addObject(sub_link)
    doc.recompute()

