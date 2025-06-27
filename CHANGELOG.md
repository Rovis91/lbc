## 1.0.5
### Fixed
* 404 error when fetching a pro user who doesn't have a public page

## 1.0.4
### Added
* A lot of new user information can be retrieved (feedback, badges & professional info).
* New [examples](examples/) directory with practical usage cases.
* `get_ad` function to retrieve ad information.
* `get_user` function to retrieve user information (with pro info such as siret).
* Automatic cookies initialization during session setup to prevent HTTP 403 errors.

### Changed
* Codebase refactored: models are now split by functionality (e.g., all user dataclasses are in `user.py`).
* Proxies can now be updated after `Client` creation via `client.proxy = ...`.
* The session can also be changed dynamically via `client.session = ...`.

### Removed
* Removed the `test/` folder (migrated to `examples/`).

## 1.0.3
### Fixed
* Incorrect raw data extraction for location and owner in `Search.build` function

## 1.0.2
### Added
* Support for full Leboncoin URL in `client.search(url=...)`
* New `shippable` argument in the `search` function

### Fixed
* Incorrect enum key assignment in the `build_search_payload_with_args` function

## 1.0.1
### Added
* Realistic `Sec-Fetch-*` headers to prevent 403 errors

## 1.0.0
* Initial release