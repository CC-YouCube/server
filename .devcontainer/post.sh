#!/bin/ash
pip install --no-cache-dir --use-pep517 -r src/requirements.txt;
pip install -U autopep8;
sudo make install-pylint;
sudo make install-pyspelling;
