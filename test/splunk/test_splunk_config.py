from titanium import installer
from titanium.splunk import Splunk


pkg_url = 'http://releases.splunk.com/released_builds/6.3.0/splunk/linux/splunk-6.3.0-aa7d4b1ccb80-Linux-x86_64.tgz'
splunk_home = '/home/eserv/titanium/splunk'


class TestSplunkConfig(object):
    '''
    Test configuring splunk configs
    '''
    def setup_class(cls):
        cls.installer = installer.install(pkg_url, splunk_home)
        cls.splunk = Splunk(splunk_home=splunk_home)

    def teardown_class(cls):
        cls.installer.uninstall()

    def test_read_config(self):
        '''
        test read conf file
        '''
        content = self.splunk.read_conf_file(
            'savedsearches', "Error in the last hour", user='admin',
            app='search', sharing='app')
        search = ('error OR failed OR severe OR ( sourcetype=access_* '
                  '( 404 OR 500 OR 503 ) )')

        assert content['search'] == search

    def test_write_config(self):
        '''
        test write config file
        '''
        # write to savedsearches.conf
        name = 'test_titanium'
        data = {'search': 'search *'}
        self.splunk.edit_conf_file('savedsearches', name, data)

        content = self.splunk.read_conf_file('savedsearches', name)
        assert content['search'] == data['search']
