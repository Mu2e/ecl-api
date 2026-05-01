"""Live smoke test against a real ECL server.

Reads credentials from the environment (ECL_URL, ECL_USER_NAME, ECL_PASSWORD)
and falls back to interactive prompts if anything is missing.  Not a unit
test — talks to the network.
"""

import os
import xml.etree.ElementTree as ET
from getpass import getpass

from ecl_api import ECL, ECLEntry


def _from_env_or_prompt(env_var, prompt, secret=False):
    val = os.environ.get(env_var)
    if val:
        return val
    return getpass(prompt) if secret else input(prompt)


url = _from_env_or_prompt('ECL_URL', 'ECL URL: ')
user = _from_env_or_prompt('ECL_USER_NAME', 'ECL user: ')
password = _from_env_or_prompt('ECL_PASSWORD', 'ECL password: ', secret=True)

ecl = ECL(url=url, user=user, password=password)

# ---- metadata helpers first (so we can pick a real category) -------------
categories = ecl.list_categories()
tags = ecl.list_tags()
forms = ecl.list_forms()
print(f'categories ({len(categories)}): {categories[:5]}...')
print(f'tags ({len(tags)}): {tags[:5]}...')
print(f'forms ({len(forms)}): {forms[:5]}...')

probe_category = categories[0] if categories else ''

# ---- XML path (default) ---------------------------------------------------
text = ecl.search(category=probe_category, limit=3)
xml = ET.fromstring(text)
entries = xml.findall('./entry')
print(f'XML search ({probe_category!r}) returned {len(entries)} entries')

# ---- JSON path (as_json) --------------------------------------------------
entries_json = ecl.search(category=probe_category, limit=3, as_json=True)
print(f'JSON search returned {len(entries_json)} entries')
if entries_json:
    e = entries_json[0]
    print(f'  first: id={e.get("id")} subject={e.get("subject")!r}')

# ---- ids_only path --------------------------------------------------------
ids = ecl.search(category=probe_category, limit=3, ids_only=True)
print(f'ids_only returned: {ids}')

# ---- get_entry ------------------------------------------------------------
if ids:
    entry = ecl.get_entry(entry_id=ids[0], as_json=True)
    print(f'get_entry({ids[0]}): keys={sorted(entry.keys())}')

# ---- ECLEntry construction (no network) -----------------------------------
entry = ECLEntry(category='Shift', formname='Shift run start checklist - v1')
entry.set_form_elements({
    "Maximize the window": "Yes",
    "Date": "07/23/24",
    "Time": "19:39:58",
    "Run number": "00000",
    "DAQ Components": "testentry",
    "Configuration": "testentry",
})
print('--- ECLEntry XML ---')
print(entry.show(pretty=True))
