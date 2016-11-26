from titanium import installer

url = 'http://releases.splunk.com/dl/ace_builds/5.0.17-20161121-1500/splunk-5.0.17-278057-x64-release.msi'
splunk_home = 'C:\\Program Files\\Splunk'

installer.install(url, splunk_home)