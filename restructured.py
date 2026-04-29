__author__ = 'WizzardTim'
# Import needed libraries
import os
import time
import pandas as pd
import numpy as np
#import win32api
# from slackclient import SlackClient
import logging as Logger
import gc
import os
import fileFunctions as ff
import svgwrite
import math as m

# Helper functions to behave properly when dealing with 8 decimals calculations, i.e. satoshis
# Used when boxsize selected equals to an amount of satoshis

def round_nearest(x, a):
    return round(round(x / a) * a, -int(m.floor(m.log10(a))))

def removeSatoshi(x):
    return int(round_nearest(x * 100000000, 0.00000001))

def replaceSatoshi(x):
    return float("{:.8f}".format(x / 100000000))


def meets_or_exceeds_boxsize(delta, boxsize):
    return float(delta) >= float(boxsize)


#     _____     _____    _____     _        _____         _                   _____ _
#    |  _  |___|   __|  |     |___|_|___   |   __|___ ___|_|___ ___    ___   |     | |___ ___ ___
#    |   __|   |   __|  | | | | .'| |   |  |   __|   | . | |   | -_|  |___|  |   --| | . |_ -| -_|
#    |__|  |_|_|__|     |_|_|_|__,|_|_|_|  |_____|_|_|_  |_|_|_|___|         |_____|_|___|___|___|
#                                                    |___|
#
# Description: This is the Main PnF Engine - uses Log or Arithmetic Scale values and 'Close' data for
# maximum performance. It is implemented using NumPy arrays for effective iteration through Pandas DataFrame.
# This approach is more effective (less time-consuming) than using DataFrame indexes for
# iteration. For the creation & testing of the engine, DuPlessis examples and data were used.
# It is one of the few (worldwide) PnF implementations that include proper initialization and
# 'one-step-back' feature (needed for 1 box reversal).
#
# Output: A Pandas DataFrame that has the following 19 columns when percentage boxsize was used:
# 'Date','e^Close','XO','Signal','Column','Boxnumber','e^Box','e^NextX','e^NextO','e^LastNextX',
# 'e^LastNextO','Close','Box','NextX','NextO','LastNextX','LastNextO','Boxsize','Log', and the same Dataframe
# without the e^ when requested with absolute value as boxsize.

def main_pnf_engine_using_close_data(MyPandasFrame, boxsize=0.029558802, reversal=3, log=True):  # default values 3%, using 3 boxes reversal

    if log==True:
        # Calculate Natural algorithm - and add it as a new column into Dataframe
        #.apply(lambda x: format(x,'.8f'))
        MyPandasFrame['logged close'] = (np.log(MyPandasFrame['close']))
        #MyPandasFrame['logged close']=m.ceil((np.log(MyPandasFrame['close'])*1e10)/1e10

        # Parse needed columns into a numpy array to be used for iteration loop
        array = np.array(MyPandasFrame[['date','high','low','close','logged close']])
    elif log==False:
        # Parse needed columns into a numpy array to be used for iteration loop
        array = np.array(MyPandasFrame[['date','high','low','close']])

    # Setting of initial parameters:

    # Thes following two are used for keeping table row indexes after the initialization loop
    CurrentRowInputArray = 0
    CurrentRowPnfArray = 0
    BeforeFirstReversal = "True"
    Date = array[0,0]
    XO = "-"
    Signal = "-"
    Column = 1
    Boxsize = boxsize # Very Important - % natural algorithm or plain number

    #Having one of the following values in case of natural algorithm:
    #1% 0.009950331
    #2% 0.019802627
    #3% 0.029558802

    if log==True:
        Close = array[0,4]  # Natural log close
        Initial_Close = array[0,4]
        Boxnumber = 0 # Initial Boxnumber equals to first logged close
        Boxvalue = array[0,4] # This is the value of the box and NOT the number of the box
    elif log==False:
        Close = removeSatoshi(array[0,3])  # Existing Close
        Boxsize = removeSatoshi(boxsize)
        #Initial_Close = Close
        #Boxnumber = int(Initial_Close / Boxsize)
        Boxnumber = int(Close / Boxsize)
        Boxvalue = Boxnumber * Boxsize # This is the value of the box and NOT the number of the box

    NextX = Boxvalue + Boxsize
    NextO = Boxvalue - Boxsize
    LastNextX = NextX
    LastNextO = NextO
    Reversal = reversal
    Log = log # Changes a lot of things - Engine was restructured to support every number

    if log==False:
        Close = replaceSatoshi(Close)
        Boxvalue = replaceSatoshi(Boxvalue)
        NextX = replaceSatoshi(NextX)
        NextO = replaceSatoshi(NextO)
        LastNextX = replaceSatoshi(LastNextX)
        LastNextO = replaceSatoshi(LastNextO)
        Boxsize = replaceSatoshi(Boxsize)

    # Make 2d array to store pnf data
    pnf_data = np.zeros(shape = [0,12])

    #print "Array columns look like:"
    #print "0)Date    1)Close    2)XO    3)Signal   4)Column    5)Boxnumber    6)Box"
    #print "7)NextX   8)NextO    9)LastNextX    10)LastNextO    11)Boxsize    12)Log"

    # First Row is Initial Date, Initial Close
    new_row = np.array([Date,          # Date
                        Close,         # Close
                        XO,            # XO
                        Signal,        # Signal
                        Column,        # Column
                        Boxnumber,     # Boxnumber
                        Boxvalue,      # Boxvalue
                        NextX,         # NextX
                        NextO,         # NextO
                        LastNextX,     # LastNextX
                        LastNextO,     # LastNextO
                        Boxsize,       # Boxsize
                        Log])          # Log

    pnf_data = np.append(pnf_data, new_row)

    # This loop contains perfect initialization for PnF calculation - Tested with Du Plessis data
    for row in range(1,len(array),1):
        # The Close value that we check depends on whether we use Log Scale or not
        if Log==True:
            Close_to_check = array[row,4] # Close to check is natural Logged Close
        elif Log==False:
            Close_to_check = removeSatoshi(array[row,3]) # Close to check is existing Close
            #Initial_Close = removeSatoshi(Initial_Close)
            Boxvalue = removeSatoshi(Boxvalue)
            Boxsize = removeSatoshi(Boxsize)

        if meets_or_exceeds_boxsize(abs(Close_to_check - Boxvalue), Boxsize):
            if Close_to_check > Boxvalue: # Keeping close
                XO = "X"

                # Workaround to print correct integer: first turn to string, then to float and then to int
                # print ((0.00000025-0.00000023)/0.00000001) # This yields 2.0 and when type-casting to int it turns to 1.0!
                # x = str((0.00000025 - 0.00000023) / 0.00000001)
                # x= int(float(x))
                if Log==True:
                    Boxnumber = int((Close_to_check - Initial_Close) / Boxsize) #+ Boxnumber
                    Boxvalue = Boxvalue + Boxnumber * Boxsize
                elif Log==False:
                    Boxnumber = int(Close_to_check / Boxsize)
                    Boxvalue = Boxnumber * Boxsize

                #Boxvalue = Boxnumber*Boxsize
                NextX = Boxvalue + Boxsize
                NextO = Boxvalue - (Boxsize * Reversal)
                LastNextX = NextX
                LastNextO = NextO

                #print "after process"
                #print "XO ",XO
                #print "Initial Close", format(Initial_Close,'.8f')
                #print "Close", format(Close_to_check,'.8f')
                #print "Boxnumber",Boxnumber
                #print "Boxsize", format(Boxsize,'.8f')
                #print "Box ",format(Box,'.8f')
                #print "NextX ",format(NextX,'.8f')
                #print "NextO",format(NextO,'.8f')
                #print "LastNextX ",format(LastNextX,'.8f')
                #print "LastNextO ",format(LastNextO,'.8f')


            elif Close_to_check < Boxvalue:
                XO = "O"
                if Log==True:
                    Boxnumber = int((Initial_Close - Close_to_check) / Boxsize) * (-1)
                    Boxvalue = Boxvalue + Boxnumber * Boxsize
                elif Log==False:
                    #Boxnumber = round(Close_to_check / Boxsize)
                    Boxnumber = int(Close_to_check /Boxsize)
                    Boxvalue = Boxnumber * Boxsize

                    #Boxvalue = Boxnumber*Boxsize

                if Close_to_check > Boxvalue:  # This check is needed because in downwards movement
                    # the box bevaves differently, e.g. with 1 box reversal and 1 boxsize,
                    # the box with value 10 is equal to [9.01,10] or (9,10], while in
                    # upwards movement it is equal to [10, 10.99] or [10,11)
                    Boxnumber = Boxnumber + 1
                    if Log==True:
                        Boxvalue = Boxvalue + Boxnumber * Boxsize
                    elif Log==False:
                        Boxvalue = Boxnumber * Boxsize

                NextX = Boxvalue + (Boxsize * Reversal)
                NextO = Boxvalue - Boxsize
                LastNextX = NextX
                LastNextO = NextO


            Date = array[row,0]
            Close = Close_to_check
            Column = Column

            if log == False:
                Close = replaceSatoshi(Close)
                Boxvalue = replaceSatoshi(Boxvalue)
                NextX = replaceSatoshi(NextX)
                NextO = replaceSatoshi(NextO)
                LastNextX = replaceSatoshi(LastNextX)
                LastNextO = replaceSatoshi(LastNextO)
                Boxsize = replaceSatoshi(Boxsize)

            new_row = np.array([Date,          # Date
                                Close,         # Close
                                XO,            # XO
                                Signal,        # Signal
                                Column,        # Column
                                Boxnumber,     # Boxnumber
                                Boxvalue,      # Boxvalue
                                NextX,         # NextX
                                NextO,         # NextO
                                LastNextX,     # LastNextX
                                LastNextO,     # LastNextO
                                Boxsize,       # Boxsize
                                Log])          # Log

            pnf_data = np.vstack([pnf_data, new_row])

            if XO == "X": # mark previous XO
                pnf_data[0][2] = "X"
            else: pnf_data[0][2] = "O"

            CurrentRowInputArray = row # keeping the row index to use afterwards in the main PnF loop
            CurrentRowPnfArray = 1     # 2 records up to this point
            break

    # Concurrency - time efficiency for web app
    # if user has given wrong boxsize then there will be no entry with 'X' or 'O' in the pnf_data till now,
    # leading to a run-time exception. But we can get over this:
    if XO == "-":
        # exception catch - no need to run main PnF loop
        result = "exception-small boxsize entered"
        return result

    listboxnumprevcolumn = list() # Used for 1 box reversal
    listboxnumsamecolumn = list() # Used for 1 box reversal

    timebeforemainloop = time.time()
    np.set_printoptions(precision=9)
    # This is the main PnF loop - to be used after initialization loop
    for row in range(CurrentRowInputArray,len(array),1):  #  starting from where we left
        # Concurrency - time efficiency for web app
        # If PnF Chart has more than 2000 Columns then we stop execution
        if Column > 2000:
            break

        # The Close value that we check depends on whether we use Log Scale or not
        if Log==True:
            Close_to_check = array[row,4] # Close to check is natural Logged Close
            Boxvalue = pnf_data[CurrentRowPnfArray, 6]
        elif Log==False:
            Close_to_check = removeSatoshi(array[row,3]) # Close to check is existing Close
            Boxvalue = removeSatoshi(pnf_data[CurrentRowPnfArray,6])
            Boxsize = removeSatoshi(pnf_data[CurrentRowPnfArray,11])
            NextX = removeSatoshi(pnf_data[CurrentRowPnfArray,7])
            NextO = removeSatoshi(pnf_data[CurrentRowPnfArray,8])
        Close_to_check_asf = ' %.8f' % (Close_to_check)

        # Debug print
        #print("Close to check:%1.8f",format(Close_to_check,'.8f')," row: ",row)
        # Check initial XO status to see whether we are in an upwards or downwards trend
        if pnf_data[CurrentRowPnfArray,2] == "X":  # we are in an upwards movement
            #if (abs(pnf_data[CurrentRowPnfArray,6]*100000000 - Close_to_check)) >= Boxsize: # We check the Boxvalue with the Close_to_check
            if meets_or_exceeds_boxsize(abs(Boxvalue - Close_to_check), Boxsize):  # We check the Boxvalue with the Close_to_check
                if meets_or_exceeds_boxsize(Close_to_check - NextX, 0):  # first case where a new X can be drawn
                    # Start filling PnF data
                    XO = "X"

                    if Log==True:
                        # Find how many boxes we are above nextX
                        BoxesaboveNextX = int((Close_to_check - NextX) / Boxsize)
                        # Since we are ascending, the NextX is 1 box above current boxnumber
                        Boxnumber = Boxnumber + BoxesaboveNextX + 1
                        #The Boxsize is the multiplication of Boxnumber*Boxsize+InitialClose
                        Boxvalue = Initial_Close + Boxnumber * Boxsize
                    elif Log==False:
                        # Find how many boxes we are above nextX
                        # BoxesaboveNextX = int((Close_to_check-NextX)/Boxsize)
                        Boxnumber = int(Close_to_check / Boxsize)
                        #The Boxsize is the multiplication of Boxnumber*Boxsize
                        Boxvalue = Boxnumber * Boxsize
                    #Boxvalue = round_nearest(Boxvalue, 0.00000001)
                    Boxsize_asf = ' %.8f' % (Boxsize)
                    Boxnumber_asf = ' %.8f' % (Boxnumber)
                    Boxvalue_asf = ' %.8f' % (Boxvalue)

                    NextX = Boxvalue + Boxsize
                    NextO = Boxvalue - (Boxsize * Reversal)

                    if BeforeFirstReversal == "True":  # used for initial LastNextX&O
                        LastNextX = NextX    # same as previous
                        LastNextO = NextO

                    Date = array[row,0]
                    Close = Close_to_check
                    Column = Column

                    if log == False:
                        Close = replaceSatoshi(Close)
                        Boxvalue = replaceSatoshi(Boxvalue)
                        NextX = replaceSatoshi(NextX)
                        NextO = replaceSatoshi(NextO)
                        LastNextX = replaceSatoshi(LastNextX)
                        LastNextO = replaceSatoshi(LastNextO)
                        Boxsize = replaceSatoshi(Boxsize)

                    new_row = np.array([Date,          # Date
                                        Close,         # Close
                                        XO,            # XO
                                        Signal,        # Signal
                                        Column,        # Column
                                        Boxnumber,     # Boxnumber
                                        Boxvalue,      # Boxvalue
                                        NextX,         # NextX
                                        NextO,         # NextO
                                        LastNextX,     # LastNextX
                                        LastNextO,     # LastNextO
                                        Boxsize,       # Boxsize
                                        Log])          # Log

                    pnf_data = np.vstack([pnf_data, new_row])

                    #CurrentRowInputArray = row # keeping the row index to use afterwards in the main PnF loop
                    CurrentRowPnfArray = CurrentRowPnfArray+1     #  PnF index updated

                elif meets_or_exceeds_boxsize(NextO - Close_to_check, 0): # we have reversal

                    if BeforeFirstReversal == "True":  # used for Initial LastNextX&O
                        BeforeFirstReversal = "False"


                    # Start filling PnF data
                    # in the reversals we change column and keep the lastnextX&O before the reversal
                    # the boxnumber also is different
                    XO = "O"


                    if Log==True:
                        # Find how many boxes we are below nextO
                        BoxesBelowNextO = int((NextO - Close_to_check) / Boxsize)
                        # Since we are ascending and have a reversal, the NextO is 3 boxes below current boxnumber
                        Boxnumber = Boxnumber - (BoxesBelowNextO + Reversal)
                        # The Boxsize is the multiplication of Boxnumber*Boxsize+InitialClose
                        Boxvalue = Initial_Close + Boxnumber * Boxsize
                    elif Log==False:
                        Boxnumber = int(Close_to_check / Boxsize)
                        #The Boxsize is the multiplication of Boxnumber*Boxsize
                        Boxvalue = Boxnumber * Boxsize
                    #Boxvalue = round_nearest(Boxvalue, 0.00000001)
                    Boxsize_asf = ' %.8f' % (Boxsize)
                    Boxnumber_asf = ' %.8f' % (Boxnumber)
                    Boxvalue_asf = ' %.8f' % (Boxvalue)


                    if Close_to_check > Boxvalue: #This check is needed because in downwards movement
                        # the box bevaves differently, e.g. with 1 box reversal and 1 boxsize,
                        # the box with value 10 is equal to [9.01,10] or (9,10], while in
                        # upwards movement it is equal to [10, 10.99] or [10,11)
                        Boxnumber = Boxnumber + 1
                        if Log==True:
                            Boxvalue = Initial_Close + Boxnumber * Boxsize
                        elif Log==False:
                            Boxvalue = Boxnumber * Boxsize

                        Boxsize_asf = ' %.8f' % (Boxsize)
                        Boxnumber_asf = ' %.8f' % (Boxnumber)
                        Boxvalue_asf = ' %.8f' % (Boxvalue)

                    # Start filling PnF data
                    # in the reversals we change column and keep the lastnextX&O before the reversal
                    # the boxnumber also is different
                    XO = "O"
                    NextX = Boxvalue + (Boxsize * Reversal)
                    NextO = Boxvalue - Boxsize
                    LastNextX = NextX    # same as previous
                    LastNextO = NextO
                    Date = array[row,0]
                    Close = Close_to_check

                    if Reversal == 1:

                        listboxnumprevcolumn = []
                        listboxnumsamecolumn = []

                        for row in pnf_data:
                            a = row
                            if a[4] == Column-1:
                                listboxnumprevcolumn.append(a[5])
                            if a[4] == Column:
                                listboxnumsamecolumn.append(a[5])

                        if len(listboxnumsamecolumn) > 1: # more than 1 X or O has been drawned, so no 1-step back is possible
                            Column = Column + 1  # Change column
                        elif len(listboxnumsamecolumn) == 1: # if our current column has only 1 boxnumber
                            if abs(int(listboxnumsamecolumn[0])-int(listboxnumprevcolumn[-1])) == 1: # we check the previous column,
                                # in order to know the distance -> if indeed 1 or more boxes are already drawn to our column
                                print("One Step Back!") # one-step back, no new column
                            else:
                                Column = Column + 1
                        else: # column is empty, we can draw
                            Column = Column + 1
                    else:
                        Column = Column + 1 # Change column

                    if log == False:
                        Close = replaceSatoshi(Close)
                        Boxvalue = replaceSatoshi(Boxvalue)
                        NextX = replaceSatoshi(NextX)
                        NextO = replaceSatoshi(NextO)
                        LastNextX = replaceSatoshi(LastNextX)
                        LastNextO = replaceSatoshi(LastNextO)
                        Boxsize = replaceSatoshi(Boxsize)

                    new_row = np.array([Date,          # Date
                                        Close,         # Close
                                        XO,            # XO
                                        Signal,        # Signal
                                        Column,        # Column
                                        Boxnumber,     # Boxnumber
                                        Boxvalue,      # Boxvalue
                                        NextX,         # NextX
                                        NextO,         # NextO
                                        LastNextX,     # LastNextX
                                        LastNextO,     # LastNextO
                                        Boxsize,       # Boxsize
                                        Log])          # Log

                    pnf_data = np.vstack([pnf_data, new_row])

                    CurrentRowPnfArray = CurrentRowPnfArray+1     #  PnF index updated


        else:  # we are in a downwards movement
                # compare current box - currentclose and see if it's bigger than boxsize
                if meets_or_exceeds_boxsize(abs(Boxvalue - Close_to_check), Boxsize): # this check is different from the ascending
                                                              # column due to filled/empty glasses
                    if meets_or_exceeds_boxsize(NextO - Close_to_check, 0):  # first case where a new O can be drawn

                        # Start filling PnF data
                        XO = "O"

                        if Log==True:
                            # Find how many boxes we are below nextO
                            BoxesbelowNextO = int((NextO - Close_to_check) / Boxsize)
                            #Since we are descending, the NextO is 1 box below current boxnumber
                            Boxnumber = Boxnumber - (BoxesbelowNextO + 1)
                            # The Boxsize is the multiplication of Boxnumber*Boxsize+InitialClose
                            Boxvalue = Initial_Close + Boxnumber * Boxsize
                        elif Log==False:
                            Boxnumber = int(Close_to_check / Boxsize)
                            #The Boxsize is the multiplication of Boxnumber*Boxsize
                            Boxvalue = Boxnumber * Boxsize
                        #Boxvalue = round_nearest(Boxvalue, 0.00000001)
                        Boxsize_asf = ' %.8f' % (Boxsize)
                        Boxnumber_asf = ' %.8f' % (Boxnumber)
                        Boxvalue_asf = ' %.8f' % (Boxvalue)

                        if Close_to_check > Boxvalue: #This check is needed because in downwards movement
                            # the box bevaves differently, e.g. with 1 box reversal and 1 boxsize,
                            # the box with value 10 is equal to [9.01,10] or (9,10], while in
                            # upwards movement it is equal to [10, 10.99] or [10,11)
                            Boxnumber = Boxnumber + 1
                            if Log == True:
                                Boxvalue = Initial_Close + Boxnumber * Boxsize
                            elif Log == False:
                                Boxvalue = Boxnumber * Boxsize

                            Boxsize_asf = ' %.8f' % (Boxsize)
                            Boxnumber_asf = ' %.8f' % (Boxnumber)
                            Boxvalue_asf = ' %.8f' % (Boxvalue)

                        NextX = Boxvalue + (Boxsize * Reversal)
                        NextO = Boxvalue - Boxsize

                        if BeforeFirstReversal == "True":  # used for initial LastNextX&O
                            LastNextX = NextX    # same as previous
                            LastNextO = NextO

                        Date = array[row,0]
                        Close = Close_to_check
                        Column = Column

                        if log == False:
                            Close = replaceSatoshi(Close)
                            Boxvalue = replaceSatoshi(Boxvalue)
                            NextX = replaceSatoshi(NextX)
                            NextO = replaceSatoshi(NextO)
                            LastNextX = replaceSatoshi(LastNextX)
                            LastNextO = replaceSatoshi(LastNextO)
                            Boxsize = replaceSatoshi(Boxsize)

                        new_row = np.array([Date,          # Date
                                            Close,         # Close
                                            XO,            # XO
                                            Signal,        # Signal
                                            Column,        # Column
                                            Boxnumber,     # Boxnumber
                                            Boxvalue,      # Boxvalue
                                            NextX,         # NextX
                                            NextO,         # NextO
                                            LastNextX,     # LastNextX
                                            LastNextO,     # LastNextO
                                            Boxsize,       # Boxsize
                                            Log])          # Log

                        pnf_data = np.vstack([pnf_data, new_row])

                        CurrentRowPnfArray = CurrentRowPnfArray+1     #  PnF index updated

                    elif meets_or_exceeds_boxsize(Close_to_check - NextX, 0): # we have reversal

                        if BeforeFirstReversal == "True":  # used for Initial LastNextX&O
                            BeforeFirstReversal = "False"

                        if Log==True:
                            # Find how many boxes we are above nextX
                            BoxesaboveNextX = int((Close_to_check-NextX)/Boxsize)
                            #Since we are descending and we have reversal, the NextX is 3 boxes above current boxnumber
                            Boxnumber= Boxnumber + (BoxesaboveNextX + Reversal)
                            # The Boxsize is the multiplication of Boxnumber*Boxsize+InitialClose
                            Boxvalue = Initial_Close + Boxnumber * Boxsize
                        elif Log==False:
                            Boxnumber = int(Close_to_check / Boxsize)
                            #The Boxsize is the multiplication of Boxnumber*Boxsize+InitialClose
                            Boxvalue = Boxnumber * Boxsize
                        Boxsize_asf = ' %.8f' % (Boxsize)
                        Boxnumber_asf = ' %.8f' % (Boxnumber)
                        Boxvalue_asf = ' %.8f' % (Boxvalue)

                        # Start filling PnF data
                        # in the reversals we change column and keep the lastnextX&O before the reversal
                        # the boxnumber also is different
                        XO = "X"
                        NextX = Boxvalue + Boxsize
                        NextO = Boxvalue - (Boxsize * Reversal)
                        LastNextX = NextX    # same as previous
                        LastNextO = NextO
                        Date = array[row,0]
                        Close = Close_to_check

                        if Reversal == 1:  # we design a 1 box reversal chart

                            listboxnumprevcolumn = []
                            listboxnumsamecolumn = []

                            for row in pnf_data:
                                a = row
                                if a[4] == Column - 1:
                                    listboxnumprevcolumn.append(a[5])
                                if a[4] == Column:
                                    listboxnumsamecolumn.append(a[5])

                            if len(listboxnumsamecolumn) > 1:  # more than 1 X or O has been drawned, so no 1-step back is possible
                                Column = Column + 1  # Change column
                            elif len(listboxnumsamecolumn) == 1:  # if our current column has only 1 boxnumber
                                if abs(int(listboxnumsamecolumn[0]) - int(listboxnumprevcolumn[-1])) == 1:  # we check the previous column,
                                    # in order to know the distance -> if indeed 1 or more boxes are already drawn to our column
                                    print("One Step Back!")  # one-step back, no new column
                                else:
                                    Column = Column + 1
                            else:  # column is empty, we can draw
                                Column = Column + 1
                        else:
                            Column = Column+1 # Change column

                        if log == False:
                            Close = replaceSatoshi(Close)
                            Boxvalue = replaceSatoshi(Boxvalue)
                            NextX = replaceSatoshi(NextX)
                            NextO = replaceSatoshi(NextO)
                            LastNextX = replaceSatoshi(LastNextX)
                            LastNextO = replaceSatoshi(LastNextO)
                            Boxsize = replaceSatoshi(Boxsize)

                        new_row = np.array([Date,          # Date
                                           Close,         # Close
                                           XO,            # XO
                                           Signal,        # Signal
                                           Column,        # Column
                                           Boxnumber,     # Boxnumber
                                           Boxvalue,      # Boxvalue
                                           NextX,         # NextX
                                           NextO,         # NextO
                                           LastNextX,     # LastNextX
                                           LastNextO,     # LastNextO
                                           Boxsize,       # Boxsize
                                           Log])          # Log

                        #pnf_data = np.append(pnf_data, new_row,axis=0)
                        pnf_data = np.vstack([pnf_data, new_row])

                        CurrentRowPnfArray = CurrentRowPnfArray+1     #  PnF index updated

    timeaftermainloop = time.time() - timebeforemainloop

    # Concurrency - time efficiency for web app
    # if the PnF has more than 2000 Columns, then don't print the svg chart
    # if Column > 2000:
    #     # exception catch - no need to run main PnF loop
    #     result = "exception-columns more than 2000"
    #     return result
    #
    #
    # # if the PnF has huge height - i.e. difference from max to min Boxnumber, then don't print the svg chart
    # if int(np.max(pnf_data[:,5])+(np.min(pnf_data[:,5])*-1)) >= 1000:
    #     # exception catch - no need to run main PnF loop
    #     result = "exception-height more than 1000"
    #     return result


    # Uncomment this for time measurement
    #print "Total PnF main engine loop time per poloniex .json:", timeaftermainloop

    columns = ['Date','Close','XO','Signal','Column','Boxnumber','Box','NextX','NextO','LastNextX','LastNextO','Boxsize','Log']

    result = pd.DataFrame(data=pnf_data[0:,0:],  columns=columns)

    #result[['Close','Box','NextX','NextO','LastNextX','LastNextO']] = result[['Close','Box','NextX','NextO','LastNextX','LastNextO']].astype(float)

    if Log==True:
        #result[['e^Close','e^Box','e^NextX','e^NextO','e^LastNextX','e^LastNextO']] = np.exp(result[['Close','Box','NextX','NextO','LastNextX','LastNextO']])
        result[['Close', 'Box', 'NextX', 'NextO', 'LastNextX', 'LastNextO']] = result[['Close', 'Box', 'NextX', 'NextO', 'LastNextX', 'LastNextO']].astype(float)
        #result[['e^Close', 'e^Box', 'e^NextX', 'e^NextO', 'e^LastNextX', 'e^LastNextO']] = round_nearest(np.exp(result[['Close', 'Box', 'NextX', 'NextO', 'LastNextX', 'LastNextO']]), 0.00000001)
        result[['e^Close', 'e^Box', 'e^NextX', 'e^NextO', 'e^LastNextX', 'e^LastNextO']] = np.exp(result[['Close', 'Box', 'NextX', 'NextO', 'LastNextX', 'LastNextO']])
        result[['e^Close', 'e^Box', 'e^NextX', 'e^NextO', 'e^LastNextX', 'e^LastNextO']] = result[['e^Close', 'e^Box', 'e^NextX', 'e^NextO', 'e^LastNextX', 'e^LastNextO']].round(8)

        # Concurrency - time efficiency for web app
        # Keep last 300 columns if 2000 < columns < 500
        # so our chart can contain 0 to 499 columns
        if np.amax(result['Column'])>500:

            # Keep only last 300 columns
            starting_column = np.amax(result['Column']) - 300
            result = result[result['Column'] >= starting_column]

            # Start Column numbering from 0
            result['Column'] = result['Column'] - starting_column

            # Set correct index to rows - starting from 0
            index = list(range(0,len(result),1))
            result = result.set_index([index])

        return result[['Date','e^Close','XO','Signal','Column','Boxnumber','e^Box','e^NextX','e^NextO','e^LastNextX','e^LastNextO','Close','Box','NextX',
                     'NextO','LastNextX','LastNextO','Boxsize','Log']]


    elif Log==False:
        result[['Close', 'Box', 'NextX', 'NextO', 'LastNextX', 'LastNextO']] = result[['Close', 'Box', 'NextX', 'NextO', 'LastNextX', 'LastNextO']].astype(float)
        result[['Close', 'Box', 'NextX', 'NextO', 'LastNextX', 'LastNextO']] = result[['Close', 'Box', 'NextX', 'NextO', 'LastNextX', 'LastNextO']].round(8)
        result['Boxsize'] = result['Boxsize'].apply(lambda x: format(x,'.8f'))

        # Concurrency - time efficiency for web app
        # Keep last 300 columns if 2000 < columns < 500
        # so our chart can contain 0 to 499 columns
        if np.amax(result['Column'])>500:

            # Keep only last 300 columns
            starting_column = np.amax(result['Column']) - 300
            result = result[result['Column'] >= starting_column]

            # Start Column numbering from 0
            result['Column'] = result['Column'] - starting_column

            # Set correct index to rows - starting from 0
            index = list(range(0,len(result),1))
            result = result.set_index([index])

        return result[['Date','Close','XO','Signal','Column','Boxnumber','Box','NextX','NextO','LastNextX','LastNextO','Boxsize','Log']]






#  _____     _____    _____     _        _____         _
# |  _  |___|   __|  |     |___|_|___   |   __|___ ___|_|___ ___
# |   __|   |   __|  | | | | .'| |   |  |   __|   | . | |   | -_|
# |__|  |_|_|__|     |_|_|_|__,|_|_|_|  |_____|_|_|_  |_|_|_|___|
#                                                 |___|
#
#  _____ _     _        _    __
# |  |  |_|___| |_     / |  |  |   ___ _ _ _
# |     | | . |   |   / /   |  |__| . | | | |
# |__|__|_|_  |_|_|  |_/    |_____|___|_____|
#         |___|
#
#
# Description: This is the Main PnF Engine - uses Log or Arithmetic Scale values and 'High/Low' data
# for maximum performance. It is implemented using NumPy arrays for effective iteration through Pandas DataFrame.
# This approach is more effective (less time-consuming) than using DataFrame indexes for
# iteration. For the creation & testing of the engine, DuPlessis examples and data were used.
# It is one of the few (worldwide) PnF implementations that include proper initialization and
# 'one-step-back' feature (needed for 1 box reversal).
#
# Output: A Pandas DataFrame that has the following 19 columns:
# 'Date','e^High','e^Low','XO','Signal','Column','Boxnumber','e^Box','e^NextX','e^NextO','e^LastNextX',
# 'e^LastNextO','High','Low','Box','NextX','NextO','LastNextX','LastNextO','Boxsize','Log'
def main_pnf_engine_using_high_low_data(MyPandasFrame, boxsize=0.029558802, reversal=3, log=True):  # default values 3%, using 3 boxes reversal

    if log==True:
        # Calculate Natural algorithm - and add it as a new column into Dataframe
        # First we calculate logged High
        MyPandasFrame['logged high']=np.around(np.log(MyPandasFrame['high']),decimals=9)

        # Then we calculate logged Low
        MyPandasFrame['logged low']=np.around(np.log(MyPandasFrame['low']),decimals=9)

        # Parse needed columns into a numpy array to be used for iteration loop
        array = np.array(MyPandasFrame[['date','high','low','logged high','logged low','close']])
    elif log==False:
        # Parse needed columns into a numpy array to be used for iteration loop
        array = np.array(MyPandasFrame[['date','high','low','close']])

    # Set initial parameters
    CurrentRowInputArray = 0 # These two are used for keeping table row indexes after the
    CurrentRowPnfArray = 0   # initialization loop
    BeforeFirstReversal = "True"
    Date = array[0,0]
    XO = "-"
    Signal = "-"
    Column = 1
    Boxsize = boxsize # Very Important - % natural algorithm
    #  Having one of the following values:
    #  1% 0.009950331
    #  2% 0.019802627
    #  3% 0.029558802

    Boxnumber = 0 # Initial Boxnumber equals to first logged close

    if log==True:
        Box = array[0,3] # This is the value of the box and NOT the number of the box, initially we set the High
        Initial_High = array[0,3]
        Initial_Low = array[0,4]
        High = array[0,3]  # Natural log high
        Low = array[0,4]  # Natural log low
    elif log==False:
        Box = array[0,1] # This is the value of the box and NOT the number of the box, initially we set the High
        Initial_High = array[0,1]
        Initial_Low = array[0,2]
        High = array[0,1]  # Existing high
        Low = array[0,2]  # Existing low

    Initial_Value_Used_for_Box = Initial_High
    NextX = Box+Boxsize
    NextO = Box-Boxsize
    LastNextX = NextX
    LastNextO = NextO
    Reversal = reversal
    Log = log # Changes a lot of things - Engine was restructured to support every number

    # Make 2d array to store pnf data
    pnf_data = np.zeros(shape = [0,14])

    #print "Array columns look like:"
    #print "0)Date    1)High     2)Low    3)XO    4)Signal   5)Column    6)Boxnumber    7)Box"
    #print "8)NextX   9)NextO    10)LastNextX    11)LastNextO    12)Boxsize    13)Reversal    14)Log"

    # First Row is Initial Date, Initial Close
    new_row = np.array([Date,          # Date
                        High,          # High
                        Low,           # Low
                        XO,            # XO
                        Signal,        # Signal
                        Column,        # Column
                        Boxnumber,     # Boxnumber
                        Box,           # Box
                        NextX,         # NextX
                        NextO,         # NextO
                        LastNextX,     # LastNextX
                        LastNextO,     # LastNextO
                        Boxsize,       # Boxsize
                        Log])          # Log

    pnf_data = np.append(pnf_data, new_row)

    # This loop contains perfect initialization for PnF calculation - Tested with Du Plessis data
    for row in range(1,len(array),1):
        # First we check whether the next High is higher than previous High+Boxsize and if not,
        # then we check the Lows. Ignore them otherwise
        # In case of Log Scale:
        # high -> array[row,3]
        # low  -> array[row,4]
        #
        # In case of non Log Scale:
        # high -> array[row,1]
        # low  -> array[row,2]
        if Log==True:
            High_to_check = array[row,3]
            Low_to_check = array[row,4]
        elif Log==False:
            High_to_check = array[row,1]
            Low_to_check = array[row,2]

        if meets_or_exceeds_boxsize((High_to_check - Initial_High), Boxsize):  # the two Highs have a difference > Boxsize

            XO = "X" # Mark ascending trend
            Boxnumber = int((High_to_check-Initial_High)/Boxsize)+Boxnumber
            Box = Box + Boxnumber*Boxsize  # correct Box = High and Initial_Value_Used_for_Box = Initial_High
            NextX = Box+Boxsize
            NextO = Box-(Boxsize*Reversal)
            LastNextX = NextX
            LastNextO = NextO
            Date = array[row,0]
            High = High_to_check
            Low = Low_to_check
            Column = Column

            new_row = np.array([Date,          # Date
                                High,          # High
                                Low,           # Low
                                XO,            # XO
                                Signal,        # Signal
                                Column,        # Column
                                Boxnumber,     # Boxnumber
                                Box,           # Box
                                NextX,         # NextX
                                NextO,         # NextO
                                LastNextX,     # LastNextX
                                LastNextO,     # LastNextO
                                Boxsize,       # Boxsize
                                Log])          # Log

            pnf_data = np.vstack([pnf_data, new_row])

            pnf_data[0][3] = "X"  # mark previous XO
            CurrentRowInputArray = row # keeping the row index to use afterwards in the main PnF loop
            CurrentRowPnfArray = 1     # 2 records up to this point

            break


        elif meets_or_exceeds_boxsize((Initial_Low - Low_to_check), Boxsize):  # the two Lows have a difference > Boxsize

            XO = "O" # Mark descending trend
            Initial_Value_Used_for_Box = Initial_Low
            Box = Initial_Value_Used_for_Box # We use the low as the starting box
            Boxnumber = int((Initial_Low-Low_to_check)/Boxsize)*(-1)
            Box = Box + (Boxnumber*Boxsize)
            NextX = Box+(Boxsize*Reversal)
            NextO = Box-Boxsize
            LastNextX = NextX
            LastNextO = NextO
            Date = array[row,0]
            High = High_to_check
            Low = Low_to_check
            Column = Column

            new_row = np.array([Date,          # Date
                                High,          # High
                                Low,           # Low
                                XO,            # XO
                                Signal,        # Signal
                                Column,        # Column
                                Boxnumber,     # Boxnumber
                                Box,           # Box
                                NextX,         # NextX
                                NextO,         # NextO
                                LastNextX,     # LastNextX
                                LastNextO,     # LastNextO
                                Boxsize,       # Boxsize
                                Log])          # Log

            pnf_data = np.vstack([pnf_data, new_row])

            pnf_data[0][3] = "O"  # mark previous XO
            pnf_data[0][7] = Initial_Value_Used_for_Box # mark previous box using Low
            pnf_data[0][8] = Initial_Value_Used_for_Box+boxsize # mark previous NextX
            pnf_data[0][9] = Initial_Value_Used_for_Box-boxsize# mark previous NextO
            pnf_data[0][10] = Initial_Value_Used_for_Box+boxsize # mark previous LastNextX
            pnf_data[0][11] = Initial_Value_Used_for_Box-boxsize # mark previous LastNextO

            CurrentRowInputArray = row # keeping the row index to use afterwards in the main PnF loop
            CurrentRowPnfArray = 1     # 2 records up to this point

            break

    # Concurrency - time efficiency for web app
    # if user has given wrong boxsize then there will be no entry with 'X' or 'O' in the pnf_data till now,
    # leading to a run-time exception. But we can get over this:
    # if XO == "-":
    #     # exception catch - no need to run main PnF loop
    #     result = "exception-small boxsize entered"
    #     return result

    timebeforemainloop = time.time()

    # This is the main PnF loop - to be used after initialization loop
    for row in range(CurrentRowInputArray,len(array),1):  #  starting from where we left
        # Check initial XO status to see whether we are in an upwards or downwards trend
        # In case of Log Scale:
        # high -> array[row,3]
        # low  -> array[row,4]
        #
        # In case of non Log Scale:
        # high -> array[row,1]
        # low  -> array[row,2]
        #
        # For pnf_data array:
        # XO   -> pnf_data[row,3]
        # high -> pnf_data[row,1]
        # low  -> pnf_data[row,2]
        # box  -> pnf_data[row,7]

        # Concurrency - time efficiency for web app
        # If PnF Chart has more than 2000 Columns then we stop execution
        if Column > 2000:
            break

        if Log==True:
            High_to_check = array[row,3]
            Low_to_check = array[row,4]
        elif Log==False:
            High_to_check = array[row,1]
            Low_to_check = array[row,2]


        if pnf_data[CurrentRowPnfArray,3] == "X":  # we are in an upwards movement
            # Since we are in an upwards movement, we check High first
            # for the comparison we use the current Box value, and not the High!
            #if (abs(pnf_data[CurrentRowPnfArray,7] - array[row,3])) >= Boxsize:

            #  Check for higher High
            if meets_or_exceeds_boxsize(High_to_check - NextX, 0):  # first case where a new X can be drawn
                # Start filling PnF data
                XO = "X"
                # Find how many boxes we are above nextX (using High as metrix)
                BoxesaboveNextX = int((High_to_check-NextX)/Boxsize)
                #Since we are ascending, the NextX is 1 box above current boxnumber
                Boxnumber=Boxnumber+BoxesaboveNextX+1
                #The Boxsize is the multiplication of Boxnumber*Boxsize+Initial_Value_Used_for_Box
                Box = Initial_Value_Used_for_Box + Boxnumber*Boxsize
                NextX = Box+Boxsize
                NextO = Box-(Boxsize*Reversal)

                if BeforeFirstReversal == "True":  # used for initial LastNextX&O
                    LastNextX = NextX    # same as previous
                    LastNextO = NextO

                Date = array[row,0]
                High = High_to_check
                Low = Low_to_check
                Column = Column

                new_row = np.array([Date,          # Date
                                    High,          # High
                                    Low,           # Low
                                    XO,            # XO
                                    Signal,        # Signal
                                    Column,        # Column
                                    Boxnumber,     # Boxnumber
                                    Box,           # Box
                                    NextX,         # NextX
                                    NextO,         # NextO
                                    LastNextX,     # LastNextX
                                    LastNextO,     # LastNextO
                                    Boxsize,       # Boxsize
                                    Log])          # Log

                pnf_data = np.vstack([pnf_data, new_row])

                #CurrentRowInputArray = row # keeping the row index to use afterwards in the main PnF loop
                CurrentRowPnfArray = CurrentRowPnfArray+1     #  PnF index updated


            # We didn't find a higher High, we check Lows to see if there is a reversal
            elif Low_to_check<=NextO:

                if Reversal != 1:
                    if BeforeFirstReversal == "True":  # used for Initial LastNextX&O
                        BeforeFirstReversal = "False"
                # Start filling PnF data
                # in the reversals we change column and keep the lastnextX&O before the reversal
                # the boxnumber also is different
                XO = "O"
                LastNextX = NextX    # same as previous
                LastNextO = NextO
                # Find how many boxes we are below nextO
                BoxesBelowNextO = int((NextO-Low_to_check)/Boxsize)
                #Since we are ascending and have a reversal, the NextO is 3 boxes below current boxnumber
                Boxnumber=Boxnumber-(BoxesBelowNextO+Reversal)
                #The Boxsize is the multiplication of Boxnumber*Boxsize+Initial_Value_Used_for_Box
                Box = Initial_Value_Used_for_Box + Boxnumber*Boxsize
                NextX = Box+(Boxsize*Reversal)
                NextO = Box-Boxsize
                Date = array[row,0]
                High = High_to_check
                Low = Low_to_check

                if Reversal == 1:  # we design a 1 box reversal chart

                    Column = Column + 1

                    if BeforeFirstReversal == "True":
                        BeforeFirstReversal == "False"

                    if ((pnf_data[CurrentRowPnfArray-1,3] == XO) & (abs(pnf_data[CurrentRowPnfArray,6]*100000000-pnf_data[CurrentRowPnfArray-1,6]*100000000) == 1)):
                        #print "One Step Back!!!"
                        Column = Column-1
                else:
                    Column = Column+1 # Change column

                new_row = np.array([Date,          # Date
                                    High,          # High
                                    Low,           # Low
                                    XO,            # XO
                                    Signal,        # Signal
                                    Column,        # Column
                                    Boxnumber,     # Boxnumber
                                    Box,           # Box
                                    NextX,         # NextX
                                    NextO,         # NextO
                                    LastNextX,     # LastNextX
                                    LastNextO,     # LastNextO
                                    Boxsize,       # Boxsize
                                    Log])          # Log

                pnf_data = np.vstack([pnf_data, new_row])

                CurrentRowPnfArray = CurrentRowPnfArray+1     #  PnF index updated

        # In case of Log Scale:
        # high -> array[row,3]
        # low  -> array[row,4]
        #
        # In case of non Log Scale:
        # high -> array[row,1]
        # low  -> array[row,2]
        #
        # For pnf_data array:
        # XO   -> pnf_data[row,3]
        # high -> pnf_data[row,1]
        # low  -> pnf_data[row,2]
        # box  -> pnf_data[row,7]

        elif pnf_data[CurrentRowPnfArray,3] == "O":   # we are in a downwards movement - XO = "O"
            # We compare current Low with next Low to see if their difference bigger than boxsize
            # We have lower Low
            if meets_or_exceeds_boxsize(NextO - Low_to_check, 0):  # first case where a new O can be drawn
                if Low_to_check == NextO:
                    checkO = "exact_box_floor_price"
                # Start filling PnF data
                XO = "O"
                # Find how many boxes we are below nextO
                BoxesbelowNextO = int((NextO-Low_to_check)/Boxsize)
                #Since we are descending, the NextO is 1 box below current boxnumber
                Boxnumber=Boxnumber-(BoxesbelowNextO+1)
                #The Boxsize is the multiplication of Boxnumber*Boxsize+Initial_Value_Used_for_Box
                Box = Initial_Value_Used_for_Box + Boxnumber*Boxsize
                NextX = Box+(Boxsize*Reversal)
                NextO = Box-Boxsize

                if BeforeFirstReversal == "True":  # used for initial LastNextX&O
                    LastNextX = NextX    # same as previous
                    LastNextO = NextO

                Date = array[row,0]
                High = High_to_check
                Low = Low_to_check
                Column = Column

                new_row = np.array([Date,          # Date
                                    High,          # High
                                    Low,           # Low
                                    XO,            # XO
                                    Signal,        # Signal
                                    Column,        # Column
                                    Boxnumber,     # Boxnumber
                                    Box,           # Box
                                    NextX,         # NextX
                                    NextO,         # NextO
                                    LastNextX,     # LastNextX
                                    LastNextO,     # LastNextO
                                    Boxsize,       # Boxsize
                                    Log])          # Log

                pnf_data = np.vstack([pnf_data, new_row])

                CurrentRowPnfArray = CurrentRowPnfArray+1     #  PnF index updated

            # Check for higher High to see whether we have a reversal
            elif meets_or_exceeds_boxsize(High_to_check - NextX, 0):

                if Reversal != 1:
                    if BeforeFirstReversal == "True":  # used for Initial LastNextX&O
                        BeforeFirstReversal = "False"

                # Start filling PnF data
                # in the reversals we change column and keep the lastnextX&O before the reversal
                # the boxnumber also is different
                XO = "X"
                LastNextX = NextX    # same as previous
                LastNextO = NextO

                # Find how many boxes we are above nextX
                BoxesaboveNextX = int((High_to_check-NextX)/Boxsize)

                #Since we are descending and we have reversal, the NextX is 3 boxes above current boxnumber
                Boxnumber=Boxnumber+(BoxesaboveNextX+Reversal)

                #The Boxsize is the multiplication of Boxnumber*Boxsize+Initial_Value_Used_for_Box
                Box = Initial_Value_Used_for_Box + Boxnumber*Boxsize

                NextX = Box+Boxsize
                NextO = Box-(Boxsize*Reversal)
                Date = array[row,0]
                High = High_to_check
                Low = Low_to_check

                if Reversal == 1:  # we design a 1 box reversal chart
                    Column = Column + 1

                    if BeforeFirstReversal == "True":  # used for Initial LastNextX&O
                        BeforeFirstReversal = "False"

                    if ((pnf_data[CurrentRowPnfArray-1,3] == XO) & (abs(pnf_data[CurrentRowPnfArray,6]-pnf_data[CurrentRowPnfArray-1,6]) == 1)):
                        #print "One Step Back!!!"
                        Column = Column-1

                else:
                    Column = Column+1 # Change column

                new_row = np.array([Date,          # Date
                                    High,          # High
                                    Low,           # Low
                                    XO,            # XO
                                    Signal,        # Signal
                                    Column,        # Column
                                    Boxnumber,     # Boxnumber
                                    Box,           # Box
                                    NextX,         # NextX
                                    NextO,         # NextO
                                    LastNextX,     # LastNextX
                                    LastNextO,     # LastNextO
                                    Boxsize,       # Boxsize
                                    Log])          # Log

                #pnf_data = np.append(pnf_data, new_row,axis=0)

                pnf_data = np.vstack([pnf_data, new_row])

                CurrentRowPnfArray = CurrentRowPnfArray+1     #  PnF index updated

    timeaftermainloop = time.time() - timebeforemainloop

    # Concurrency - time efficiency for web app
    # if the PnF has more than 2000 Columns, then don't print the svg chart
    #if Column > 2000:
    #    # exception catch - no need to run main PnF loop
    #    result = "exception-columns more than 2000"
    #    return result
    ## if the PnF has huge height - i.e. difference from max to min Boxnumber, then don't print the svg chart
    #if int(np.max(pnf_data[:,6])+(np.min(pnf_data[:,6])*-1)) >= 1000:
    #    # exception catch - no need to run main PnF loop
    #    result = "exception-height more than 1000"
    #    return result

    # Uncomment this for time measurement
    #print "Total PnF main engine loop time per poloniex .json:", timeaftermainloop

    columns = ['Date','High','Low','XO','Signal','Column','Boxnumber','Box','NextX','NextO','LastNextX','LastNextO','Boxsize','Log']

    result = pd.DataFrame(data=pnf_data[0:,0:],  columns=columns)

    result[['High','Low','Box','NextX','NextO','LastNextX','LastNextO']] = result[['High','Low','Box','NextX','NextO','LastNextX',
                                                                                   'LastNextO']].astype(float)

    if Log==True:
        result[['e^High','e^Low','e^Box','e^NextX','e^NextO','e^LastNextX','e^LastNextO']] =np.exp(result[['High','Low','Box','NextX',
                                                                                                           'NextO','LastNextX','LastNextO']])
        result[['e^High','e^Low','e^Box','e^NextX','e^NextO','e^LastNextX','e^LastNextO']] = result[['e^High','e^Low','e^Box','e^NextX','e^NextO','e^LastNextX','e^LastNextO']].round(8)

        # Concurrency - time efficiency for web app
        # Keep last 300 columns if 2000 < columns < 500
        # so our chart can contain 0 to 499 columns
        if np.amax(result['Column'])>500:

            # Keep only last 300 columns
            starting_column = np.amax(result['Column']) - 300
            result = result[result['Column'] >= starting_column]

            # Start Column numbering from 0
            result['Column'] = result['Column'] - starting_column

            # Set correct index to rows - starting from 0
            index = list(range(0,len(result),1))
            result = result.set_index([index])

        return result[['Date','e^High','e^Low','XO','Signal','Column','Boxnumber','e^Box','e^NextX','e^NextO','e^LastNextX',
                       'e^LastNextO','High','Low','Box','NextX','NextO','LastNextX','LastNextO','Boxsize','Log']]


    elif Log==False:
        result[['High', 'Low', 'Box', 'NextX', 'NextO', 'LastNextX', 'LastNextO']] = result[['High', 'Low', 'Box', 'NextX', 'NextO', 'LastNextX', 'LastNextO']].round(8)
        result['Boxsize'] = result['Boxsize'].apply(lambda x: format(x,'.8f'))

        # Concurrency - time efficiency for web app
        # Keep last 300 columns if 2000 < columns < 500
        # so our chart can contain 0 to 499 columns
        if np.amax(result['Column'])>500:

            # Keep only last 300 columns
            starting_column = np.amax(result['Column']) - 300
            result = result[result['Column'] >= starting_column]

            # Start Column numbering from 0
            result['Column'] = result['Column'] - starting_column

            # Set correct index to rows - starting from 0
            index = list(range(0,len(result),1))
            result = result.set_index([index])

        return result[['Date','High','Low','XO','Signal','Column','Boxnumber','Box','NextX','NextO','LastNextX','LastNextO','Boxsize','Log']]





#      _____     _____    _____ _             _    ____      _           _   _
#     |  _  |___|   __|  |   __|_|___ ___ ___| |  |    \ ___| |_ ___ ___| |_|_|___ ___
#     |   __|   |   __|  |__   | | . |   | .'| |  |  |  | -_|  _| -_|  _|  _| | . |   |
#     |__|  |_|_|__|     |_____|_|_  |_|_|__,|_|  |____/|___|_| |___|___|_| |_|___|_|_|
#                                |___|
#
#      _____         _
#     |   __|___ ___|_|___ ___
#     |   __|   | . | |   | -_|
#     |_____|_|_|_  |_|_|_|___|
#               |___|
#
# Description: This is the PnF Signal Detection Engine - having as input the DataFrame
# created by the Main PnF Engine. It is implemented using DataFrame indexes for iteration.
# It searches for Double Top/Double Bottom signal patterns & Breakouts.
#
# Output: An .html file containing the result of the processed Pandas DataFrame, with the
# 'Signal' Column updated
def pnf_signal_detection_engine(result, filename, boxsize=0.029558802, reversal=3, highlow_close="high_low"):  # default values 3%, using 3 boxes reversal

    timebeforemainloop = time.time() # Used to measure execution time of the loop

    # Beginning of signal detection - "Double Top" - "Double Bottom"
    Column_ix = result.columns.get_loc('Column') # get column index of column "Column"
    Signal_ix = result.columns.get_loc('Signal') # get column index of column "Signal"
    XO_ix = result.columns.get_loc('XO') # get column index of column "XO"
    LastNextX_ix = result.columns.get_loc('LastNextX') # get column index of column "LastNextX"
    LastNextO_ix = result.columns.get_loc('LastNextO') # get column index of column "LastNextO"
    Box_ix = result.columns.get_loc('Box') # get column index of column "Box"
    run_once_flagX = 0 # this flag is to save the 2columns previous lastnextX while preserving upwards movement
    run_once_flagY = 0 # this flag is to save the 2columns previous lastnextO while preserving downwards movement
    dt_breakout_once = False # this flag is to print the Double Top Breakout once per upwards movement
    db_breakout_once = False # this flag is to print the Double Bottom Breakout once per downwards movement
    Boxsize = boxsize # Very Important - % natural algorithm
    Reversal = reversal


    for row in range(0,len(result),1): # beginning scanning the table row-by-row
        if result.iat[row,Column_ix] >= 5: # we start with the 5th column

            if result.iat[row,XO_ix] == 'X': # we are in an upwards move

                #Initialize these two flags because we are in the opposite movement
                run_once_flagY = 0
                db_breakout_once = False

                # find maximum box number of previous column and check for a breakout - many ways to do this
                # we use the LastNext of the previous row - we also save the value referral till reversal
                if run_once_flagX == 0:
                    LastNextX2columnsbefore = result.iat[row-1,LastNextX_ix]
                    run_once_flagX = 1
                    doubletop = False
                    doubletop_breakout = False
                    db_breakout_once = False

                if (doubletop_breakout & doubletop)== False:
                    if result.iat[row,Box_ix]  >= LastNextX2columnsbefore: # Current box is above LastNextX
                        #Thus we have a Double Top breakout
                        if dt_breakout_once == False:
                            result.iat[row,Signal_ix] = "Double Top Breakout" # Print it once per upwards movement
                            dt_breakout_once = True

                        doubletop = True
                        doubletop_breakout = True

                    elif result.iat[row,Box_ix]  == (LastNextX2columnsbefore-Boxsize): # Current box is at the same previous peak
                        # We have a Double Top
                        result.iat[row,Signal_ix] = "Double Top"
                        #doubletop = True

            if result.iat[row,XO_ix] == 'O': # we are in an downwards move

                #Initialize these two flags because we are in the opposite movement
                run_once_flagX = 0
                dt_breakout_once = False

                # find minimum box number of previous column and check for a breakout - many ways to do this
                # we use the LastNextO of the previous row - we also save the value for referral till reversal
                if run_once_flagY == 0:
                    LastNextO2columnsbefore = result.iat[row-1,LastNextO_ix]
                    run_once_flagY = 1
                    doublebottom = False
                    doublebottom_breakout = False
                    dt_breakout_once = False

                if (doublebottom_breakout & doublebottom)== False:
                    if result.iat[row,Box_ix]  <= LastNextO2columnsbefore: # Current box is above LastNextX
                        #Thus we have a Double Top breakout
                        if db_breakout_once == False:
                            result.iat[row,Signal_ix] = "Double Bottom Breakout" # Print it once per upwards movement
                            db_breakout_once = True

                        doublebottom = True
                        doublebottom_breakout = True
                    elif result.iat[row,Box_ix]  == (LastNextO2columnsbefore+Boxsize): # Current box is at the same previous peak
                        # We have a Double Top
                        result.iat[row,Signal_ix] = "Double Bottom"


    timeaftermainloop = time.time() - timebeforemainloop # Total loop time

    # Uncomment this for time measurement
    #print "Total PnF Signal Detection Engine loop time per poloniex .json:", timeaftermainloop

    # TIP (Boxsize):
    #Having one of the following values:
    #1% 0.009950331
    #2% 0.019802627
    #3% 0.029558802

    # The code below stores and names the created .html file
    if highlow_close=="high_low":  # Process was done on a High/Low Df

        High_Low_PnF_data_folder = "High_Low_PnF_data"

        if ff.is_dir_exist(High_Low_PnF_data_folder)==False:
            ff.create_dir(High_Low_PnF_data_folder)

        if Boxsize == 0.009950331:

            print("Processing "+filename+" High/Low 1% * "+str(Reversal))
            new_html_filename = filename+" 1 percent - "+str(Reversal)+" box reversal - High Low"+".html"
            result.to_html(open(High_Low_PnF_data_folder+"\\"+new_html_filename, 'w'))

        elif Boxsize == 0.019802627:
            print("Processing "+filename+" High/Low 2% * "+str(Reversal))
            new_html_filename = filename+" 2 percent - "+str(Reversal)+" box reversal - High Low"+".html"
            result.to_html(open(High_Low_PnF_data_folder+"\\"+new_html_filename, 'w'))

        elif Boxsize == 0.029558802:
            print("Processing "+filename+" High/Low 3% * "+str(Reversal))
            new_html_filename = filename+" 3 percent - "+str(Reversal)+" box reversal - High Low"+".html"
            result.to_html(open(High_Low_PnF_data_folder+"\\"+new_html_filename, 'w'))

        else: # non-log Boxsize
            print("Processing "+filename+" High/Low "+str(Boxsize)+" * "+str(Reversal))
            new_html_filename = filename+" "+str(format(Boxsize,'.8f'))+" - "+str(Reversal)+" box reversal - High Low"+".html"
            result.to_html(open(High_Low_PnF_data_folder+"\\"+new_html_filename, 'w'))

    elif highlow_close=="close":  # Process was done on a Close Df

        Close_PnF_data_folder = "Close_PnF_data"

        if ff.is_dir_exist(Close_PnF_data_folder)==False:
            ff.create_dir(Close_PnF_data_folder)

        if Boxsize == 0.009950331:
            print("Processing "+filename+" Close 1% * "+str(Reversal))
            new_html_filename = filename+" 1 percent - "+str(Reversal)+" box reversal - Close"+".html"
            result.to_html(open(Close_PnF_data_folder+"\\"+new_html_filename, 'w'))

        elif Boxsize == 0.019802627:
            print("Processing "+filename+" Close 2% * "+str(Reversal))
            new_html_filename = filename+" 2 percent - "+str(Reversal)+" box reversal - Close"+".html"
            result.to_html(open(Close_PnF_data_folder+"\\"+new_html_filename, 'w'))

        elif Boxsize == 0.029558802:
            print("Processing "+filename+" Close 3% * "+str(Reversal))
            new_html_filename = filename+" 3 percent - "+str(Reversal)+" box reversal - Close"+".html"
            result.to_html(open(Close_PnF_data_folder+"\\"+new_html_filename, 'w'))

        else: # non-log Boxsize
            print("Processing "+filename+" Close "+str(Boxsize)+" * "+str(Reversal))
            new_html_filename = filename+" "+str(format(Boxsize,'.8f'))+" - "+str(Reversal)+" box reversal - Close"+".html"
            result.to_html(open(Close_PnF_data_folder+"\\"+new_html_filename, 'w'))




#
#     _____ _             _    _____     _   _ ___ _         _   _            _____             _
#    |   __|_|___ ___ ___| |  |   | |___| |_|_|  _|_|___ ___| |_|_|___ ___   |   __|___ ___ _ _|_|___ ___
#    |__   | | . |   | .'| |  | | | | . |  _| |  _| |  _| .'|  _| | . |   |  |__   | -_|  _| | | |  _| -_|
#    |_____|_|_  |_|_|__,|_|  |_|___|___|_| |_|_| |_|___|__,|_| |_|___|_|_|  |_____|___|_|  \_/|_|___|___|
#            |___|
#
#
# Description: Signal Notification Service - checks whether a Double Top/Double Bottom or a
# Double Top/Double Bottom Breakout has occurred and notifies the user at runtime
#
# Output: Invokes a Message Pop-up Window with relevant details
def signal_notification_service(result, filename, highlow_close="high_low", boxsize=0.029558802, reversal=3, log=True):

    Boxsize = boxsize
    Reversal = reversal

    # Set indexes for DataFrame columns
    Signal_ix = result.columns.get_loc('Signal') # get column index of column "Signal"

    if log==True:
        NextX_ix = result.columns.get_loc('e^NextX') # get column index of column "e^NextX"
        NextO_ix = result.columns.get_loc('e^NextO') # get column index of column "e^NextO"
    elif log==False:
        NextX_ix = result.columns.get_loc('NextX') # get column index of column "NextX"
        NextO_ix = result.columns.get_loc('NextO') # get column index of column "NextO"

    if highlow_close=="close":
        if log==True:
            Close_ix = result.columns.get_loc('e^Close') # get column index of column "e^Close"
        elif log==False:
            Close_ix = result.columns.get_loc('Close') # get column index of column "Close"
    elif highlow_close=="high_low":
        if log==True:
            High_ix = result.columns.get_loc('e^High') # get column index of column "e^High"
            Low_ix = result.columns.get_loc('e^Low') # get column index of column "e^Low"
            #Close_ix = result.columns.get_loc('e^Close') # get column index of column "e^Close"
        elif log==False:
            High_ix = result.columns.get_loc('High') # get column index of column "High"
            Low_ix = result.columns.get_loc('Low') # get column index of column "Low"

    if log==True:
        Box_ix = result.columns.get_loc('e^Box') # get column index of column "e^Box"
    elif log==False:
        Box_ix = result.columns.get_loc('Box') # get column index of column "Box"

    # Set values of last row to strings, after appropriate rounding - used in bot messaging
    Signal = str(result.iat[len(result)-1,Signal_ix])
    if highlow_close=="close":
        Close  = str(format(np.around((result.iat[len(result)-1,Close_ix]),decimals=8),'.8f'))
    elif highlow_close=="high_low":
        High = str(format(np.around((result.iat[len(result)-1,High_ix]),decimals=8),'.8f'))
        Low = str(format(np.around((result.iat[len(result)-1,Low_ix]),decimals=8),'.8f'))
        #Close  = str(np.around((result.iat[len(result)-1,Close_ix]),decimals=8))

    Current_Box = str(format(np.around((result.iat[len(result)-1,Box_ix]),decimals=8),'.8f'))
    NextX = str(format(np.around((result.iat[len(result)-1,NextX_ix]),decimals=8),'.8f'))
    NextO = str(format(np.around((result.iat[len(result)-1,NextO_ix]),decimals=8),'.8f'))


    if (result.iat[len(result)-1,Signal_ix] == "Double Bottom")|(result.iat[len(result)-1,Signal_ix] == "Double Bottom Breakout")\
        |(result.iat[len(result)-1,Signal_ix] == "Double Top") | (result.iat[len(result)-1,Signal_ix] == "Double Top Breakout"):

        # This is used for Slack integration
        # For methods see https://api.slack.com/methods/chat.postMessage
        # This token belongs to the 'crypt-xo_bot' user
        token = os.getenv("SLACK_TOKEN", "")

        # Create a SlackClient instance
        # sc = SlackClient(token)

        if highlow_close=="close":

            # Message for bot to be posted
            message_for_bot = Signal+" signal Detected!\n"+\
                          " \nDetails:"+\
                          "\n\t\t Pair:         "+filename+\
                          "\n\t\t Close:        "+Close+\
                          "\n\t\t Current Box:  "+Current_Box+\
                          "\n\t\t Next X:       "+NextX+\
                          "\n\t\t Next O:       "+NextO+\
                          "\n\n"

            # Username of bot - varies according to the processed filename and boxsize
            if Boxsize == 0.009950331:
                username_for_bot = "Crypt-XO BOT Engine: Poloniex PnF 1% * "+str(Reversal)+ " Close"
            elif Boxsize == 0.019802627:
                username_for_bot = "Crypt-XO BOT Engine: Poloniex PnF 2% * "+str(Reversal)+ " Close"
            elif Boxsize == 0.029558802:
                username_for_bot = "Crypt-XO BOT Engine: Poloniex PnF 3% * "+str(Reversal)+ " Close"
            else:
                username_for_bot = "Crypt-XO BOT Engine: Poloniex PnF "+str(Boxsize)+" * "+str(Reversal)+ " Close"

        elif highlow_close=="high_low":

            # Message for bot to be posted
            message_for_bot = Signal+" signal Detected!\n"+\
                              " \nDetails:"+\
                              "\n\t\t Pair:         "+filename+\
                              "\n\t\t High:         "+High+\
                              "\n\t\t Low:          "+Low+\
                              "\n\t\t Current Box:  "+Current_Box+\
                              "\n\t\t Next X:       "+NextX+\
                              "\n\t\t Next O:       "+NextO+\
                              "\n\n"

            # Username of bot - varies according to the processed filename and boxsize
            if Boxsize == 0.009950331:
                username_for_bot = "Crypt-XO BOT Engine: Poloniex PnF 1% * "+str(Reversal)+" High Low"
            elif Boxsize == 0.019802627:
                username_for_bot = "Crypt-XO BOT Engine: Poloniex PnF 2% * "+str(Reversal)+" High Low"
            elif Boxsize == 0.029558802:
                username_for_bot = "Crypt-XO BOT Engine: Poloniex PnF 3% * "+str(Reversal)+" High Low"
            else:
                username_for_bot = "Crypt-XO BOT Engine: Poloniex PnF "+str(Boxsize)+" * "+str(Reversal)+ " High Low"

        # Currently 3 bot system: 1) Slack, 2) Windows Message Box, 3) Python Console

        # 1. This call posts a slack message into bot channel
        #print sc.api_call(
        #    "chat.postMessage", channel="#bot", text=message_for_bot,
        #    username=username_for_bot, icon_emoji=':robot_face:'
        #)

        # 2. This call creates a popup window for the Windows OS
        #win32api.MessageBox(0, message_for_bot, username_for_bot, 0x00001000)   # This will be expanded to provide further
                                                                                # details, i.e.: Box, coin name etc

        # 3. Python Console
        print("                                                      ")
        print(" _____             _       __ __ _____    _       _   ")
        print("|     |___ _ _ ___| |_ ___|  |  |     |  | |_ ___| |_ ")
        print("|   --|  _| | | . |  _|___|-   -|  |  |  | . | . |  _|")
        print("|_____|_| |_  |  _|_|     |__|__|_____|  |___|___|_|  ")
        print("          |___|_|                                     ")
        print("                                                      ")
        print(username_for_bot)
        print(message_for_bot)
        print("------------------------------------------------------")



#
#   _____ _           _   _            _____         _
#  |     | |_ ___ ___| |_|_|___ ___   |   __|___ ___|_|___ ___
#  |   --|   | .'|  _|  _| |   | . |  |   __|   | . | |   | -_|
#  |_____|_|_|__,|_| |_| |_|_|_|_  |  |_____|_|_|_  |_|_|_|___|
#                              |___|            |___|
#
#
# Description: Charting Engine - obvious use by its name
#
# Output: Generates an SVG chart, with appropriate filename.
# 'highlow_close' is used just for naming the SVG file.
def charting_engine(result, filename, highlow_close="high_low", boxsize=0.029558802, reversal=3, log=True):
    # Start experimenting with the drawing function
    # the height of the graph is determined by the min&max Boxnumber + some buffer, e.g. 5 boxes up & down
    minimum_Boxnumber = int(np.amin(result[['Boxnumber']]))
    maximum_Boxnumber = int(np.amax(result[['Boxnumber']]))
    buffer_Boxnumber_down = 20
    buffer_Boxnumber_up = 20
    box = boxsize

    # Used for debugging
    #print ("Minimum Boxnumber:", minimum_Boxnumber)
    #print ("Maximum Boxnumber:", maximum_Boxnumber)

    # the width of the grapsh is determined by the number of columns + some buffer, e.g. 5 more columns
    maximum_Column = int(np.amax(result[['Column']]))
    buffer_Column = 5

    # Used for debugging
    #print "Maximum Column:", maximum_Column

    # to print the Boxes Scale, we take the first e^Box and calculate relevant boxes,
    # depending on the min&max Boxnumber + buffer and Boxsize (e.g. 0.029558802)
    # the initial e^Box (or Box when log scale is used) is also helpful as a reference point
    initial_Box = result['Box'][0]
    # Used for debugging
    #print ("Initial Box:", initial_Box)

    # Used for filename
    box_string = ""
    if box == 0.009950331:
        box_string = "1 percent - "+str(reversal)+" reversal"
    elif box == 0.019802627:
        box_string = "2 percent - "+str(reversal)+" reversal"
    elif box == 0.029558802:
        box_string = "3 percent - "+str(reversal)+" reversal"
    elif box == 0.00000001:
        box_string = "1 Satoshi - "+str(reversal)+" reversal"
    elif box == 0.00000002:
        box_string = "2 Satoshi - "+str(reversal)+" reversal"
    elif box == 0.00000005:
        box_string = "5 Satoshi - "+str(reversal)+" reversal"
    elif box == 0.00000010:
        box_string = "10 Satoshi - "+str(reversal)+" reversal"
    elif box == 0.00000020:
        box_string = "20 Satoshi - "+str(reversal)+" reversal"
    elif box == 0.00000025:
        box_string = "25 Satoshi - "+str(reversal)+" reversal"
    elif box == 0.00000100:
        box_string = "100 Satoshi - "+str(reversal)+" reversal"
    elif box == 0.00000150:
        box_string = "150 Satoshi - "+str(reversal)+" reversal"
    elif box == 0.00000200:
        box_string = "200 Satoshi - "+str(reversal)+" reversal"
    elif box == 0.00000250:
        box_string = "250 Satoshi - "+str(reversal)+" reversal"
    elif box == 0.00000500:
        box_string = "500 Satoshi - "+str(reversal)+" reversal"
    elif box == 0.00001000:
        box_string = "1000 Satoshi - "+str(reversal)+" reversal"

    # The code below stores and names the created .html file
    if highlow_close=="high_low":  # Process was done on a High/Low Df

        High_Low_PnF_data_folder = "High_Low_PnF_data"

        if ff.is_dir_exist(High_Low_PnF_data_folder)==False:
            ff.create_dir(High_Low_PnF_data_folder)

        filename = High_Low_PnF_data_folder+"\\"+filename


    elif highlow_close=="close":  # Process was done on a Close Df

        Close_PnF_data_folder = "Close_PnF_data"

        if ff.is_dir_exist(Close_PnF_data_folder)==False:
            ff.create_dir(Close_PnF_data_folder)

        filename = Close_PnF_data_folder+"\\"+filename


    # maximum height in pixels?
    max_height_pixels = (maximum_Boxnumber-minimum_Boxnumber)+buffer_Boxnumber_down+buffer_Boxnumber_up+buffer_Column
    max_height_pixels = max_height_pixels*35
    offset_from_left_x = 185

    # Chart SVG must have:
    # preserveAspectRatio = "xMinYMin meet"
    # width = offset_from_left_x+((maximum_Column+3)*40)
    # height = max_height_pixels- (35*4)

    # Create SVG drawing
    dwg = svgwrite.Drawing(filename=filename+"_"+highlow_close+" "+box_string+'.svg', profile='full',preserveAspectRatio="xMinYMin meet",
                           #size=(offset_from_left_x+((maximum_Column+3)*40),(max_height_pixels- (35*4))))
                           #size=((offset_from_left_x+(maximum_Column+3)*40)*0.6,(max_height_pixels- (35*4))*0.6),id="clickable",onclick="loadSVG()")
                           #size=((offset_from_left_x+(maximum_Column)*35)*0.6,(max_height_pixels- (35*4))*0.6),id="clickable",onclick="loadSVG()")
                           size=(((maximum_Column+buffer_Column+3)*35)*0.6,(max_height_pixels- (35*4))*0.6),id="clickable",onclick="loadSVG()")

    group_chart = dwg.add(dwg.g(transform = "scale(0.6)"))

    # Viewbox - important for SVG scaling
    j = 50

    # Scale SVG must have:
    # preserveAspectRatio = "xMinYMin meet"
    # width = offset_from_left_x
    # height = max_height_pixels

    # Create SVG drawing
    dwg2 = svgwrite.Drawing(filename=filename+"_"+highlow_close+" "+box_string+'_scale'+'.svg', profile='full',preserveAspectRatio="xMinYMin meet",
                            style="margin-bottom: 10;",
                            #size=(offset_from_left_x*0.6,max_height_pixels*0.6))
                            size=(offset_from_left_x*0.6,(max_height_pixels- (35*4))*0.6))

    group_scale = dwg2.add(dwg2.g(transform = "scale(0.6)"))

    # Construction of scale
    for i in range((maximum_Boxnumber+buffer_Boxnumber_up),(minimum_Boxnumber-buffer_Boxnumber_down),-1):
        if log==True:
            Box = np.around(np.exp(initial_Box+(box*i)),decimals=8)
        elif log==False:
            #Box = np.around(initial_Box+(box*i),decimals=8)
            Box = np.around((box * i), decimals=8)
            #print(initial_Box,box)
        Box = format(Box, '.8f')
        #np.around(np.exp(initial_Box+(box*i)),decimals=8)

        #print "i:",i," Box:",Box

        # depict scale in svg
        y2 = str(j)
        y3 = str(j+5)
        # add Boxes
        text = dwg2.text(Box,insert=(0,y2),style = ("font-size:30px; font-weight:600; font-family:sans-serif; fill:grey;"))
        # add horizontal lines
        #line = dwg2.line(start=(0,y3), end=(offset_from_left_x+((maximum_Column+6)*40),y3), stroke=svgwrite.rgb(10, 10, 16, '%'), fill="#598da6")
        line = dwg2.line(start=(0,y3), end=(offset_from_left_x,y3), stroke="grey", fill="#598da6")
        j += 35

        group_scale.add(text)
        group_scale.add(line)

    # add first vertical line
    line = dwg2.line(start=(180,25), end=(180,max_height_pixels-(35*4)), stroke="grey", fill="#598da6")
    group_scale.add(line)
    #dwg2.viewbox(width=offset_from_left_x*0.6, height=max_height_pixels*0.6)
    dwg2.viewbox(width=offset_from_left_x*0.6, height=(max_height_pixels- (35*4))*0.6)
    dwg2.save()

    array = np.array(result[['XO','Column','Boxnumber']])

    # loop to draw pnf by iterating through dataframe
    flag_first_column = 0
    for row in range (0,len(array),1):

        XO = array[row,0]
        Column = array[row,1]-1 # -1 is to make first column appear outmost left, at zero pixels
        Boxnumber = array[row,2]
        #print "Row",row
        #print "XO",XO
        #print "Column",Column
        #print "Boxnumber",Boxnumber

        # the offset from above is 50px - this is the maximum boxnumber
        # so, if we begin using a top-down approach, like we did for the scale,
        # then we should calculate the distance between each boxnumber and maximum
        # boxnumber (max height)
        offset_from_above = 50
        height = maximum_Boxnumber - Boxnumber + buffer_Boxnumber_up

        offset_y = offset_from_above + (height*35)
        #offset_from_left_x = 185
        #offset_x = offset_from_left_x + (Column*40)
        offset_x = (Column*35)+5

        # column distance = current column*40 - Used for x axis
        if XO == "O":
            if row > 0:
                if array[row-1,0] == "X": # we come from a reversal
                    # check for middle O boxes
                    #print "Coming from reversal - previous column was X - missing O boxes found!!"
                    # find how many boxes should be written
                    number_boxes_in_middle = abs(array[row-1, 2]-Boxnumber)
                    for i in range(1,number_boxes_in_middle,1):
                        # start drawing middle boxes
                        missing_boxnumber = Boxnumber+i
                        #print "missing_boxnumber",  missing_boxnumber
                        missing_box_height = maximum_Boxnumber - missing_boxnumber + buffer_Boxnumber_up

                        missing_offset_y = offset_from_above + (missing_box_height*35)
                        #offset_from_left_x = 185
                        #missing_offset_x = offset_from_left_x + (Column*40)

                        #text = dwg.text("O",insert=(missing_offset_x,missing_offset_y),style = ("font-size:35px; font-family:Courier"), fill="red")
                        #text = dwg.text("O",insert=(offset_x,missing_offset_y),style = ("font-size:35px; font-family:Courier"), fill="red")
                        text = dwg.text("O",insert=(offset_x,missing_offset_y),style = ("font-size:35px; font-family:Courier"), fill="orange")
                        #print "checkpoint missing boxes"
                        group_chart.add(text)
                    # draw current box
                    #text = dwg.text("O",insert=(offset_x,offset_y),style = ("font-size:35px; font-family:Courier"), fill="red")
                    text = dwg.text("O",insert=(offset_x,offset_y),style = ("font-size:35px; font-family:Courier"), fill="orange")
                    #print "checkpoint 1"
                    group_chart.add(text)



                elif array[row-1,0] == "O": # we are still in a downtrend

                    # check whether the difference between current box and previous is bigger than 1
                    # in that case more Os shall be written, to occupy middle boxes
                    # check for middle boxes
                    if abs(array[row-1, 2]-Boxnumber) > 1:
                        #print "missing boxes found!!"
                        # find how many boxes should be written
                        number_boxes_in_middle = abs(array[row-1, 2]-Boxnumber)
                        for i in range(1,number_boxes_in_middle,1):
                            # start drawing middle boxes
                            missing_boxnumber = Boxnumber+i
                            #print "missing_boxnumber",  missing_boxnumber
                            missing_box_height = maximum_Boxnumber - missing_boxnumber + buffer_Boxnumber_up

                            missing_offset_y = offset_from_above + (missing_box_height*35)
                            #offset_from_left_x = 185
                            #missing_offset_x = offset_from_left_x + (Column*40)

                            #text = dwg.text("O",insert=(missing_offset_x,missing_offset_y),style = ("font-size:35px; font-family:Courier"), fill="red")
                            #text = dwg.text("O",insert=(offset_x,missing_offset_y),style = ("font-size:35px; font-family:Courier"), fill="red")
                            text = dwg.text("O",insert=(offset_x,missing_offset_y),style = ("font-size:35px; font-family:Courier"), fill="orange")
                            #print "checkpoint missing boxes"
                            group_chart.add(text)
                        # draw current box
                        #text = dwg.text("O",insert=(offset_x,offset_y),style = ("font-size:35px; font-family:Courier"), fill="red")
                        text = dwg.text("O",insert=(offset_x,offset_y),style = ("font-size:35px; font-family:Courier"), fill="orange")
                        #print "checkpoint 1"
                        group_chart.add(text)
                    elif abs(array[row-1, 2]-Boxnumber) == 1: # no middle box, just one box down
                        #text = dwg.text("O",insert=(offset_x,offset_y),style = ("font-size:35px; font-family:Courier"), fill="red")
                        text = dwg.text("O",insert=(offset_x,offset_y),style = ("font-size:35px; font-family:Courier"), fill="orange")
                        #print "checkpoint 1"
                        group_chart.add(text)

            elif row == 0:
                # row is 0 - first row - no check for middle boxes
                #text = dwg.text("O",insert=(offset_x,offset_y),style = ("font-size:35px; font-family:Courier"), fill="red")
                text = dwg.text("O",insert=(offset_x,offset_y),style = ("font-size:35px; font-family:Courier"), fill="orange")
                #print "checkpoint O"
                group_chart.add(text)



        elif XO == "X":  # X Column

            if row > 0: # not first row
                if array[row-1,0] == "O": # we come from a reversal - thus reversal boxes
                    # check for how many middle X boxes should be drawn
                    number_boxes_in_middle = abs(array[row-1, 2]-Boxnumber)
                    #print "Coming from reversal - previous column was O - missing X boxes found!!"
                    # find how many boxes should be written
                    number_boxes_in_middle = abs(array[row-1, 2]-Boxnumber)
                    for i in range(1,number_boxes_in_middle,1):
                        # start drawing middle boxes
                        missing_boxnumber = Boxnumber-i
                        #print "missing_boxnumber X",  missing_boxnumber
                        missing_box_height = maximum_Boxnumber - missing_boxnumber + buffer_Boxnumber_up
                        missing_offset_y = offset_from_above + (missing_box_height*35)
                        #offset_from_left_x = 185
                        #missing_offset_x = offset_from_left_x + (Column*40)
                        #text = dwg.text("X",insert=(missing_offset_x,missing_offset_y),style = ("font-size:35px; font-family:Courier"), fill="lime")
                        text = dwg.text("X",insert=(offset_x,missing_offset_y),style = ("font-size:35px; font-family:Courier"), fill="lime")
                        #print "checkpoint missing X boxes"
                        group_chart.add(text)
                    # draw current  X box
                    text = dwg.text("X",insert=(offset_x,offset_y),style = ("font-size:35px; font-family:Courier"), fill="lime")
                    #print "checkpoint 1 X"
                    group_chart.add(text)


                elif array[row-1,0] == "X": # we are still in an uptrend

                    # check whether the difference between current box and previous is bigger than 1
                    # in that case more Os shall be written, to occupy middle boxes
                    # check for middle boxes
                    if abs(array[row-1, 2]-Boxnumber) > 1:
                        #print "missing X boxes found!!"
                        # find how many boxes should be written
                        number_boxes_in_middle = abs(array[row-1, 2]-Boxnumber)
                        for i in range(1,number_boxes_in_middle,1):
                            # start drawing middle boxes
                            missing_boxnumber = Boxnumber-i
                            #print "missing_boxnumber X",  missing_boxnumber
                            missing_box_height = maximum_Boxnumber - missing_boxnumber + buffer_Boxnumber_up
                            missing_offset_y = offset_from_above + (missing_box_height*35)
                            #offset_from_left_x = 185
                            #missing_offset_x = offset_from_left_x + (Column*40)
                            #text = dwg.text("X",insert=(missing_offset_x,missing_offset_y),style = ("font-size:35px; font-family:Courier"), fill="lime")
                            text = dwg.text("X",insert=(offset_x,missing_offset_y),style = ("font-size:35px; font-family:Courier"), fill="lime")
                            #print "checkpoint missing X boxes"
                            group_chart.add(text)
                        # draw current box
                        text = dwg.text("X",insert=(offset_x,offset_y),style = ("font-size:35px; font-family:Courier"), fill="lime")
                        #print "checkpoint 1 X"
                        group_chart.add(text)
                    elif abs(array[row-1, 2]-Boxnumber) == 1: # no middle box, just one box down
                        text = dwg.text("X",insert=(offset_x,offset_y),style = ("font-size:35px; font-family:Courier"), fill="lime")
                        #print "checkpoint 1 X"
                        group_chart.add(text)

            elif row == 0:
                # row is 0 - first row - no check for middle boxes
                text = dwg.text("X",insert=(offset_x,offset_y),style = ("font-size:35px; font-family:Courier"), fill="lime")
                #print "checkpoint X"
                group_chart.add(text)

    # Add horizontal lines
    j = 50
    # Construction of scale
    for i in range((maximum_Boxnumber+buffer_Boxnumber_up),(minimum_Boxnumber-buffer_Boxnumber_down),-1):
        # depict scale in svg
        y2 = str(j)
        y3 = str(j+5)
        # add horizontal lines
        #line = dwg.line(start=(0,y3), end=(offset_from_left_x+((maximum_Column+6)*40),y3), stroke="grey", fill="#598da6")
        #line = dwg.line(start=(0,y3), end=(offset_from_left_x+((maximum_Column)*35),y3), stroke="grey", fill="#598da6")
        line = dwg.line(start=(0,y3), end=(((maximum_Column+buffer_Column+3)*35),y3), stroke="grey", fill="#598da6")
        #line = dwg2.line(start=(0,y3), end=(offset_from_left_x,y3), stroke="grey", fill="#598da6")
        j += 35
        group_chart.add(line)

    # add vertical lines
    for i in range(0,maximum_Column+buffer_Column+3,1):
        line = dwg.line(start=(35+i*35,25), end=(35+i*35,max_height_pixels-35), stroke="grey", fill="#598da6")
        group_chart.add(line)

    #dwg.viewbox(width=offset_from_left_x+((maximum_Column+3)*40), height=max_height_pixels+100)
    #dwg.viewbox(width=offset_from_left_x+((maximum_Column+3)*40), height=max_height_pixels)
    #dwg.viewbox(width=(offset_from_left_x+((maximum_Column+3)*40))*0.6, height=((max_height_pixels- (40*4))*0.6)-10)
    #dwg.viewbox(width=(offset_from_left_x+((maximum_Column)*35))*0.6, height=((max_height_pixels- (35*4))*0.6)-10)
    dwg.viewbox(width=(((maximum_Column+buffer_Column+3)*35))*0.6, height=((max_height_pixels- (35*4))*0.6)-10)
    #dwg.viewbox(width=100, height=100, preserveAspectRatio="xMidYMid meet")
    #print max_height_pixels
    # Save the created SVG
    dwg.save()
    dwg_filename = filename+"_"+highlow_close+" "+box_string+'.svg'
    dwg2_filename = filename+"_"+highlow_close+" "+box_string+'_scale'+'.svg'
    return (dwg_filename,dwg2_filename)



# Helper functions:
# This function sets the appropriate default options values for Pandas and NumPy libraries, for cryptocoins data
def set_pandas_and_numpy_options(asset="cryptocoins"):
    if asset=="cryptocoins":
        # Set pandas display output options
        pd.set_option('display.precision', 8)
        pd.set_option('display.max_columns', 500)
        pd.set_option('expand_frame_repr', False)

        # Set numpy display output options
        np.set_printoptions(precision=8,suppress=True)


# Get poloniex output files
def get_poloniex_output(dirname):

    # List to contain the output files
    poloniex_output_list = []

    # Append absolute file paths into list (for files ending with '.json')
    for files in os.listdir(poloniex_output_path):
        if files.endswith('.json'):
            abspath = os.path.abspath(poloniex_output_path+files)
            poloniex_output_list.append(abspath)

    return poloniex_output_list



# This call is used to make the module runable as a standalone python file
if __name__ == "__main__":

    # Set Pandas and NumPy options for use with cryptocoins data
    # To be used also with different options, when the project expands,
    # e.g. to process stocks, options, etfs and so on
    set_pandas_and_numpy_options("cryptocoins")

    # Path to poloniex output files
    poloniex_output_path = "poloniex_output/"

    # List to contain the output files
    poloniex_output_list = get_poloniex_output(poloniex_output_path)

    # This loop prints the filenames, without the extension. Used for checking purposes
    for files in poloniex_output_list:
        print(os.path.splitext(os.path.basename(files))[0])

    # Load files into PnF Engine and services
    for files in poloniex_output_list:

        #  In this part we feed the .json files into the PnF engines.
        #  The order is the following:
        #
        #  PnF Engine:
        #  "1% * 3 Box reversal" using 'High' & 'Low' Data
        #  "2% * 3 Box reversal" using 'High' & 'Low' Data
        #  "3% * 3 Box reversal" using 'High' & 'Low' Data
        #  "1% * 3 Box reversal" using 'Close' Data
        #  "2% * 3 Box reversal" using 'Close' Data
        #  "3% * 3 Box reversal" using 'Close' Data
        #  We have separate DataFrames as a result
        #
        #  Signal Detection Engine:
        #  Uses the above results from the 'PnF Engine',
        #  Saves result as .html file into relevant folder.
        #
        #  Signal Notification Engine:
        #  Scans the last row of each Dataframe,
        #  notifies the user if a "Double Top/Double Bottom" or
        #  a "Double Top/Double Bottom Breakout" has been detected.
        #  The notification can be an auto-post Slack Message Bot,
        #  a Windows pop up window, an email etc.

        # Get current filename that is being processed, without the extension part
        current_filename = os.path.splitext(os.path.basename(files))[0]

        # Read .json that we stored from poloniex
        MyPandasFrame = pd.read_json(path_or_buf = poloniex_output_path+current_filename+".json",
                                     orient = 'DataFrame',
                                     precise_float = True)

        # Enable this if you want to check initial .json data into human readable html format
        #MyPandasFrame.to_html(open(current_filename+'unprocessed_Df.html','w'))

        # TIP (Boxsize):
        #Having one of the following values:
        #1% 0.009950331
        #2% 0.019802627
        #3% 0.029558802

        #                1%           2%           3%
        #boxlist = [0.009950331, 0.019802627, 0.029558802]
        boxlist = [0.00000002]

        for box in boxlist:
            ## Call Main PnF Engine using High & Low data
            result_df_PnF = main_pnf_engine_using_high_low_data(MyPandasFrame, boxsize=box, reversal=4, log=False)

            print(result_df_PnF)
            ## Call Signal Detection Engine using High & Low data
            #pnf_signal_detection_engine(result_df_PnF, current_filename, boxsize=box, highlow_close="high_low", reversal=1)
#
            # Call Charting Engine using High & Low data
            charting_engine(result_df_PnF, current_filename, highlow_close="high_low", boxsize=box, reversal=4, log=False)
#
            ## Call Signal Notification Service using High & Low data
            #signal_notification_service(result_df_PnF, current_filename, boxsize=box, highlow_close="high_low", log=False)

            ## Call Main PnF Engine using Close
            #result_df_PnF = main_pnf_engine_using_close_data(MyPandasFrame, boxsize=box, reversal=1, log=True)

            result_df_PnF.to_html(open("result.html", 'w'))

            ## Call Signal Detection Engine using Close
            #pnf_signal_detection_engine(result_df_PnF, current_filename, boxsize=box, highlow_close="close", reversal=3)
#
            ## Call Charting Engine using Close
            #charting_engine(result_df_PnF,current_filename,highlow_close="close", boxsize=box, reversal=3, log=False)
#
            ## Call Signal Notification Service using Close
            #signal_notification_service(result_df_PnF, current_filename, boxsize=box, highlow_close="close", log=False)


        # Delete from memory
        #del MyPandasFrame
        #del result_df_PnF



    # Perform Garbage Collection
    # http://stackoverflow.com/questions/32247643/how-to-delete-multiple-pandas-python-dataframes-from-memory-to-save-ram
    gc.collect()
