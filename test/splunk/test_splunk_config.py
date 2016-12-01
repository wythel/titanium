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
