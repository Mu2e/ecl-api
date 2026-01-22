'''
Contains code to talk to the ECL API
'''
import uuid
import hashlib
import requests
from urllib.parse import urlparse

class ECL:
    '''
    The main ECL class that handles the connection with the ECL
    '''

    #pylint: disable=invalid-name,too-many-arguments

    def __init__(self, url, user, password, timeout=60, debug=False):
        '''
        Contructor

        Args:
            url (str): the URL
            user (str): the username
            password (str): the password
            timeout (int): request timeout in seconds
        '''

        self._url = url if self.check_server(url) else self.get_active_server()
        self._password = password
        self._user = user

        self._to = timeout

        self._debug = debug

    def check_server(self, base_url, timeout=5):
        """
        Check if a server is responsive.
        Returns True if server responds, False otherwise.
        """
        if base_url == '' or base_url is None:
            return False
        try:
            response = requests.get(base_url, timeout=timeout)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def get_active_server(self, base_url="https://dbweb0.fnal.gov/ECL/sbnd/E/index"):
        """
        Follow redirect from dbweb0 to find the active server.
        Returns the base URL of the active server.
        """
        try:
            # Make a request that allows redirects
            response = requests.get(base_url, allow_redirects=True, timeout=10)
            
            # Extract the final URL after redirects
            final_url = response.url
            
            # Parse to get the scheme and netloc (e.g., https://dbweb1.fnal.gov:8443)
            parsed = urlparse(final_url)
            active_server = f"{parsed.scheme}://{parsed.netloc}/ECL/sbnd/E"
            
            return active_server
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
               category='Purity+Monitors',
               after='',
               before='',
               form_name='',
               tag='',
               username='',
               substring='',
               words='',
               limit=100):
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
        arguments += self.generate_salt()

        # headers = {'content-type': 'text/xml'}

        headers = {
            'X-Signature-Method': 'md5',
            'X-User': self._user,
            'X-Signature': self.signature(arguments)
        }

        r = requests.get(url + arguments, headers=headers, timeout=self._to)

        return r.text



    def get_entry(self, entry_id=2968):
        '''
        Gets a particular entry.

        Args:
            entry_id (int): The ID of the entry 
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

        return r.text


    def post(self, entry, do_post=False):
        '''
        Posts an entry to the e-log

        Args:
            entry (ECLEntry): the entry
            do_post (bool): set this to True to submit the entry to the ECL
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

        if do_post:
            r = requests.post(url + arguments, headers=headers, data=xml_data, timeout=self._to)

            if self._debug:
                print(r.url)
                print(r.text)

            print('Posted.')
