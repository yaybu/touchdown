Installation
============

Installing from PyPi
--------------------

You can install Touchdown from PyPi with pip. The suggested way is to install
it in a virtualenv::

    pip install touchdown

Right now we don't depend on optional libraries. In order to work with AWS you
will need to install botocore::

    pip install botocore

And in order to deploy server configuration you'll need to install fuselage::

    pip install fuselage


Installing from GitHub
----------------------

If you are hacking on Touchdown the recommended way to get started is to clone
the repo and build a virtualenv::

    git clone git://github.com/yaybu/touchdown
    cd touchdown
    virtualenv .
    source bin/activate
    pip install -e .
