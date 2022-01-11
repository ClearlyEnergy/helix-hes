HELIX-HES
=========

Connectivity to Department of Energy Home Energy Score Connectivity for HELIX

Installation
------------

- git clone https://github.com/ClearlyEnergy/helix-hes.git
- pip install .

Test Coverage
-------------

- python setup.py test

Run Locally
-----------
Example to create HES from HPXML
python3

import base64
import os

from hes import hes
hes = hes.HesHelix(wsdl, user_name, password, user_key)
for example: hes_tst = hes.HesHelix('https://sandbox.hesapi.labworks.org/st_api/wsdl', os.environ.get('HES_USER_NAME',''), os.environ.get('HES_PASSWORD',''), os.environ.get('HES_USER_KEY',''))
f_hpxml = open(os.path.abspath(os.getcwd())+"/tests/house1.hpxml", "r")
f_bytes = f_hpxml.read().encode("utf-8")
hes_tst.hpxml = base64.standard_b64encode(f_bytes)
result = hes_tst.submit_hpxml_inputs()
