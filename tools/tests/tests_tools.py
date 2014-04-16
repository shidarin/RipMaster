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
import subprocess
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

# Config =======================================================================

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

# mkvInfo() ====================================================================

# Most of these are from http://www.auby.no/files/video_tests/
# Which has a collection of mkv files with settings noted.
# Up is a recompress of a bluray rip

# Direct bluray remux
# Planet Earth 'Fresh Water' clip
# No audio or subtitles
MKVINFO_BIRDS = """File '/Users/sean/Downloads/birds.mkv': container: Matroska [duration:23064745313 is_providing_timecodes:1]
Track ID 0: video (V_MPEG4/ISO/AVC) [number:1 uid:1 codec_id:V_MPEG4/ISO/AVC codec_private_length:40 codec_private_data:01640029ffe1001967640029ac34e501e0087b0110001974f004c4b408f183196001000468eebcb0 language:eng pixel_dimensions:1920x1072 display_dimensions:1920x1072 default_track:1 forced_track:0 enabled_track:1 packetizer:mpeg4_p10_video default_duration:41708400]
"""
# Horribly low video bitrate, mostly interesting for the double audio tracks
# Harry Potter 4?
# No subtitles
MKVINFO_HARRY_POTTER = """File '/Users/sean/Downloads/harrypotter.mkv': container: Matroska [title:Harry\sPotter\s4[Eng-Hindi]Dual.Audio\sBRRIP\s720p-=[champ_is_here]=- duration:57605000000 segment_uid:ad577ea53da9f80b8647220b4c737914 is_providing_timecodes:1]
Track ID 0: video (V_MPEG4/ISO/AVC) [number:1 uid:576199555 codec_id:V_MPEG4/ISO/AVC codec_private_length:41 codec_private_data:0164001fffe100196764001fac34e6014010ec04400065d3c01312d023c60c668001000568eeb2c8b0 language:eng track_name:-=[champ_is_here]=- pixel_dimensions:1280x528 display_dimensions:1280x528 default_track:0 forced_track:0 enabled_track:1 packetizer:mpeg4_p10_video default_duration:40001876 content_encoding_algorithms:3]
Track ID 1: audio (A_AAC) [number:2 uid:925045919 codec_id:A_AAC codec_private_length:7 codec_private_data:131056e59d4800 language:eng track_name:-=[champ_is_here]=- default_track:0 forced_track:0 enabled_track:1 default_duration:42666666 audio_sampling_frequency:24000 audio_channels:2]
Track ID 2: audio (A_MPEG/L3) [number:3 uid:3085470903 codec_id:A_MPEG/L3 codec_private_length:0 language:hin track_name:-=[champ_is_here]=- default_track:0 forced_track:0 enabled_track:1 default_duration:24000000 audio_sampling_frequency:48000 audio_channels:2 content_encoding_algorithms:3]
"""

# Direct hddvd remux
# HDDVD Sampler Trailer
MKVINFO_HDDVD = """File '/Users/sean/Downloads/hddvd.mkv': container: Matroska [duration:121897000000 segment_uid:987a9f2ff86231d08e8e7b04974f51d7 is_providing_timecodes:1]
Track ID 0: video (V_MS/VFW/FOURCC, WVC1) [number:1 uid:1 codec_id:V_MS/VFW/FOURCC codec_private_length:77 codec_private_data:4d000000800700003804000001001800575643310000000001000000010000000000000000000000240000010fdbfe3bf21bca3bf886f180ca02020309a5b8d707fc0000010e5ac7fcefc86c40 language:eng track_name:1080p\sVC-1 pixel_dimensions:1920x1080 display_dimensions:1920x1080 default_track:1 forced_track:0 enabled_track:1]
Track ID 1: audio (A_AC3) [number:2 uid:418009001 codec_id:A_AC3 codec_private_length:0 language:eng track_name:Dolby\sDigital\s2.0\s640kbps default_track:1 forced_track:0 enabled_track:1 default_duration:32000000 audio_sampling_frequency:48000 audio_channels:2]
Track ID 2: audio (A_EAC3) [number:3 uid:2 codec_id:A_EAC3 codec_private_length:0 language:eng track_name:Dolby\sDigital\sPlus\s5.1\s640kbps default_track:0 forced_track:0 enabled_track:1 audio_sampling_frequency:48000 audio_channels:6]
"""

# Good ol' xvid with slightly newer aac
# Matrix 2 Trailer
# codec_private_data has been truncated for Matrix subtitles
MKVINFO_MATRIX = """File '/Users/sean/Downloads/matrix.mkv': container: Matroska [duration:151458000000 segment_uid:b1a7f34114a6037281d087758c7756bb is_providing_timecodes:1]
Track ID 0: video (V_MS/VFW/FOURCC, XVID) [number:1 uid:2738550924 codec_id:V_MS/VFW/FOURCC codec_private_length:40 codec_private_data:28000000800200005a01000001000c00585649440046140000000000000000000000000000000000 language:eng track_name:Matrix\sReloaded\sTrailer\sXviD\s1.0\sBeta1 pixel_dimensions:640x346 display_dimensions:640x346 default_track:0 forced_track:0 enabled_track:1 default_duration:41666663]
Track ID 1: audio (A_AAC) [number:2 uid:1982383230 codec_id:A_AAC codec_private_length:5 codec_private_data:139056e5a0 language:eng track_name:HE-AAC\s50-70 default_track:0 forced_track:0 enabled_track:1 default_duration:46439909 audio_sampling_frequency:22050 audio_channels:2]
Track ID 2: subtitles (S_TEXT/UTF8) [number:3 uid:3270128816 codec_id:S_TEXT/UTF8 codec_private_length:0 language:ara track_name:Arabic default_track:0 forced_track:0 enabled_track:1]
Track ID 3: subtitles (S_TEXT/SSA) [number:4 uid:3563875756 codec_id:S_TEXT/SSA codec_private_length:796 codec_private_data:5b536hjkj language:cat track_name:Catalan default_track:0 forced_track:0 enabled_track:1]
Track ID 4: subtitles (S_TEXT/SSA) [number:5 uid:2003350774 codec_id:S_TEXT/SSA codec_private_length:783 codec_private_data:5b5363726 language:dut track_name:Dutch default_track:0 forced_track:0 enabled_track:1]
Track ID 5: subtitles (S_TEXT/SSA) [number:6 uid:2619120828 codec_id:S_TEXT/SSA codec_private_length:783 codec_private_data:5b5363726 language:eng track_name:English default_track:0 forced_track:0 enabled_track:1]
Track ID 6: subtitles (S_TEXT/SSA) [number:7 uid:2674700248 codec_id:S_TEXT/SSA codec_private_length:783 codec_private_data:5b5363726 language:fin track_name:Finnish default_track:0 forced_track:0 enabled_track:1]
Track ID 7: subtitles (S_TEXT/SSA) [number:8 uid:1203285810 codec_id:S_TEXT/SSA codec_private_length:783 codec_private_data:5b5363726 language:fre track_name:French default_track:0 forced_track:0 enabled_track:1]
Track ID 8: subtitles (S_TEXT/SSA) [number:9 uid:1639611508 codec_id:S_TEXT/SSA codec_private_length:783 codec_private_data:5b5363726 language:ger track_name:German default_track:0 forced_track:0 enabled_track:1]
Track ID 9: subtitles (S_TEXT/UTF8) [number:10 uid:3466603604 codec_id:S_TEXT/UTF8 codec_private_length:0 language:jpn track_name:Japanese default_track:0 forced_track:0 enabled_track:1]
Track ID 10: subtitles (S_TEXT/SSA) [number:11 uid:3705802066 codec_id:S_TEXT/SSA codec_private_length:783 codec_private_data:5b5363726 language:por track_name:Portuguese default_track:0 forced_track:0 enabled_track:1]
Track ID 11: subtitles (S_TEXT/SSA) [number:12 uid:301356576 codec_id:S_TEXT/SSA codec_private_length:783 codec_private_data:5b5363726 language:slv track_name:Slovenian default_track:0 forced_track:0 enabled_track:1]
Track ID 12: subtitles (S_TEXT/SSA) [number:13 uid:995510696 codec_id:S_TEXT/SSA codec_private_length:783 codec_private_data:5b5363726 language:spa track_name:Spanish default_track:0 forced_track:0 enabled_track:1]
Attachment ID 1: type 'image/jpeg', size 50436 bytes, description 'Cover', file name 'reloaded.jpg'
"""

# Typical recompressed 1080p
# Monster's Inc
# Unstyled Subs
MKVINFO_MONSTERS = """File '/Users/sean/Downloads/monsters.mkv': container: Matroska [duration:60146000000 segment_uid:a2aa8aa73f85cd5eb3fef28b9cfa9dec is_providing_timecodes:1]
Track ID 0: video (V_MPEG4/ISO/AVC) [number:1 uid:1 codec_id:V_MPEG4/ISO/AVC codec_private_length:42 codec_private_data:01640029ffe1001a67640029ac72100780227e5c04400065d3c01312d023c60c648001000568eeb2c8b0 language:eng pixel_dimensions:1920x1080 display_dimensions:1920x1080 default_track:1 forced_track:0 enabled_track:1 packetizer:mpeg4_p10_video default_duration:41708398]
Track ID 1: audio (A_DTS) [number:2 uid:1500554119 codec_id:A_DTS codec_private_length:0 language:eng default_track:1 forced_track:0 enabled_track:1 audio_sampling_frequency:48000 audio_channels:6]
Track ID 2: subtitles (S_TEXT/UTF8) [number:3 uid:1823251899 codec_id:S_TEXT/UTF8 codec_private_length:0 language:eng default_track:1 forced_track:0 enabled_track:1]
"""

# Planet remuxed into mp4
# Planet Earth 'Pole to Pole'
MKVINFO_PLANET_MP4 = """File '/Users/sean/Downloads/planet.mp4': container: QuickTime/MP4 [is_providing_timecodes:1]
Track ID 0: video (avc1) [packetizer:mpeg4_p10_video language:und]
Track ID 1: audio (ac-3) [language:und]
"""

# Typical recompressed 720p
# Planet Earth 'Pole to Pole'
# codec_private_data has been truncated for Planet subtitles and video track
MKVINFO_PLANET_MKV = """File '/Users/sean/Downloads/planet.mkv': container: Matroska [title:Planet.Earth.EP01.From.Pole.to.Pole.2006.720p.HDDVD.x264-ESiR duration:112832000000 segment_uid:9dfdf4d61d9a001c824ed959632725a4 is_providing_timecodes:1]
Track ID 0: video (V_MPEG4/ISO/AVC) [number:1 uid:1 codec_id:V_MPEG4/ISO/AVC codec_private_length:167 codec_private_data:01640033ffe1001867 language:eng track_name:Planet\sEarth\s-\sEP01\s-\sFrom\sPole\sto\sPole pixel_dimensions:1280x720 display_dimensions:1280x720 default_track:1 forced_track:0 enabled_track:1 packetizer:mpeg4_p10_video default_duration:41708398 content_encoding_algorithms:3]
Track ID 1: audio (A_AC3) [number:2 uid:1935087543 codec_id:A_AC3 codec_private_length:0 language:eng track_name:AC3\s5.1 default_track:1 forced_track:0 enabled_track:1 default_duration:32000000 audio_sampling_frequency:48000 audio_channels:6 content_encoding_algorithms:3]
Track ID 2: subtitles (S_TEXT/ASS) [number:3 uid:2745533361 codec_id:S_TEXT/ASS codec_private_length:804 codec_private_data:5b5360a0d0a language:eng default_track:1 forced_track:0 enabled_track:1]
Track ID 3: subtitles (S_TEXT/ASS) [number:4 uid:784888213 codec_id:S_TEXT/ASS codec_private_length:841 codec_private_data:5b5360a0d0a language:rum default_track:0 forced_track:0 enabled_track:1]
Attachment ID 1: type 'application/x-truetype-font', size 64352 bytes, file name 'exprswy_free.ttf'
Attachment ID 2: type 'application/x-truetype-font', size 135984 bytes, file name 'Framd.TTF'
"""

# Common h264 web container and settings
# Duke Nukem Forever Trailer
MKVINFO_SHRINKAGE_MP4 = """File '/Users/sean/Downloads/shrinkage.mp4': container: QuickTime/MP4 [is_providing_timecodes:1]
Track ID 0: video (avc1) [packetizer:mpeg4_p10_video]
Track ID 1: audio (mp4a)
"""

# Shrinkage remuxed into mkv
# Duke Nukem Forever Trailer
MKVINFO_SHRINKAGE_MKV = """File '/Users/sean/Downloads/shrinkage.mkv': container: Matroska [duration:70036000000 segment_uid:9012b88e3ae8545399260c3c1a4ff087 is_providing_timecodes:1]
Track ID 0: video (V_MPEG4/ISO/AVC) [number:1 uid:3769869216 codec_id:V_MPEG4/ISO/AVC codec_private_length:48 codec_private_data:014d401fffe10021674d401f967602802dd80a0400002ef0000afc80d18006ad002ac5ef7c1e1108dc01000468fe3c80 language:und pixel_dimensions:1280x720 display_dimensions:1280x720 default_track:1 forced_track:0 enabled_track:1 packetizer:mpeg4_p10_video default_duration:33382294 content_encoding_algorithms:3]
Track ID 1: audio (A_AAC) [number:2 uid:1132748215 codec_id:A_AAC codec_private_length:2 codec_private_data:1210 language:und default_track:1 forced_track:0 enabled_track:1 default_duration:23219954 audio_sampling_frequency:44100 audio_channels:2]
"""

# Common anime combination of h264 and vorbis
# Some anime
# Styled and unstyled subs
# codec_private_data has been truncated for Suzimiya subtitles
MKVINFO_SUZIMIYA = """File '/Users/sean/Downloads/suzimiya.mkv': container: Matroska [title:The\sMelancholy\sof\sHaruhi\sSuzumiya\c\sSpecial\sEnding duration:71972000000 segment_uid:8a794570c6caa8798bcda561b0d29ed0 is_providing_timecodes:1]
Track ID 0: video (V_MPEG4/ISO/AVC) [number:1 uid:1 codec_id:V_MPEG4/ISO/AVC codec_private_length:40 codec_private_data:01640033ffe1001967640033ac34e300b03da1000800000301df851e8f18318c8001000468eebcb0 language:jpn track_name:The\sMelancholy\sof\sHaruhi\sSuzumiya\c\sSpecial\sEnding pixel_dimensions:704x480 display_dimensions:853x480 default_track:1 forced_track:0 enabled_track:1 packetizer:mpeg4_p10_video default_duration:41708375]
Track ID 1: audio (A_VORBIS) [number:2 uid:3442966448 codec_id:A_VORBIS codec_private_length:4412 codec_private_data:020808 language:jpn track_name:2ch\sVorbis default_track:1 forced_track:0 enabled_track:1 audio_sampling_frequency:48000 audio_channels:2]
Track ID 2: subtitles (S_TEXT/ASS) [number:3 uid:1455485350 codec_id:S_TEXT/ASS codec_private_length:6681 codec_private_data:5b5 language:eng track_name:Styled\sASS default_track:1 forced_track:0 enabled_track:1]
Track ID 3: subtitles (S_TEXT/ASS) [number:4 uid:1197227420 codec_id:S_TEXT/ASS codec_private_length:5796 codec_private_data:5ba0d0a language:eng track_name:Styled\sASS\s(Simple) default_track:0 forced_track:0 enabled_track:1]
Track ID 4: subtitles (S_TEXT/UTF8) [number:5 uid:1212881333 codec_id:S_TEXT/UTF8 codec_private_length:0 language:eng track_name:Plain\sSRT default_track:0 forced_track:0 enabled_track:1]
Attachment ID 1: type 'application/x-truetype-font', size 66844 bytes, file name 'GosmickSansBold.ttf'
Attachment ID 2: type 'application/x-truetype-font', size 158380 bytes, file name 'epmgobld_ending.ttf'
"""

# Rip using ripmaster, renecoded with handbrake. Bluray audio preserved.
# Up
# codec_private_data has been truncated for Up subtitles
MKVINFO_UP = """File '/Users/sean/Downloads/Up.mkv': container: Matroska [duration:5767563000000 segment_uid:8e3ddb4566e67afca3142a25835e9c1d is_providing_timecodes:1]
Track ID 0: video (V_MPEG4/ISO/AVC) [number:1 uid:1493619965 codec_id:V_MPEG4/ISO/AVC codec_private_length:44 codec_private_data:014d4028ffe1001c674d4028eca03c0113f2e02d4040405000003e90000bb808f183196001000568ef823c80 language:eng pixel_dimensions:1920x1080 display_dimensions:1920x1080 default_track:1 forced_track:0 enabled_track:1 packetizer:mpeg4_p10_video default_duration:41708332 content_encoding_algorithms:3]
Track ID 1: audio (A_DTS) [number:2 uid:1095497111 codec_id:A_DTS codec_private_length:0 language:eng default_track:1 forced_track:0 enabled_track:1 default_duration:10666666 audio_sampling_frequency:48000 audio_channels:6 content_encoding_algorithms:3]
Track ID 2: audio (A_DTS) [number:3 uid:1518318168 codec_id:A_DTS codec_private_length:0 language:eng default_track:0 forced_track:0 enabled_track:1 default_duration:10666666 audio_sampling_frequency:48000 audio_channels:6 content_encoding_algorithms:3]
Track ID 3: subtitles (S_VOBSUB) [number:4 uid:2154180997 codec_id:S_VOBSUB codec_private_length:348 codec_private_data:73693630a language:eng default_track:0 forced_track:0 enabled_track:1 content_encoding_algorithms:0]
Chapters: 35 entries
"""

#===============================================================================
# CLASSES
#===============================================================================

# Mock Objects =================================================================

class MockMovie(object):
    def __init__(self, fakePath):
        self._path = fakePath

    @property
    def path(self):
        return self._path

# _trackInfo() =================================================================

class TestTrackInfo(unittest.TestCase):
    """Tests the private function _trackInfo for correct handling of tracks"""

    #===========================================================================
    # TESTS
    #===========================================================================

    def testBadLine(self):
        """Line that doesn't start with Track ID raises ValueError"""

        self.assertRaises(
            ValueError,
            tools._trackInfo,
            'not a real line'
        )

    #===========================================================================

    def testBadTrackType(self):
        """If a line is a Track with an ID but not a known track type"""

        self.assertRaises(
            ValueError,
            tools._trackInfo,
            'Track ID 5: telepathic (junk for the rest'
        )

    #===========================================================================

    def testSingleDigitTrackID(self):
        """Tests that track ID is derived correctly for single digit ints"""

        trackLine = _buildTrackLine(5, 'video', {'hello': 'goodbye'})

        trackID, trackType, trackDict = tools._trackInfo(trackLine)

        self.assertEqual(
            5,
            trackID
        )

    #===========================================================================

    def testDoubleDigitTrackID(self):
        """Tests that track ID is derived correctly for double digit ints"""

        trackLine = _buildTrackLine(43, 'video', {'hello': 'goodbye'})

        trackID, trackType, trackDict = tools._trackInfo(trackLine)

        self.assertEqual(
            43,
            trackID
        )

    #===========================================================================

    def testTripleDigitTrackID(self):
        """Tests that track ID is derived correctly for triple digit ints"""

        trackLine = _buildTrackLine(989, 'video', {'hello': 'goodbye'})

        trackID, trackType, trackDict = tools._trackInfo(trackLine)

        self.assertEqual(
            989,
            trackID
        )

    #===========================================================================

    def testVideoTrackType(self):
        """Tests that track type is derived correctly for video"""

        trackLine = _buildTrackLine(0, 'video', {'hello': 'goodbye'})

        trackID, trackType, trackDict = tools._trackInfo(trackLine)

        self.assertEqual(
            'video',
            trackType,
        )

    #===========================================================================

    def testAudioTrackType(self):
        """Tests that track type is derived correctly for audio"""

        trackLine = _buildTrackLine(23, 'audio', {'hello': 'goodbye'})

        trackID, trackType, trackDict = tools._trackInfo(trackLine)

        self.assertEqual(
            'audio',
            trackType,
        )

    #===========================================================================

    def testVideoTrackType(self):
        """Tests that track type is derived correctly for video"""

        trackLine = _buildTrackLine(967, 'subtitles', {'hello': 'goodbye'})

        trackID, trackType, trackDict = tools._trackInfo(trackLine)

        self.assertEqual(
            'subtitles',
            trackType,
        )

    #===========================================================================

    def testNoDefaultTrack(self):
        """Tests that a default_track key is added to the dictionary"""

        trackLine = _buildTrackLine(0, 'video', {'hello': 'goodbye'})

        trackID, trackType, trackDict = tools._trackInfo(trackLine)

        self.assertTrue(
            'default_track' in trackDict.keys()
        )

        self.assertEqual(
            trackDict['default_track'],
            '0'
        )

    #===========================================================================

    def testNoForcedTrack(self):
        """Tests that a forced_track key is added to the dictionary"""

        trackLine = _buildTrackLine(20, 'audio', {'hello': 'goodbye'})

        trackID, trackType, trackDict = tools._trackInfo(trackLine)

        self.assertTrue(
            'forced_track' in trackDict.keys()
        )

        self.assertEqual(
            trackDict['forced_track'],
            '0'
        )

    #===========================================================================

    def testNoLanguage(self):
        """Tests that a language key is added to the dictionary"""

        trackLine = _buildTrackLine(0, 'video', {'hello': 'goodbye'})

        trackID, trackType, trackDict = tools._trackInfo(trackLine)

        self.assertTrue(
            'language' in trackDict.keys()
        )

        self.assertEqual(
            trackDict['language'],
            'eng'
        )

    #===========================================================================

    def testDefaultTrackTrue(self):
        """Tests that a default_track value of 1 is kept"""

        trackLine = _buildTrackLine(0, 'video',
                                    {'hello': 'goodbye', 'default_track': '1'})

        trackID, trackType, trackDict = tools._trackInfo(trackLine)

        self.assertTrue(
            'default_track' in trackDict.keys()
        )

        self.assertEqual(
            trackDict['default_track'],
            '1'
        )

    #===========================================================================

    def testForcedTrackTrue(self):
        """Tests that a forced_track value of 1 is kept"""

        trackLine = _buildTrackLine(20, 'audio',
                                    {'hello': 'goodbye', 'forced_track': '1'})

        trackID, trackType, trackDict = tools._trackInfo(trackLine)

        self.assertTrue(
            'forced_track' in trackDict.keys()
        )

        self.assertEqual(
            trackDict['forced_track'],
            '1'
        )

    #===========================================================================

    def testEngLanguage(self):
        """Tests that a language value other than 'eng' is kept"""

        trackLine = _buildTrackLine(0, 'video',
                                    {'hello': 'goodbye', 'language': 'ger'})

        trackID, trackType, trackDict = tools._trackInfo(trackLine)

        self.assertTrue(
            'language' in trackDict.keys()
        )

        self.assertEqual(
            trackDict['language'],
            'ger'
        )

    #===========================================================================

    def testTrackDict1(self):
        """Tests that track dict is derived correctly"""

        goodTrackDict = {
            "number": "1", "uid": "1493619965",
            "codec_id": "V_MPEG4/ISO/AVC", "codec_private_length": "44",
            "codec_private_data": "014d4028ffe1001c80", "language": "eng",
            "pixel_dimensions": "1920x1080", "display_dimensions": "1920x1080",
            "default_track": "1", "forced_track": "0", "enabled_track": "1",
            "packetizer": "mpeg4_p10_video", "default_duration": "41708332",
            "content_encoding_algorithms": "3"
        }

        trackLine = _buildTrackLine(0, 'video', goodTrackDict)

        trackID, trackType, trackDict = tools._trackInfo(trackLine)

        self.assertEqual(
            goodTrackDict,
            trackDict
        )

    #===========================================================================

    def testTrackDict2(self):
        """Tests that track dict is derived correctly"""

        goodTrackDict = {
            "number": "2", "uid": "3442966448", "codec_id": "A_VORBIS",
            "codec_private_length": "4412", "codec_private_data": "020808",
            "language": "jpn", "track_name": "2ch\\sVorbis",
            "default_track": "1", "forced_track": "0", "enabled_track": "1",
            "audio_sampling_frequency": "48000", "audio_channels": "2"
        }

        trackLine = _buildTrackLine(1, 'audio', goodTrackDict)

        trackID, trackType, trackDict = tools._trackInfo(trackLine)

        self.assertEqual(
            goodTrackDict,
            trackDict
        )

    #===========================================================================

    def testTrackDict3(self):
        """Tests that track dict is derived correctly"""

        goodTrackDict = {
            "number": "12", "uid": "301356576", "codec_id": "S_TEXT/SSA",
            "codec_private_length": "783", "codec_private_data": "5b5363726",
            "language": "slv", "track_name": "Slovenian", "default_track": "0",
            "forced_track": "0", "enabled_track": "1"
        }

        trackLine = _buildTrackLine(11, 'subtitles', goodTrackDict)

        trackID, trackType, trackDict = tools._trackInfo(trackLine)

        self.assertEqual(
            goodTrackDict,
            trackDict
        )

# Config =======================================================================

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

# mkvInfo() ====================================================================

class TestMkvInfoBasic(unittest.TestCase):
    """Tests basic mkvInfo functionality"""

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

    @mock.patch('tools.PIPE')
    @mock.patch('tools.Popen')
    def testPopenCalledCorrectly(self, mockPopen, mockPIPE):
        """Tests that Popen was called correctly"""
        mockPopen.stdout.return_value = StringIO()
        mockPIPE.return_value = StringIO()

        fakeMoviePath = '/the/best/fake/path.mkv'

        movie = MockMovie(fakeMoviePath)

        tools.mkvInfo(movie)

        mockPopen.assert_called_once_with(
            [self.mkvMerge, '-I', fakeMoviePath],
            shell=True,
            stdout=mockPIPE
        )

#===============================================================================
# PRIVATE FUNCTIONS
#===============================================================================

def _buildTrackLine(id, trackType, trackDict):
    """Builds a mkvMerge -I style track ID line from inputs"""
    # Our goal is to construct this:
    # Track ID 0: video (V_MPEG4/ISO/AVC) [number:1 uid:1493619965 codec_id:V_MPEG4/ISO/AVC language:eng pixel_dimensions:1920x1080 display_dimensions:1920x1080 default_track:1 forced_track:0 enabled_track:1 packetizer:mpeg4_p10_video default_duration:41708332 content_encoding_algorithms:3]
    # From just the id, type and dict. We don't actually care about the codec

    # We need to go from:
    # {'okay': 'then', 'hello': 'goodbye'}
    # To:
    # [okay:then hello:goodbye]
    trackDict = str(trackDict)
    trackDict = trackDict[1:-1]  # Remove {}
    trackDict = trackDict.replace("'", '')
    trackDict = trackDict.replace(': ', ':')
    trackDict = trackDict.replace(',', '')
    trackDict = '[{trackDict}]'.format(trackDict=trackDict)

    trackLine = "Track ID {id}: {trackType} (AWESOME) {trackDict}\r\n".format(
        id=id,
        trackType=trackType,
        trackDict=trackDict
    )

    return trackLine

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