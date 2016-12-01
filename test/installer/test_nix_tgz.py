from titanium import installer

url = 'http://releases.splunk.com/released_builds/6.3.0/splunk/linux/splunk-6.3.0-aa7d4b1ccb80-Linux-x86_64.tgz'
splunk_home = '/home/eserv/titanium/splunk'

my_installer = installer.install(url, splunk_home)

assert my_installer.is_installed(), "Splunk is not installed"

my_installer.uninstall()

assert not my_installer.is_installed(), "Splunk is not uninstalled"
