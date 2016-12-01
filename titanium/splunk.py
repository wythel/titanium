import os
import netifaces
from splunklib import client
from splunklib.binding import HTTPError
from util import run_cmd
from exceptions import CommandExecutionError
import logging

logger = logging.getLogger(__name__)


class Splunk(object):
    '''
    This class represents a splunk instance
    '''
    def __init__(self, splunk_home, username="admin", password="changeme",
                 scheme='https', owner="admin", app="search", sharing="user"):
        '''
        :param host: The host name (the default is "localhost").
        :type host: ``string``
        :param port: The port number (the default is 8089).
        :type port: ``integer``
        :param scheme: The scheme for accessing the service (the default is
                       "https").
        :type scheme: "https" or "http"
        :param `owner`: The owner context of the namespace (optional).
        :type owner: ``string``
        :param `app`: The app context of the namespace (optional).
        :type app: ``string``
        :param sharing: The sharing mode for the namespace (the default is
                        "user").
        :type sharing: "global", "system", "app", or "user"
        :param `username`: The Splunk account username, which is used to
                           authenticate the Splunk instance.
        :type username: ``string``
        :param `password`: The password for the Splunk account.
        :type password: ``string``
        '''
        self.splunk = client.connect(
            username=username, password=password, owner=owner, app=app,
            sharing=sharing, scheme=scheme, autologin=True)

        self.splunk_home = splunk_home
        self.username = username
        self.password = password
        self.scheme = scheme

    def cli(self, cli, auth="admin:changeme"):
        '''
        run cli
        '''
        execute = os.path.join(self.splunk_home, 'bin', 'splunk')
        if auth is None:
            cmd = '{e} {c}'.format(e=execute, c=cli)
        else:
            cmd = '{e} {c} -auth {a}'.format(e=execute, c=cli, a=auth)

        process = run_cmd(cmd)
        return process

    def is_running(self):
        '''
        return splunk is running or not
        '''
        result = self.cli("status", auth=None)
        return 'splunkd is running' in result['stdout']

    def start(self):
        '''
        start splunk via cli
        '''
        result = self.cli("start", auth=None)
        return result['retcode']

    def stop(self):
        '''
        stop splunk via cli
        '''
        result = self.cli("stop", auth=None)
        return result['retcode']

    def restart(self, interface='cli'):
        '''
        restart splunk
        '''
        if 'cli' == interface:
            self.cli('restart', auth=None)
        elif 'rest' == interface:
            self.splunk.restart()
        else:
            self.cli('restart', auth=None)

    def change_namespace(self, owner, app, sharing):
        '''
        '''
        self.splunk = client.connect(
            username=self.username, password=self.password, owner=owner,
            app=app, sharing=sharing, autologin=True)

    @property
    def mgmt_port(self):
        '''
        get mgmt uri of splunk

        :return: The mgmt uri of splunk, return None if Splunk is not started
        :rtype: string
        '''
        # todo auth parameter

        cli_result = self.cli("show splunkd-port")

        if 0 == cli_result['retcode']:
            port = cli_result['stdout'].replace("Splunkd port: ", "").strip()
            return port
        else:
            return None

    def get_mgmt_uri(self):
        '''
        Get mgmt uri
        '''
        ip = netifaces.ifaddresses('eth0')[netifaces.AF_INET][0]['addr']
        return ip + ":" + self.mgmt_port

    def add_license(self, path):
        '''
        add license to splunk
        :param path: path to the license file
        '''
        result = self.cli("add license {p}".format(p=path))

        if 0 == result['retcode']:
            return self.restart()
        else:
            return result

    def remove_search_peer(self, peers):
        '''
        remove search peer from a search head
        :type servers: list
        :param servers: ex, ['<ip>:<port>','<ip>:<port>', ...]
        '''
        # try to remove servers not in list
        # todo fix username and password
        if type(peers) is not list:
            peers = [peers, ]

        for peer in peers:
            result = self.cli('remove search-server -url {h}'.format(h=peer))
            if result['retcode'] != 0:
                raise CommandExecutionError(
                    result['stderr'] + result['stdout'])

    def edit_conf_file(
            self, conf_name, stanza_name, data=None, app=None,
            owner=None, sharing='system', do_restart=True):
        """
        config conf file by REST, if a data is existed, it will skip

        :param conf_name: name of config file
        :param stanza_name: stanza need to config
        :param data: data under stanza
        :param do_restart: restart after configuration
        :param app: namespace of the conf
        :param owner: namespace of the conf
        :param sharing: The scope you want the conf to be. it can be user,
                        app, or system.
        :return: no return value
        :raise EnvironmentError: if restart fail
        """
        self.change_namespace(app=app, owner=owner, sharing=sharing)
        conf = self.splunk.confs[conf_name]

        data = dict() if data is None else data

        try:
            stanza = conf[stanza_name]
        except KeyError:
            conf.create(stanza_name)
            stanza = conf[stanza_name]
        except HTTPError as err:
            logger.critical('%s is existed' % str(stanza_name))
            logger.debug(err)

        stanza.submit(data)

        if do_restart:
            self.restart()

    def read_conf_file(
            self, conf_name, stanza_name, key_name=None, owner=None, app=None,
            sharing='system'):
        """
        read config file

        :param conf_name: name of config file
        :param stanza_name: stanza need to config
        :param key_name: key for the value you want to read
        :param owner: namespace of the conf
        :param app: namespace of the conf
        :param sharing: The scope you want the conf to be. it can be
            user, app, or system.
        :return: if no key_name, stanza content will be returned, else will be
            value of given stanza and key_name
        """
        self.change_namespace(app=app, owner=owner, sharing=sharing)

        try:
            conf = self.splunk.confs[conf_name]
        except KeyError:
            logger.warn("no such conf file %s" % conf_name)
            return None

        try:
            stanza = conf[stanza_name]
        except KeyError:
            logger.warn('no such stanza, %s' % stanza_name)
            return None

        if key_name is None:
            return stanza.content

        if key_name not in stanza.content:
            logger.warn('no such key name, %s' % key_name)
            return None

        return stanza[key_name]

    def is_stanza_existed(
            self, conf_name, stanza_name, owner=None, app=None,
            sharing='system'):
        '''
        check if a stanza is existed in the given conf file

        :type conf_name: string
        :type stanza_name: string
        :type sharing: string
        :param conf_name: name of the conf file
        :param stanza_name: name of the stanza to check
        :param owner: namespace of the conf
        :param app: namespace of the conf
        :param sharing: The scope you want the conf to be. it can be user, app,
                        or system.
        :return: boolean
        '''
        self.change_namespace(owner=owner, app=app, sharing=sharing)

        try:
            conf = self.splunk.confs[conf_name]
        except KeyError:
            logger.warn("no such conf file %s" % conf_name)
            return None
        return stanza_name in conf

    def config_cluster_master(
            self, pass4SymmKey, cluster_label, replication_factor=2,
            search_factor=2, number_of_sites=1,
            site_replication_factor="origin:2,total:3",
            site_search_factor="origin:2,total:3"):
        """
        config splunk as a master of a indexer cluster

        :param pass4SymmKey: it's a key to communicate between indexer cluster
        :param cluster_label: the label for indexer cluster
        :param search_factor: factor of bucket be able to search
        :param replication_factor: factor of bucket be able to replicate
        :param number_of_sites: number of sites of the cluster
        :param site_replication_factor: site replication factor for the cluster
        :param site_search_factor: site search factor of the cluster
        """

        def get_availaible_sites():
            return ', '.join(
                ["site" + str(i) for i in range(1, number_of_sites+1)])

        if number_of_sites > 1:
            # multi-site
            self.edit_conf_file(
                'server', 'general', {'site': 'site1'}, do_restart=False)

            data = {'pass4SymmKey': pass4SymmKey,
                    'mode': 'master',
                    'cluster_label': cluster_label,
                    'multisite': True,
                    'available_sites': get_availaible_sites(),
                    'site_replication_factor': site_replication_factor,
                    'site_search_factor': site_search_factor}
        else:
            # single-site
            data = {'pass4SymmKey': pass4SymmKey,
                    'replication_factor': replication_factor,
                    'search_factor': search_factor,
                    'mode': 'master',
                    'cluster_label': cluster_label}

        self.edit_conf_file('server', 'clustering', data)

    def config_cluster_slave(
            self, pass4SymmKey, cluster_label, master_uri,
            replication_port=9887, site=None):
        """
        config splunk as a peer(indexer) of a indexer cluster

        :param pass4SymmKey: is a key to communicate between indexer cluster
        :param cluster_label: the label for indexer cluster
        :param replication_port: port to replicate data
        :param master_uri: <ip>:<port> of mgmt_uri, ex 127.0.0.1:8089,
            if not specified, will search minion under same master with role
            indexer-cluster-master
        :param site: None if the slave is on single site, else "site1"
                     or "site2"...
        :type site: string
        """

        self.edit_conf_file(
            'server', "replication_port://{p}".format(p=replication_port),
            do_restart=False)

        data = {'pass4SymmKey': pass4SymmKey,
                'master_uri': 'https://{u}'.format(u=master_uri),
                'mode': 'slave',
                'cluster_label': cluster_label}

        if site is not None:  # for multi-site
            self.edit_conf_file(
                'server', 'general', {'site': site}, do_restart=False)

        self.edit_conf_file('server', 'clustering', data)

    def config_cluster_searchhead(
            self, pass4SymmKey, cluster_label, master_uri, site=None):
        """
        config splunk as a search head of a indexer cluster
        http://docs.splunk.com/Documentation/Splunk/latest/Indexer/Enableclustersindetail

        :param pass4SymmKey:  is a key to communicate between indexer cluster
        :param cluster_label: the label for indexer cluster
        :param master_uri: <ip>:<port> of mgmt_uri, ex 127.0.0.1:8089,
            if not specified, will search minion under same master with role
            splunk-cluster-master
        :param site: None if the search head is on single site, else
            "site1" or "site2"...
        :type site: string
        """

        data = {'pass4SymmKey': pass4SymmKey,
                'master_uri': 'https://{u}'.format(u=master_uri),
                'mode': 'searchhead',
                'cluster_label': cluster_label}

        if site is not None:  # for multi-site
            self.edit_conf_file(
                'server', 'general', {'site': site}, do_restart=False)
            data['multisite'] = True

        self.edit_conf_file('server', 'clustering', data)

    def config_shcluster_deployer(self, pass4SymmKey, shcluster_label):
        '''
        config a splunk as a deployer of a search head cluster

        :param shcluster_label: label for the shc
        :param pass4SymmKey: is a key to communicate between cluster
        '''
        data = {'pass4SymmKey': pass4SymmKey,
                'shcluster_label': shcluster_label}

        self.edit_conf_file('server', 'shclustering', data=data)

    def config_shcluster_member(
            self, pass4SymmKey, shcluster_label, replication_port,
            conf_deploy_fetch_url, replication_factor=None):
        '''
        config splunk as a member of a search head cluster

        :param pass4SymmKey: pass4SymmKey for SHC
        :param shcluster_label: shcluster's label
        :param replication_port: replication port for SHC
        :param replication_factor: replication factor for SHC,
            if it's None use default provided by Splunk
        :param conf_deploy_fetch_url: deployer's mgmt uri
        '''
        if not conf_deploy_fetch_url.startswith("https://"):
            conf_deploy_fetch_url = 'https://{u}'.format(
                u=conf_deploy_fetch_url)

        replication_factor_str = ''
        if replication_factor:
            replication_factor_str = '-replication_factor {n}'.format(
                n=replication_factor)

        cmd = 'init shcluster-config -mgmt_uri {mgmt_uri}' \
              '-replication_port {replication_port} ' \
              '{replication_factor_str} ' \
              '-conf_deploy_fetch_url {conf_deploy_fetch_url} ' \
              '-secret {security_key} -shcluster_label {label}' \
              .format(
                    mgmt_uri=self.get_mgmt_uri(),
                    replication_port=replication_port,
                    replication_factor_str=replication_factor_str,
                    conf_deploy_fetch_url=conf_deploy_fetch_url,
                    security_key=pass4SymmKey,
                    label=shcluster_label)

        result = self.cli(cmd)
        if result['retcode'] != 0:
            raise CommandExecutionError(result['stderr'] + result['stdout'])

        result = self.restart()
        if result['retcode'] != 0:
            raise CommandExecutionError(result['stderr'] + result['stdout'])

    def bootstrap_shcluster_captain(self, shc_members):
        '''
        bootstrap a splunk instance as a captain of a search head cluster
        captain

        :param servers_list: list of shc members,
            ex. https://192.168.0.2:8089,https://192.168.0.3:8089
        '''
        servers_list = ','.join(shc_members)

        cmd = 'bootstrap shcluster-captain -servers_list {s} '.format(
            s=servers_list)

        result = self.cli(cmd)

        if 0 != result['retcode']:
            raise CommandExecutionError("Error bootstraping shc captain")

    def config_search_peer(
            self, peers, remote_username='admin', remote_password='changeme'):
        '''
        config splunk as a peer of a distributed search environment

        if a search head is part of indexer cluster search head,
        will raise EnvironmentError

        :param peers: list value, ex, ['<ip>:<port>','<ip>:<port>']
        :param remote_username: splunk username of the search peer
        :param remote_password: splunk password of the search peer
        :raise CommandExecutionError, if failed
        '''

        for peer in peers:
            cmd = ('add search-server -host {h} -remoteUsername {u} '
                   '-remotePassword {p}'.format(
                     h=peer, p=remote_password, u=remote_username))
            result = self.cli(cmd)

            if result['retcode'] != 0:
                raise CommandExecutionError(
                    result['stderr'] + result['stdout'])

    def config_deployment_client(self, server):
        '''
        config deploymeny client

        deployment client is not compatible if a splunk is
        :param server: mgmt uri of deployment server
        '''
        cmd = 'set deploy-poll {s}'.format(s=server)
        cli_result = self.cli(cmd)
        if cli_result['retcode'] != 0:
            raise CommandExecutionError(str(cli_result))

        restart_result = self.cli('restart')
        if restart_result['retcode'] != 0:
            raise CommandExecutionError(str(restart_result))

    def config_license_slave(self, master_uri):
        '''
        config splunk as a license slave

        :param master_uri: uri of the license master
        :type master_uri: string
        '''
        self.edit_conf_file('server', 'license', {'master_uri': master_uri})

    def create_users(self, count, prefix='user', roles=['user']):
        '''
        create a batch of users
        '''
        if not isinstance(roles, list):
            roles = [roles, ]

        for i in range(count):
            user = prefix + str(i)
            self.splunk.users.create(username=user, password=user, roles=roles)

    def create_saved_searches(self, count, search, prefix='search', **kwargs):
        '''
        create a batch of saved searches
        '''
        for i in range(count):
            name = prefix + str(i)
            self.splunk.saved_searches.create(
                name=name, search=search, **kwargs)

    def enable_listen(self, port):
        '''
        enable listening on the splunk instance
        :param port: the port number to enable listening
        :type port: integer
        :return: None
        '''
        result = self.cli("enable listen {p}".format(p=port))

        if result['retcode'] != 0:
            raise CommandExecutionError(result['stderr'] + result['stdout'])

    def add_forward_server(self, server):
        '''
        add forward server to the splunk instance
        :param server: server to add to the splunk instance
        :type server: string
        :return: None
        '''
        result = self.cli("add forward-server {s}".format(s=server))

        if result['retcode'] != 0:
            raise CommandExecutionError(result['stderr'] + result['stdout'])

    def add_deployment_app(self, name):
        '''
        add an deployment app by making a new dierctory in
        $SPLUNK_HOME/etc/deployment-apps
        '''
        cmd = 'mkdir {p}'.format(
            p=os.path.join(self.splunk_home, 'etc', 'deployment-apps', name))
        result = run_cmd(cmd)

        if result['retcode'] != 0:
            raise CommandExecutionError(result['stderr'] + result['stdout'])
