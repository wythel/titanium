import pytest

def pytest_addoption(parser):
    parser.addoption("--splunk-home", default="/opt/splunk",
    	dest="splunk_home", help="where to install splunk")
    parser.addoption("--skip-install-splunk", action='store_true',
    	dest='skip_install_splunk',
    	help="add this option if splunk is ready to be tested")
    parser.addoption("--pkg-url", dest="pkg_url",
    	help="url to the package for testing")

def pytest_configure(config):
	'''
	config pytest
	'''
	config.splunk_home = config.getvalue('splunk_home')
	config.skip_install_splunk = config.getvalue('skip_install_splunk')
	config.pkg_url = config.getvalue('pkg_url')