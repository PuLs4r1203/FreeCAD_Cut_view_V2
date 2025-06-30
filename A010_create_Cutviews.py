# -*- coding: utf-8 -*-
"""
Create Cutviews Macro for FreeCAD
=================================

This macro provides a graphical user interface (GUI) in FreeCAD to automate the creation of cut views for assemblies or parts. 
It is designed to streamline the workflow for generating sectional views by guiding the user through a series of selections and actions. 
The macro is modular and interacts with other scripts for group structure creation, link management, cube generation, and cut operations.

Features:
---------
- **Plane Selection:**
  Allows the user to select a `Part::Plane` or `Part::DatumPlane` from the 3D view. 
  The selected plane's name and label are displayed in the GUI.

- **Body Selection:**
  Enables selection of any body object (e.g., `Part::Body`, `App::Part`, `Assembly::Assembly`, etc.). 
  The selected body's name and label are shown in the GUI.

- **Cutview Letter Assignment:**
  Lets the user assign a letter (A-Z) to the cutview, which is used for group naming and organization.

- **Cube Size Selection:**
  Provides a dropdown to select the cube size (500 mm to 5000 mm in 500 mm increments) for the cut operation.

- **Automated Workflow:**
  Includes buttons to execute the following steps individually or as a complete sequence:
    - Create group structure    (visibility = False by default, watch in the code)
    - Create links              (visibility = False by default, watch in the code)
    - Create cubes              (visibility = False by default, watch in the code)
    - Perform cuts              (visibility = False by default, watch in the code)
    - Execute all steps in order ("Create Cutview")

- **State Management:**
  Checks for existing groups, links, cubes, and cuts to prevent duplicate operations and ensure a consistent workflow.

- **User Feedback:**
  Provides real-time feedback and error messages in the FreeCAD console and GUI fields.

Usage:
------
1. Run this macro in FreeCAD.
2. Use the GUI to select a plane and a body from the 3D view or in the tree.
3. Assign a letter for the cutview and store it (the letter will be used for group naming).
4. Select the desired cube size (it is necessary for the cut operation).
5. Click the appropriate buttons to create the group structure, links, cubes, and cuts, or ... (visibility = False by default, watch in the code)
6. Use the "Create Cutview" button to perform all steps automatically.

Dependencies:
-------------
- FreeCAD 1.1.0dev
- PySide (Qt for Python)
- The following scripts must be present in the same directory:
    - A020_create_group_structure.py
    - A030_create_links.py
    - A040_create_cubes.py
    - A050_create_cuts.py

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

import FreeCAD, FreeCADGui
from PySide import QtGui
import time                         # for selection wait
import importlib                    # For reloading modules during runtime

import A020_create_group_structure  # Group structure creation logic
import A030_create_links            # Link creation logic
import A040_create_cubes            # Cube creation logic
import A050_create_cuts             # Cut creation logic

# Store selections for later use
global selected_plane, selected_body
selected_plane = None
selected_body = None

class Create_Cutviews:
    def __init__(self):
        self.form = QtGui.QWidget()
        self.form.setWindowTitle("Create Cutviews")
        self.layout = QtGui.QVBoxLayout(self.form)

        # === Selection area (Selectors) ===
        selection_group = QtGui.QGroupBox("")
        selection_layout = QtGui.QVBoxLayout(selection_group)

        # --- 1. Plane Selector ---
        plane_row = QtGui.QHBoxLayout()
        self.plane_select_button = QtGui.QPushButton("Select Plane")
        plane_row.addWidget(self.plane_select_button)
        self.line_edit = QtGui.QLineEdit("No plane selected")
        self.line_edit.setStyleSheet("color: grey;")
        plane_row.addWidget(self.line_edit)
        self.plane_select_button.clicked.connect(self.toggle_select_plane)
        self.plane_select_button_held = False
        selection_layout.addLayout(plane_row)

        # --- 2. Body Selector ---
        body_row = QtGui.QHBoxLayout()
        self.body_select_button = QtGui.QPushButton("Select Body")
        body_row.addWidget(self.body_select_button)
        self.body_line_edit = QtGui.QLineEdit("No body selected")
        self.body_line_edit.setStyleSheet("color: grey;")
        body_row.addWidget(self.body_line_edit)
        self.body_select_button.clicked.connect(self.toggle_select_body)
        self.body_select_button_held = False
        selection_layout.addLayout(body_row)

        # --- 3. Cutview Letter (Dropdown, Button, Display) ---
        letter_row = QtGui.QHBoxLayout()
        self.letter_combo = QtGui.QComboBox()
        self.letter_combo.addItem(" - ")  # Default entry
        self.letter_combo.addItems([chr(i) for i in range(65, 91)])  # A-Z
        self.letter_combo.setCurrentIndex(0)
        self.letter_combo.setFixedWidth(90)
        letter_row.addWidget(self.letter_combo)
        self.store_letter_button = QtGui.QPushButton("-->Store letter-->")
        letter_row.addWidget(self.store_letter_button)
        self.store_letter_button.clicked.connect(self.handle_store_letter)
        self.letter_display = QtGui.QLineEdit()
        self.letter_display.setReadOnly(True)
        self.letter_display.setFixedWidth(50)
        self.letter_display.setText(" - ")
        letter_row.addWidget(self.letter_display)
        selection_layout.addLayout(letter_row)

        # --- 4. Cube Size (Dropdown) ---
        size_row = QtGui.QHBoxLayout()
        size_label = QtGui.QLabel("Cube size:")
        size_label.setFixedWidth(90)
        size_row.addWidget(size_label)
        self.size_input = QtGui.QComboBox()
        sizes = [str(i) + " mm" for i in range(500, 5001, 500)]
        self.size_input.addItems(sizes)
        self.size_input.setCurrentIndex(0)  # Default to 500mm
        size_row.addWidget(self.size_input)
        selection_layout.addLayout(size_row)

        # === Action area (Buttons) ===
        # The buttons are arranged vertically for clarity
        self.create_Group_structure_Button = QtGui.QPushButton("Create Group-structure")
        self.create_Group_structure_Button.setToolTip("Executes the code: A020_create_group_structure.py")
        self.create_Group_structure_Button.setVisible(False)  # Not visible by default, but present in code
        selection_layout.addWidget(self.create_Group_structure_Button)

        self.create_Links_button = QtGui.QPushButton("Create Links")
        self.create_Links_button.setToolTip("Executes the code: A030_create_links.py")
        self.create_Links_button.setVisible(False)  # Not visible by default, but present in code
        selection_layout.addWidget(self.create_Links_button)

        self.create_solid_button = QtGui.QPushButton("Create Cubes")
        self.create_solid_button.setToolTip("Executes the code: A040_create_cubes.py")
        self.create_solid_button.setVisible(False)  # Not visible by default, but present in code
        selection_layout.addWidget(self.create_solid_button)

        self.do_cuts_button = QtGui.QPushButton("Do cuts")
        self.do_cuts_button.setToolTip("Executes the code: A050_create_cuts.py")
        self.do_cuts_button.setVisible(False)  # Not visible by default, but present in code
        self.do_cuts_button.clicked.connect(self.handle_do_cuts)
        selection_layout.addWidget(self.do_cuts_button)

        self.do_all_button = QtGui.QPushButton("Create Cutview")
        self.do_all_button.setToolTip("Executes the codes: A020_create_group_structure.py, A030_create_links.py, A040_create_cubes.py, A050_create_cuts.py")
        self.do_all_button.clicked.connect(self.handle_do_all)
        selection_layout.addWidget(self.do_all_button)

        # === Finalize layout ===
        self.layout.addWidget(selection_group)

        # === Initial values ===
        self.selected_plane = None
        self.selected_body = None
        self.selected_letter = None  # Must be set explicitly

    def accept(self):
        FreeCADGui.Control.closeDialog()
        return True

    def deactivate_all_select_buttons(self, except_button=None):
        # Reset plane button, but keep selection if available
        if except_button != 'plane':
            self.plane_select_button_held = False
            self.plane_select_button.setStyleSheet("")
            if not self.selected_plane:
                self.line_edit.setStyleSheet("color: grey;")
                self.line_edit.setText("No plane selected")
        # Reset body button, but keep selection if available
        if except_button != 'body':
            self.body_select_button_held = False
            self.body_select_button.setStyleSheet("")
            if not self.selected_body:
                self.body_line_edit.setStyleSheet("color: grey;")
                self.body_line_edit.setText("No body selected")
        # Additional buttons can be added here in the same way

    def toggle_select_plane(self):
        if not self.plane_select_button_held:
            self.deactivate_all_select_buttons(except_button='plane')
            self.plane_select_button_held = True
            self.plane_select_button.setStyleSheet("background-color: #0078d7; color: white;")
            self.select_plane()
        else:
            self.plane_select_button_held = False
            self.plane_select_button.setStyleSheet("")
            self.selected_plane = None
            self.line_edit.setStyleSheet("color: grey;")
            self.line_edit.setText("No plane selected")

    def select_plane(self):
        # Only run if button is held
        if not self.plane_select_button_held:
            return
        self.line_edit.setStyleSheet("color: grey;")
        self.line_edit.setText("Please select a plane in the tree or 3D view...")
        FreeCADGui.Selection.clearSelection()
        allowed_plane_types = [
            'Part::Plane',
            'Part::DatumPlane',
            # More plane types can be added here in the future
        ]
        while self.plane_select_button_held:
            QtGui.QApplication.processEvents()
            sel = FreeCADGui.Selection.getSelection()
            if sel:
                obj = sel[0]
                if getattr(obj, 'TypeId', '') not in allowed_plane_types:
                    msg = f"{obj.Label or obj.Name} is not a plane. Please select a valid plane type."
                    self.line_edit.setStyleSheet("color: orange;")
                    self.line_edit.setText(msg)
                    FreeCAD.Console.PrintError("Please select a plane in the tree or 3D view...\n")
                    FreeCADGui.Selection.clearSelection()
                    continue
                self.line_edit.setStyleSheet("color: white;")
                self.line_edit.setText(f"{obj.Name} - {obj.Label}")
                self.selected_plane = obj
                self.plane_select_button_held = False
                self.plane_select_button.setStyleSheet("")
                break
            time.sleep(0.01)
        if not self.selected_plane:
            self.line_edit.setStyleSheet("color: grey;")
            self.line_edit.setText("No plane selected")

    def toggle_select_body(self):
        if not self.body_select_button_held:
            self.deactivate_all_select_buttons(except_button='body')
            self.body_select_button_held = True
            self.body_select_button.setStyleSheet("background-color: #0078d7; color: white;")
            self.select_body()
        else:
            self.body_select_button_held = False
            self.body_select_button.setStyleSheet("")
            self.selected_body = None
            self.body_line_edit.setStyleSheet("color: grey;")
            self.body_line_edit.setText("No body selected")

    def select_body(self):
        # Only run if button is held
        if not self.body_select_button_held:
            return
        self.body_line_edit.setStyleSheet("color: grey;")
        self.body_line_edit.setText("Please select a body in the tree or 3D view...")
        FreeCADGui.Selection.clearSelection()
        allowed_types = [
            'Assembly::Assembly',
            'Assembly::AssemblyObject',
            'App::Part',
            'Part::Body',
            'PartDesign::Body',
            'App::Link',
            'App::LinkSub', # More body types can be added here in the future   
        ]
        while self.body_select_button_held:
            QtGui.QApplication.processEvents()
            sel = FreeCADGui.Selection.getSelection()
            if sel:
                obj = sel[0]
                if getattr(obj, 'TypeId', '') not in allowed_types:
                    msg = f"{obj.Label or obj.Name} is not a valid body. Please select an Assembly, Body, Link, or Sub-Link."
                    self.body_line_edit.setStyleSheet("color: orange;")
                    self.body_line_edit.setText(msg)
                    FreeCAD.Console.PrintError("Please select a body in the tree or 3D view...\n")
                    FreeCADGui.Selection.clearSelection()
                    continue
                self.body_line_edit.setStyleSheet("color: white;")
                self.body_line_edit.setText(f"{obj.Name} - {obj.Label}")
                self.selected_body = obj
                self.body_select_button_held = False
                self.body_select_button.setStyleSheet("")
                break
            time.sleep(0.01)
        if not self.selected_body:
            self.body_line_edit.setStyleSheet("color: grey;")
            self.body_line_edit.setText("No body selected")

    def handle_store_letter(self):
        letter = self.letter_combo.currentText()
        if letter == " - ":
            FreeCAD.Console.PrintError("Please select a letter and store it.\n")
            self.selected_letter = None
            self.letter_display.setText(" - ")
            return
        self.selected_letter = letter
        self.letter_display.setText(letter)
        FreeCAD.Console.PrintMessage(f"The letter '{letter}' has been stored.\n")

    def group_state(self, letter):
        """
        Checks if a group for the given letter already exists and what it contains.
        Returns:
            - 'no_group'   : no group exists
            - 'has_cuts'   : group contains at least one Cut object (TypeId 'Part::Cut')
            - 'only_links' : group contains only Links (TypeId 'App::Link')
            - 'empty'      : group exists but is empty
            - 'other'      : group contains other objects
        """
        doc = FreeCAD.ActiveDocument
        group_name = f"Cut_{letter}"
        group = None
        for obj in doc.Objects:
            if getattr(obj, 'TypeId', '') == 'App::DocumentObjectGroup' and obj.Name == group_name:
                group = obj
                break
        if not group:
            return 'no_group'
        if not hasattr(group, 'Group') or not group.Group:
            return 'empty'
        has_cuts = any(getattr(o, 'TypeId', '') == 'Part::Cut' for o in group.Group)
        only_links = all(getattr(o, 'TypeId', '') == 'App::Link' for o in group.Group)
        if has_cuts:
            return 'has_cuts'
        if only_links:
            return 'only_links'
        return 'other'

    def handle_create_group_structure(self):
        letter = self.letter_combo.currentText()
        state = self.group_state(letter)
        if state == 'has_cuts':
            FreeCAD.Console.PrintError(f"Group Cut_{letter} already contains cuts. Operation aborted.\n")
            return
        if state == 'no_group' or state == 'empty':
            importlib.reload(A020_create_group_structure)
            A020_create_group_structure.A020_create_group_structure(self)
        # If only links are present, do not create a new group

    def handle_create_links(self):
        letter = self.letter_combo.currentText()
        state = self.group_state(letter)
        if state == 'has_cuts':
            FreeCAD.Console.PrintError(f"Group Cut_{letter} already contains cuts. No further links will be created.\n")
            return
        if state == 'only_links':
            FreeCAD.Console.PrintMessage(f"Group Cut_{letter} already contains links. No further links will be created.\n")
            return
        if state == 'no_group' or state == 'empty':
            importlib.reload(A030_create_links)
            A030_create_links.A030_create_links(self)

    def handle_create_cube(self):
        letter = self.letter_combo.currentText()
        state = self.group_state(letter)
        if state == 'has_cuts':
            FreeCAD.Console.PrintError(f"Group Cut_{letter} already contains cuts. No further cubes will be created.\n")
            return
        if state == 'no_group':
            FreeCAD.Console.PrintError(f"Group Cut_{letter} does not exist. Please create links first.\n")
            return
        importlib.reload(A040_create_cubes)
        A040_create_cubes.A040_create_cubes(self)

    def handle_do_cuts(self):
        letter = self.letter_combo.currentText()
        state = self.group_state(letter)
        if state == 'has_cuts':
            FreeCAD.Console.PrintError(f"Group Cut_{letter} already contains cuts. No further cuts will be created.\n")
            return
        if state == 'no_group':
            FreeCAD.Console.PrintError(f"Group Cut_{letter} does not exist. Please create links first.\n")
            return
        importlib.reload(A050_create_cuts)
        doc = FreeCAD.ActiveDocument
        group_name = f"Cut_{letter}"
        group = None
        for obj in doc.Objects:
            if getattr(obj, 'TypeId', '') == 'App::DocumentObjectGroup' and obj.Name == group_name:
                group = obj
                break
        sub_links = [o for o in group.Group if getattr(o, 'TypeId', '') == 'App::Link'] if group else []
        num_cubes = len(sub_links)
        next_letter = letter
        A050_create_cuts.A050_create_cuts(doc, sub_links, next_letter, num_cubes)
        if self.selected_body and hasattr(self.selected_body, 'ViewObject'):
            self.selected_body.ViewObject.Visibility = False

    def handle_do_all(self):
        # Check if all prerequisites are met
        if not self.selected_plane:
            FreeCAD.Console.PrintError("Please select a plane first.\n")
            return
        if not self.selected_body:
            FreeCAD.Console.PrintError("Please select a body first.\n")
            return
        letter = self.selected_letter
        if not letter or letter == " - ":
            FreeCAD.Console.PrintError("Please select and store a letter before using 'Create Cutview'.\n")
            return
        state = self.group_state(letter)
        if state == 'has_cuts':
            FreeCAD.Console.PrintError(f"Group Cut_{letter} already contains cuts. Operation aborted.\n")
            return
        # 1. Group structure
        if state == 'no_group' or state == 'empty':
            importlib.reload(A020_create_group_structure)
            A020_create_group_structure.A020_create_group_structure(self)
        # 2. Links
        if state == 'no_group' or state == 'empty':
            importlib.reload(A030_create_links)
            A030_create_links.A030_create_links(self)
        # 3. Cubes
        importlib.reload(A040_create_cubes)
        A040_create_cubes.A040_create_cubes(self)
        # 4. Cuts
        importlib.reload(A050_create_cuts)
        doc = FreeCAD.ActiveDocument
        group_name = f"Cut_{letter}"
        group = None
        for obj in doc.Objects:
            if getattr(obj, 'TypeId', '') == 'App::DocumentObjectGroup' and obj.Name == group_name:
                group = obj
                break
        sub_links = [o for o in group.Group if getattr(o, 'TypeId', '') == 'App::Link'] if group else []
        num_cubes = len(sub_links)
        next_letter = letter
        A050_create_cuts.A050_create_cuts(doc, sub_links, next_letter, num_cubes)
        if self.selected_body and hasattr(self.selected_body, 'ViewObject'):
            self.selected_body.ViewObject.Visibility = False

    @property
    def cube_size(self):
        """
        Returns the currently selected cube size (mm) as an integer.
        """
        text = self.size_input.currentText()
        if text.endswith(" mm"):
            return int(text.replace(" mm", ""))
        try:
            return int(text)
        except Exception:
            return 500  # Fallback default

# Show the task panel (dialog)
if "cutviews_taskpanel_instance" not in globals():
    cutviews_taskpanel_instance = None
if cutviews_taskpanel_instance is not None:
    del cutviews_taskpanel_instance
cutviews_taskpanel_instance = Create_Cutviews()
FreeCADGui.Control.showDialog(cutviews_taskpanel_instance)