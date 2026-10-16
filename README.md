# zipslip.py

A small CLI for building ZIP archives whose **entry names (arcnames)**
can be set independently of the real on-disk filename of the file being
added.

This is a thin wrapper around the Python standard library's
[`zipfile.ZipFile.write(filename, arcname=...)`](https://docs.python.org/3/library/zipfile.html#zipfile.ZipFile.write)
and `writestr()`, which already support this — the script just exposes
it through a convenient `argparse`-based CLI instead of requiring a
few lines of Python each time.

## Why

["Zip Slip"](https://security.snyk.io/research/zip-slip-vulnerability)
is a well-known vulnerability class: server-side code that extracts a
ZIP archive and writes each entry to disk using the entry's name
as-is (e.g. `open(os.path.join(dest_dir, entry.filename), "wb")`)
without validating that the resolved path stays inside the intended
output directory. A malicious archive with an entry name like
`../../../etc/passwd` or an absolute path can then make the extractor
write outside the destination directory.

This repo is a learning/portfolio project built while working through
a Zip Slip exercise on a lab/CTF training platform. `zipslip.py` lets
you quickly build test archives with chosen (including path-traversal
or absolute) entry names, so you can exercise your own extraction code
and confirm it rejects/normalizes unsafe entries correctly (e.g. by
checking `os.path.realpath()` of each resolved destination against the
intended output directory before writing).

**This tool only builds ZIP files using the standard library. It does
not extract archives and does not exploit anything by itself** — it is
meant to produce test input for your own extraction/sanitization code.

## Usage

```
python zipslip.py -o OUTPUT.zip [--list] [--force|-f] \
    add SOURCE_FILE --as ARCNAME \
    [add SOURCE_FILE --as ARCNAME ...] \
    [add-text "literal text" --as ARCNAME ...]
```

- `-o / --output` — path of the ZIP archive to create (required).
- `add <file> --as <arcname>` — add an existing file from disk, stored
  under the given entry name.
- `add-text "<text>" --as <arcname>` — add a literal string as a file's
  content, stored under the given entry name.
- `--list` — after writing, print the archive's `namelist()`.
- `-f / --force` — overwrite the output file if it already exists.

Multiple `add` / `add-text` entries can be combined in a single
invocation; they are written in the order given.

### Example

```
python zipslip.py -o demo.zip --list \
  add payload.txt --as "../../tmp/evil.txt" \
  add-text "hello" --as "notes/readme.txt"
```

```
Wrote demo.zip with 2 entries.
Archive namelist():
  '../../tmp/evil.txt'
  'notes/readme.txt'
```

## Who this is for

Anyone studying archive-extraction security (e.g. working through a
Zip Slip lab exercise) who wants a quick way to generate ZIP archives
with specific, chosen entry names — without hand-writing `zipfile`
boilerplate each time — in order to test their own safe-extraction
code.

## License

MIT
