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

CONFIG_STRUCTURE_BARE = """[Programs]
BDSupToSub: {sup2Sub}
HandbrakeCLI: {handBrake}
Java: {java}
mkvExtract: {mkvExtract}
mkvMerge: {mkvMerge}
"""

CONFIG_NO_PROGRAMS = """[Handbrake Settings]
animation_BFrames: 8
audio_Fallback: ffac3
language: English
sorting: alphabetical
sorting_Reverse: no
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

        self.bFrames = '8'
        self.audioFallback = 'ffac3'
        self.language = 'English'
        self.sorting = 'alphabetical'
        self.sortingReverse = 'no'
        self.x264Speed = 'slow'

        self.quality = {
            'uq': {'1080': '20', '720': '19', '480': '16'},
            'hq': {'1080': '20', '720': '19', '480': '16'},
            'bq': {'1080': '20', '720': '19', '480': '16'}
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
        try:
            bFramesValue = int(self.bFrames)
        except ValueError:
            self.assertNotEqual(
                self.bFrames,
                self.config.bFrames
            )
            self.assertEqual(
                None,
                self.config.bFrames
            )
        else:
            self.assertEqual(
                bFramesValue,
                self.config.bFrames
            )

    #===========================================================================

    def testAudioFallback(self):
        """Tests that the audio fallback setting was read correctly"""
        if self.audioFallback in tools.AUDIO_FALLBACKS:
            self.assertEqual(
                self.audioFallback,
                self.config.audioFallback
            )
        else:
            self.assertNotEqual(
                self.audioFallback,
                self.config.audioFallback
            )
            self.assertEqual(
                tools.AUDIO_FALLBACK_DEFAULT,
                self.config.audioFallback
            )

    #===========================================================================

    def testLanguage(self):
        """Tests that the language setting was read correctly"""
        if self.language in tools.LANGUAGES:
            self.assertEqual(
                self.language,
                self.config.language
            )
        else:
            self.assertNotEqual(
                self.language,
                self.config.language
            )
            self.assertEqual(
                tools.LANGUAGE_DEFAULT,
                self.config.language
            )

    #===========================================================================

    def testSorting(self):
        """Tests that the sorting setting was read correctly"""
        if self.sorting in tools.SORTINGS:
            self.assertEqual(
                self.sorting,
                self.config.sorting
            )
        else:
            self.assertNotEqual(
                self.sorting,
                self.config.sorting
            )
            self.assertEqual(
                tools.SORTING_DEFAULT,
                self.config.sorting
            )

    #===========================================================================

    def testSortingReverse(self):
        """Tests that the reverse sorting setting was read correctly"""
        if self.sortingReverse.lower() in ["1", "yes", "true", "on"]:
            self.assertTrue(
                self.config.sortingReverse
            )
        elif self.sortingReverse.lower() in ["0", "no", "false", "off"]:
            self.assertFalse(
                self.config.sortingReverse
            )
        else:
            self.assertEqual(
                tools.SORTING_REVERSE_DEFAULT,
                self.config.sortingReverse
            )

    #===========================================================================

    def testX264Speed(self):
        """Tests that the x264 Speed setting was read correctly"""
        if self.x264Speed in tools.X264_SPEEDS:
            self.assertEqual(
                self.x264Speed,
                self.config.x264Speed
            )
        else:
            self.assertNotEqual(
                self.x264Speed,
                self.config.x264Speed
            )
            self.assertEqual(
                tools.X264_SPEED_DEFAULT,
                self.config.x264Speed
            )

    #===========================================================================

    def testQualityDictinary(self):
        """Tests that the quality dictionary was read correctly"""
        for qual in ['bq', 'hq', 'uq']:
            for res in ['1080', '720', '480']:
                try:
                    int(self.quality[qual][res])
                except ValueError:
                    self.assertNotEqual(
                        self.quality[qual][res],
                        self.config.quality[qual][res]
                    )
                    self.assertEqual(
                        tools.QUALITY_DEFAULT,
                        self.config.quality[qual][res]
                    )
                else:
                    self.assertEqual(
                        int(self.quality[qual][res]),
                        self.config.quality[qual][res]
                    )

#===============================================================================

class TestNonStandardConfigSetup(TestStandardConfigSetup):
    """Tests a varied, but still valid, config"""

    #===========================================================================
    # SETUP & TEARDOWN
    #===========================================================================

    def setUp(self):

        # Suppress stdout
        self.held = sys.stdout
        sys.stdout = StringIO()

        # Build out custom ini file
        self.sup2Sub = "/usr/apps/bin/mkvTools/BDSup2Sub.jar"
        self.handBrake = "/usr/apps/Handbrake/HandBrakeCLI"
        self.java = "/usr/apps/Java/jre7/bin/java"
        self.mkvExtract = "/usr/apps/bin/mkvTools/mkvextract"
        self.mkvMerge = "/usr/apps/bin/mkvTools/mkvmerge"

        self.bFrames = '30'
        self.audioFallback = 'faac'
        self.language = 'English'
        self.sorting = 'quality'
        self.sortingReverse = '1'
        self.x264Speed = 'ultrafast'

        self.quality = {
            'uq': {'1080': '24', '720': '18', '480': '34'},
            'hq': {'1080': '22', '720': '24', '480': '50'},
            'bq': {'1080': '18', '720': '36', '480': '79'}
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

#===============================================================================

class TestNonStandardConfigSetupB(TestStandardConfigSetup):
    """Tests a varied, but still valid, config"""

    #===========================================================================
    # SETUP & TEARDOWN
    #===========================================================================

    def setUp(self):

        # Suppress stdout
        self.held = sys.stdout
        sys.stdout = StringIO()

        # Build out custom ini file
        self.sup2Sub = r"Z:\\Program Files (x86)\MKVToolNix\BDSup2Sub.jar"
        self.handBrake = r"Z:\\Program Files\Handbrake\HandBrakeCLI.exe"
        self.java = r"Z:\\Program Files (x86)\Java\jre7\bin\java"
        self.mkvExtract = r"Z:\\Program Files (x86)\MKVToolNix\mkvextract.exe"
        self.mkvMerge = r"Z:\\Program Files (x86)\MKVToolNix\mkvmerge.exe"

        self.bFrames = '0'
        self.audioFallback = 'vorbis'
        self.language = 'English'
        self.sorting = 'resolution'
        self.sortingReverse = 'Yes'
        self.x264Speed = 'placebo'

        self.quality = {
            'uq': {'1080': '99', '720': '1', '480': '50'},
            'hq': {'1080': '98', '720': '2', '480': '25'},
            'bq': {'1080': '97', '720': '3', '480': '75'}
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

#===============================================================================

class TestBareConfigSetup(TestStandardConfigSetup):
    """Tests a minimal, but still valid, config"""

    #===========================================================================
    # SETUP & TEARDOWN
    #===========================================================================

    def setUp(self):

        # Suppress stdout
        self.held = sys.stdout
        sys.stdout = StringIO()

        # Build out custom ini file
        self.sup2Sub = "/usr/apps/bin/mkvTools/BDSup2Sub.jar"
        self.handBrake = "/usr/apps/Handbrake/HandBrakeCLI"
        self.java = "/usr/apps/Java/jre7/bin/java"
        self.mkvExtract = "/usr/apps/bin/mkvTools/mkvextract"
        self.mkvMerge = "/usr/apps/bin/mkvTools/mkvmerge"

        self.bFrames = ''
        self.audioFallback = ''
        self.language = ''
        self.sorting = ''
        self.sortingReverse = ''
        self.x264Speed = ''

        self.quality = {
            'uq': {'1080': '', '720': '', '480': ''},
            'hq': {'1080': '', '720': '', '480': ''},
            'bq': {'1080': '', '720': '', '480': ''}
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

#===============================================================================

class TestBadConfigSetup(TestStandardConfigSetup):
    """Tests a config with bad optional values"""

    #===========================================================================
    # SETUP & TEARDOWN
    #===========================================================================

    def setUp(self):

        # Suppress stdout
        self.held = sys.stdout
        sys.stdout = StringIO()

        # Build out custom ini file
        self.sup2Sub = "/usr/apps/bin/mkvTools/BDSup2Sub.jar"
        self.handBrake = "/usr/apps/Handbrake/HandBrakeCLI"
        self.java = "/usr/apps/Java/jre7/bin/java"
        self.mkvExtract = "/usr/apps/bin/mkvTools/mkvextract"
        self.mkvMerge = "/usr/apps/bin/mkvTools/mkvmerge"

        self.bFrames = 'banana'
        self.audioFallback = 'mp3'
        self.language = 'Pastafarian'
        self.sorting = 'rating'
        self.sortingReverse = 'dunno'
        self.x264Speed = 'asap'

        self.quality = {
            'uq': {'1080': 'goodest', '720': 'farier', '480': 'poor'},
            'hq': {'1080': 'gooder', '720': 'fair', '480': 'trash'},
            'bq': {'1080': 'good', '720': 'ok', '480': 'garbage'}
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

#===============================================================================

class TestMissingRequirementsConfig(unittest.TestCase):
    """Tests a config read with a missing option or section or even no config"""

    #===========================================================================
    # SETUP & TEARDOWN
    #===========================================================================

    def setUp(self):

        # Suppress stdout
        self.held = sys.stdout
        sys.stdout = StringIO()

    #===========================================================================

    def tearDown(self):
        # Restore stdout
        sys.stdout = self.held

    #===========================================================================
    # TESTS
    #===========================================================================

    def testNoSup2SubOptionError(self):
        """Tests that a NoOptionError becomes a ValueError"""

        # Build out custom ini file
        self.sup2Sub = ""
        self.handBrake = "/usr/apps/Handbrake/HandBrakeCLI"
        self.java = "/usr/apps/Java/jre7/bin/java"
        self.mkvExtract = "/usr/apps/bin/mkvTools/mkvextract"
        self.mkvMerge = "/usr/apps/bin/mkvTools/mkvMerge"

        # Get our formatted ini file
        self.configFile = _fillConfig(self, bare=True)

        # Build our config
        with tempfile.NamedTemporaryFile(mode='r+b') as f:
            f.write(self.configFile)
            # Calling readlines on the temp file. Without this Config fails to
            # read it. I have no idea why.
            f.readlines()
            self.assertRaises(
                ValueError,
                tools.Config,
                f.name
            )

    #===========================================================================

    def testNoHandbrakeOptionError(self):
        """Tests that a NoOptionError becomes a ValueError"""

        # Build out custom ini file
        self.sup2Sub = "/usr/apps/bin/mkvTools/BDSup2Sub.jar"
        self.handBrake = ""
        self.java = "/usr/apps/Java/jre7/bin/java"
        self.mkvExtract = "/usr/apps/bin/mkvTools/mkvextract"
        self.mkvMerge = "/usr/apps/bin/mkvTools/mkvMerge"

        # Get our formatted ini file
        self.configFile = _fillConfig(self, bare=True)

        # Build our config
        with tempfile.NamedTemporaryFile(mode='r+b') as f:
            f.write(self.configFile)
            # Calling readlines on the temp file. Without this Config fails to
            # read it. I have no idea why.
            f.readlines()
            self.assertRaises(
                ValueError,
                tools.Config,
                f.name
            )

    #===========================================================================

    def testNoJavaOptionError(self):
        """Tests that a NoOptionError becomes a ValueError"""

        # Build out custom ini file
        self.sup2Sub = "/usr/apps/bin/mkvTools/BDSup2Sub.jar"
        self.handBrake = "/usr/apps/Handbrake/HandBrakeCLI"
        self.java = ""
        self.mkvExtract = "/usr/apps/bin/mkvTools/mkvextract"
        self.mkvMerge = "/usr/apps/bin/mkvTools/mkvMerge"

        # Get our formatted ini file
        self.configFile = _fillConfig(self, bare=True)

        # Build our config
        with tempfile.NamedTemporaryFile(mode='r+b') as f:
            f.write(self.configFile)
            # Calling readlines on the temp file. Without this Config fails to
            # read it. I have no idea why.
            f.readlines()
            self.assertRaises(
                ValueError,
                tools.Config,
                f.name
            )

    #===========================================================================

    def testNoMkvExtractOptionError(self):
        """Tests that a NoOptionError becomes a ValueError"""

        # Build out custom ini file
        self.sup2Sub = "/usr/apps/bin/mkvTools/BDSup2Sub.jar"
        self.handBrake = "/usr/apps/Handbrake/HandBrakeCLI"
        self.java = "/usr/apps/Java/jre7/bin/java"
        self.mkvExtract = ""
        self.mkvMerge = "/usr/apps/bin/mkvTools/mkvMerge"

        # Get our formatted ini file
        self.configFile = _fillConfig(self, bare=True)

        # Build our config
        with tempfile.NamedTemporaryFile(mode='r+b') as f:
            f.write(self.configFile)
            # Calling readlines on the temp file. Without this Config fails to
            # read it. I have no idea why.
            f.readlines()
            self.assertRaises(
                ValueError,
                tools.Config,
                f.name
            )

    #===========================================================================

    def testNoMkvMergeOptionError(self):
        """Tests that a NoOptionError becomes a ValueError"""

        # Build out custom ini file
        self.sup2Sub = "/usr/apps/bin/mkvTools/BDSup2Sub.jar"
        self.handBrake = "/usr/apps/Handbrake/HandBrakeCLI"
        self.java = "/usr/apps/Java/jre7/bin/java"
        self.mkvExtract = "/usr/apps/bin/mkvTools/mkvextract"
        self.mkvMerge = ""

        # Get our formatted ini file
        self.configFile = _fillConfig(self, bare=True)

        # Build our config
        with tempfile.NamedTemporaryFile(mode='r+b') as f:
            f.write(self.configFile)
            # Calling readlines on the temp file. Without this Config fails to
            # read it. I have no idea why.
            f.readlines()
            self.assertRaises(
                ValueError,
                tools.Config,
                f.name
            )

    #===========================================================================

    def testNoPrograms(self):
        """Tests that a NoSectionError becomes a ValueError"""

        # Get our formatted ini file
        self.configFile = CONFIG_NO_PROGRAMS

        # Build our config
        with tempfile.NamedTemporaryFile(mode='r+b') as f:
            f.write(self.configFile)
            # Calling readlines on the temp file. Without this Config fails to
            # read it. I have no idea why.
            f.readlines()
            self.assertRaises(
                ValueError,
                tools.Config,
                f.name
            )

    #===========================================================================

    def testNoConfig(self):
        """Tests that a missing config file raises an IOError"""

        mockOpen = mock.mock_open()
        with mock.patch('__builtin__.open', mockOpen, create=True):
            self.assertRaises(
                IOError,
                tools.Config,
                'fakeIniFile.ini'
            )

            mockOpen.assert_called_once_with('fakeIniFile.ini', 'w')
            mockOpen().write.assert_called_once_with(tools.SAMPLE_CONFIG)

#===============================================================================
# PRIVATE FUNCTIONS
#===============================================================================

def _fillConfig(config, bare=False):
    """Fills a config file and returns the formatted string"""
    if not bare:
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
    else:
        configFile = CONFIG_STRUCTURE_BARE.format(
            sup2Sub=config.sup2Sub,
            handBrake=config.handBrake,
            java=config.java,
            mkvExtract=config.mkvExtract,
            mkvMerge=config.mkvMerge
        )

    return configFile

#===============================================================================
# FUNCTIONS
#===============================================================================

if __name__ == '__main__':
    unittest.main()