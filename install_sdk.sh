# Installs xblock-sdk and dependencies needed to run the tests suite.
# Run this script inside a fresh virtual environment.
pip install -e git://github.com/edx/xblock-sdk.git#egg=xblock-sdk
pip install -r $VIRTUAL_ENV/src/xblock-sdk/requirements/base.txt
pip install -r $VIRTUAL_ENV/src/xblock-sdk/requirements/test.txt
## should be installed by requirements/base.txt, but for some reason fails
pip install -e git+https://github.com/edx/django-pyfs.git@1.0.3#egg=django-pyfs==1.0.3