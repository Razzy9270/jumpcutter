# JumpCutter

Automatically cuts out silent parts of videos.
This is forked from the original JumpCutter made by **carykh**.

Explanation can be found here: https://www.youtube.com/watch?v=DQ8orIurGxw

## Information

This forked version of JumpCutter is designed to run more efficiently and jumpcut videos faster. It should be noted that it may take a long time for the jumpcutter tool to finish, depending on your computer's hardware.

It is strongly recommended to check the duriation of the video before attempting to jumpcut. The longer the video, the more space it could take up, as it exports every frame in the video as a **.jpg** image file.

## Requirements

You will need **Python 3.7.3** and **ffmpeg** for this script to work, with a computer running **Windows 10**.

Other operating systems may work with this script, but they are currently **untested**.

## Building with NIX
`nix-build` to get a script with all the libraries and ffmpeg, `nix-build -A bundle` to get a single binary.
