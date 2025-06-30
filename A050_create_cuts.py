# -*- coding: utf-8 -*-
"""
A050_create_cuts Macro for FreeCAD
==================================

This macro is a helper function for the Cutviews workflow in FreeCAD. 
It performs a boolean cut (Part_Cut) for each pair of link and cut cube 
in the selected cutview group (e.g., selected letter = F --> 'Cut_F' group). 
The macro matches links and cubes by their label prefix and creates a cut object for each pair.

Features:
---------
- Iterates over all App::Link objects in the selected cutview group.
- Finds the corresponding cut cube (PartDesign::Body) by label.
- Selects both objects and executes the Part_Cut command.
- Renames the resulting cut object for clarity.
- Provides user feedback via FreeCAD console messages and warnings.

Usage:
------
This function is intended to be called from a GUI panel or macro. It expects:
    - doc: the active FreeCAD document
    - sub_links: a list of App::Link objects in the cutview group
    - letter: the selected cutview letter (A-Z)
    - num_cubes: the number of cubes/links in the group

Dependencies:
-------------
- FreeCAD 1.1.0dev
- re (Python standard library)

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
import re

def A050_create_cuts(doc, sub_links, letter, num_cubes):
    """
    For each pair (Link + Cutcube), perform a Part_Cut operation.
    The cut cubes are found by their label.
    """
    for sublink in sub_links:
        link_label = sublink.Label
        # Extract prefix: everything up to the first underscore after the number (e.g., L001_Link, C001_Link, etc.)
        match = re.match(r"([A-Z]\d+)_Link", link_label)
        if not match:
            App.Console.PrintWarning(f"No valid link prefix found in {link_label}\n")
            continue
        prefix = match.group(1)
        cube_label = f"{prefix}_Cutcube"
        # Find the cut cube object by label
        cube_obj = next((o for o in doc.Objects if getattr(o, 'Label', '') == cube_label), None)
        if not cube_obj:
            App.Console.PrintWarning(f"No cut cube found for {link_label} (searched: {cube_label})\n")
            continue
        # Select and perform cut
        Gui.Selection.clearSelection()
        Gui.Selection.addSelection(sublink)
        Gui.Selection.addSelection(cube_obj)
        Gui.runCommand('Part_Cut', 0)
        cut_obj = doc.ActiveObject
        # Optionally: rename the new object
        if cut_obj:
            cut_label = link_label.replace('_Link', '_Cut_[') + "]"
            cut_obj.Label = cut_label
            App.Console.PrintMessage(f"Created: {cut_label}\n")