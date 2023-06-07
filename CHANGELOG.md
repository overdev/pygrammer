# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

### Fixed

- Constant name typo `NC_ZERO_OR_MORE` in `compose_reference()`
- Fixed code generation for inline groups in the form `( A | B | C )?`
- Fixed parsing capture of inline groups where the inline group was including items after its delimiter

### Changed

- Code generated for testing rule matching (`is_*()`) got way simpler and faster, also causing a LOC reduction of up to 20%.
- `parse()` moved to templates and shows better log messages

### Added

- CLI argument `-verbosity` or `-v` to generated parser module do define initial log verbosity level (Defaults to `error`)

## 0.1beta1 - 2023-06-05

### Added

- Core features: grammar parser, parser generator and CLI functionality
- Token decorators and exclusions: `@something` and `^TOKEN_GROUP` to change how token definitions are treated
- Rule attributes and directives: `@{attribute:value, directive}` to change how rule definitions are treated

<!--
### Fixed

- Fixed bugs, typos and whatnot

### Changed

- Changes in dependencies, APIs etc.

### Deprecated

- Stuff will be removed in future versions

### Removed

- Stuff deprecated in previous versions
-->

<!--
## [0.1.0] - 2023-06-04

### Added

- Initial release.

[unreleased]: https://github.com/overdev/pygrammer/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/overdev/pygrammer/compare/v0.0.8...v0.1.0
-->
