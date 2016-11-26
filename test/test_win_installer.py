from titanium import installer

url = 'http://releases.splunk.com/dl/ace_builds/5.0.17-20161121-1500/splunk-5.0.17-278057-x64-release.msi'
splunk_home = 'C:\\Program Files\\Splunk'

my_installer = installer.install(url, splunk_home)

assert my_installer.is_installed(), "Splunk is not installed"

my_installer.uninstall()

assert not my_installer.is_installed(), "Splunk is not uninstalled"
