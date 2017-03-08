First, install python3-flask, PLSI, and run through the flow once manually
in the PLSI directory to pre-cache all the tools, etc.

Then, create the config.cfg configuration file.

Then, create the database with:

  python3 plsiweb.py create_db

Finally, run the web interface:

  python3 plsiweb.py

It will run by default at http://localhost:5050/#.

