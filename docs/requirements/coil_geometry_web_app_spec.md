# Electromagnet Coil Configuration Web Application Specification

## Project Goal

Create a web application that can be accessed by others, with the purpose of designing electromagnet coil configurations, and then exporting.

## Master File Requirements

The master file should contain, per coil:
- coil ID and group ID
- units
- analytic type or sampled centerline
- full transform: position + rotation
- conductor cross-section shape and dimensions
- number of turns / winding pitch / layering
- current magnitude and sign
- material
- optional discretized filament paths for Biot–Savart evaluation

## File Formats

- Save coil definitions in HDF5.
- Export geometry to STEP.

## User Interaction Abilities

- easily add, duplicate or delete individual coils
- easily move (translate) individual or a group of coils by either selecting all the coils with the mouse and then dragging, OR typing in exact coordinates. Both options should be available.
- easily rotate coils (quick options for rotation by 90 degrees in any direction, and fine tuning options available too)
- adjust the type (gauge) of enamelled copper wire
- adjust number of loops for a given coil
- adjust the width of the u-channel that each coil sits in
- be able to view each individual turning of each wire loop, so I can visualise what for example 100 loops of one coil would look like. IMPORTANT ensure this detail is included in the exported coil data too.
- be able to adjust the magnitude and direction of current in each coil
- be able to bring up a window showing the currents in each individual coil, with sliders such that I can individually change the current in each separate coil. Show a 3D visual of my whole coil setup in the corner, so that I can see which coil (by making it light up) I am adjusting while using these sliders.
- include master controls for current, wire gauge, and number of loops. HOWEVER if for example, some coils have different currents to other coils, if I increase the master current, DON’T make all the coil’s currents equal. Simply increase each coil’s current at the same rate. The same applies for wire gauge and number of loops.
- IF I choose to press it, have the option to generate a high resolution 2D B-Field diagram parallel to the xy plane, through the cross section of the whole coil geometry
- ability to turn on and off axis
- ability to save coil geometries as a file that can then be imported back into the same web app if I want to make changes, or if I want to send it to someone else to open on the web app
- ability to lock (and unlock) individual coils in place, i.e. no edits can be made unless I press unlock

## UI Requirements

- NO text overlapping
- no gradients if they’re only for aesthetic purposes
- display in the corner total length of wire, total mass of wire, and total power requirements (based off of the type of wire, length and current being used)
- have a main tool bar at the top, that is retractable
- show direction of current in each coil, but have the ability to turn this off and on

---

# Additional Required System Rules and Engineering Constraints

## 1. Architecture Boundary

- Build this as a real web application with a frontend and backend, not a frontend-only demo.

### Frontend Responsibilities
- 3D editing and visualization
- coil selection, grouping, translation, rotation, duplication, deletion
- exact numeric editing of transforms and coil parameters
- per-coil and master controls
- import/export UI
- current-adjustment window with sliders and live highlighting of the selected coil in the 3D view
- display of total wire length, total wire mass, and total power

### Backend Responsibilities
- HDF5 master-file generation and parsing
- STEP export
- high-resolution 2D B-field slice generation
- heavy geometric calculations, validation, discretization, and other compute-heavy tasks

### Source of Truth
- The editable source of truth must be the master project file, not the STEP export.
- STEP is export-only and must never become the primary editable representation.

## 2. Source of Truth and Data Fidelity

- The master project file must preserve a physically meaningful coil definition, not just a visual mesh.
- The editable model must preserve BOTH:
  - a parametric coil definition
  - an explicit per-turn representation
- If the user chooses visible individual turns, the exported master data must also preserve that full per-turn geometry and not silently collapse the coil into a simplified lumped object.
- Each coil in the master data must contain:
  - coil ID
  - group ID
  - units
  - analytic type or sampled centerline
  - full transform: position + rotation
  - conductor cross-section shape and dimensions
  - number of turns
  - winding pitch
  - layering
  - current magnitude and sign
  - material
  - optional discretized filament paths for Biot–Savart evaluation
- The app must be able to re-import its own saved project files with no loss of coil metadata or geometric fidelity.

## 3. Import/Export Versioning and Compatibility

- Every saved project file must include:
  - schema version
  - application version
  - export timestamp
  - project name
  - optional creator metadata
- Design the file format so future versions of the app can open older files safely.
- On import, the app must validate the schema version and show clear warnings if the file is outdated or partially incompatible.
- Never fail silently on import.

## 4. Geometry and Physical Validation

- The app must validate geometry before saving/exporting and during editing where practical.
- It must detect and clearly warn or block for:
  - overlapping windings within a coil
  - impossible turn spacing
  - wire that does not physically fit inside the selected U-channel
  - coil-to-coil collisions
  - geometry self-intersections
  - invalid transforms or degenerate geometry
- Validation must use the actual outer dimensions of the enamelled wire, not just bare copper diameter.
- The app must warn if selected wire gauge, turn count, pitch, layering, and U-channel dimensions are physically incompatible.
- The app must clearly distinguish between:
  - warning: unusual but still allowed
  - error: physically impossible or invalid for export

## 5. Electrical Model and Calculation Rules

- Use DC only.
- Use room-temperature copper with constant resistivity.
- Assume parallel wiring.
- Treat all coils as parallel-connected DC branches for aggregate reporting.
- The UI must still allow per-coil current control, and the software must treat those as independently specified branch currents for design purposes.
- For all calculations, use a fixed room-temperature copper resistivity assumption and do not include temperature dependence.
- Compute and display at minimum:
  - per-coil wire length
  - total wire length
  - per-coil wire mass
  - total wire mass
  - per-coil resistance
  - total equivalent resistance for the parallel network
  - per-coil power
  - total power
  - required voltage per branch from V = I*R
- Use enamelled copper wire data with both:
  - bare conductor diameter
  - insulated outer diameter
- Packing/fit calculations must use insulated outer diameter.
- Resistance and mass calculations must use copper conductor properties.
- The software must support selecting standard enamelled copper wire gauges and must allow adding custom wire definitions.
- Master controls for current, wire gauge, and number of loops must preserve relative differences between coils rather than forcing all coils to become identical.

## 6. Grouping Behaviour

- Users must be able to create groups and dissolve groups.
- Do not support nested groups. A coil can belong to at most one group at a time.
- When a group is translated or rotated, the transform pivot must be the group centroid.
- Users must be able to duplicate a whole group as one action.
- Users must be able to hide, show, and isolate groups.

## 7. Selection, Snapping, and Layout Tools

- Support box select.
- Support shift-click multi-select.
- Support select-by-list from an object tree / coil list.
- Support snap to grid.
- Grid snapping must also help line up meaningful coil reference points, for example aligning the centres of two circular coils.
- Support mirror across the x, y, or z planes.
- Support duplication as:
  - linear array
  - circular pattern

## 8. History and Project Safety

- Include full undo/redo history.
- Include autosave of the local project.
- Include confirm-before-delete for destructive actions such as deleting coils, deleting groups, or clearing a project.

## 9. Performance Requirements

- The app must remain usable when many coils and many individual turns are visible.
- Separate:
  - editable model data
  - rendered display data
  - exported high-fidelity data
- Use performance-aware rendering so that interaction stays responsive even for large turn counts.
- Preserve full per-turn fidelity in the saved master file and in export data even if the interactive display uses performance optimizations.
- Use background workers or equivalent methods for expensive recalculations where appropriate.

## 10. B-Field Slice Feature

- The user must be able to generate a high-resolution 2D B-field slice parallel to the xy-plane at a user-chosen z = constant height.
- The user must be able to set:
  - slice height z
  - x/y grid boundaries
  - grid resolution
- Show the slice plane in the 3D visualiser before calculation so the user can see exactly where the field is being sampled.
- The B-field slice must be computed only from discretised filament paths stored in the master file.
- The result must support:
  - colour map
  - contour map
  - vector overlay
- The user must be able to turn these display layers on and off independently.

## 11. Coordinate System, Rotations, and Units

- Use a single global XYZ coordinate frame with origin at (0,0,0).
- All coil positions and group positions are defined relative to this global origin.
- Use degrees for rotation values in both the UI and exported project data.
- Let the user choose whether the app uses metres or centimetres.
- Store the chosen units explicitly in the project file.
- Let the user control axis/grid labelling intervals, for example:
  - 5 cm, 10 cm, 15 cm, ...
  - or 10 cm, 20 cm, 30 cm, ...
- Never use hidden unit conversions without making them explicit in the saved data.

## 12. Coil Metadata and Organisation

- Each coil must have:
  - user-editable name
  - coil ID
  - optional colour
  - optional notes
- Include an object tree / list panel so the user can:
  - select coils
  - select groups
  - hide/show items
  - isolate items
  - search/filter items

## 13. U-Channel Rules

- Each coil has at most one associated U-channel.
- A U-channel may hold only one coil.
- U-channel wall thickness is fixed at 1 mm.
- U-channel width is user-adjustable.
- U-channel depth must automatically adjust to the depth needed to hold the selected coil's number of wire loops.
- The U-channel is visual only and is not part of the physical/electromagnetic export model unless explicitly requested later.
- The default viewing convention must be with the U-channel hidden so the user mainly sees the wires.
- The user must be able to show or hide the U-channel at any time.
- Fill up U channel from the centre, and one layer at a time.

## 14. Hosting and Sharing

- The application must be designed as a public hosted web app that other people can access.
- Users must be able to save a project file, send it to someone else, and have that person open it in the same web app.
- Include project preview / thumbnail support if practical.

## 15. Acceptance Criteria

- A user can create, duplicate, delete, group, and ungroup coils without UI overlap or broken layout.
- A user can box-select multiple coils and transform them together.
- Group rotation must occur about the group centroid.
- A 100-turn coil must visibly show all individual turns.
- Saving and re-importing a project must preserve coil geometry, metadata, units, currents, wire gauge, turn count, grouping, and per-turn data.
- A saved project file must open correctly in another user's copy of the hosted web app.
- The current-control window must allow separate adjustment of each coil and clearly highlight the active coil in the 3D view.
- The master controls for current, wire gauge, and turn count must preserve relative differences between coils rather than forcing all coils to become identical.
- The B-field slice tool must allow user-defined z-slice height, grid bounds, and resolution, and must display the sampling plane in the 3D scene.
- The app must compute the B-field slice from discretised filament paths from the master file only.
- Undo/redo and autosave must work reliably.
- STEP export and HDF5 project save/load must complete without silently dropping coil data.
