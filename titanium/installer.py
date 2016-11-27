import sys
import shutil
import tempfile
import logging
import requests
import subprocess
import os
from zipfile import ZipFile


PLATFORM = sys.platform
logger = logging.getLogger(__name__)


def download_file(url, destination):
    '''
    download a file to destination
    '''
    response = requests.get(url, stream=True)
    with open(destination, "wb") as saved_file:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                saved_file.write(chunk)


def install(splunk_pkg_url, splunk_home, type='splunk', upgrade=False):
    """
    install Splunk

    :param splunk_pkg_url: url to download splunk pkg
    :type splunk_pkg_url: string
    :param type: splunk, splunkforwarder or splunklite
    :type type: string
    :param upgrade: True if you want to upgrade splunk
    :type upgrade: bool
    :param splunk_home: path for splunk install to
    :type splunk_home: string
    :rtype: dict
    :return: command line result in dict ['retcode', 'stdout', 'stderr']
    """
    url = splunk_pkg_url

    # download the package
    dest_root = tempfile.gettempdir()
    pkg_path = os.path.join(dest_root, os.path.basename(url))
    logger.debug('download pkg to: {p}'.format(p=pkg_path))
    logger.debug('download pkg from: {u}'.format(u=url))

    download_file(url=url, destination=pkg_path)

    installer = InstallerFactory.create_installer(
        splunk_type=type, pkg_path=pkg_path, splunk_home=splunk_home)

    if installer.is_installed() and not upgrade:
        msg = 'splunk is installed on {s}'.format(s=splunk_home)
        logger.debug(msg)
        print msg

    installer.install()
    return installer


def run_cmd(cmd):
    '''
    run command with subprocess
    '''
    proc = subprocess.Popen(cmd, env=os.environ, shell=True,
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    proc.wait()
    return proc


class InstallerFactory(object):
    def __init__(self):
        pass

    @staticmethod
    def create_installer(pkg_path, splunk_type, splunk_home):
        if "linux" in PLATFORM:
            return LinuxTgzInstaller(pkg_path, splunk_type, splunk_home)
        elif "win" in PLATFORM:
            if pkg_path.endswith('.zip'):
                return WindowsZipInstaller(pkg_path, splunk_type, splunk_home)
            else:
                return WindowsMsiInstaller(pkg_path, splunk_type, splunk_home)
        else:
            raise (Exception,
                   "The platform {p} is not supported".format(p=PLATFORM))


class Installer(object):
    def __init__(self, pkg_path, splunk_type, splunk_home):
        self.splunk_type = splunk_type
        self.pkg_path = pkg_path
        self.splunk_home = splunk_home

    def install(self, pkg_path, splunk_home=None):
        pass

    def is_installed(self):
        pass

    def uninstall(self):
        pass


class LinuxTgzInstaller(Installer):
    def __init__(self, pkg_path, splunk_type, splunk_home):
        super(LinuxTgzInstaller, self).__init__(
            pkg_path, splunk_type, splunk_home)

    def install(self):
        if not os.path.exists(self.splunk_home):
            os.mkdir(self.splunk_home)

        if self.is_installed():
            cmd = "{s}/bin/splunk stop".format(s=self.splunk_home)
            run_cmd(cmd)

        cmd = ("tar --strip-components=1 -xf {p} -C {s}; {s}/bin/splunk "
               "start --accept-license --answer-yes"
               .format(s=self.splunk_home, p=self.pkg_path))

        return run_cmd(cmd)

    def is_installed(self):
        return os.path.exists(os.path.join(self.splunk_home, "bin", "splunk"))

    def uninstall(self):
        if not self.is_installed():
            return True

        # stop splunk
        cmd = "{h}/bin/splunk stop -f".format(h=self.splunk_home)
        run_cmd(cmd)

        # remove splunk home
        shutil.rmtree(self.splunk_home)


class WindowsMsiInstaller(Installer):
    def __init__(self, pkg_path, splunk_type, splunk_home):
        super(WindowsMsiInstaller, self).__init__(
            pkg_path, splunk_type, splunk_home)

    def install(self, **kwargs):
        if not os.path.exists(self.splunk_home):
            os.mkdir(self.splunk_home)

        if self.is_installed():
            cmd = "{s}\\bin\\splunk stop".format(s=self.splunk_home)
            run_cmd(cmd)

        install_flags = []
        for key, value in kwargs.iteritems():
            install_flags.append('{k}="{v}"'.format(k=key, v=value))

        cmd = 'msiexec /i "{c}" INSTALLDIR="{h}" AGREETOLICENSE=Yes {f} {q} ' \
              '/L*V "C:\\msi_install.log"'. \
              format(c=self.pkg_path, h=self.splunk_home, q='/quiet',
                     f=' '.join(install_flags))

        return run_cmd(cmd)

    def is_installed(self):
        return os.path.exists(
            os.path.join(self.splunk_home, "bin", "splunk.exe"))

    def uninstall(self):
        if not self.is_installed():
            return True

        # stop splunk
        cmd = "{s}\\bin\\splunk stop".format(s=self.splunk_home)
        run_cmd(cmd)

        # uninstall
        cmd = 'msiexec /x {c} /quiet SUPPRESS_SURVEY=1'.format(c=self.pkg_path)
        run_cmd(cmd)


class WindowsZipInstaller(Installer):
    def __init__(self, pkg_path, splunk_type, splunk_home):
        super(WindowsZipInstaller, self).__init__(
            pkg_path, splunk_type, splunk_home)

    def install(self):
        if not os.path.exists(self.splunk_home):
            os.mkdir(self.splunk_home)

        if self.is_installed():
            cmd = "{s}\\bin\\splunk stop".format(s=self.splunk_home)
            run_cmd(cmd)

        par_home = os.path.dirname(self.splunk_home)

        # unzip the pkg
        zip_file = ZipFile(self.pkg_path)
        zip_file.extractall(path=par_home)

        cmd = ("{s}\\bin\\splunk.exe enable boot-start & "
               "{s}\\bin\\splunk.exe start --accept-license --answer-yes"
               .format(
                s=self.splunk_home, p=self.pkg_path, par=par_home))
        return run_cmd(cmd)

    def is_installed(self):
        return os.path.exists(
            os.path.join(self.splunk_home, "bin", "splunk.exe"))

    def uninstall(self):
        if not self.is_installed():
            return True

        # stop splunk
        cmd = "{s}\\bin\\splunk stop".format(s=self.splunk_home)
        run_cmd(cmd)

        shutil.rmtree(self.splunk_home)

        run_cmd('sc delete Splunkd')
        run_cmd('sc delete Splunkweb')
