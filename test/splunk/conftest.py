import pytest
from titanium import installer
from titanium.splunk import Splunk


def pytest_addoption(parser):
    parser.addoption(
        "--splunk-home", default="/opt/splunk",
        dest="splunk_home", help="where to install splunk")
    parser.addoption(
        "--skip-install-splunk", action='store_true',
        dest='skip_install_splunk',
        help="add this option if splunk is ready to be tested")
    parser.addoption(
        "--pkg-url", dest="pkg_url",
        help="url to the package for testing")
    parser.addoption(
        "--license-path", dest="license_path",
        help="path to the license for testing")


@pytest.fixture(scope='session')
def install(request):
    config = request.config

    if not config.getoption('--skip-install-splunk'):
        my_installer = installer.install(
            config.getoption('--pkg-url'), config.getoption('--splunk-home'))
        yield my_installer
        my_installer.uninstall()
    else:
        yield None


@pytest.fixture(scope='function')
def splunk(request):
    config = request.config
    splunk = Splunk(config.getoption('--splunk-home'))
    yield splunk
    if not splunk.is_running():
        splunk.start()


@pytest.fixture(scope='function')
def license(request):
    config = request.config
    yield config.getoption('--license-path')