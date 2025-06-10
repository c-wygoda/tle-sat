## v0.8.6 (2025-06-10)

### Fix

- update lockfile on bumping

## v0.8.5 (2025-06-10)

### Fix

- include uv.lock in release commit

## v0.8.4 (2025-06-10)

### Fix

- update lockfile to use uv lockfile schema 1.2

## v0.8.3 (2025-06-10)

### Fix

- ensure only culmination events are considered for passes

## v0.8.2 (2025-06-06)

### Fix

- clip value to [-1.0, 1.0] before feeding into arccos

## v0.8.1 (2025-01-30)

### Fix

- footprint was calculated on wrong side of orbit

## v0.8.0 (2025-01-06)

### Feat

- allow numpy v2

## v0.7.0 (2024-11-19)

### Feat

- allow setting ephemeris filename

## v0.6.0 (2024-10-15)

### Feat

- add method to compute swath
- add orbit_track method
- add method to compute LOS intersection with earth

### Fix

- wrong import in CLI

## v0.5.0 (2024-09-28)

### Feat

- export main attributes in package directly
- catch footprint error with a custom exception

## v0.4.1 (2024-09-27)

### Fix

- push both branch and tags on release

## v0.4.0 (2024-07-23)

### Feat

- support python versions 3.10 and up

## v0.3.1 (2024-07-22)

### Refactor

- rename package to tle-sat

## v0.3.0 (2024-07-19)

### Feat

- add absolute off-nadir angle to view angles

## v0.2.1 (2024-07-16)

### Refactor

- rename to "tle-tools"

## v0.2.0 (2024-05-30)

### Feat

- add passes calculation
- add footprint calculation to satellite
- add vector rotate method
- use dataclass instead of tuple for off-nadir

### Refactor

- rename off nadir to view angles

## v0.1.0 (2024-05-15)

### Feat

- add off-nadir calculations
- add satellite class with position method

## v0.0.0 (2024-05-13)
