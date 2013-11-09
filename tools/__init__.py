#/usr/bin/python
# Ripmaster.tools
# Module containing tools used by Ripmaster
# By Sean Wallitsch, 2013/11/05

#===============================================================================
# IMPORTS
#===============================================================================

# Standard Imports
import os

#===============================================================================
# GLOBALS
#===============================================================================

RESOLUTIONS = [1080, 720, 480]
RESOLUTION_WIDTH = {1080: 1920, 720: 1280, 480: 720}
QUALITY = ['uq', 'hq', 'bq']
H264_PRESETS = ['animation', 'film', 'grain', 'PSNR', 'SSIM', 'Fast Decode']
FPS_PRESETS = ['30p', '25p', '24p']
EXTRACTABLE_AUDIO = ['truehd']
EXTRACTABLE_SUBTITLE = ['pgs']

#===============================================================================
# PRIVATE FUNCTIONS
#===============================================================================

def _stripAndRemove(string, remove=None):
    """Strips whitespace and optional chars from both sides of the target string.

    Args:
        target : (str)
            The string to strip leading and trailing whitespace from

        remove=None : (str)
            The string to remove from the string

    Raises:
        N/A

    Returns:
        (str)
            The target string after being stripped on either end.

    """

    stringStripped = string.lstrip().rstrip()
    stringRemoved = stringStripped.replace(remove, '')
    stringFinal = stringRemoved.lstrip().rstrip()

    return stringFinal

#===============================================================================
# CLASSES
#===============================================================================

class Config(object):
    """ Class containing the basic encoding environment as described by the .ini

    Args:
        iniFile : (str)
            Ripmaster's configuration file

    Sample config file:

    Java = C:/Program Files (x86)/Java/jre7/bin/java
    BDSupToSub = C:/Program Files (x86)/MKVToolNix/BDSup2Sub.jar
    HandbrakeCLI = C:/Program Files/Handbrake/HandBrakeCLI.exe

    x264 Speed = slow
    Baseline Quality
        1080p = 20
        720p = 20
        480p = 20
    High Quality
        1080p = 19
        720p = 19
        480p = 19
    Ultra Quality
        1080p = 10
        720p = 10
        480p = 10

    Language = English

    Leading and trailing whitespaces are automatically removed, but all entries
    are case sensitive. Make sure there's still a space between the argument
    and the '=' sign.

    """

    java = ''
    sup2Sub = ''
    handBrake = ''
    x264Speed = ''
    language = ''

    quality = {'uq': {}, 'hq': {}, 'bq': {}}

    def __init__(self, iniFile):
        self.getSettings(iniFile)

    def getSettings(self, iniFile):

        with open(iniFile, "r") as f:
            lines = f.read().splitlines()
            for i in range(len(lines)):
                line = lines[i].lstrip()
                if line.startswith('Java'):
                    Config.java = _stripAndRemove(
                        line, 'Java ='
                    )
                elif line.startswith('BDSupToSub'):
                    Config.sup2Sub = _stripAndRemove(
                        line, 'BDSupToSub ='
                    )
                elif line.startswith('HandbrakeCLI'):
                    Config.handBrake = _stripAndRemove(
                        line, 'HandbrakeCLI ='
                    )
                elif line.startswith('x264 Speed'):
                    Config.x264Speed = _stripAndRemove(
                        line, 'x264 Speed ='
                    )
                elif line.startswith('Baseline Quality'):
                    Config.quality['bq']['1080'] = int(_stripAndRemove(
                        lines[i+1], '1080p =')
                    )
                    Config.quality['bq']['720'] = int(_stripAndRemove(
                        lines[i+2], '720p =')
                    )
                    Config.quality['bq']['480'] = int(_stripAndRemove(
                        lines[i+3], '480p =')
                    )
                elif line.startswith('High Quality'):
                    Config.quality['hq']['1080'] = int(_stripAndRemove(
                        lines[i+1], '1080p =')
                    )
                    Config.quality['hq']['720'] = int(_stripAndRemove(
                        lines[i+2], '720p =')
                    )
                    Config.quality['hq']['480'] = int(_stripAndRemove(
                        lines[i+3], '480p =')
                    )
                elif line.startswith('Ultra Quality'):
                    Config.quality['uq']['1080'] = int(_stripAndRemove(
                        lines[i+1], '1080p =')
                    )
                    Config.quality['uq']['720'] = int(_stripAndRemove(
                        lines[i+2], '720p =')
                    )
                    Config.quality['uq']['480'] = int(_stripAndRemove(
                        lines[i+3], '480p =')
                    )
                elif line.startswith('Language'):
                    Config.language = _stripAndRemove(line, 'Language =')

    def debug(self):
        print Config.java
        print Config.sup2Sub
        print Config.handBrake
        print Config.x264Speed
        print Config.language
        print Config.quality

class AudioTrack(object):
    """A single audio track.

    Args:
        file : (str)
            The source file that the track is being pulled from.

    """
    def __init__(self, movie, trackID, fileType):
        self.movie = movie
        self.trackID = trackID
        self.fileType = fileType
        self.extracted = False
        self.extractedAudio = None

    def extractTrack(self):
        command = "{trackID}:".format(trackID=self.trackID)
        fileName = self.movie.fileName.replace('.mkv', '')
        fileName += "_Track{TrackID}_audio.{ext}".format(
            TrackID=self.trackID,
            ext=self.fileType
        )

        self.extractedAudio = os.path.join(
            self.movie.root,
            self.movie.subdir,
            fileName
        ).replace('\\', '/')

        mkvExtract(self.movie.path, command, self.extractedAudio)

        self.extracted = True

class SubtitleTrack(object):
    """A single subtitle track.

    Args:
        movie : (<tools.Movie>)
            The movie object that contains the original subtitle.

    """
    def __init__(self, movie, trackID, fileType):
        self.movie = movie
        self.trackID = trackID
        self.fileType = fileType
        self.extracted = False
        self.extractedSup = None

        # When converted, there will be an Idx file and a Sub file
        self.converted = False
        self.convertedIdx = None
        self.convertedSub = None

        # forced means the track contains forced flags
        # forcedOnly means the track ONLY contains forced flags
        self.forced = False
        self.forcedOnly = False

        # If a track contains both forced and unforced tracks, there will be an
        # additional track saved out.
        self.convertedIdxForced = None
        self.convertedSubForced = None

    def extractTrack(self):
        command = "{trackID}:".format(trackID=str(self.trackID))
        fileName = self.movie.fileName.replace('.mkv', '')
        # TODO: Should this be locked into .sup?
        fileName += "_Track{trackID}_sub.sup".format(trackID=self.trackID)

        self.extractedSup = os.path.join(
            self.movie.root,
            self.movie.subdir,
            fileName
        ).replace('\\', '/')

        mkvExtract(self.movie.path, command, self.extractedSup)

        self.extracted = True

    def convertTrack(self):

        if movie.resolution == 480:
            res = 'ntsc'
        else:
            res = "{res}p".format(res=str(movie.resolution))

        # Our only option flag is really resolution
        options = "-r {res}".format(res=res)

        # Use the extractedSup as a baseline, replace the file extension
        # We check for and replace the period to make sure we grab the ext
        self.convertedIdx = self.extractedSup.replace('.sup', '.idx')
        self.convertedSub = self.extractedSup.replace('.sup', '.idx')

        # Using deprecated os.popen (easier) to put shell output in list
        shellOut = bdSup2Sub(movie.path, options, self.convertedIdx, popen=True)

        # We need to check the results for FORCED subtitles
        #
        # If the amount of Forced subtitles is less than the total subs
        # We'll just create a new .idx file in addition to the default one.
        #
        # If the amount of Forced subtitles is the same as the total subs,
        # the entire subtitle track is forced, so we remove the resultFiles
        # and create a new FORCED .idx
        for line in shellOut:

            totalCount = 0

            if line.startswith('#'):
                lineList = line.split(' ')
                # The last count entry from BD will set the total
                try:
                    totalCount = int(lineList[1])
                except ValueError:
                    pass

            # There should only be 1 entry with 'forced' in it, that entry
            # looks like:
            #
            # 'Detected 39 forced captions.'
            if 'forced' in line:
                forcedCaptions = line.split()[1]

                if forcedCaptions > 0:
                    self.forced = True
                if forcedCaptions == totalCount:
                    self.forcedOnly = True

                self.convertedIdxForced = self.convertedIdx.replace(
                    '.idx',
                    '_forced.idx'
                )
                self.convertedSubForced = self.convertedSub.replace(
                    '.sub',
                    '_forced.sub'
                )

            if self.forced and not self.forcedOnly:
                # If some forced subtitles exist (but not the entire subtitle
                # track is forced), we'll create a new _FORCED.idx in addition
                # to the one already exported.
                options += ' -D'

                bdSup2Sub(movie.path, options, self.convertedIdxForced)

            elif self.forced and self.forcedOnly:
                # If the track is entirely forced subtitles, we'll rename the
                # extracted file to be the _forced file.
                os.rename(self.convertedIdx, self.convertedIdxForced)
                os.rename(self.convertedSub, self.convertedSubForced)

        self.converted = True

class Movie(object):
    """A movie file, with all video, audio and subtitle tracks"""
    def __init__(self, root, subdir, fname):
        self.root = root
        self.subdir = subdir
        self.fileName = fname

        self.path = os.path.join(
            self.root,
            self.subdir,
            self.fileName
        ).replace('\\', '/')

        self.destination = self.path.replace('.mkv', '--converted.mkv')

        # TODO: We should derive our default res based on the video track
        self.resolution = 1080
        self.quality = Config.quality['bq']['1080']
        self.preset = None
        self.tv = False
        self.fps = None

        self._getInstructions()

        # Subtitle and Audio Tracks
        # TODO: Support multiple video tracks per file?
        self.videoTracks = []
        self.audioTracks = []
        self.subtitleTracks = []

        self.vobsub = False

        self._getTracks()

        # Progress

        self.extracted = False
        self.converted = False
        self.encoded = False
        self.merged = False

    def _getInstructions(self):
        """Parses the directory name to grab all the given instructions"""
        try:
            instructionSet = self.subdir.split('__')[-1].split('_')
        except IndexError: # No '__' present in filename
            instructionSet = []

        # This is comparing against global variables at the top of the module
        for size in RESOLUTIONS:
            if size in instructionSet:
                self.resolution = size
        for level in QUALITY:
            if level in instructionSet:
                self.quality = Config.quality[level][str(self.resolution)]
        for preset in H264_PRESETS:
            if preset in instructionSet:
                self.preset = preset
        for fps in FPS_PRESETS:
            if fps in instructionSet:
                # We need to remove the 'p' off the back of the '30p'
                self.fps = int(fps.replace('p', ''))
        if 'tv' in instructionSet:
            self.tv = True

    def _getTracks(self):
        """Runs mkvInfo on the file to grab all the tracks, creating them"""
        videoTracks, audioTracks, subtitleTracks = mkvInfo(self)

        self.videoTracks = videoTracks
        self.audioTracks = audioTracks
        self.subtitleTracks = subtitleTracks

    def extractTracks(self):
        """Extracts relevant tracks"""

        for track in self.videoTracks:
            # TODO: Multiple video track support
            pass

        for track in self.audioTracks:
            if track.fileType in EXTRACTABLE_AUDIO:
                track.extractTrack()

        for track in self.subtitleTracks:
            if track.fileType in EXTRACTABLE_SUBTITLE:
                track.extractTrack()

        self.extracted = True

    def convertTracks(self):
        """Converts subtitles to correct res and fileType"""

        # TODO: Is there an audio codec that handbrake AND mkvMerge can't
        # read?

        for track in self.subtitleTracks:
            track.convertTrack()

        self.converted = True

    def encodeMovie(self):
        """Encodes the video, supported audio and subtitle tracks"""

        #
        # VIDEO OPTIONS
        #

        # File Format, Chapter Markers, Encoder, Encoder Speed
        options = '-f mkv -m -e x264 --x264-preset ' + Config.x264Speed

        # Encoder Tuning
        if self.preset:
            options += ' --x264-tune {preset}'.format(preset=self.preset)

        # Encoder Quality
        options += ' -q {quality}'.format(quality=str(self.quality))

        # Encoder Framerate
        if self.fps:
            if self.fps == 24:
                fps = '23.976'
            elif self.fps == 30:
                fps = '29.97'
            elif self.fps == 25:
                fps = '25'
            else:
                # If we got an unknown value, we're just going to go with 24p
                self.fps = '23.976'
            options += ' -r {fps}'.format(fps=fps)

        options += ' --cfr'

        #
        # AUDIO OPTIONS
        #

        # TODO: Is there demand for an audioless convert?
        options += ' -a '

        passthroughAudio = []

        for track in self.audioTracks:
            if track.fileType not in EXTRACTABLE_AUDIO:
                passthroughAudio.append(track)

        for track in passthroughAudio:
            options += str(track.trackID)
            if track != passthroughAudio[-1]:
                options += ','
            else:
                options += ' -E '
        for track in passthroughAudio:
            options += 'copy'
            if track != passthroughAudio[-1]:
                options += ','

        # TODO: Fallback audio should be a config preference
        options += ' --audio-fallback ffac3'

        #
        # PICTURE SETTINGS
        #

        options += ' -w {width} --loose-anamorphic'.format(
            width=str(RESOLUTION_WIDTH[self.resolution])
        )

        #
        # FILTERS
        #

        if self.tv:
            options += ' -d slower'

        #
        # SUBTITLES
        #

        for track in self.subtitleTracks:
            if track.fileType == 'vobsub':
                self.vobsub = True

        if self.vobsub:
            options += ' -N {lang} -s scan'.format(lang=Config.language)

        handbrake(self.path, options, self.destination)

        self.encoded = True

#===============================================================================
# FUNCTIONS
#===============================================================================

def handBrake(file, options, dest):
    """CLI command builder for converting video and audio with Handbrake

    Args:
        file : (str)
            The source file the video and audio tracks are to be converted from.

        options : (str)
            The option command line arguments to pass to handbrake

        dest : (str)
            The destination file to write to.

    Raises:
        N/A

    Returns:
        None

    """
    c = '""' + Config.handBrake + '"' + ' -i ' + file + ' -o ' + dest + ' ' + \
        options + '"'
    print "HandBrake Settings:"
    print c
    os.system(c)

def mkvExtract(file, command, dest):
    """CLI command builder for extracting tracks with mkvextract

    Args:
        file : (str)
            The source file the tracks are to be extracted from.

        command : (str)
            The track command to be executed. Usually looks like: '3:'.

        dest : (str)
            The destination file to be written to.

    Raises:
        N/A

    Returns:
        None

    The full filepath this builds should look like:

    '"mkvextract tracks I:/src/fold/file.mkv 3:I:/dest/fold/subtitle.sup "'

    """
    os.system('"mkvextract tracks ' + file + ' ' + command + dest + ' "')


def mkvInfo(movie):
    """Uses CLI to fetch names all audio, video and subtitle tracks from a mkv

    Args:
        movie : (<tools.Movie>)
            The file to get the info from

    Raises:
        N/A

    Returns:
        [[str], [str], [str]]
            A list contraining a list of video tracks, audio tracks and subtitle
            tracks.

    """

    file = movie.path

    # mkvMerge will return a listing of each track
    # TODO: Remove deprecated popen
    info = os.popen('"mkvmerge -i ' + file + '"').read()
    info = info.split('\n')

    # info is now a list, each entry a line
    #
    # Example:
    #
    # File 'I:\Rips\RawBR\Jack_Reacher\Jack_Reacher_t01.mkv': container: Matroska
    # Track ID 0: video (V_MPEG4/ISO/AVC)
    # Track ID 1: audio (A_AC3)
    # Track ID 2: audio (A_TRUEHD)
    # Track ID 3: subtitles (S_HDMV/PGS)

    AUDIO_TYPES = {
        '(A_AAC)\r': 'aac',
        '(A_DTS)\r': 'dts',
        '(A_AC3)\r': 'ac3',
        '(A_TRUEHD)\r': 'truehd',
        '(A_MP3)\r': 'mp3',
        '(A_MS/ACM)\r': 'acm',
        }

    SUBTITLE_TYPES = {
        '(S_VOBSUB)\r': 'vobsub',
        '(S_HDMV/PGS)\r': 'pgs'
        }

    trackList = []

    for line in info:
        if 'Track ID' in line:
            trackList.append(line)

    # trackList now only contains the lines with Track in them

    subtitleTracks = []
    audioTracks = []
    videoTracks = [] # No plans to use video tracks for now

    for line in trackList:
         # Splitting on ':' gives us the ID on one side, the type on the other
        lineList = line.split(':')

        if 'subtitles' in lineList[1]:
            trackID = int(lineList[0].replace('Track ID ', ''))
            fileType = SUBTITLE_TYPES[lineList[1].replace(' subtitles ', '')]
            track = SubtitleTrack(movie, trackID, fileType)
            subtitleTracks.append(track)

        elif 'audio' in lineList[1]:
            trackID = int(lineList[0].replace('Track ID ', ''))
            fileType = AUDIO_TYPES[lineList[1].replace(' audio ', '')]
            track = AudioTrack(movie, trackID, fileType)
            audioTracks.append(track)

        elif 'video' in lineList[1]:
            videoTracks.append(int(lineList[0].replace('Track ID ', '')))

    return videoTracks, audioTracks, subtitleTracks

def bdSup2Sub(file, options, dest, popen=False):
    """CLI command builder for converting susbtitles with BDSup2Sub

    Args:
        file : (str)
            The source file the subtitles must be converted from.

        options : (str)
            Resolution, Forced Only and other CLI commands for BDSup2Sub

        dest : (str)
            Destination filename to be written to. If a pair of files, BDSup2Sub
            will automatically write the paired file based off this string.

        popen=False : (bool)
            If True, os.popen will be used rather than os.system, and the read()
            method will be returned, rather than just executed.

    Raises:
        N/A

    Returns:
        [str]
            If popen=True, the console output of BDSup2Sub will be returned as a
            list.

    """
    c = '"' + Config.java + ' -jar ' + BD + ' ' +  options +\
        ' -o ' + dest + ' ' + file + '"'

    if popen:
        return os.popen(c).read().split('\n')
    else:
        os.system(c)