import sys
import shutil
import tempfile
import logging
import requests


PLATFORM = sys.platform
logger = logging.getLogger(__name__)


class InstallerFactory(object):
    def __init__(self):
        pass

    @staticmethod
    def create_installer(pkg_path, splunk_type=None):
        if "linux" in PLATFORM:
            installer = LinuxTgzInstaller(splunk_type)
        elif "win" in PLATFORM:
            if pkg_path.endswith('.zip'):
                installer = WindowsZipInstaller()
            else:
                installer = WindowsMsiInstaller(splunk_type)
        else:
            # to do: throw error when platform is not supported
            raise NotImplementedError
        return installer


class Installer(object):
    def __init__(self, pkg_path, splunk_type):
        self.splunk_type = splunk_type
        self.pkg_path = pkg_path

    def install(self, pkg_path, splunk_home=None):
        pass

    def is_installed(self):
        pass

    def uninstall(self):
        pass


class WindowsMsiInstaller(Installer):
    def __init__(self, splunk_type):
        super(WindowsMsiInstaller, self).__init__(splunk_type)
        if not self.splunk_home:
            self.splunk_home = "C:\\Program Files\\Splunk"

    def install(self, pkg_path, splunk_home=None, **kwargs):
        if splunk_home:
            self.splunk_home = splunk_home

        install_flags = []
        for key, value in kwargs.iteritems():
            install_flags.append('{k}="{v}"'.format(k=key, v=value))

        cmd = 'msiexec /i "{c}" INSTALLDIR="{h}" AGREETOLICENSE=Yes {f} {q} ' \
              '/L*V "C:\\msi_install.log"'. \
            format(c=pkg_path, h=self.splunk_home, q='/quiet',
                   f=' '.join(install_flags))

        self.pkg_path = pkg_path

        return __salt__['cmd.run_all'](cmd, python_shell=True)

    def is_installed(self):
        if "splunk" == self.splunk_type:
            result = __salt__['service.available']('Splunkd')
        elif "splunkforwarder" == self.splunk_type:
            result = __salt__['service.available']('SplunkForwarder')
        elif self.splunk_type is None:
            result = False
        else:
            raise Exception, "Unexpected splunk_type: {s}".format(
                s=self.splunk_type)

        log.debug('service.available return : %s' % result)
        return result

    def uninstall(self):
        if not is_installed():
            return

        pkg_path = self.pkg_path
        if not pkg_path:
            raise EnvironmentError("Can't uninstall without pkg file")

        cmd = 'msiexec /x {c} /quiet SUPPRESS_SURVEY=1'.format(c=pkg_path)
        result = __salt__['cmd.run_all'](cmd, python_shell=True)
        if result['retcode'] == 0:
            os.remove(pkg_path)
            __salt__['grains.delval']('pkg_path')
            __salt__['grains.delval']('splunk_type')


class LinuxTgzInstaller(Installer):
    def __init__(self, splunk_type):
        super(LinuxTgzInstaller, self).__init__(splunk_type)
        if not self.splunk_home:
            self.splunk_home = "/opt/splunk"

    def install(self, pkg_path, splunk_home=None, **kwargs):
        if splunk_home:
            self.splunk_home = splunk_home

        if self.is_installed():
            cmd = "{s}/bin/splunk stop".format(s=self.splunk_home)
            __salt__['cmd.run_all'](cmd)

        if not os.path.exists(self.splunk_home):
            os.mkdir(self.splunk_home)

        cmd = ("tar --strip-components=1 -xf {p} -C {s}; {s}/bin/splunk "
               "start --accept-license --answer-yes"
               .format(s=self.splunk_home, p=pkg_path))
        self.pkg_path = pkg_path

        return __salt__['cmd.run_all'](cmd, python_shell=True)

    def is_installed(self):
        return os.path.exists(os.path.join(self.splunk_home, "bin", "splunk"))

    def uninstall(self):
        if not self.is_installed():
            return
        cli("stop -f")
        ret = __salt__['cmd.run_all'](
            "rm -rf {h}".format(h=self.splunk_home))
        if 0 == ret['retcode']:
            os.remove(self.pkg_path)
            __salt__['grains.delval']('pkg_path')
            __salt__['grains.delval']('splunk_type')
        else:
            raise CommandExecutionError(ret['stdout'] + ret['stderr'])

        if __salt__['grains.has_value']('splunk_mgmt_uri'):
            __salt__['grains.delval']('splunk_mgmt_uri')


class WindowsZipInstaller(Installer):
    def __init__(self):
        super(WindowsZipInstaller, self).__init__()
        if not self.splunk_home:
            self.splunk_home = "C:\\splunk"

    def install(self, pkg_path, splunk_home=None, **kwargs):
        if splunk_home:
            self.splunk_home = splunk_home

        if self.is_installed():
            cli('stop')

        if not os.path.exists(self.splunk_home):
            os.mkdir(self.splunk_home)

        self.pkg_path = pkg_path
        par_home = os.path.dirname(self.splunk_home)

        cmd = ("cd c:\\ & unzip {p} -d {par} & {s}\\bin\\splunk.exe enable boot-start "
               "& {s}\\bin\\splunk.exe start "
               "--accept-license --answer-yes".format(s=self.splunk_home, p=pkg_path, par=par_home))

        return __salt__['cmd.run_all'](cmd, python_shell=True)


    def is_installed(self):
        return os.path.exists(os.path.join(self.splunk_home, "bin", "splunk.exe"))

    def uninstall(self):
        if not self.is_installed():
            return
        ret = cli("stop -f")
        shutil.rmtree(self.splunk_home)

        cmd = 'sc delete Splunkd'
        __salt__['cmd.run_all'](cmd, python_shell=True)

        cmd = 'sc delete Splunkweb'
        __salt__['cmd.run_all'](cmd, python_shell=True)

        if 0 == ret['retcode']:
            os.remove(self.pkg_path)
            __salt__['grains.delval']('pkg_path')
            __salt__['grains.delval']('splunk_type')
        else:
            raise CommandExecutionError(ret['stdout'] + ret['stderr'])

        if __salt__['grains.has_value']('splunk_mgmt_uri'):
            __salt__['grains.delval']('splunk_mgmt_uri')


def download_file(url, destination):
    '''
    download a file to destination
    '''
    response = requests.get(url, stream=True)
    with open(destination, "wb") as saved_file:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                saved_file.write(chunk)


def install(splunk_pkg_url, type='splunk', start_after_install=True,
            upgrrade=False, splunk_home=None):
    """
    install Splunk

    :param splunk_pkg_url: url to download splunk pkg
    :type splunk_pkg_url: string
    :param type: splunk, splunkforwarder or splunklite
    :type type: string
    :param start_after_install: true: start splunk right after installation
    :type start_after_install: boolean
    :param upgrrade: True if you want to upgrade splunk
    :type upgrrade: bool
    :param splunk_home: path for splunk install to
    :type splunk_home: string
    :rtype: dict
    :return: command line result in dict ['retcode', 'stdout', 'stderr']
    """
    url = splunk_pkg_url

    # download the package
    dest_root = tempfile.gettempdir()
    pkg_path = os.path.join(dest_root, os.sep, os.path.basename(url))
    logger.debug('download pkg to: {p}'.format(p=pkg_path))
    logger.debug('download pkg from: {u}'.format(u=url))

    download_file(url=url, destination=pkg_path)

    installer = InstallerFactory.create_installer(splunk_type=type,
                                                  pkg_path=pkg_path)

    if installer.is_installed() and not is_upgrade:
        logger.debug('splunk is installed')
        return dict({'retcode': 9,
                     'stdout': 'splunk is installed',
                     'stderr': 'splunk is installed'})

    return installer.install(pkg_path, splunk_home)
