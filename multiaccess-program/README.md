[![Build Status](https://travis-ci.org/makerspace/multiaccess-program.svg?branch=add-and-update-members)](https://travis-ci.org/makerspace/multiaccess-program)
[![Coverage Status](https://coveralls.io/repos/github/makerspace/multiaccess-program/badge.svg)](https://coveralls.io/github/makerspace/multiaccess-program)

# Program to Update MultiAccess With Data from MakerAdmin

A Windows program that will fetch data from MakerAdmin (or a file)
with member information, then updates rfid_tag and end date, adds new
members and blocks members that should no logner have access.

Users of the program is supposed to make all updates in the MakerAdmin
system (including entering of new rfid_tags) then run
`multi_access_sync.exe` with MultiAccess turned off, then start
MultiAccess and use it to send the updates to the building.

## MultiAccess

Multiaccess is a program developed by Aptus and is used to admin their
access system. The program is pretty old and may no longer be
maintained. The version used in the Makerspace buiding is 7.16.6.

## MakerAdmin

MakerAdmin is the system for administrating members of Stockholm
Makerspace, there is an API endpoint used by this program to fetch
member information
[https://github.com/makerspace/MakerAdmin-MultiAccessSync].

## Database Structure

See [Docs/Database.md](Docs/Database.md)

## Development Environment

Written in Python (requires Python >= 3.6).

### Install Dependencies
You may need to install `unixodbc-dev` on ubuntu.

`sudo make init`

This installs the Python dependencies described in `requirements.txt`

### Run Tests
`make test`

### Create Windows Executables
`make dist`

## Installation

Just copy the binary (`multi_access_sync.exe`) to the computer
connected to the house and run it in a `cmd`.
