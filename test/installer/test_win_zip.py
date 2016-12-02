from titanium import installer

url = 'https://www.dropbox.com/s/w33tvovj1fqnx6w/splunk-6.3.2-aaff59bb082c-windows-64.zip?dl=0'
splunk_home = 'C:\\Program Files\\Splunk'

my_installer = installer.install(url, splunk_home)

assert my_installer.is_installed(), "Splunk is not installed"

my_installer.uninstall()

assert not my_installer.is_installed(), "Splunk is not uninstalled"
