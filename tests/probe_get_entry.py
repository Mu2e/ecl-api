"""Print raw XML returned by xml_get for a single entry.

Debug helper — used to inspect the actual response shape so the JSON
parser in ECL._entry_to_dict can be improved.
"""
import os
import sys

from ecl_api import ECL

ecl = ECL(
    url=os.environ['ECL_URL'],
    user=os.environ['ECL_USER_NAME'],
    password=os.environ['ECL_PASSWORD'],
)

entry_id = int(sys.argv[1]) if len(sys.argv) > 1 else 4963
print(ecl.get_entry(entry_id=entry_id))
