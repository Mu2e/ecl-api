'''
Contains code to talk to the ECL API
'''
import os
import uuid
import hashlib
import requests
import xml.etree.ElementTree as etree
from urllib.parse import urlparse

class ECL:
    '''
    The main ECL class that handles the connection with the ECL
    '''

    #pylint: disable=invalid-name,too-many-arguments

    def __init__(self, url=None, user=None, password=None, timeout=60, debug=False, as_json=False):
        '''
        Contructor

        Args:
            url (str): the URL. Falls back to the ECL_URL environment variable.
            user (str): the username. Falls back to the ECL_USER_NAME environment variable.
            password (str): the password. Falls back to the ECL_PASSWORD environment variable.
            timeout (int): request timeout in seconds
            as_json (bool): default response format. If True, methods return parsed
                            Python objects (dicts/lists) instead of raw XML/text.
                            Each method accepts its own as_json= override.
        '''

        url = url if url is not None else os.environ.get('ECL_URL')
        user = user if user is not None else os.environ.get('ECL_USER_NAME')
        password = password if password is not None else os.environ.get('ECL_PASSWORD')

        if user is None:
            raise ValueError('ECL user not provided (pass user= or set ECL_USER_NAME)')
        if password is None:
            raise ValueError('ECL password not provided (pass password= or set ECL_PASSWORD)')

        self._url = self._normalize_url(self._resolve_server(url))
        self._password = password
        self._user = user

        self._to = timeout

        self._debug = debug
        self._as_json = as_json

        self._metadata_cache = None

    def _sample_metadata(self, sample_size=500, force_refresh=False):
        """
        Sample recent entries and collect the unique categories, tags, and
        forms in use. Result is cached on the instance after the first call.
        """
        if self._metadata_cache is not None and not force_refresh:
            return self._metadata_cache

        entries = self.search(limit=sample_size, as_json=True)

        categories = set()
        tags = set()
        forms = set()
        for e in entries:
            if e.get('category'):
                categories.add(e['category'])
            if e.get('form'):
                forms.add(e['form'])
            for t in e.get('tags', []):
                if t:
                    tags.add(t)

        self._metadata_cache = {
            'categories': sorted(categories),
            'tags': sorted(tags),
            'forms': sorted(forms),
        }
        return self._metadata_cache

    def list_categories(self, sample_size=500, force_refresh=False):
        """Return the categories seen in the most recent `sample_size` entries."""
        return self._sample_metadata(sample_size, force_refresh)['categories']

    def list_tags(self, sample_size=500, force_refresh=False):
        """Return the tags seen in the most recent `sample_size` entries."""
        return self._sample_metadata(sample_size, force_refresh)['tags']

    def list_forms(self, sample_size=500, force_refresh=False):
        """Return the forms seen in the most recent `sample_size` entries."""
        return self._sample_metadata(sample_size, force_refresh)['forms']

    def _want_json(self, as_json):
        return self._as_json if as_json is None else as_json

    @staticmethod
    def _parse_entries(xml_text):
        """Parse <entries> XML into a list of <entry> elements.

        Falls back to per-entry parsing if the document as a whole is
        malformed (occasionally an entry contains control characters or
        unescaped markup that breaks the strict parser).
        """
        try:
            root = etree.fromstring(xml_text)
            return root.findall('entry')
        except etree.ParseError:
            pass

        entries = []
        chunks = xml_text.split('</entry>')
        for chunk in chunks[:-1]:
            start = chunk.find('<entry')
            if start < 0:
                continue
            piece = chunk[start:] + '</entry>'
            try:
                entries.append(etree.fromstring(piece))
            except etree.ParseError:
                continue
        return entries

    @staticmethod
    def _entry_to_dict(entry):
        """Convert an <entry> element into a JSON-friendly dict.

        Handles both shapes returned by the API:
          - xml_search: <entry id=... images=... files=...> with <text>,
                        <subject>, <tag>, <form><field/></form> children.
          - xml_get:    bare <entry> (no id), text lives inside
                        <form><field name="text">...</field></form>.
        """
        out = dict(entry.attrib)
        for key in ('id', 'images', 'files'):
            if key in out:
                try:
                    out[key] = int(out[key])
                except (TypeError, ValueError):
                    pass

        subject = entry.find('subject')
        if subject is not None and subject.text is not None:
            out['subject'] = subject.text

        text = entry.find('text')
        if text is not None and text.text is not None:
            out['text'] = text.text

        out['tags'] = [t.attrib.get('name') for t in entry.findall('tag') if t.attrib.get('name')]

        form = entry.find('form')
        if form is not None:
            out['form'] = form.attrib.get('name')
            fields = {
                f.attrib.get('name'): f.text
                for f in form.findall('field')
                if f.attrib.get('name')
            }
            # xml_get puts the body in <field name="text"> — promote it so
            # callers can read out['text'] regardless of which endpoint hit.
            if 'text' in fields and 'text' not in out:
                out['text'] = fields.pop('text')
            if fields:
                out['fields'] = fields

        return out

    @staticmethod
    def _normalize_url(url):
        """Strip a trailing /index and ensure the URL ends with /E."""
        if not url:
            return url
        url = url.rstrip('/')
        if url.endswith('/index'):
            url = url[:-len('/index')]
        if not url.endswith('/E'):
            url = url + '/E'
        return url

    def _resolve_server(self, base_url):
        """
        Resolve base_url to the active server, following any redirects.
        Preserves the experiment path (e.g. /ECL/mu2e/E) from base_url so
        a mu2e URL is never silently rewritten into a different experiment.
        """
        if base_url is None:
            raise ValueError('ECL url not provided (pass url= or set ECL_URL)')

        parsed_in = urlparse(base_url)
        path = parsed_in.path.rstrip('/')
        if path.endswith('/index'):
            path = path[:-len('/index')]
        if not path.endswith('/E'):
            path = path + '/E'

        probe_url = f"{parsed_in.scheme or 'https'}://{parsed_in.netloc}{path}/index"

        try:
            response = requests.get(probe_url, allow_redirects=True, timeout=10)
            parsed = urlparse(response.url)
            return f"{parsed.scheme}://{parsed.netloc}{path}"
        except requests.exceptions.RequestException as e:
            print(f"Error discovering active server: {e}")
            return None

    def generate_salt(self):
        '''
        Generates the salt random string
        '''

        return 'salt=' + str(uuid.uuid4())

    def signature(self, arguments, data=''):
        '''
        Constructs the signature, which is made with the arguments to pass to
        the API, the password, and the data (is POST) separated by ":". And the
        encoded.
        '''

        string = arguments
        string += ':'
        string += self._password
        string += ':'
        string += data

        # print('Signature string:', string)

        m = hashlib.md5()
        m.update(string.encode('utf-8'))
        return m.hexdigest()


    def search(self,
               category='',
               after='',
               before='',
               form_name='',
               tag='',
               username='',
               substring='',
               words='',
               limit=100,
               ids_only=False,
               as_json=None):
        '''
        Searched the last entries in a given category

        Args:
            category (str): the category to search in
            after (str): searches for entries after a certain date. The date has to be in the following formats:
                            <n>days (ex: "1days" for the last 24h entries)
                            <n>hours (ex: "1hours" for the last hour entries)
                            <n>minutes (ex: "1minutes" for the last minute entries)
                            yyyy-mm-dd+hh:mm:ss (ex: "2012-04-01+12:00:00"
            before (str): searches for entries before a certain date. The date has to be in the following formats:
                            <n>days (ex: "1days" for the last 24h entries)
                            <n>hours (ex: "1hours" for the last hour entries)
                            <n>minutes (ex: "1minutes" for the last minute entries)
                            yyyy-mm-dd+hh:mm:ss (ex: "2012-04-01+12:00:00"
            form_name: searches entries that have "form_name" only
            tag: searches entries with a certain tag only
            username: searches entries from a particular user only
            substring: search for entries having specified text as substring - can be slow
            words: indexed search for entries having the words
            limit (int): limit to the number of entries
            ids_only (bool): if True, request only entry IDs from the server
                             and return a list[int] of IDs instead of raw XML
            as_json (bool): if True, parse the XML and return a list[dict].
                            Ignored when ids_only=True (that already returns
                            a list[int]). Defaults to the instance setting.
        '''

        url = self._url
        url += '/xml_search?'

        arguments=''

        if len(category):
            arguments += f'c={category}&'
        if len(after):
            arguments += f'a={after}&'
        if len(before):
            arguments += f'b={before}&'
        if len(form_name):
            arguments += f'f={form_name}&'
        if len(tag):
            arguments += f't={tag}&'
        if len(username):
            arguments += f'u={username}&'
        if len(substring):
            arguments += f'st={substring}&'
        if len(words):
            arguments += f'si={words}&'
        if limit is not None:
            arguments += f'l={limit}&'
        if ids_only:
            arguments += 'o=ids&'
        arguments += self.generate_salt()

        # headers = {'content-type': 'text/xml'}

        headers = {
            'X-Signature-Method': 'md5',
            'X-User': self._user,
            'X-Signature': self.signature(arguments)
        }

        r = requests.get(url + arguments, headers=headers, timeout=self._to)

        if ids_only:
            return [int(e.attrib['id']) for e in self._parse_entries(r.text)
                    if 'id' in e.attrib]

        if self._want_json(as_json):
            return [self._entry_to_dict(e) for e in self._parse_entries(r.text)]

        return r.text



    def get_entry(self, entry_id, as_json=None):
        '''
        Gets a particular entry.

        Args:
            entry_id (int): The ID of the entry
            as_json (bool): if True, parse the XML and return a dict.
                            Defaults to the instance setting.
        '''

        url = self._url
        url += '/xml_get?'

        arguments = f'e={entry_id}&'
        arguments += self.generate_salt()

        headers = {
            'X-Signature-Method': 'md5',
            'X-User': self._user,
            'X-Signature': self.signature(arguments)
        }

        r = requests.get(url + arguments, headers=headers, timeout=self._to)

        if self._want_json(as_json):
            entries = self._parse_entries(r.text)
            element = None
            if entries:
                element = entries[0]
            else:
                # _parse_entries already failed to recover; if the response
                # is a bare <entry> root, try parsing it directly.
                try:
                    root = etree.fromstring(r.text)
                    if root.tag == 'entry':
                        element = root
                except etree.ParseError:
                    pass
            if element is None:
                return {}
            out = self._entry_to_dict(element)
            # xml_get omits the id (the caller already knows it); inject it
            # so the dict shape matches what xml_search produces.
            out.setdefault('id', int(entry_id))
            return out

        return r.text


    def post(self, entry, do_post=False, as_json=None):
        '''
        Posts an entry to the e-log

        Args:
            entry (ECLEntry): the entry
            do_post (bool): set this to True to submit the entry to the ECL
            as_json (bool): if True, return a dict {status, reason, body}
                            instead of the raw response text. Defaults to the
                            instance setting.
        '''

        entry.set_author(self._user)

        xml_data = entry.show()

        url = self._url
        url += '/xml_post?'

        arguments = self.generate_salt()

        # headers = {'content-type': 'text/xml'}

        headers = {
            'content-type': 'text/xml',
            'X-Signature-Method': 'md5',
            'X-User': self._user,
            'X-Signature': self.signature(arguments, xml_data)
        }

        if self._debug:
            print('Headers:', headers)
            print('URL:', url + arguments)

        if not do_post:
            return None

        r = requests.post(url + arguments, headers=headers, data=xml_data, timeout=self._to)

        if self._debug:
            print(r.url)
            print(r.text)

        if self._want_json(as_json):
            return {'status': r.status_code, 'reason': r.reason, 'body': r.text}

        return r.text
