from titanium import installer

url = 'https://www.dropbox.com/s/erb3s5v5drfymh5/splunk-6.3.1-f3e41e4b37b2-x64-release.msi?dl=0'
splunk_home = 'C:\\Program Files\\Splunk'

my_installer = installer.install(url, splunk_home)

assert my_installer.is_installed(), "Splunk is not installed"

my_installer.uninstall()

assert not my_installer.is_installed(), "Splunk is not uninstalled"
