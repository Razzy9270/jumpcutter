# JumpCutter

Automatically cuts out silent parts of videos.
This is forked from the original JumpCutter made by **carykh**.

Explanation can be found here: https://www.youtube.com/watch?v=DQ8orIurGxw

## Heads-up

It is strongly recommended to check the duriation of the video before attempting to jumpcut.
The longer the video, the more space it could take up, as it exports every frame in the video as a **.jpg** image file.

## Requirements

You will need **Python 3** for this to work.
**ffmpeg** is a requirement for this to work as well.

This forked version of JumpCutter has only been tested on **Windows 10 v1809 LTSC** (Build 17763) so far.
It should work on other operating systems, but they are untested.

## Building with NIX
`nix-build` to get a script with all the libraries and ffmpeg, `nix-build -A bundle` to get a single binary.
