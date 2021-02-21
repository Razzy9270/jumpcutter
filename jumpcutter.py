import numpy as np
import subprocess
import threading
import datetime
import fnmatch
import random
import shutil
import time
import math
import os
import re

from audiotsm.io.wav import WavReader, WavWriter
from shutil import copyfile, rmtree
from audiotsm import phasevocoder
from contextlib import closing
from scipy.io import wavfile
from pytube import YouTube
from pathlib import Path
from PIL import Image
from cv2 import cv2

# This is a forked version of the original JumpCutter made by carykh.

ORIGINAL_FRAMES_FOLDER_RAW = "ORIGINAL_FRAMES"
NEW_FRAMES_FOLDER_RAW = "NEW_FRAMES"

ORIGINAL_FRAMES_FOLDER = os.path.abspath(ORIGINAL_FRAMES_FOLDER_RAW)
NEW_FRAMES_FOLDER = os.path.abspath(NEW_FRAMES_FOLDER_RAW)
AUDIO_FADE_ENVELOPE_SIZE = 400

def clear():
    if os.name == 'nt': 
        _ = os.system('cls') 
    else: 
        _ = os.system('clear')

def convertBlankToUnspecified(string):
    unspecified = string.replace("", "Unspecified")
    return unspecified

def downloadFile(url):
    print("Downloading YouTube Video...")
    name = YouTube(url).streams.first().download()
    newname = name.replace(" ", "_")
    os.rename(name, newname)
    print("Downloaded specified YouTube video.")
    print(f"Located in: {name}")
    time.sleep(5)
    return newname

def inputToOutputFilename(filename):
    dotIndex = filename.rfind(".")
    return filename[:dotIndex] + "_MODIFIED" + filename[dotIndex:]

class introductionMessage():
    clear()
    print("Welcome to JumpCutter!")
    print("Forked version made by Razzy9270, original version made by carykh.")
    print("You will have to specify a few things before continuing.")
    time.sleep(5)

class chooseOption():
    clear()
    print("Step 1: Please choose a jumpcutting option.")
    print("\n")
    print("1. Specified Video: Automatically jumpcuts a input file specified by the user.\n2. Specified YouTube Video: Automatically downloads the YouTube Video specified using the URL specified by the user.")
    print("\n")

choice = input("Choose an option: ")

def checkSelection():
    if choice == "1":
        clear()
        print("Step 2: Specify the input file to jumpcut; it must end with a '.mp4' at the end.")
        print("\n")
        rawFileName = input(" > ")
        newFileName = rawFileName.replace(" ", "_")
        os.rename(rawFileName, newFileName)
        pathFile = os.path.abspath(str(newFileName))
        return str(pathFile)
    elif choice == "2":
        clear()
        print("Step 2: Specify the YouTube Video to jumpcut; this must be a URL.")
        print("\n")
        url = input(" > ")
        clear()
        pathFile = downloadFile(url)
        return str(pathFile)

selectionChoice = checkSelection()

class chooseOutputFile():
    clear()
    print("Step 3: Specify the output file name.")
    print("You can leave this blank if you want it to use the default '[INPUT FILE]_MODIFIED' name; remember to put '.mp4' at the end.")
    print("\n")

outputFile = input(" > ")

class checkSilentThreshold():
    clear()
    print("Step 4: Specify the silent threshold.")
    print("The volume amount that frames' audio needs to surpass to be considered as 'sounded'.")
    print("Please specify an integer between 0 (Silence) to 1 (Maximum volume).")
    print("You can leave this blank if you want it to use the default value (0.05).")
    print("\n")

silentThreshold = convertBlankToUnspecified(input(" > "))

class checkSoundedSpeed():
    clear()
    print("Step 5: Specify the sounded speed.")
    print("This is the speed that sounded parts of your specified video should be played at.")
    print("Default value is 1, meaning the sounded video parts will be played back at normal speed; minimum is 0.5, and maximum is 999999.")
    print("\n")

soundedSpeed = convertBlankToUnspecified(input(" > "))

class checkSilentSpeed():
    clear()
    print("Step 6: Specify the silent speed.")
    print("This is the speed that silent parts of your specified video should be played at.")
    print("Default value is 5, meaning the silent video parts will be played back at 5 times the normal speed; minimum is 0.5, and maximum is 999999.")
    print("\n")

silentSpeed = convertBlankToUnspecified(input(" > "))

class checkFrameMargin():
    clear()
    print("Step 7: Specify the frame margin.")
    print("How many frames on either the side of speech should be included?")
    print("Default value is 3, minimum is 0.")
    print("\n")

frameMargin = convertBlankToUnspecified(input(" > "))

class checkFrameQuality():
    clear()
    print("Step 8: Specify the frame quality.")
    print("Specify the quality of frames to be extracted from the input video.")
    print("Select a number from 1 (Highest quality) to 31 (Lowest quality); default value is 3.")
    print("\n")

videoFrameQuality = convertBlankToUnspecified(input(" > "))

def checkVideoFrameRate():
    openCap = cv2.VideoCapture(str(selectionChoice))
    mediaFrameRate = openCap.get(cv2.CAP_PROP_FPS)
    return mediaFrameRate
    
videoFrameRate = float(checkVideoFrameRate())

def checkAudioSampleRate():
    return int(48000)

audioSampleRate = float(checkAudioSampleRate())

def checkSilentThresholdInput():
    if str(silentThreshold) == "Unspecified":
        return float(0.05)
    elif float(silentThreshold.replace("Unspecified", "")) > 1:
        return float(1)
    else:
        return float(silentThreshold.replace("Unspecified", ""))

def checkSoundedSpeedInput():
    if str(soundedSpeed) == "Unspecified":
        return float(1)
    elif float(soundedSpeed.replace("Unspecified", "")) < 0.5:
        return float(0.5)
    elif float(soundedSpeed.replace("Unspecified", "")) > 999999:
        return float(999999)
    else:
        return float(soundedSpeed.replace("Unspecified", ""))

def checkSilentSpeedInput():
    if str(silentSpeed) == "Unspecified":
        return float(5)
    elif float(silentSpeed.replace("Unspecified", "")) < 0.5:
        return float(0.5)
    elif float(silentSpeed.replace("Unspecified", "")) > 999999:
        return float(999999)
    else:
        return float(silentSpeed.replace("Unspecified", ""))

def checkFrameMarginInput():
    if str(frameMargin) == "Unspecified":
        return int(3)
    else:
        return int(frameMargin.replace("Unspecified", ""))

def checkFrameQualityInput():
    if str(videoFrameQuality) == "Unspecified":
        return int(3)
    elif int(videoFrameQuality.replace("Unspecified", "")) < 1:
        return int(1)
    elif int(videoFrameQuality.replace("Unspecified", "")) > 31:
        return int(31)
    else:
        return int(videoFrameQuality.replace("Unspecified", ""))

frameRate = float(videoFrameRate)
SAMPLE_RATE = float(audioSampleRate)
SILENT_THRESHOLD = float(checkSilentThresholdInput())
FRAME_SPREADAGE = float(checkFrameMarginInput())
NEW_SPEED = [float(checkSilentSpeedInput()), float(checkSoundedSpeedInput())]
INPUT_FILE = str(selectionChoice)
FRAME_QUALITY = int(checkFrameQualityInput())

assert INPUT_FILE != None, "Please specify an input file."
    
if len(outputFile) >= 1:
    OUTPUT_FILE = str(outputFile)
else:
    OUTPUT_FILE = str(inputToOutputFilename(INPUT_FILE))

time.sleep(2.5)

clear()

print("You have finished setting up.")
input("Press the ENTER key to start.")

class removeOriginalDirectory():
    clear()
    print("Checking if the 'ORIGINAL_FRAMES' directory exists...")
    dirpath = Path(ORIGINAL_FRAMES_FOLDER)
    time.sleep(2.5)
    if dirpath.exists() and dirpath.is_dir():
        print("Directory exists, removing old directory...")
        shutil.rmtree(dirpath)
        print("Removed old 'ORIGINAL_FRAMES' directory.")
        print("Creating new 'ORIGINAL_FRAMES' directory...")
        os.mkdir(ORIGINAL_FRAMES_FOLDER)
        print("Created new 'ORIGINAL_FRAMES' directory.")
        time.sleep(2.5)
        clear()
    else:
        print("Creating 'ORIGINAL_FRAMES' directory...")
        os.mkdir(ORIGINAL_FRAMES_FOLDER)
        print("Created directory 'ORIGINAL_FRAMES'.")
        time.sleep(2.5)
        clear()
    
class removeNewDirectory():
    clear()
    print("Checking for 'NEW_FRAMES' directory...")
    dirpath = Path(NEW_FRAMES_FOLDER)
    time.sleep(2.5)
    if dirpath.exists() and dirpath.is_dir():
        print("Directory exists, removing old directory...")
        shutil.rmtree(dirpath)
        print("Removed old 'NEW_FRAMES' directory.")
        print("Creating new 'NEW_FRAMES' directory...")
        os.mkdir(NEW_FRAMES_FOLDER)
        print("Created new 'NEW_FRAMES' directory.")
        time.sleep(2.5)
        clear()
    else:
        print("Creating 'NEW_FRAMES' directory...")
        os.mkdir(NEW_FRAMES_FOLDER)
        print("Created directory 'NEW_FRAMES'.")
        time.sleep(2.5)
        clear()

def getMaxVolume(s):
    maxv = float(np.max(s))
    minv = float(np.min(s))
    return max(maxv,-minv)

def copyFrame(inputFrame, outputFrame):
    source_folder = "{0}/frame{:06d}.jpg".format(ORIGINAL_FRAMES_FOLDER, inputFrame+1)
    destination_folder = "{0}/newFrame{:06d}.jpg".format(NEW_FRAMES_FOLDER, outputFrame+1)
    if not os.path.isfile(source_folder):
        return False
    shutil.move(source_folder, destination_folder)
    if outputFrame%50 == 49:
        clear()
        exportedModifiedFramesRaw = round(int(outputFrame+1) / videoFrameRate)
        exportedModifiedFramesLength = datetime.timedelta(seconds=exportedModifiedFramesRaw)
        print("Stage 2: Exporting new frames")
        print("=============================")
        print(f"Frames exported: {str(outputFrame+1)}")
        print(f"Exported length: {exportedModifiedFramesLength}")
    return True

print("Exporting input file's audio...")

command = 'ffmpeg -i "{0}" -ab 160k -ac 2 -ar {1} -vn "{2}/audio.wav"'.format(INPUT_FILE, int(audioSampleRate), ORIGINAL_FRAMES_FOLDER)
subprocess.call(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

clear()

def startFirstSegmentThread():
    while True:
        fileCapture = cv2.VideoCapture(str(selectionChoice))

        directoryRaw = "ORIGINAL_FRAMES"
        directory = str(os.path.abspath(directoryRaw))

        checkExportedFrameCount = len(fnmatch.filter(os.listdir(directory), '*.jpg'))
        checkTotalFrameCount = int(fileCapture.get(cv2.CAP_PROP_FRAME_COUNT))

        progressRaw = checkExportedFrameCount / checkTotalFrameCount
        progressPercentage = float(progressRaw) * 100

        exportedFramesRaw = round(checkExportedFrameCount / videoFrameRate)
        totalFramesRaw = round(checkTotalFrameCount / videoFrameRate)

        exportedFramesLength = datetime.timedelta(seconds=exportedFramesRaw)
        totalFramesLength = datetime.timedelta(seconds=totalFramesRaw)

        global haltFirstSegmentCountingThread

        if haltFirstSegmentCountingThread:
            break
        elif int(checkExportedFrameCount)%50 == 49:
            clear()
            print("Stage 1: Exporting input file frames into images")
            print("================================================")
            print(f"Export progress: {round(progressPercentage)}%")
            print("Frames exported: {:,} / {:,}".format(int(checkExportedFrameCount) + 1, int(checkTotalFrameCount)))
            print(f"Exported length: {exportedFramesLength} / {totalFramesLength}")

firstSegmentThread = threading.Thread(target=startFirstSegmentThread)
firstSegmentThread.start()

haltFirstSegmentCountingThread = False

command = 'ffmpeg -i "{0}" -qscale:v {1} "{2}/frame%06d.jpg" -hide_banner'.format(INPUT_FILE, str(FRAME_QUALITY), ORIGINAL_FRAMES_FOLDER)
subprocess.call(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

haltFirstSegmentCountingThread = True
firstSegmentThread.join()

checkExportedFrameCount = len(fnmatch.filter(os.listdir(ORIGINAL_FRAMES_FOLDER), '*.jpg'))

writeInputFileFrameCount = open(f"{ORIGINAL_FRAMES_FOLDER}/totalFrameCount.txt", "w+")
writeInputFileFrameCount.write(f"{checkExportedFrameCount}")
writeInputFileFrameCount.close()

clear()

command = f'ffmpeg -i "{ORIGINAL_FRAMES_FOLDER}/input.mp4" 2>&1'
f = open(ORIGINAL_FRAMES_FOLDER + "/params.txt", "w")
subprocess.call(command, shell=True, stdout=f)

sampleRate, audioData = wavfile.read(f"{ORIGINAL_FRAMES_FOLDER}/audio.wav")
audioSampleCount = audioData.shape[0]
maxAudioVolume = getMaxVolume(audioData)

f = open(f"{ORIGINAL_FRAMES_FOLDER}/params.txt", 'r+')
pre_params = f.read()
f.close()
params = pre_params.split('\n')
for line in params:
    m = re.search('Stream #.*Video.* ([0-9]*) fps', line)
    if m is not None:
        frameRate = float(m.group(1))

samplesPerFrame = sampleRate / frameRate

audioFrameCount = int(math.ceil(audioSampleCount / samplesPerFrame))

hasLoudAudio = np.zeros((audioFrameCount))

for i in range(audioFrameCount):
    start = int(i*samplesPerFrame)
    end = min(int((i+1)*samplesPerFrame),audioSampleCount)
    audiochunks = audioData[start:end]
    maxchunksVolume = float(getMaxVolume(audiochunks))/maxAudioVolume
    if maxchunksVolume >= SILENT_THRESHOLD:
        hasLoudAudio[i] = 1

chunks = [[0, 0, 0]]
shouldIncludeFrame = np.zeros((audioFrameCount))
for i in range(audioFrameCount):
    start = int(max(0,i-FRAME_SPREADAGE))
    end = int(min(audioFrameCount,i+1+FRAME_SPREADAGE))
    shouldIncludeFrame[i] = np.max(hasLoudAudio[start:end])
    if (i >= 1 and shouldIncludeFrame[i] != shouldIncludeFrame[i-1]):
        chunks.append([chunks[-1][1],i,shouldIncludeFrame[i-1]])

chunks.append([chunks[-1][1],audioFrameCount,shouldIncludeFrame[i-1]])
chunks = chunks[1:]

outputAudioData = np.zeros((0,audioData.shape[1]))
outputPointer = 0

lastExistingFrame = None
for chunk in chunks:
    audioChunk = audioData[int(chunk[0]*samplesPerFrame):int(chunk[1]*samplesPerFrame)]
    
    sFile = ORIGINAL_FRAMES_FOLDER + "/tempStart.wav"
    eFile = ORIGINAL_FRAMES_FOLDER + "/tempEnd.wav"
    wavfile.write(sFile, int(audioSampleRate), audioChunk)
    with WavReader(sFile) as reader:
        with WavWriter(eFile, reader.channels, reader.samplerate) as writer:
            tsm = phasevocoder(reader.channels, speed=NEW_SPEED[int(chunk[2])])
            tsm.run(reader, writer)
    _, alteredAudioData = wavfile.read(eFile)
    leng = alteredAudioData.shape[0]
    endPointer = outputPointer+leng
    outputAudioData = np.concatenate((outputAudioData,alteredAudioData/maxAudioVolume))

    #outputAudioData[outputPointer:endPointer] = alteredAudioData/maxAudioVolume

    # smooth out transitiion's audio by quickly fading in/out
    
    if leng < AUDIO_FADE_ENVELOPE_SIZE:
        outputAudioData[outputPointer:endPointer] = 0 # audio is less than 0.01 sec, let's just remove it.
    else:
        premask = np.arange(AUDIO_FADE_ENVELOPE_SIZE) / AUDIO_FADE_ENVELOPE_SIZE
        mask = np.repeat(premask[:, np.newaxis],2,axis=1) # make the fade-envelope mask stereo
        outputAudioData[outputPointer:outputPointer + AUDIO_FADE_ENVELOPE_SIZE] *= mask
        outputAudioData[endPointer-AUDIO_FADE_ENVELOPE_SIZE:endPointer] *= 1-mask

    startOutputFrame = int(math.ceil(outputPointer/samplesPerFrame))
    endOutputFrame = int(math.ceil(endPointer/samplesPerFrame))
    for outputFrame in range(startOutputFrame, endOutputFrame):
        inputFrame = int(chunk[0]+NEW_SPEED[int(chunk[2])]*(outputFrame-startOutputFrame))
        didItWork = copyFrame(inputFrame,outputFrame)
        if didItWork:
            lastExistingFrame = inputFrame
        else:
            copyFrame(lastExistingFrame, outputFrame)

    outputPointer = endPointer

clear()

print("Creating modified audio file...")

wavfile.write(f"{ORIGINAL_FRAMES_FOLDER}/audioNew.wav", int(audioSampleRate), outputAudioData)

clear()

checkUnmodifiedExportedFrameCount = len(fnmatch.filter(os.listdir(ORIGINAL_FRAMES_FOLDER), '*.jpg'))
checkModifiedExportedFrameCount = len(fnmatch.filter(os.listdir(NEW_FRAMES_FOLDER), '*.jpg'))

checkInputFileFrameCount = open(f"{ORIGINAL_FRAMES_FOLDER}/totalFrameCount.txt", "r")

improvementPercentageRaw = checkModifiedExportedFrameCount / int(checkInputFileFrameCount.read())
improvementPercentageOne = float(improvementPercentageRaw) * 100
improvementPercentageFinal = 100 - int(improvementPercentageOne)

modifiedVideoLengthRaw = round(checkModifiedExportedFrameCount / videoFrameRate)
unusedFramesLengthRaw = round(checkUnmodifiedExportedFrameCount / videoFrameRate)

modifiedVideoLength = datetime.timedelta(seconds=modifiedVideoLengthRaw)
unusedFramesLength = datetime.timedelta(seconds=unusedFramesLengthRaw)

print("Stage 3: Exporting modified video with new frames")
print("=================================================")
print("Exporting modified video...")
print("Please wait until the video exporting is finished.")
print("=================================================")
print("Technical information:")
print(f"Used frames: {checkModifiedExportedFrameCount} [{modifiedVideoLength}]")
print(f"Unused frames: {checkUnmodifiedExportedFrameCount} [{unusedFramesLength}]")
print(f"Improved video by: {improvementPercentageFinal}%")

command = 'ffmpeg -framerate {0} -i "{1}/newFrame%06d.jpg" -i "{2}/audioNew.wav" -strict -2 "{3}"'.format(str(frameRate), NEW_FRAMES_FOLDER, ORIGINAL_FRAMES_FOLDER, OUTPUT_FILE)
subprocess.call(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

clear()

print("Modified video has been finalized.")
print("Deleting directories 'ORIGINAL_FRAMES' and 'NEW_FRAMES'...")

time.sleep(1)

shutil.rmtree(ORIGINAL_FRAMES_FOLDER)
shutil.rmtree(NEW_FRAMES_FOLDER)

print("Successfully deleted directories 'ORIGINAL_FRAMES' and 'NEW_FRAMES'.")

time.sleep(2.5)

clear()

print("Video successfully modified.")
input("Press the ENTER key to exit...")

clear()
