#/usr/bin/python
# Ripmaster Tool Tests
# Tests for the Ripmaster tools
# By Sean Wallitsch, 2014/04/06
"""
Tests for all of the classes and functions inside of Ripmaster's tools module.

REQUIREMENTS:

mock
"""

#===============================================================================
# IMPORTS
#===============================================================================

# Standard Imports
import os
import mock
from StringIO import StringIO
import sys
import unittest

# Grab our test's path and append the Ripmaster root directory
# We have to do this since Ripmaster isn't meant to be an installed tool- it's
# a standalone and therefore will not be installed like normal.

# There has to be a better method than:
# 1) Getting our current directory
# 2) Splitting into list
# 3) Splicing out the last 3 entires (filepath, test dir, tools dir)
# 4) Joining
# 5) Appending to our Python path.


sys.path.append('/'.join(os.path.realpath(__file__).split('/')[:-3]))

# Ripmaster Imports
import tools

#===============================================================================
# GLOBALS
#===============================================================================

SAMPLE_CONFIG = """[Programs]
BDSupToSub: C://Program Files (x86)/MKVToolNix/BDSup2Sub.jar
HandbrakeCLI: C://Program Files/Handbrake/HandBrakeCLI.exe
Java: C://Program Files (x86)/Java/jre7/bin/java
mkvExtract: C://Program Files (x86)/MKVToolNix/mkvextract.exe
mkvMerge: C://Program Files (x86)/MKVToolNix/mkvmerge.exe

[Handbrake Settings]
animation_BFrames: 8
audio_Fallback: ffac3
language: English
x264_Speed: slow

[Base Encode Quality]
1080p: 20
720p: 20
480p: 20

[High Encode Quality]
1080p: 19
720p: 19
480p: 19

[Ultra Encode Quality]
1080p: 16
720p: 16
480p: 16"""

#===============================================================================
# CLASSES
#===============================================================================

class TestConfigSetup(unittest.TestCase):
    """Tests basic setup of Config"""

    #===========================================================================
    # SETUP & TEARDOWN
    #===========================================================================

    @mock.patch('__main__.open', mock.mock_open(read_data=SAMPLE_CONFIG), create=True)
    @mock.patch('os.path.exists')
    def setUp(self, mockExists):
        mockExists.return_value = True
        self.config = tools.Config('bestIniFile.ini')

    #===========================================================================
    # TESTS
    #===========================================================================

    def testItHappened(self):
        self.config.debug()

#===============================================================================
# FUNCTIONS
#===============================================================================

if __name__ == '__main__':
    unittest.main()