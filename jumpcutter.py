import numpy as np
import subprocess
import argparse
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

# This is a forked version of the original JumpCutter made by carykh.

def convertBlankToUnspecified(string):
    unspecified = string.replace("", "Unspecified")
    return unspecified

def clear():
    if os.name == 'nt': 
        _ = os.system('cls') 
    else: 
        _ = os.system('clear')

def downloadFile(url):
    name = YouTube(url).streams.first().download()
    newname = name.replace(' ','_')
    os.rename(name, newname)
    print("Downloaded specified YouTube video.")
    print(f"Located in: {name}")
    time.sleep(5)
    return newname

def inputToOutputFilename(filename):
    dotIndex = filename.rfind(".")
    return filename[:dotIndex]+"_MODIFIED"+filename[dotIndex:]

class introductionMessage():
    clear()
    print("Welcome to JumpCutter!")
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
        print("Step 2: Specify the input file to jumpcut; this must end with a '.mp4' at the end.")
        print("\n")
        file = input(" > ")
        return file
    elif choice == "2":
        clear()
        print("Step 2: Specify the YouTube Video to jumpcut; this must be a URL.")
        print("\n")
        url = input(" > ")
        pathFile = downloadFile(url)
        return pathFile

selectionChoice = checkSelection()

class chooseOutputFile():
    clear()
    print("Step 3: Specify the output file name.")
    print("You can leave this blank if you want it to use the default '[INPUT FILE]_MODIFIED' name.")
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
    print("Default value is 3, minimum is 0, and maximum is 60.")
    print("\n")

frameMargin = convertBlankToUnspecified(input(" > "))

class checkSampleRate():
    clear()
    print("Step 8: Specify the sample rate.")
    print("Specify the sample rate of the input and output videos.")
    print("Default value is 44100.")
    print("\n")

videoSampleRate = convertBlankToUnspecified(input(" > "))

class checkFrameRate():
    clear()
    print("Step 9: Specify the frame rate.")
    print("Specify the frame rate of the input and output videos.")
    print("Default value is 30.")
    print("\n")

videoFrameRate = convertBlankToUnspecified(input(" > "))

class checkFrameQuality():
    clear()
    print("Step 10: Specify the frame quality.")
    print("Specify the quality of frames to be extracted from the input video.")
    print("Select a number from 1 (Highest quality) to 31 (Lowest quality); default value is 3.")
    print("\n")

videoFrameQuality = convertBlankToUnspecified(input(" > "))

def checkSilentThresholdInput():
    if silentThreshold == "Unspeficied":
        return 0.05
    elif silentThreshold < 0:
        return 0
    elif silentThreshold > 1:
        return 1

def checkSoundedSpeedInput():
    if soundedSpeed == "Unspecified":
        return 1
    elif soundedSpeed < 0.5:
        return 0.5
    elif soundedSpeed > 999999:
        return 999999

def checkSilentSpeedInput():
    if silentSpeed == "Unspecified":
        return 5
    elif silentSpeed < 0.5:
        return 0.5
    elif silentSpeed > 999999:
        return 999999

def checkFrameMarginInput():
    if frameMargin == "Unspecified":
        return 3
    elif frameMargin < 0:
        return 0
    elif frameMargin > 60:
        return 60

def checkSampleRateInput():
    if videoSampleRate == "Unspecified":
        return 44100
    elif videoSampleRate < 22050:
        return 22050
    elif videoSampleRate > 48000:
        return 48000

def checkFrameRateInput():
    if videoFrameRate == "Unspecified":
        return 30
    elif videoFrameRate < 1:
        return 1
    elif videoFrameRate > 60:
        return 60

def checkFrameQualityInput():
    if videoFrameQuality == "Unspecified":
        return 3
    elif videoFrameQuality < 1:
        return 1
    elif videoFrameQuality > 31:
        return 31

frameRate = float(checkFrameRateInput())
SAMPLE_RATE = float(checkSampleRateInput())
SILENT_THRESHOLD = float(checkSilentThresholdInput())
FRAME_SPREADAGE = float(checkFrameMarginInput())
NEW_SPEED = [float(checkSilentSpeedInput()), float(checkSoundedSpeedInput())]
INPUT_FILE = str(selectionChoice)
FRAME_QUALITY = int(checkFrameQualityInput())

assert INPUT_FILE != None , "Please specify an input file."
    
if len(outputFile) >= 1:
    OUTPUT_FILE = str(outputFile)
else:
    OUTPUT_FILE = str(inputToOutputFilename(INPUT_FILE))

time.sleep(2.5)

clear()

print("You have finished setting up things.")
input("Press the ENTER key to start.")

class removeOriginalDirectory():
    clear()
    print("Checking if the 'ORIGINAL_FRAMES' directory exists...")
    dirpath = Path("ORIGINAL_FRAMES")
    time.sleep(2.5)
    if dirpath.exists() and dirpath.is_dir():
        print("Directory exists, removing old directory...")
        shutil.rmtree(dirpath)
        print("Removed old 'ORIGINAL_FRAMES' directory.")
        time.sleep(2.5)
        clear()
    else:
        print("'ORIGINAL_FRAMES' directory does not exist, creating a new one...")
        time.sleep(2.5)
        clear()
    
class removeNewDirectory():
    clear()
    print("Checking for 'NEW_FRAMES' directory...")
    dirpath = Path("NEW_FRAMES")
    time.sleep(2.5)
    if dirpath.exists() and dirpath.is_dir():
        print("Directory exists, removing old directory...")
        shutil.rmtree(dirpath)
        os.mkdir("NEW_FRAMES")
        print("Created new 'NEW_FRAMES' directory.")
        time.sleep(2.5)
        clear()
    else:
        print("Creating 'NEW_FRAMES' directory...")
        os.mkdir("NEW_FRAMES")
        print("Created directory 'NEW_FRAMES'.")
        time.sleep(2.5)
        clear()

def getMaxVolume(s):
    maxv = float(np.max(s))
    minv = float(np.min(s))
    return max(maxv,-minv)

def copyFrame(inputFrame,outputFrame):
    src = TEMP_FOLDER + "/frame{:06d}".format(inputFrame+1) + ".jpg"
    dst = DESTINATION_FOLDER + "/newFrame{:06d}".format(outputFrame+1) + ".jpg"
    if not os.path.isfile(src):
        return False
    copyfile(src, dst)
    if outputFrame%100 == 99:
        clear()
        print(str(outputFrame+1)+" new frames exported.")
    return True

def createPath(s):
    #assert (not os.path.exists(s)), "The filepath "+s+" already exists. Don't want to overwrite it. Aborting."

    try:
        os.mkdir(s)
    except OSError:  
        assert False, "Creation of the directory %s failed. (The folder may already exist. Delete or rename it, and try again.)"

TEMP_FOLDER = "ORIGINAL_FRAMES"
DESTINATION_FOLDER = "NEW_FRAMES"
AUDIO_FADE_ENVELOPE_SIZE = 400 # smooth out transitiion's audio by quickly fading in/out (arbitrary magic number whatever)
    
createPath(TEMP_FOLDER)

command = "ffmpeg -i "+INPUT_FILE+" -qscale:v "+str(FRAME_QUALITY)+" "+TEMP_FOLDER+"/frame%06d.jpg -hide_banner"
subprocess.call(command, shell=True)

command = "ffmpeg -i "+INPUT_FILE+" -ab 160k -ac 2 -ar "+str(SAMPLE_RATE)+" -vn "+TEMP_FOLDER+"/audio.wav"

subprocess.call(command, shell=True)

command = "ffmpeg -i "+TEMP_FOLDER+"/input.mp4 2>&1"
f = open(TEMP_FOLDER+"/params.txt", "w")
subprocess.call(command, shell=True, stdout=f)



sampleRate, audioData = wavfile.read(TEMP_FOLDER+"/audio.wav")
audioSampleCount = audioData.shape[0]
maxAudioVolume = getMaxVolume(audioData)

f = open(TEMP_FOLDER+"/params.txt", 'r+')
pre_params = f.read()
f.close()
params = pre_params.split('\n')
for line in params:
    m = re.search('Stream #.*Video.* ([0-9]*) fps',line)
    if m is not None:
        frameRate = float(m.group(1))

samplesPerFrame = sampleRate/frameRate

audioFrameCount = int(math.ceil(audioSampleCount/samplesPerFrame))

hasLoudAudio = np.zeros((audioFrameCount))



for i in range(audioFrameCount):
    start = int(i*samplesPerFrame)
    end = min(int((i+1)*samplesPerFrame),audioSampleCount)
    audiochunks = audioData[start:end]
    maxchunksVolume = float(getMaxVolume(audiochunks))/maxAudioVolume
    if maxchunksVolume >= SILENT_THRESHOLD:
        hasLoudAudio[i] = 1

chunks = [[0,0,0]]
shouldIncludeFrame = np.zeros((audioFrameCount))
for i in range(audioFrameCount):
    start = int(max(0,i-FRAME_SPREADAGE))
    end = int(min(audioFrameCount,i+1+FRAME_SPREADAGE))
    shouldIncludeFrame[i] = np.max(hasLoudAudio[start:end])
    if (i >= 1 and shouldIncludeFrame[i] != shouldIncludeFrame[i-1]): # Did we flip?
        chunks.append([chunks[-1][1],i,shouldIncludeFrame[i-1]])

chunks.append([chunks[-1][1],audioFrameCount,shouldIncludeFrame[i-1]])
chunks = chunks[1:]

outputAudioData = np.zeros((0,audioData.shape[1]))
outputPointer = 0

lastExistingFrame = None
for chunk in chunks:
    audioChunk = audioData[int(chunk[0]*samplesPerFrame):int(chunk[1]*samplesPerFrame)]
    
    sFile = TEMP_FOLDER+"/tempStart.wav"
    eFile = TEMP_FOLDER+"/tempEnd.wav"
    wavfile.write(sFile,SAMPLE_RATE,audioChunk)
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
        premask = np.arange(AUDIO_FADE_ENVELOPE_SIZE)/AUDIO_FADE_ENVELOPE_SIZE
        mask = np.repeat(premask[:, np.newaxis],2,axis=1) # make the fade-envelope mask stereo
        outputAudioData[outputPointer:outputPointer+AUDIO_FADE_ENVELOPE_SIZE] *= mask
        outputAudioData[endPointer-AUDIO_FADE_ENVELOPE_SIZE:endPointer] *= 1-mask

    startOutputFrame = int(math.ceil(outputPointer/samplesPerFrame))
    endOutputFrame = int(math.ceil(endPointer/samplesPerFrame))
    for outputFrame in range(startOutputFrame, endOutputFrame):
        inputFrame = int(chunk[0]+NEW_SPEED[int(chunk[2])]*(outputFrame-startOutputFrame))
        didItWork = copyFrame(inputFrame,outputFrame)
        if didItWork:
            lastExistingFrame = inputFrame
        else:
            copyFrame(lastExistingFrame,outputFrame)

    outputPointer = endPointer

wavfile.write(TEMP_FOLDER+"/audioNew.wav",SAMPLE_RATE,outputAudioData)

command = "ffmpeg -framerate "+str(frameRate)+" -i "+ DESTINATION_FOLDER +"/newFrame%06d.jpg -i "+TEMP_FOLDER+"/audioNew.wav -strict -2 "+OUTPUT_FILE
subprocess.call(command, shell=True)

clear()

print("Modified video has been finalized.")
print("Deleting directories 'ORIGINAL_FRAMES' and 'NEW_FRAMES'...")

time.sleep(1)

shutil.rmtree(TEMP_FOLDER)
shutil.rmtree(DESTINATION_FOLDER)

print("Successfully deleted directories 'ORIGINAL_FRAMES' and 'NEW_FRAMES'.")

time.sleep(2.5)

clear()

print("Video successfully modified.")
input("Press the ENTER key to exit...")

clear()
