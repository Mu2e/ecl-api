# ecl-api

> Forked from [marcodeltutto/ecl-api](https://github.com/marcodeltutto/ecl-api).

-----

The Electronic Collaboration Logbook ([ECL](https://cdcvs.fnal.gov/redmine/projects/crl)) is an e-logbook used at FNAL. This package allows retrieving and posting entries via Python using the ECL [XML/REST API](https://cdcvs.fnal.gov/redmine/projects/crl/wiki/ECL_XML_API).

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [License](#license)

## Installation

```console
pip install ecl-api
```

## Usage

Start a connection with the ECL:

```python
from ecl_api import ECL, ECLEntry

password = "your_ecl_pwd"
url = "your_ecl_link" # e.g. 'https://dbweb9.fnal.gov:8443/ECL/sbnd/E'

ecl = ECL(url=url, user='sbndprm', password=password)
```

Post a generic entry:
```python
entry = ECLEntry(category='Purity Monitors', text='Example text', preformatted=True)

entry.add_image(name='Image Name', filename='/path/to/image.png')

ecl.post(entry, do_post=False)
```

Post a form:
```python
entry = ECLEntry(category='Shift', formname='Shift run start checklist - v1')

form = {
    "Maximize the window": "Yes",
    "Date": "07/23/24",
    "Time": "19:39:58",
    "Run number": "00000",
    "DAQ Components": "testentry",
    "Configuration": "testentry" 
}

entry.set_form_elements(form)

print(entry.show(pretty=True))

ecl.post(entry, do_post=False)
```

Retrieve an entry
```python

ecl.get_entry(entry_id=7252)
```

Retrieve the last N entries in a certain category

```python
text = ecl.search(category='Shift', limit=3)
```

`search` accepts several optional filters — combine any of them:

| Argument     | Description                                                                 |
|--------------|-----------------------------------------------------------------------------|
| `category`   | Category name (defaults to `'Purity+Monitors'` for legacy reasons; pass `''` to disable) |
| `after`      | Only entries after this time. Accepts `'<n>days'`, `'<n>hours'`, `'<n>minutes'`, or `'yyyy-mm-dd+hh:mm:ss'` |
| `before`     | Same format as `after`, upper bound                                         |
| `form_name`  | Restrict to a particular form                                               |
| `tag`        | Restrict to entries with this tag                                           |
| `username`   | Restrict to entries by this author                                          |
| `substring`  | Free-text substring match in the entry body (slow — no index)               |
| `words`      | Indexed word search (faster than `substring`)                               |
| `limit`      | Max number of entries to return                                             |
| `ids_only`   | If `True`, return a `list[int]` of entry IDs only (cheap, server-side)      |
| `as_json`    | If `True`, return a `list[dict]` instead of raw XML                         |

Examples:
```python
# Last 24 hours of shift entries from a specific user
ecl.search(category='Shift', after='1days', username='sgrant', as_json=True)

# Just the IDs of the 50 most recent entries with a tag
ecl.search(category='', tag='onsite', limit=50, ids_only=True)

# Indexed full-text search
ecl.search(category='', words='cryostat warmup', as_json=True)
```

Unpack content of `text`:
```python
import xml.etree.ElementTree as ET

xml = ET.fromstring(text)
entries = xml.findall('./entry')
for entry in entries:
	print(entry.attrib, entry.tag)
	...
```

### Returning parsed objects (JSON-friendly)

By default, `search`, `get_entry`, and `post` return raw XML/text. Set `as_json=True`
on either the constructor (default for every call) or on a single call to get
parsed Python objects instead:

```python
ecl = ECL(url=url, user='sbndprm', password=password, as_json=True)

entries = ecl.search(category='Shift', limit=3)
# -> list[dict], one dict per entry. Typical keys:
#    id (int), author, subject, category, timestamp,
#    html, formatted, form, images (int), files (int),
#    text, tags (list[str]), and fields (dict) when the form has extra fields.

entry = ecl.get_entry(entry_id=7252)
# -> dict with the same shape
```

Per-call override:
```python
entries = ecl.search(category='Shift', limit=3, as_json=True)
ids = ecl.search(category='Shift', limit=3, ids_only=True)  # list[int]
```

### Listing categories, tags, and forms

The ECL XML API does not expose category/tag/form catalogs directly. Instead,
these helpers sample the most recent `sample_size` entries (default 500) and
return the unique values seen. Results are cached on the `ECL` instance after
the first call — pass `force_refresh=True` to re-sample.

```python
ecl.list_categories()       # -> sorted list[str]
ecl.list_tags()             # -> sorted list[str]
ecl.list_forms()            # -> sorted list[str]

ecl.list_categories(sample_size=2000)
ecl.list_tags(force_refresh=True)
```

Note: rarely-used categories/tags may not appear if no recent entry uses them.

## MCP server

`ecl-api` ships an optional [Model Context Protocol](https://modelcontextprotocol.io)
server that exposes ECL search, retrieval, and (optionally) posting as tools
for LLM agents.

Install with the `mcp` extra:
```console
pip install "ecl-api[mcp]"
```

Set the same environment variables the library reads:
```bash
export ECL_URL="https://dbweb9.fnal.gov:8443/ECL/sbnd/E"
export ECL_USER_NAME="xml-user"
export ECL_PASSWORD="..."
```

Run the server:
```console
ecl-mcp           # stdio transport — for Claude Desktop and similar clients
ecl-mcp-stdio     # alias of ecl-mcp
ecl-mcp-server    # streamable-http on 127.0.0.1:8766
```

### Read-only by default

The server is **read-only by default**: only `search_entries`, `search_entry_ids`,
`get_entry`, `list_categories`, `list_tags`, and `list_forms` are registered.
To enable the `post_entry` tool, set:
```bash
export ECL_MCP_READ_ONLY=false
```

`post_entry` itself takes a `do_post` argument (default `False`) so an agent
can prepare and inspect entries without committing them.

### Environment variables

| Variable             | Default       | Purpose                                  |
|----------------------|---------------|------------------------------------------|
| `ECL_URL`            | _(required)_  | ECL base URL                             |
| `ECL_USER_NAME`      | _(required)_  | XML user name                            |
| `ECL_PASSWORD`       | _(required)_  | XML user password                        |
| `ECL_MCP_READ_ONLY`  | `true`        | Set to `false` to register `post_entry`  |
| `ECL_MCP_HOST`       | `127.0.0.1`   | HTTP bind host (`ecl-mcp-server` only)   |
| `ECL_MCP_PORT`       | `8766`        | HTTP bind port (`ecl-mcp-server` only)   |
| `ECL_MCP_LOG_LEVEL`  | `WARNING`     | Logger level                             |


## License

`ecl-api` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
