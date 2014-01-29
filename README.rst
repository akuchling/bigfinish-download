bigfinish-download
==================

Script to synchronize all of your purchases from bigfinish.com with a
local directory of audio files.  This is done efficiently without
redundant downloading, to save both your network bandwidth and Big
Finish's servers.


Usage
=====

.. warning:: Account Security

   Concerned about the security of your Big Finish account username/password?
   You MUST READ AND AUDIT the ``bf-download.py`` script to be sure
   that it isn't doing anything nefarious.  If you can't understand
   Python code, DO NOT USE THE SCRIPT.

The script downloads all of your purchases to a directory.  Basic usage
of the script is::

   ./bf-download.py USERNAME PASSWORD DIRECTORY

For example, to put your library in the ``drama/`` directory::

   ./bf-download.py bffan password drama/

Some purchases are available in both MP3 and audiobook format.  The
default is to download the MP3 format in that case, but you can add
the ``--prefer-audiobook`` switch if you'd like to get the audiobook
version.

The ``-n`` or ``--dry-run`` switches will prevent the script from
accessing bigfinish.com at all; they assume you've already run the
script once so that an initial list of your library has been
downloaded and saved to the directory.  The HTML source for your
library page is saved as ``<directory>/.library.html``, and the
internal data structure is recorded as ``<directory>/.library.json``.

You can also add ``-v`` or ``--verbose`` to make the script print
progress messages as it runs.


Requirements
============

The script is written in Python 3.3; it will probably work with Python 3.4.


Installation
============

1. Create a virtual environment in the same directory as this README::

     virtualenv --python=python3.3 .

2. Activate the virtual environment::

     source bin/activate

3. Install the required packages::

     pip install -r requirements.txt

4. You should now be able to run the script; try running:

     ./bf-download.py --help
