# winding sub-package
# Each module computes one class of winding property.
#
# Conventions:
#   - All inputs and outputs are SI (metres, ohms, kg, amperes).
#   - Packing geometry uses wire.insulatedD (insulated OD).
#   - Resistance and mass use wire.area (bare copper cross-section).
#   - wire_length = circumference × turns (single nominal radius).
