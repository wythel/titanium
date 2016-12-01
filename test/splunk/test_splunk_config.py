from titanium import installer
from titanium.splunk import Splunk


class TestSplunkConfig(object):
    '''
    Test configuring splunk configs
    '''

    def test_read_config(self, install_splunk, splunk):
        '''
        test read conf file
        '''
        content = splunk.read_conf_file(
            'savedsearches', "Errors in the last hour", owner='admin',
            app='search', sharing='app')
        search = ('error OR failed OR severe OR ( sourcetype=access_* '
                  '( 404 OR 500 OR 503 ) )')

        assert content['search'] == search

    def test_write_config(self, install_splunk, splunk):
        '''
        test write config file
        '''
        # write to savedsearches.conf
        name = 'test_titanium'
        data = {'search': 'search *'}
        splunk.edit_conf_file('savedsearches', name, data)

        content = splunk.read_conf_file('savedsearches', name)
        assert content['search'] == data['search']

    def test_get_mgmt_port(self, install_splunk, splunk):
        '''
        test getting mgmt port
        '''
        assert '8089' == splunk.mgmt_port

    def test_is_splunk_running(self, install_splunk, splunk):
        '''
        test if splunk is running
        '''
        assert splunk.is_running()

    def test_stop_splunk(self, install_splunk, splunk):
        '''
        test stop splunk
        '''
        splunk.stop()
        assert not splunk.is_running()
