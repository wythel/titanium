import pytest
from titanium import installer
from titanium.splunk import Splunk


pkg_url = pytest.config.pkg_url
splunk_home = pytest.config.splunk_home
skip_installation = pytest.config.skip_install_splunk


class TestSplunkConfig(object):
    '''
    Test configuring splunk configs
    '''
    def setup_class(cls):
        if not skip_installation:
            cls.installer = installer.install(pkg_url, splunk_home)
        cls.splunk = Splunk(splunk_home=splunk_home)

    def teardown_class(cls):
        if not skip_installation:
            cls.installer.uninstall()

    def test_read_config(self):
        '''
        test read conf file
        '''
        content = self.splunk.read_conf_file(
            'savedsearches', "Errors in the last hour", owner='admin',
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
