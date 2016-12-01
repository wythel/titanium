def test_config_cluster_master(install, splunk):
    '''
    test config cluster master
    '''
    splunk.config_cluster_master(
        pass4SymmKey='1234', cluster_label="titanium", replication_factor=2,
        search_factor=2, number_of_sites=1)

    content = splunk.read_conf_file('server', 'clustering')

    assert content['cluster_label'] == 'titanium'
    assert content['replication_factor'] == '2'
    assert content['search_factor'] == '2'
