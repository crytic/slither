`slither-format` generates automatically patches. The patches are compatible with `git`.

Carefully review each patch before applying it.

## Usage
`slither-format target`.

The patches will be generated in `crytic-export/patches`

## Detectors supported
- `unused-state`
- `solc-version`
- `pragma`
- `naming-convention`
- `external-function`
- `constable-states`
- `constant-function` 