# -*- coding: utf-8 -*-
"""
Created on Sat Oct  1 13:48:09 2022

@author: pcapdessus
"""

import dateutil.parser as dparser
import datetime as dt
import numpy as np
import sys
import os
import logging as log
import glob
import time
import subprocess
from logging.handlers import RotatingFileHandler

PICT_FOLDERPATH = './Pictures/'
LOG_FILEPATH = './log.txt'
"""
if os.stat(LOG_FILEPATH).st_size == 0 :
    os.remove(LOG_FILEPATH)
"""

my_handler = RotatingFileHandler(LOG_FILEPATH, mode='a', maxBytes=2048)
my_handler.setFormatter('%(asctime)s - %(levelname)s - %(message)s')
my_handler.setLevel(log.DEBUG)

app_log = log.getLogger('root')
app_log.setLevel(log.DEBUG)

FILEPATH_ALREADY_SHOWN="ALREADY_SHOWN_PICTS"
TRANSITION_TIME_IN_SEC = 3600 #1h

def get_pict_available(pict_folderpath, filepath_already_shown):

    # Return the list of file in <pict_folderpath> whose name is
    # not in <filepath_already_shown>
    list_file_available = []
    list_already_shown = []
    if filepath_already_shown is not None:
        with open(filepath_already_shown, 'r') as f_already:
            list_already_shown = f_already.read().splitlines()
            if list_already_shown is None:
                list_already_shown = []

    for file in glob.glob(pict_folderpath+'*.jpg'):
        if file not in list_already_shown:
            list_file_available.append(file)

    app_log.info(f'[func] len(already_shown) {len(list_already_shown)} '
                 f'len(list_available)={len(list_file_available)}')

    return list_file_available


def choose_pict(pict_folderpath, filepath_already_shown):

    file_list_available = get_pict_available(pict_folderpath, filepath_already_shown)
    if len(file_list_available) != 0:
        rand_idx = np.random.randint(0, len(file_list_available))
        file_chosen = file_list_available[rand_idx]
    else:
        # All the pict have been consumed
        file_chosen = None
    return file_chosen

def set_current_pict(file_chosen, curr_pict_filepath='CURRENT_PICT'):
    with open(curr_pict_filepath, 'w') as fid_curr_pict:
        fid_curr_pict.writelines(file_chosen)


def set_current_date(date_filepath='DATE'):
    with open(date_filepath, 'w') as fid_date:
        fid_date.writelines([str(dt.datetime.now())])

def append_already_done_pict(filepath_pict, filepath_already_shown=FILEPATH_ALREADY_SHOWN):
    with open(filepath_already_shown, 'a') as f:
        f.writelines(filepath_pict+'\n')

def display_picture(pict_filepath):
    # low level / linux cmd
    # shut down screen

    DEBUG = False

    if DEBUG:
        app_log.info(f'[display_picture] displaying pict {pict_filepath}')

    else:

        app_log.info('[display_picture] killing fbi')
        subprocess.run('sudo killall fbi || true' , shell=True)

        app_log.info('[display_picture] turning the screen to black')
        subprocess.run('dd if=/dev/zero of=/dev/fb0 || true', shell=True)

        # use fbi to display picture
        app_log.info('[display_picture] displaying pict')
        cmd = 'sudo fbi -a -T 1 -t 600 --noverbose ' + pict_filepath + '|| true'
        app_log.info('[display_picture] cmd: {cmd}')
        subprocess.run(cmd, shell=True )

def get_current_pict(curr_pict_filepath='CURRENT_PICT'):
    with open(curr_pict_filepath, 'r') as fid_curr_pict:
        curr_pict = fid_curr_pict.readlines()
    return curr_pict[0]

def get_last_date(date_filepath='DATE'):
    with open(date_filepath, 'r') as fid_date:
        date = fid_date.readlines()

        return dparser.parse(date[0])

if __name__ == '__main__':

    #

    # flag to handle first switch on after init phase
    first_diplay_flag = False

    while True:

        if not os.path.isfile('INIT'):
            # Initial state where not file exist
            app_log.info('[INIT_STATE] No init file has been found.'
                     ' Creation of needed file (INIT, CURRENT_PICT, ALREADY_SHOWN_PICTS')

            open('INIT', 'w')
            open(FILEPATH_ALREADY_SHOWN, 'w')

            # Choose the first pic (here ALREADY_SHOWN_PICTS is empty )
            file_chosen = choose_pict(PICT_FOLDERPATH, None)
            app_log.info(f'[INIT_STATE] pict chosen:{file_chosen}')

            set_current_pict(file_chosen)
            set_current_date()
            display_picture(file_chosen)
            first_diplay_flag = True

        else:
            #
            last_date = get_last_date()
            curr_pict = get_current_pict()
            curr_date = dt.datetime.now()

            # Avoid to call display without necessity (i.e TRANSITION_TIME_IN_SEC/7)
            # but prevent waiting TRANSITION_TIME_IN_SEC when turning on for first time
            # after INIT
            if not first_diplay_flag:
                display_picture(curr_pict)
                first_diplay_flag = True

            if(curr_date - last_date).seconds > TRANSITION_TIME_IN_SEC:
                app_log.info(f'Time elapsed for {curr_pict} ({(curr_date - last_date).seconds} seconds)')
                app_log.info(f'Putting {curr_pict} in already done list')
                append_already_done_pict(curr_pict, FILEPATH_ALREADY_SHOWN)
                file_chosen = choose_pict(PICT_FOLDERPATH, FILEPATH_ALREADY_SHOWN)

                if file_chosen is not None:
                    app_log.info(f'[NOMINAL_STATE] pict chosen:{file_chosen}')
                    set_current_pict(file_chosen)
                    set_current_date()
                    display_picture(file_chosen)
                else:
                    # No picture available anymore (all have been shown)
                    # Need to go back to init state
                    app_log.info("<<<<<<<<<<<<< TIME TO RESET >>>>>>>>>>>>>>>>")
                    print(f"<<<<<<<<<<<<< TIME TO RESET >>>>>>>>>>>>>>>")
                    os.remove('INIT')
                    #my_handler.shouldRollover()
                    os.remove(FILEPATH_ALREADY_SHOWN)

            else:
                curr_date = dt.datetime.now()
                app_log.info(f'[NOMINAL_STATE] last date:{last_date}')


        # Waiting phase
        time.sleep(TRANSITION_TIME_IN_SEC/7)
