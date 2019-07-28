The new Classic ADS
===================

This is a clean-room reimplementation of (a small subset of) the Classic
ADS interface.

NASA ADS (Astrophysics Data System) provides API to access the database
programmatically, and a Javascript-based modern web interface at
https://ui.adsabs.harvard.edu, while the classic HTML-based ADS
interface will be retired soon.
This package provides a replacement for the most commonly used tasks
(author/title/abstract query, abstract display, reference and citation
search) in the traditional, pure HTML interface. It translates the HTML
form input into a query for the ADS API, executes the query, and formats
the output.
It is compatible with Python 2 and 3, uses no external libraries except
``requests``, and produces pure HTML with no fancy Javascript, which can
be viewed in any browser and even in a text mode.

The package can be used locally by running the script ``server.py`` and
pointing the browser to http://0.0.0.0:8000 (or perhaps another port #).
One needs to set the environment variable ADS_TOKEN to a 40-character
access token, provided by the ADS for registered users.

Alternatively, this package powers the website http://adsabs.net
