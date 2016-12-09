import json


def test_read_config(install, splunk):
    '''
    test read conf file
    '''
    splunk.change_namespace('nobody', 'search', 'app')
    content = splunk.read_conf_file(
        'savedsearches', "Errors in the last hour", owner='admin',
        app='search', sharing='app')
    search = ('error OR failed OR severe OR ( sourcetype=access_* '
              '( 404 OR 500 OR 503 ) )')

    assert content['search'] == search


def test_write_config(install, splunk):
    '''
    test write config file
    '''
    # write to savedsearches.conf
    name = 'test_titanium'
    data = {'search': 'search *'}

    splunk.change_namespace('admin', 'search', 'app')
    splunk.edit_conf_file('savedsearches', name, data)

    content = splunk.read_conf_file('savedsearches', name)
    assert content['search'] == data['search']


def test_get_mgmt_port(install, splunk):
    '''
    test getting mgmt port
    '''
    assert '8089' == splunk.mgmt_port


def test_is_splunk_running(install, splunk):
    '''
    test if splunk is running
    '''
    assert splunk.is_running()


def test_stop_splunk(install, splunk):
    '''
    test stop splunk
    '''
    splunk.stop()
    assert not splunk.is_running()


def test_add_license(install, splunk, license):
    '''
    test adding splunk license
    '''
    splunk.add_license(license)
    response = splunk.get('licenser/stacks', output_mode='json').body.readall()
    response = json.loads(response)
    assert 'enterprise' in [entry['name'] for entry in response['entry']]


def test_config_deployment_client(install, splunk):
    '''
    test configuring deployment client
    '''
    server = 'titanium:8089'
    splunk.config_deployment_client(server)
    splunk.change_namespace('nobody', 'nobody', 'system')
    target_uri = splunk.read_conf_file(
        'deploymentclient', 'target-broker:deploymentServer', 'targetUri')
    assert target_uri == server


def test_enable_listen(install, splunk):
    '''
    test enable listening
    '''
    port = '9990'
    splunk.enable_listen(port)
    assert port in splunk.get_listening_ports()


def test_add_forward_server(install, splunk):
    '''
    test adding forward server
    '''
    server = 'titanium:9995'
    splunk.add_forward_server(server)
    splunk.change_namespace('nobody', 'nobody','system')
    conf = splunk.read_conf_file('outputs')

    assert 'tcpout-server://' + server in [staza.name for staza in conf.list()]
    assert server in conf['tcpout:default-autolb-group']['server'].split(',')
