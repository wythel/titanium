import sys
from titanium import installer

url = sys.argv[1]
splunk_home = '/home/eserv/titanium/splunk'

my_installer = installer.install(url, splunk_home)

assert my_installer.is_installed(), "Splunk is not installed"

my_installer.uninstall()

assert not my_installer.is_installed(), "Splunk is not uninstalled"
