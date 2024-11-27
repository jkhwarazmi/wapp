#!/bin/bash

source ../flask/bin/activate
export FLASK_APP=run.py
export FLASK_DEBUG=1

flask run
