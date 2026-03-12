# Wire Data

## Source and Verification Status

⚠️ **Bare copper diameters** below are standard AWG values (IEC 60317 / NEMA MW1000 nominal). Verified.

⚠️ **Insulated ODs** are approximate class-1 enamel values. These **must be verified against IEC 60317-0-1** (or the specific wire manufacturer's datasheet) before being used in fit/packing calculations. They are included here as starting-point estimates only.

## Wire Usage Rules

- **`bareD`** → used for: `area = π*(bareD/2)²`, resistance `R = ρL/A`, mass `m = ρ_Cu × L × A`
- **`insulatedD`** → used for: packing (turns-per-layer), U-channel fit check
- These must never be swapped or conflated.

## AWG Table

All dimensions in **metres (m)**.

| AWG | bareD (m) | bareD (mm) | insulatedD (m) ⚠️ approx | area (m²) |
|-----|-----------|------------|--------------------------|-----------|
| 4   | 5.189e-3  | 5.189      | 5.31e-3                  | 2.114e-5  |
| 6   | 4.115e-3  | 4.115      | 4.22e-3                  | 1.329e-5  |
| 8   | 3.264e-3  | 3.264      | 3.35e-3                  | 8.366e-6  |
| 10  | 2.588e-3  | 2.588      | 2.66e-3                  | 5.261e-6  |
| 12  | 2.053e-3  | 2.053      | 2.11e-3                  | 3.310e-6  |
| 14  | 1.628e-3  | 1.628      | 1.68e-3                  | 2.081e-6  |
| 16  | 1.291e-3  | 1.291      | 1.34e-3                  | 1.309e-6  |
| 18  | 1.024e-3  | 1.024      | 1.07e-3                  | 8.231e-7  |
| 20  | 8.128e-4  | 0.8128     | 8.53e-4                  | 5.188e-7  |
| 22  | 6.438e-4  | 0.6438     | 6.78e-4                  | 3.255e-7  |
| 24  | 5.106e-4  | 0.5106     | 5.41e-4                  | 2.047e-7  |
| 26  | 4.049e-4  | 0.4049     | 4.32e-4                  | 1.287e-7  |
| 28  | 3.211e-4  | 0.3211     | 3.43e-4                  | 8.096e-8  |
| 30  | 2.546e-4  | 0.2546     | 2.74e-4                  | 5.089e-8  |
| 32  | 2.019e-4  | 0.2019     | 2.18e-4                  | 3.200e-8  |

### Computed area formula

```
area = π * (bareD / 2)²
```

Values above are rounded to 4 significant figures. Physics code should compute `area` from `bareD` directly and not use the table value.

---

## Physical Constants (for reference)

```
ρ_Cu (resistivity, 20°C, DC) = 1.68e-8 Ω·m
ρ_Cu (density)               = 8960   kg/m³
```

Source: constants.py in `/physics/physics/constants.py`

---

## Custom Wire Support

The spec requires support for custom wire definitions. A custom wire must supply:
- `awg: null`
- `label`: user-defined string
- `bareD`: bare copper OD in metres
- `insulatedD`: insulated OD in metres
- `area`: bare copper area in m² (= π*(bareD/2)²; can be computed, but must be explicit in the stored object)

---

## Legacy Note

The legacy prototype (`legacy/App copy.txt`) contains an AWG table in mm. The values match the `bareD` column above. The legacy code did **not** store insulated OD separately — it used bare copper diameter for both packing and resistance, which is incorrect per the spec. Do not carry this forward.
