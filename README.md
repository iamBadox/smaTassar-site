# Små Tassar website

Public product information, privacy, and support pages for the Små Tassar iOS
app.

## Routes

- Home: <https://iambadox.github.io/smaTassar-site/>
- Privacy: <https://iambadox.github.io/smaTassar-site/privacy/>
- Support: <https://iambadox.github.io/smaTassar-site/support/>

## Local preview

Serve the repository root with any static file server:

```sh
python3 -m http.server 8000
```

Then open <http://localhost:8000/>.

## Validation

The site has no build step or runtime dependencies. Validate its HTML structure
and internal links with:

```sh
python3 scripts/validate_site.py
```

GitHub Actions runs the same validation for pull requests. Production deploys
only run for `main` and manual workflow dispatches.
