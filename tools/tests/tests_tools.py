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
import tempfile
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

CONFIG_STRUCTURE = """[Programs]
BDSupToSub: {sup2Sub}
HandbrakeCLI: {handBrake}
Java: {java}
mkvExtract: {mkvExtract}
mkvMerge: {mkvMerge}

[Handbrake Settings]
animation_BFrames: {bFrames}
audio_Fallback: {audioFallback}
language: {language}
sorting: {sorting}
sorting_Reverse: {sortingReverse}
x264_Speed: {x264Speed}

[Base Encode Quality]
1080p: {bq1080}
720p: {bq720}
480p: {bq480}

[High Encode Quality]
1080p: {hq1080}
720p: {hq720}
480p: {hq480}

[Ultra Encode Quality]
1080p: {uq1080}
720p: {uq720}
480p: {uq480}"""

#===============================================================================
# CLASSES
#===============================================================================

class TestStandardConfigSetup(unittest.TestCase):
    """Tests basic setup of Config"""

    #===========================================================================
    # SETUP & TEARDOWN
    #===========================================================================

    def setUp(self):

        # Suppress stdout
        self.held = sys.stdout
        sys.stdout = StringIO()

        # Build out custom ini file
        self.sup2Sub = "Z://Program Files (x86)/MKVToolNix/BDSup2Sub.jar"
        self.handBrake = "Z://Program Files/Handbrake/HandBrakeCLI.exe"
        self.java = "Z://Program Files (x86)/Java/jre7/bin/java"
        self.mkvExtract = "Z://Program Files (x86)/MKVToolNix/mkvextract.exe"
        self.mkvMerge = "Z://Program Files (x86)/MKVToolNix/mkvmerge.exe"

        self.bFrames = 8
        self.audioFallback = 'ffac3'
        self.language = 'English'
        self.sorting = 'alphabetical'
        self.sortingReverse = False
        self.x264Speed = 'slow'

        self.quality = {
            'uq': {'1080': 20, '720': 19, '480': 16},
            'hq': {'1080': 20, '720': 19, '480': 16},
            'bq': {'1080': 20, '720': 19, '480': 16}
        }

        # Get our formatted ini file
        self.configFile = _fillConfig(self)

        # Build our config
        with tempfile.NamedTemporaryFile(mode='r+b') as f:
            f.write(self.configFile)
            # Calling readlines on the temp file. Without this Config fails to
            # read it. I have no idea why.
            f.readlines()
            self.config = tools.Config(f.name)

    #===========================================================================

    def tearDown(self):
        # Restore stdout
        sys.stdout = self.held

    #===========================================================================
    # TESTS
    #===========================================================================

    def testBDSupToSub(self):
        """Tests that BDSupTOSub path was read correctly"""
        self.assertEqual(
            self.sup2Sub,
            self.config.sup2Sub
        )

    #===========================================================================

    def testHandbrakeCLI(self):
        """Tests that Handbrake path was read correctly"""
        self.assertEqual(
            self.handBrake,
            self.config.handBrake
        )

    #===========================================================================

    def testJava(self):
        """Tests that the Java path was read correctly"""
        self.assertEqual(
            self.java,
            self.config.java
        )

    #===========================================================================

    def testMkvExtract(self):
        """Tests that the mkvExtract path was read correctly"""
        self.assertEqual(
            self.mkvExtract,
            self.config.mkvExtract
        )

    #===========================================================================

    def testMkvMerge(self):
        """Tests that the mkvMerge path was read correctly"""
        self.assertEqual(
            self.mkvMerge,
            self.config.mkvMerge
        )

    #===========================================================================

    def testAnimationBFrames(self):
        """Tests that the animation bframes setting was read correctly"""
        self.assertEqual(
            self.bFrames,
            self.config.bFrames
        )

    #===========================================================================

    def testAudioFallback(self):
        """Tests that the audio fallback setting was read correctly"""
        self.assertEqual(
            self.audioFallback,
            self.config.audioFallback
        )

    #===========================================================================

    def testLanguage(self):
        """Tests that the language setting was read correctly"""
        self.assertEqual(
            self.language,
            self.config.language
        )

    #===========================================================================

    def testSorting(self):
        """Tests that the sorting setting was read correctly"""
        self.assertEqual(
            self.sorting,
            self.config.sorting
        )

    #===========================================================================

    def testSortingReverse(self):
        """Tests that the reverse sorting setting was read correctly"""
        self.assertEqual(
            self.sortingReverse,
            self.config.sortingReverse
        )

    #===========================================================================

    def testX264Speed(self):
        """Tests that the x264 Speed setting was read correctly"""
        self.assertEqual(
            self.x264Speed,
            self.config.x264Speed
        )

    #===========================================================================

    def testQualityDictinary(self):
        """Tests that the quality dictionary was read correctly"""
        for qual in ['bq', 'hq', 'uq']:
            for res in ['1080', '720', '480']:
                self.assertEqual(
                    self.quality[qual][res],
                    self.config.quality[qual][res]
                )

#===============================================================================
# PRIVATE FUNCTIONS
#===============================================================================

def _fillConfig(config):
    """Fills a config file and returns the formatted string"""
    configFile = CONFIG_STRUCTURE.format(
        sup2Sub=config.sup2Sub,
        handBrake=config.handBrake,
        java=config.java,
        mkvExtract=config.mkvExtract,
        mkvMerge=config.mkvMerge,
        bFrames=config.bFrames,
        audioFallback=config.audioFallback,
        language=config.language,
        sorting=config.sorting,
        sortingReverse=config.sortingReverse,
        x264Speed=config.x264Speed,
        bq1080=config.quality['bq']['1080'],
        bq720=config.quality['bq']['720'],
        bq480=config.quality['bq']['480'],
        hq1080=config.quality['hq']['1080'],
        hq720=config.quality['hq']['720'],
        hq480=config.quality['hq']['480'],
        uq1080=config.quality['uq']['1080'],
        uq720=config.quality['uq']['720'],
        uq480=config.quality['uq']['480'],
    )

    return configFile

#===============================================================================
# FUNCTIONS
#===============================================================================

if __name__ == '__main__':
    unittest.main()