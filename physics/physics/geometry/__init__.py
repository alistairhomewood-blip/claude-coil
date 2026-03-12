# geometry sub-package
#
# Flat-coil modules (circular, racetrack, elliptical):
#   circumference() — analytic perimeter of one turn
#   base_path()     — single closed path in local coil frame
#                     (XY plane, z=0, centred at origin, CCW from +Z)
#
# Toroidal-family modules (toroidal, elongated_toroidal):
#   per_turn_length()  — exact arc length of turn k
#   total_wire_length() — exact total conductor length
#   filament_paths()   — N distinct closed paths in local torus frame
#                        (centred at origin, Z-up); caller applies orient()
#
# orient() in common.py applies ZYX Euler rotation then translation
# to produce global coordinates.
