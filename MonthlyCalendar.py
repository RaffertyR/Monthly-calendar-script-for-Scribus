#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
VERSION: 5.0 of 2021-12-07
AUTHOR: Rafferty River. 
LICENSE: GNU GENERAL PUBLIC LICENSE Version 3, 29 June 2007. 
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY.

DESCRIPTION & USAGE:
(tested on Scribus 1.5.7 with python 3 on Windows 10 and Linux Mint 20).
This Scribus script generates a classic monthly calendar with following options:
1) You can choose between more than 20 languages (default is English). 
You may add, change or delete languages in the localization list in this script.
Please respect the Python syntax.
2) You can choose your default calendar font from the list of fonts available on your system. 
Please check if all special characters for your language are available in the chosen font! 
You can change fonts of many items afterwards in the Styles menu (Edit - Styles).
3) Calendar year and week starting day are to be given. Saturdays and Sundays will 
be printed by default in separate colors (many colors can be changed afterwards with
Edit - Colors and Fills).
4) Option to show week numbers with (or without) a week numbers heading in 
your local language. 
5) Option to import holidays and special days from a 'holidays.txt' file for your country. 
Automatic calculation of the recurring holiday dates for each calendar year. 
6) Option to import a 'moonphases.txt' file in order to draw the moon phase symbols 
on the calendar.
7) Select one or more months or the whole year.
8) You have the possibility to determine where on the page the calendar month will 
be drawn with the offsets from top and / or left margin. Option to draw an empty 
image frame within the top and / or left 'offset' area and to get an 'inner' margin 
between this frame and the calendar grid.
9) Option to draw draw mini calendars for previous and next months in the calendar 
month heading.
10) You can easily change the default styles and colors for month title, weekday names, 
week numbers, holiday dates and texts, special dates, weekend days, normal dates, 
mini calendars and moon phases afterwards.  You can hide the separate layers for moons, 
holiday texts and images. Automatic change to abbreviated weekday names if cells 
are too small. Many other build-in controls.

Parts of this script are taken from the CalendarWizard script from Petr Vanek
and Bernhard Reiter which is provided with Scribus.
"""
######################################################
# imports
from __future__ import division # overrules Python 2 integer division
import sys
import locale
import calendar
import datetime
from datetime import date, timedelta
import csv
import platform

try:
    from scribus import *
except ImportError:
    print("This Python script is written for the Scribus \
      scripting interface.")
    print("It can only be run from within Scribus.")
    sys.exit(1)

os = platform.system()
if os != "Windows" and os != "Linux":
    print("Your Operating System is not supported by this script.")
    messageBox("Script failed",
        "Your Operating System is not supported by this script.",
        ICON_CRITICAL)	
    sys.exit(1)

python_version = platform.python_version()
if python_version[0:1] != "3":
    print("This script runs only with Python 3.")
    messageBox("Script failed",
        "This script runs only with Python 3.",
        ICON_CRITICAL)	
    sys.exit(1)

try:
    from tkinter import * # python 3
    from tkinter import messagebox, filedialog, font
except ImportError:
    print("This script requires Python Tkinter properly installed.")
    messageBox('Script failed',
               'This script requires Python Tkinter properly installed.',
               ICON_CRITICAL)
    sys.exit(1)

######################################################
# you can insert additional languages and unicode pages in the 'localization'-list below:
localization = [['Bulgarian', 'CP1251', 'bg_BG.UTF8'], 
    ['Croatian', 'CP1250', 'hr_HR.UTF8'], 
    ['Czech', 'CP1250', 'cs_CZ.UTF8'], 
    ['Danish', 'CP1252','da_DK.UTF8'],
    ['Dutch', 'CP1252', 'nl_NL.UTF8'], 
    ['English', 'CP1252', 'en_US.UTF8'], 
    ['Estonian', 'CP1257', 'et_EE.UTF8'], 
    ['Finnish', 'CP1252', 'fi_FI.UTF8'], 
    ['French', 'CP1252', 'fr_FR.UTF8'], 
    ['German', 'CP1252', 'de_DE.UTF8'], 
    ['German_Austria', 'CP1252', 'de_AT.UTF8'], 
    ['Greek', 'CP1253', 'el_GR.UTF8'], 
    ['Hungarian', 'CP1250', 'hu_HU.UTF8'] ,
    ['Italian', 'CP1252', 'it_IT.UTF8'],
    ['Lithuanian', 'CP1257', 'lt_LT.UTF8'], 
    ['Latvian', 'CP1257', 'lv_LV.UTF8'],
    ['Norwegian', 'CP1252', 'nn_NO.UTF8'],
    ['Polish', 'CP1250', 'pl_PL.UTF8'], 
    ['Portuguese', 'CP1252', 'pt_PT.UTF8'],
    ['Romanian', 'CP1250', 'ro_RO.UTF8'],
    ['Russian', 'CP1251', 'ru_RU.UTF8'], 
    ['Slovak', 'CP1250', 'sk_SK.UTF8'],
    ['Slovenian', 'CP1250', 'sl_SI.UTF8'],
    ['Spanish', 'CP1252', 'es_ES.UTF8'], 
    ['Swedish', 'CP1252', 'sv_SE.UTF8']]

######################################################
class ScMonthCalendar:
    """ Calendar matrix creator itself. One month per page."""

    def __init__(self, year, months = [], firstDay = calendar.SUNDAY, weekNr=True, 
                weekNrHd="Wk", offsetX=0.0, marginX=0.0, offsetY=0.0,  marginY=0.0, 
                drawImg=True, miniCals=True, cFont='Symbola Regular', lang='English',
                holidaysList = list(), moonsList = list()):
        """ Setup basic things """
        # params
        self.year = year
        self.months = months
        self.weekNr = weekNr
        self.weekNrHd = weekNrHd #week numbers heading
        self.offsetX = offsetX
        self.offsetY = offsetY
        self.marginX = marginX
        self.marginY = marginY
        self.drawImg = drawImg # draw placeholder for image or logo (between margins and offsetX / offsetY)
        self.miniCals = miniCals # draw mini calendars for previous and next months in the calendar heading
        self.holidaysList = holidaysList #imported and converted from '*holidays.txt' (or empty list)
        if len(self.holidaysList) != 0:
            self.drawHolidays = True
        else:
            self.drawHolidays = False
        self.moonsList = moonsList #imported and converted from 'moonphases.txt' (or empty list)
        if len(self.moonsList) != 0:
            self.drawMoons = True
        else:
            self.drawMoons = False
        self.cFont = cFont
        self.lang = lang
        ix = [[x[0] for x in localization].index(self.lang)]
        if os == "Windows":
            self.calUniCode = (localization[ix[0]][1]) # get unicode page for the selected language
        else: # Linux
            self.calUniCode = "UTF-8"
        self.dayOrder=[] # weekday names in local language
        self.dayOrderAbbr=[] # abbreviated weekday names in local language
        self.dayOrderMini=[] # first letter of weekday names in local language
        for i in range (0,7):
            #Problem: no scripter command to change the First Line Offset ('FLOP').
            #Solution: add the "|"-sign (invisible by setting text color to "None") in order to have correct text alignment 
            self.dayOrder.append(calendar.day_name[i])
            self.dayOrderAbbr.append(calendar.day_abbr[i])
            try:            
                self.dayOrderMini.append((calendar.day_abbr[i][:1]).upper() + "|")
            except UnicodeError: # for Greek, Russian, etc.
                self.dayOrderMini.append((calendar.day_abbr[i][:2]).upper() + "|")
        if firstDay == calendar.SUNDAY:
            dl = self.dayOrder[:6]
            dl.insert(0, self.dayOrder[6])
            self.dayOrder = dl
            dl = self.dayOrderAbbr[:6]
            dl.insert(0, self.dayOrderAbbr[6])
            self.dayOrderAbbr = dl
            dl = self.dayOrderMini[:6]
            dl.insert(0, self.dayOrderMini[6])
            self.dayOrderMini = dl
        self.mycal = calendar.Calendar(firstDay)
        # layers
        self.layerCal = 'Calendar'
        self.layerMoons = 'Moons'
        self.layerHolidays = 'Holidays'
        self.layerImg = 'Images'
        # various parameters
        self.scalingFactor = 1 # for scaling header
        self.miniFactor = 1 / 7 # width of mini calendar cel
        self.smallCel = False # cell width / height is more than 1.33
        self.displac = 0 # variable for various displacements
        # character styles
        self.cStylMonthHeading = "char_style_MonthHeading"
        self.cStylDayNames = "char_style_DayNames"
        self.cStylWeekNo = "char_style_WeekNo"
        self.cStylMoons = "char_style_Moons"
        self.cStylHolidays = "char_style_Holidays"
        self.cStylDate = "char_style_Date"
        self.cStylMini = "char_style_Mini"
        # paragraph styles
        self.pStyleMonthHeading = "par_style_MonthHeading"
        self.pStyleDayNames = "par_style_DayNames"
        self.pStyleWeekNo = "par_style_WeekNo"
        self.pStyleMoons = "par_style_Moons"
        self.pStyleHolidays = "par_style_Holidays"
        self.pStyleDate = "par_style_Date"
        self.pStyleMini = "par_style_Mini"
        # line styles
        self.gridLineStyle = "grid_Line_Style"
        self.gridLineStyleDayNames = "grid_DayNames_Style"
        self.gridLineStyleWeekNo = "grid_WeekNo_Style"
        self.gridLineStyleMonthHeading = "grid_MonthHeading_Style"
        # other settings
        self.firstPage = True # create only 2nd 3rd ... pages. No 1st one.
        calendar.setfirstweekday(firstDay)
        progressTotal(len(months))
 
    def createCalendar(self):
        """ Walk through months dict and call monthly sheet """
        if not newDocDialog():
            return 'Create a new document first, please'
        originalUnit = getUnit()
        setUnit(UNIT_POINTS)
        self.setupDocVariables()
        scribus.createCharStyle(name=self.cStylMonthHeading,font=self.cFont,
            fontsize=((self.rowSize * self.scalingFactor) // 1.5), fillcolor="txtMonthHeading")
        scribus.createCharStyle(name=self.cStylDayNames, font=self.cFont,
            fontsize=(self.rowSize // 4), fillcolor="txtDayNames")
        scribus.createCharStyle(name=self.cStylWeekNo,font=self.cFont,
            fontsize=(self.rowSize // 4), fillcolor="txtWeekNo")
        scribus.createCharStyle(name=self.cStylMoons,font=self.cFont,
            fontsize=(self.rowSize // 4), fillcolor="txtDate")
        scribus.createCharStyle(name=self.cStylHolidays, font=self.cFont,
            fontsize=(self.rowSize // 8), fillcolor="txtDate")
        scribus.createCharStyle(name=self.cStylDate, font=self.cFont,
            fontsize=(self.rowSize // 2), fillcolor="txtDate")
        scribus.createCharStyle(name=self.cStylMini, font=self.cFont,
            fontsize=(self.rowSize // 8), fillcolor="txtDate")
        scribus.createParagraphStyle(name=self.pStyleMonthHeading, linespacingmode=0,
            linespacing=((self.rowSize*self.scalingFactor)//1.5), alignment=ALIGN_CENTERED,
            charstyle=self.cStylMonthHeading)
        scribus.createParagraphStyle(name=self.pStyleDayNames, linespacingmode=2,
            alignment=ALIGN_CENTERED, firstindent=3,
            charstyle=self.cStylDayNames)
        scribus.createParagraphStyle(name=self.pStyleWeekNo, alignment=ALIGN_CENTERED,
            charstyle=self.cStylWeekNo)
        scribus.createParagraphStyle(name=self.pStyleMoons, alignment=ALIGN_CENTERED,
            charstyle=self.cStylMoons)
        scribus.createParagraphStyle(name=self.pStyleHolidays,  linespacingmode=0,
            linespacing=(self.rowSize//8),alignment=ALIGN_CENTERED,
            charstyle=self.cStylHolidays)
        scribus.createParagraphStyle(name=self.pStyleDate, alignment=ALIGN_CENTERED,
            charstyle=self.cStylDate)
        scribus.createParagraphStyle(name=self.pStyleMini,  linespacingmode=1,
            linespacing=(self.rowSize//8),alignment=ALIGN_CENTERED,
            charstyle=self.cStylMini)
        run = 0
        for i in self.months:
            run += 1
            progressSet(run)
            cal = self.mycal.monthdatescalendar(self.year, i + 1)
            self.createMonthCalendar(i, cal)
        setUnit(originalUnit)
        return None

    def setupDocVariables(self):
        """ Compute base metrics here. Page layout is bordered by margins
            and empty image frame(s). """
        # default calendar colors
        defineColorCMYK("Black", 0, 0, 0, 255)
        defineColorCMYK("White", 0, 0, 0, 0)
        defineColorCMYK("fillMonthHeading", 0, 0, 0, 0) # default is White
        defineColorCMYK("txtMonthHeading", 0, 0, 0, 255) # default is Black
        defineColorCMYK("fillDayNames", 0, 0, 0, 200) # default is Dark Grey
        defineColorCMYK("txtDayNames", 0, 0, 0, 0) # default is White
        defineColorCMYK("fillWeekNo", 0, 0, 0, 200) # default is Dark Grey
        defineColorCMYK("txtWeekNo", 0, 0, 0, 0) # default is White
        defineColorCMYK("fillDate", 0, 0, 0, 0) # default is White
        defineColorCMYK("txtDate", 0, 0, 0, 255) # default is Black
        defineColorCMYK("fillWeekend", 0, 0, 0, 25) # default is Light Grey
        defineColorCMYK("fillWeekend2", 0, 0, 0, 25) # default is Light Grey
        defineColorCMYK("txtWeekend", 0, 0, 0, 200) # default is Dark Grey
        defineColorCMYK("fillHoliday", 0, 0, 0, 25) # default is Light Grey
        defineColorCMYK("txtHoliday", 0, 234, 246, 0) # default is Red
        defineColorCMYK("fillSpecialDate", 0, 0, 0, 0) # default is White
        defineColorCMYK("txtSpecialDate", 0, 0, 0, 128) # default is Middle Grey
        defineColorCMYK("gridColor", 0, 0, 0, 128) # default is Middle Grey
        defineColorCMYK("gridMonthHeading", 0, 0, 0, 0) # default is White
        defineColorCMYK("gridDayNames", 0, 0, 0, 128) # default is Middle Grey
        defineColorCMYK("gridWeekNo", 0, 0, 0, 128) # default is Middle Grey
        # document measures
        page = getPageSize()
        self.pageX = page[0]
        self.pageY = page[1]
        marg = getPageMargins()
        self.marginT = marg[0]
        self.marginL = marg[1]
        self.marginR = marg[2]
        self.marginB = marg[3]
        self.width = self.pageX - self.marginL - self.marginR
        self.height = self.pageY - self.marginT - self.marginB
        # cell rows and cols
        self.rows = 8.0 # month heading 1.5 + weekday names 0.5 +  6 weeks
        self.rowSize = (self.height - self.offsetY) / self.rows
        if self.weekNr:
            self.cols = 7.5 # weekNr column is 0.5 of weekday column
        else:
            self.cols = 7.0 # 7 weekdays
        self.colSize = (self.width - self.offsetX) / self.cols
        if (self.colSize / self.rowSize) < 1.33: # chosen by experience
            self.smallCel = True                       # to avoid text overflows
            self.dayOrder = self.dayOrderAbbr # change to abbreviated weekday names
            self.scalingFactor = 0.5
            self.miniFactor = 1.5 / 7
        baseLine = float(self.rowSize)/4 # python 2 does only know integer division -> float()
        h = (self.rowSize*2 +self.marginT+self.offsetY)
        x = (float(h)/baseLine)-(float(h)//baseLine)
        y = x*baseLine+baseLine/2
        setBaseLine(baseLine, y * 0.8) # for correct aligment of weekdays names
                                                      #  with ascender and descender characters
        # line styles
        scribus.createCustomLineStyle(self.gridLineStyle, [
            {
                'Color': "gridColor",
                'Width': 1
            }
        ]);
        scribus.createCustomLineStyle(self.gridLineStyleMonthHeading, [
            {
                'Color': "gridMonthHeading",
                'Width': 1
            }
        ]);
        scribus.createCustomLineStyle(self.gridLineStyleDayNames, [
            {
                'Color': "gridDayNames",
                'Width': 1
            }
        ]);
        scribus.createCustomLineStyle(self.gridLineStyleWeekNo, [
            {
                'Color': "gridWeekNo",
                'Width': 1
            }
        ]);
        # layers
        createLayer(self.layerCal)
        if self.drawMoons:
            createLayer(self.layerMoons)
        if self.drawHolidays:
            createLayer(self.layerHolidays)
        if self.drawImg:
            createLayer(self.layerImg)
        self.masterPage = masterPageNames()[0] #'Normal'

    def createImg(self):
        """ Wrapper for everytime-the-same image frame. """
        setActiveLayer(self.layerImg)
        if self.offsetX != 0:
            createImage(self.marginL, self.marginT, self.offsetX - self.marginX, self.height)
        if self.offsetY != 0: # if top AND left frame -> top frame does not overlap with left frame
            createImage(self.marginL + self.offsetX, self.marginT,
                self.width-self.offsetX, self.offsetY - self.marginY)

    def createMonthCalendar(self, month, cal):
        """ Create a page and draw one month calendar on it """
        self.createLayout()
        if self.drawImg:
            self.createImg()
        setActiveLayer(self.layerCal)
        if self.miniCals: # draw mini calendars beside the month heading
            #     previous month
            colCnt = 0
            if month == 0: # January
                mini_mth = 12 # December of previous year
                year = self.year - 1
            else:
                mini_mth = month
                year = self.year
            self.displac = self.colSize * 0.05
            self.createMiniHeader(calendar.month_name[mini_mth], colCnt)
            miniCal = self.mycal.monthdatescalendar(year, mini_mth)
            self.createMiniCals(mini_mth, miniCal, colCnt)
            #     next month
            colCnt = self.cols - 1   # 6 or 6.5 if weekNr
            if month == 11: # December
                mini_mth = 1 # January of next year
                year = self.year + 1
            else:
                mini_mth = month + 2
                year = self.year
            self.displac = - (self.colSize * 0.05) - (self.colSize * ((self.miniFactor * 7) - 1))
            self.createMiniHeader(calendar.month_name[mini_mth], colCnt)
            miniCal = self.mycal.monthdatescalendar(year, mini_mth)
            self.createMiniCals(mini_mth, miniCal, colCnt)

        self.displac = 0
        if self.smallCel and (len(self.weekNrHd) > 0):
            if len(self.weekNrHd) > 2:
                self.weekNrHd = (self.weekNrHd[:1])
            self.displac = 0.05
        self.createHeader(calendar.month_name[month+1])

        rowCnt = 2.0
        for week in cal:
            if self.weekNr:
                cel = createText(self.marginL + self.offsetX,
                                 self.marginT + self.offsetY + rowCnt * self.rowSize, 
                                 self.colSize*0.5, self.rowSize)
                yr, mt, dt = str((week[0])).split("-")
                setText(str(datetime.date(int(yr), int(mt), int(dt)).isocalendar()[1]), cel)
                setFillColor("fillWeekNo", cel)
                setCustomLineStyle(self.gridLineStyleWeekNo, cel)
                deselectAll()
                selectObject(cel)
                setParagraphStyle(self.pStyleWeekNo, cel)
                setTextVerticalAlignment(ALIGNV_CENTERED,cel)
                colCnt = 0.5
            else:
                colCnt = 0
            for day in week:
                cel = createText(self.marginL+self.offsetX + colCnt * self.colSize,
                                 self.marginT+self.offsetY + rowCnt * self.rowSize,
                                 self.colSize, self.rowSize)
                colCnt += 1
                setFillColor("fillDate", cel)
                setCustomLineStyle(self.gridLineStyle, cel)
                if day.month == (month+1):
                    setText(str(day.day), cel)
                    deselectAll()
                    selectObject(cel)
                    setParagraphStyle(self.pStyleDate, cel)
                    setTextVerticalAlignment(ALIGNV_CENTERED, cel)
                    weekend = False # day is  weekend day
                    if calendar.firstweekday() == 6:
                        x = 1
                    else:
                        x = 6
                    if (int(colCnt) == x) or (int(colCnt) == 7):
                        weekend = True
                        setTextColor("txtWeekend", cel)
                        setFillColor("fillWeekend", cel)
                    holidayColor = False # holiday
                    for x in range(len(self.holidaysList)):
                            if (self.holidaysList[x][0] == (day.year) and
                                self.holidaysList[x][1] == str(day.month) and
                                self.holidaysList[x][2] == str(day.day)): 
                                if self.holidaysList[x][4] == '1':
                                    holidayColor = True
                                    setTextColor("txtHoliday", cel)
                                    setFillColor("fillHoliday", cel)
                                else:
                                    setTextColor("txtSpecialDate", cel)
                                    if getFillColor(cel) == "fillWeekend":
                                        setFillColor("fillWeekend", cel)
                                    else:
                                        setFillColor("fillSpecialDate", cel)
                                setActiveLayer(self.layerHolidays)
                                txtHoliday = createText(self.marginL+self.offsetX + (colCnt - 1)* self.colSize,
                                    self.marginT+self.offsetY + rowCnt * self.rowSize,
                                    self.colSize, self.rowSize)
                                setText("|" + self.holidaysList[x][3] + "|", txtHoliday)
                                deselectAll()
                                selectObject(txtHoliday)
                                setParagraphStyle(self.pStyleHolidays, txtHoliday)
                                setTextDistances(0, 0,  0, self.rowSize * 0.05, txtHoliday)
                                setTextVerticalAlignment(ALIGNV_BOTTOM, txtHoliday)
                                selectText(0, 1, txtHoliday)
                                setTextColor("None", txtHoliday)  # change "|"-character color to become invisible
                                selectText(getTextLength(txtHoliday) - 1, 1, txtHoliday)
                                setTextColor("None", txtHoliday)  # change "|"-character color to become invisible
                                setActiveLayer(self.layerCal)
                    if self.drawMoons:
                        setActiveLayer(self.layerMoons)
                        for x in range(len(self.moonsList)): # draw moon phases
                            if (self.moonsList[x][0]==str(day.month) and 
                                self.moonsList[x][1]==str(day.day)):                        
                                cel = createText(self.marginL+self.offsetX + (colCnt-1) * self.colSize,
                                    self.marginT+self.offsetY + rowCnt * self.rowSize,
                                    self.colSize, self.rowSize)
                                setText(self.moonsList[x][2], cel) #  draw moon phase
                                deselectAll()
                                selectObject(cel)
                                setParagraphStyle(self.pStyleMoons, cel)
                                setTextDistances(self.colSize * 0.05, 0,  self.rowSize * 0.05, 
                                    self.rowSize * 0.05, cel)
                                setTextAlignment(ALIGN_LEFT, cel)
                                if self.smallCel:
                                    setTextVerticalAlignment(ALIGNV_TOP, cel)
                                else:
                                    setTextVerticalAlignment(ALIGNV_CENTERED, cel)
                                    setFontSize(self.rowSize // 3, cel)
                                if weekend:
                                    setTextColor("txtWeekend", cel)
                                if holidayColor:
                                    setTextColor("txtHoliday", cel)
                        setActiveLayer(self.layerCal)
                else:  # fill previous or next month empty weekend cells
                    if calendar.firstweekday() == 6:
                        x = 1
                    else:
                        x = 6
                    if (int(colCnt) == x) or (int(colCnt) == 7):
                        setFillColor("fillWeekend2", cel)
            rowCnt += 1

        while rowCnt < 8:
            self.createEmptyWeekRow(rowCnt)
            rowCnt += 1

    def createEmptyWeekRow(self, rowCnt):
        """ Add empty week row(s) at bottom of month """
        if self.weekNr:
            cel = createText(self.marginL + self.offsetX,
                             self.marginT + self.offsetY + rowCnt * self.rowSize, 
                             self.colSize*0.5, self.rowSize)
            setFillColor("fillWeekNo", cel)
            setCustomLineStyle(self.gridLineStyleWeekNo, cel)
            colCnt = 0.5
        else:
            colCnt = 0
        for y in range(0, 7):
            cel = createText(self.marginL+self.offsetX + colCnt * self.colSize,
                             self.marginT+self.offsetY + rowCnt * self.rowSize,
                             self.colSize, self.rowSize)
            if calendar.firstweekday() == 6:
                x = 0
            else:
                x = 5
            if (int(colCnt) == x) or (int(colCnt) == 6):
                setFillColor("fillWeekend2", cel)
            else:
                setFillColor("fillDate", cel)
            setCustomLineStyle(self.gridLineStyle, cel)
            colCnt += 1

    def createLayout(self):
        """ Create the page and optional bells and whistles around """
        """ Wrapper to the new page with layers """
        if self.firstPage:
            self.firstPage = False
            newPage(-1, self.masterPage) # create a new page using the masterPage
            deletePage(1) # now it's safe to delete the first page
            gotoPage(1)
        else:
            newPage(-1, self.masterPage)

    def createHeader(self, monthName):
        """ Draw calendar header: Month name """
        cel = createText(self.marginL + self.offsetX, self.marginT + self.offsetY,
            self.width - self.offsetX, self.rowSize * 1.5)
        mtHd = monthName
        setText(mtHd.upper() + " " + str(self.year), cel)
        deselectAll()
        selectObject(cel)
        scribus.setParagraphStyle(self.pStyleMonthHeading, cel)
        setTextVerticalAlignment(ALIGNV_CENTERED, cel)
        setFillColor("fillMonthHeading", cel)
        setCustomLineStyle(self.gridLineStyleMonthHeading, cel)
        selectObject(cel)
        moveSelectionToBack()
        """ Draw calendar header: Weekday names. """
        rowCnt = 1.5
        colCnt = 0
        if self.weekNr:
            cel = createText(self.marginL + self.offsetX,
                self.marginT + self.offsetY + self.rowSize * rowCnt, self.colSize * 0.5,
                self.rowSize * 0.5)
            try:
                setText(self.weekNrHd, cel)
            except:
                pass
            deselectAll()
            selectObject(cel)
            setParagraphStyle(self.pStyleDayNames, cel)
            setTextVerticalAlignment(ALIGNV_TOP, cel)
            setTextColor("txtWeekNo", cel)
            setFillColor("fillWeekNo", cel)
            setCustomLineStyle(self.gridLineStyleWeekNo, cel)
            colCnt = 0.5
        for j in self.dayOrder: # day names
            cel = createText(self.marginL + self.offsetX + colCnt * self.colSize,
                self.marginT + self.offsetY + self.rowSize * rowCnt, self.colSize, self.rowSize * 0.5)
            setText(j, cel)
            deselectAll()
            selectObject(cel)
            setParagraphStyle(self.pStyleDayNames, cel)
            setTextVerticalAlignment(ALIGNV_TOP, cel)
            setTextColor("txtDayNames", cel)
            setFillColor("fillDayNames", cel)
            setCustomLineStyle(self.gridLineStyleDayNames, cel)
            colCnt+=1

    def createMiniHeader(self, monthName, colCnt):
        """ Draw mini month calendars for previous and next months in the header """
        rowCnt = 2.5
        colCnt = colCnt / self.miniFactor
        cel = createText(self.marginL + self.offsetX + self.displac + colCnt * self.colSize * self.miniFactor,
                self.marginT + self.offsetY + self.rowSize / 8 * rowCnt,
                self.colSize * self.miniFactor * 7, self.rowSize / 8)
        mtHd = monthName
        setText(mtHd.upper(), cel)
        deselectAll()
        selectObject(cel)
        setParagraphStyle(self.pStyleMini, cel)
        setTextVerticalAlignment(ALIGNV_CENTERED, cel)
        rowCnt = 4
        for j in self.dayOrderMini: # day names
            cel = createText(self.marginL + self.offsetX + self.displac + colCnt * self.colSize * self.miniFactor,
                self.marginT + self.offsetY + self.rowSize / 8 * rowCnt,
                self.colSize * self.miniFactor, self.rowSize / 8)
            setText(j, cel)
            deselectAll()
            selectObject(cel)
            setParagraphStyle(self.pStyleMini, cel)
            setTextVerticalAlignment(ALIGNV_CENTERED, cel)
            selectText(getTextLength(cel) - 1, 1, cel)
            setTextColor("None", cel)  # change "|"-character color to become invisible
            colCnt+=1

    def createMiniCals(self, mini_mth, miniCal, colCnt):
        """ Draw mini month calendars for previous and next months in the header """
        rowCnt = 5
        colCnt0 = colCnt
        for week in miniCal:
            colCnt = colCnt0 / self.miniFactor
            for day in week:
                cel = createText(self.marginL + self.offsetX + self.displac 
                    + colCnt * self.colSize * self.miniFactor,
                    self.marginT + self.offsetY + self.rowSize / 8 * rowCnt,
                    self.colSize * self.miniFactor, self.rowSize / 8)
                colCnt += 1
                if day.month == (mini_mth):
                    setText(str(day.day), cel)
                    deselectAll()
                    selectObject(cel)
                    setParagraphStyle(self.pStyleMini, cel)
                    setTextVerticalAlignment(ALIGNV_CENTERED,cel)
                if calendar.firstweekday() == 6:
                    x = 1
                else:
                    x = 6
                if (int(colCnt - colCnt0 / self.miniFactor) == x) \
                        or (int(colCnt - colCnt0 / self.miniFactor) == 7):
                        setTextColor("txtWeekend", cel) # weekend days Color
                for x in range(len(self.holidaysList)):
                    if (self.holidaysList[x][0]==(day.year) and
                        self.holidaysList[x][1]==str(day.month) and 
                        self.holidaysList[x][2]==str(day.day) and
                        self.holidaysList[x][4] == '1'):
                        setTextColor("txtHoliday", cel) # holidays Color
            rowCnt += 1

######################################################
class calcHolidays:
    """ Import local holidays from '*holidays.txt'-file and convert the variable
    holidays into dates for the given year."""

    def __init__(self, year):
        self.year = year

    def calcEaster(self):
        """ Calculate Easter date for the calendar Year using Butcher's Algorithm. 
        Works for any date in the Gregorian calendar (1583 and onward)."""
        a = self.year % 19
        b = self.year // 100
        c = self.year % 100
        d = (19 * a + b - b // 4 - ((b - (b + 8) // 25 + 1) // 3) + 15) % 30
        e = (32 + 2 * (b % 4) + 2 * (c // 4) - d - (c % 4)) % 7
        f = d + e - 7 * ((a + 11 * d + 22 * e) // 451) + 114	
        easter = datetime.date(int(self.year), int(f//31), int(f % 31 + 1))
        return easter

    def calcEasterO(self):
        """ Calculate Easter date for the calendar Year using Meeus Julian Algorithm. 
        Works for any date in the Gregorian calendar between 1900 and 2099."""
        d = (self.year % 19 * 19 + 15) % 30
        e = (self.year % 4 * 2 + self.year % 7 * 4 - d + 34) % 7 + d + 127
        m = e / 31
        a = e % 31 + 1 + (m>4)
        if a>30: a, m=1,5
        easter = datetime.date(int(self.year), int(m), int(a))
        return easter

    def calcVarHoliday(self, base, delta):
        """ Calculate variable Christian holidays dates for the calendar Year. 
        'base' is Easter and 'delta' the days from Easter."""
        holiday = base + timedelta(days=int(delta))
        return holiday

    def calcNthWeekdayOfMonth(self, n, weekday, month, year):
        """ Returns (month, day) tuple that represents nth weekday of month in year.
        If n==0, returns last weekday of month. Weekdays: Monday=0."""
        if not 0 <= n <= 5:
            raise IndexError("Nth day of month must be 0-5. Received: {}".format(n))
        if not 0 <= weekday <= 6:
            raise IndexError("Weekday must be 0-6")
        firstday, daysinmonth = calendar.monthrange(year, month)
        # Get first WEEKDAY of month
        first_weekday_of_kind = 1 + (weekday - firstday) % 7
        if n == 0:
        # find last weekday of kind, which is 5 if these conditions are met, else 4
            if first_weekday_of_kind in [1, 2, 3] and first_weekday_of_kind + 28 <= daysinmonth:
                n = 5
            else:
                n = 4
        day = first_weekday_of_kind + ((n - 1) * 7)
        if day > daysinmonth:
            raise IndexError("No {}th day of month {}".format(n, month))
        return (year, month, day)

    def importHolidays(self):
        """ Import local holidays from '*holidays.txt'-file."""
        holidaysFile = filedialog.askopenfilename(title="Open the \
'holidays.txt'-file or cancel")
        holidaysList=list()
        try:
            csvfile = open(holidaysFile, mode="rt",  encoding="utf8")
        except:
            print("Holidays wil NOT be shown.")
            messageBox("Warning:",
               "Holidays wil NOT be shown.",
               ICON_CRITICAL)
            return holidaysList # returns an empty holidays list
        csvReader = csv.reader(csvfile, delimiter=",")
        for row in csvReader:
            try:
                if row[0] == "fixed":
                    holidaysList.append((self.year, row[1], row[2], row[4], row[5]))
                    if row[1] == "12":
                        holidaysList.append((self.year - 1, row[1], row[2], row[4], row[5]))
                    if row[1] == "1":
                        holidaysList.append((self.year + 1, row[1], row[2], row[4], row[5]))
                elif row[0] == "nWDOM": # nth WeekDay Of Month
                    dt=self.calcNthWeekdayOfMonth(int(row[3]), int(row[2]), int(row[1]), int(self.year))
                    holidaysList.append((self.year, str(dt[1]), str(dt[2]), row[4], row[5]))
                    if row[1] == "12":
                        dt=self.calcNthWeekdayOfMonth(int(row[3]), int(row[2]), int(row[1]), int(self.year - 1))
                        holidaysList.append((self.year - 1, str(dt[1]), str(dt[2]), row[4], row[5]))
                    if row[1] == "1":
                        dt=self.calcNthWeekdayOfMonth(int(row[3]), int(row[2]), int(row[1]), int(self.year + 1))
                        holidaysList.append((self.year + 1, str(dt[1]), str(dt[2]), row[4], row[5]))
                elif row[0] == "variable":
                    if row[1] == "easter" or row[1] == "easterO" :
                        if row[1] == "easterO" :
                            base=self.calcEasterO()
                        else:
                            base=self.calcEaster()
                        dt=self.calcVarHoliday(base, int(row[2]))
                        holidaysList.append(((dt.year), str(dt.month), str(dt.day), row[4], row[5]))
                else:
                    pass #do nothing
            except:
                print("Not a valid Holidays file.\nHolidays wil NOT be shown.")
                messageBox("Warning:",
                    "Not a valid Holidays file.\nHolidays wil NOT be shown.",
                    ICON_CRITICAL)
                break
        csvfile.close()
        return holidaysList

######################################################
class calcMoons:
    """ Import moon phases from '*moons.txt'-file and adapt them with the 
    time zone difference into moon phase dates for the given year."""

    def __init__(self, year, utcdiff):
        self.year = year
        self.utcdiff = utcdiff

    def importMoons(self):
        """ Import utc moon phases from '*moonphases.txt'-file."""
        moonsFile = filedialog.askopenfilename(title="Open the \
'moonphases.txt'-file or cancel")
        moonsList=list()
        try:
            csvfile = open(moonsFile, 'rt')
        except:
            print("Moon phases wil NOT be shown.")
            messageBox("Warning:",  "Moon phases wil NOT be shown.", ICON_CRITICAL)
            return moonsList # returns an empty moons list
        csvReader = csv.reader(csvfile, delimiter=",")
        for row in csvReader:
            try:
                if int(row[0]) == self.year:
                    dt = datetime.date(int(row[0]), int(row[1]), int(row[2]))
                    timeHr = int(int(row[3][:(row[3].find(":"))]) + self.utcdiff) \
                        # utc hour +/- time zone difference
                    if row[4] == '0':
                        x = u"\U000025CF" #  New Moon (also u"\U0001F311")
                    elif row[4] == '1':
                        x = u"\U000025D0" # First Quarter (also u"\U0001F313")
                    elif row[4] == '2':
                        x = u"\U000025CB" # Full Moon (also u"\U0001F315")
                    elif row[4] == '3':
                        x = u"\U000025D1" # Last Quarter (also u"\U0001F317")
                    if timeHr > 23:
                        dt = dt + timedelta(days=int(1)) # date + 1 day
                        moonsList.append((str(dt.month), str(dt.day), x))
                    elif timeHr < 0:
                        dt = dt - timedelta(days=int(1)) # date - 1 day
                        moonsList.append((str(dt.month), str(dt.day), x))
                    else:
                        moonsList.append((row[1], row[2], x))
            except:
                print("Not a valid Moonphases file.\nMoons wil NOT be shown.")
                messageBox("Warning:",
                    "Not a valid Moonphases file.\nMoons wil NOT be shown.",
                    ICON_CRITICAL)
                break
        csvfile.close()
        return moonsList

######################################################
class TkCalendar(Frame):
    """ GUI interface for Scribus calendar wizard with Tkinter"""

    def __init__(self, master=None):
        """ Setup the dialog """
        Frame.__init__(self, master)
        self.grid()
        self.master.resizable(0, 0)
        self.master.title('Scribus Monthly Calendar')

        #define widgets
        self.statusVar = StringVar()
        self.statusLabel = Label(self, fg="red", textvariable=self.statusVar)
        self.statusVar.set('Select Options and Values')

        # languages (reference to the localization dictionary)
        langX = 'English'
        self.langLabel = Label(self, text='Select language:')
        self.langFrame = Frame(self)
        self.langFrame.grid()
        self.langScrollbar = Scrollbar(self.langFrame, orient=VERTICAL)
        self.langScrollbar.grid(row=0, column=1, sticky=N+S)
        self.langListbox = Listbox(self.langFrame, selectmode=SINGLE, height=12,
            yscrollcommand=self.langScrollbar.set)
        self.langListbox.grid(row=0, column=0, sticky=N+S+E+W)
        self.langScrollbar.config(command=self.langListbox.yview)
        for i in range(len(localization)):
            self.langListbox.insert(END, localization[i][0])
        self.langButton = Button(self, text='Change language',
            command=self.languageChange)
        
        # choose font
        self.fontLabel = Label(self, text='Change font:')
        self.fontFrame = Frame(self)
        self.fontScrollbar = Scrollbar(self.fontFrame, orient=VERTICAL)
        self.fontListbox = Listbox(self.fontFrame, selectmode=SINGLE, height=12, 
            yscrollcommand=self.fontScrollbar.set)
        self.fontScrollbar.config(command=self.fontListbox.yview)
        fonts = getFontNames()
        fonts.sort()
        for i in fonts:
            self.fontListbox.insert(END, i)
        self.font = 'Symbola Regular'
        self.fontButton = Button(self, text='Apply selected font', command=self.fontApply)

        # year
        self.yearLabel = Label(self, text='Year:')
        self.yearVar = StringVar()
        self.yearEntry = Entry(self, textvariable=self.yearVar, width=4)

        # start of week
        self.weekStartsLabel = Label(self, text='Week begins with:')
        self.weekVar = IntVar()
        self.weekMondayRadio = Radiobutton(self, text='Mon', variable=self.weekVar,
            value=calendar.MONDAY)
        self.weekSundayRadio = Radiobutton(self, text='Sun', variable=self.weekVar,
            value=calendar.SUNDAY)

       # include weeknumber
        self.weekNrLabel = Label(self, text='Show week numbers:')
        self.weekNrVar = IntVar()
        self.weekNrCheck = Checkbutton(self, variable=self.weekNrVar)
        self.weekNrHdLabel = Label(self, text='Week numbers heading:')
        self.weekNrHdVar = StringVar()
        self.weekNrHdEntry = Entry(self, textvariable=self.weekNrHdVar, width=6)
        
        # offsetX, offsetY and inner margins
        self.offsetXLabel = Label(self, text='Calendar offset \nfrom left margin (pt):')
        self.offsetXVar = DoubleVar()
        self.offsetXEntry = Entry(self, textvariable=self.offsetXVar, width=7)
        self.offsetYLabel = Label(self, text='Calendar offset \nfrom top margin (pt):')
        self.offsetYVar = DoubleVar()
        self.offsetYEntry = Entry(self, textvariable=self.offsetYVar, width=7)
        self.marginXLabel = Label(self, text='Inner vertical margin (pt):')
        self.marginXVar = DoubleVar()
        self.marginXEntry = Entry(self, textvariable=self.marginXVar, width=7)
        self.marginYLabel = Label(self, text='Inner horizontal margin (pt):')
        self.marginYVar = DoubleVar()
        self.marginYEntry = Entry(self, textvariable=self.marginYVar, width=7)

        # draw image frame
        self.imageLabel = Label(self, text='Draw Image Frame:')
        self.imageVar = IntVar()
        self.imageCheck = Checkbutton(self, variable=self.imageVar)

        # holidays
        self.holidaysLabel = Label(self, text='Show holidays:')
        self.holidaysVar = IntVar()
        self.holidaysCheck = Checkbutton(self, variable=self.holidaysVar)

        # moon phases
        self.moonsLabel = Label(self, text='Show moon phases:')
        self.moonsVar = IntVar()
        self.moonsCheck = Checkbutton(self, variable=self.moonsVar)

        # UTC difference for moon phases
        self.utcdiffLabel = Label(self, text='Time zone difference from UTC:\n \
(for moon phases)')
        self.utcdiffVar = StringVar()
        self.utcdiffEntry = Entry(self, textvariable=self.utcdiffVar, width=7)

        # mini calendars
        self.minicalsLabel = Label(self, text='Show mini calendars:')
        self.minicalsVar = IntVar()
        self.minicalsCheck = Checkbutton(self, variable=self.minicalsVar)

        # months
        self.monthLabel = Label(self, text='Months:')
        self.monthListbox = Listbox(self, selectmode=MULTIPLE, height=12)
        self.wholeYearLabel = Label(self, text='Whole year:')
        self.wholeYear = IntVar()
        self.wholeYearCheck = Checkbutton(self, command=self.setWholeYear,
            variable=self.wholeYear)

        # closing/running
        self.okButton = Button(self, text="OK", width=6, command=self.okButton_pressed)
        self.cancelButton = Button(self, text="Cancel", command=self.quit)

        # setup values
        self.yearVar.set(str(datetime.date(1, 1, 1).today().year+1)) # added +1 for next year
        #self.wholeYearCheck.select()   # (un)comment to change the default selection on / off
        self.weekMondayRadio.select()
        self.weekNrCheck.select()
        self.weekNrHdVar.set("wk")
        self.offsetXVar.set("0.0")
        self.offsetYVar.set("0.0")
        self.marginXVar.set("0.0")
        self.marginYVar.set("0.0")
        #self.imageCheck.select()
        self.holidaysCheck.select()
        self.moonsCheck.select()
        self.utcdiffVar.set("+1")
        self.minicalsCheck.select()

        # make layout
        self.columnconfigure(0, pad=6)
        currRow = 0
        self.statusLabel.grid(column=0, row=currRow, columnspan=4)
        currRow += 1
        self.langLabel.grid(column=0, row=currRow, sticky=W)
        self.fontLabel.grid(column=1, row=currRow, sticky=W) 
        self.monthLabel.grid(column=3, row=currRow, sticky=W)
        currRow += 1
        self.langFrame.grid(column=0, row=currRow, rowspan=6, sticky=N)
        self.fontFrame.grid(column=1, row=currRow, sticky=N)
        self.fontScrollbar.grid(column=1, row=currRow, sticky=N+S+E)
        self.fontListbox.grid(column=0, row=currRow, sticky=N+S+W)
        self.monthListbox.grid(column=3, row=currRow, rowspan=8, sticky=N)
        currRow += 2
        self.langButton.grid(column=0, row=currRow)
        self.fontButton.grid(column=1, row=currRow)
        self.wholeYearLabel.grid(column=2, row=currRow, sticky=N+E)
        self.wholeYearCheck.grid(column=3, row=currRow, sticky=N+W)
        currRow += 1
        self.yearLabel.grid(column=0, row=currRow, sticky=S+E)
        self.yearEntry.grid(column=1, row=currRow, sticky=S+W)
        self.offsetYLabel.grid(column=2, row=currRow, sticky=S+E)
        self.offsetYEntry.grid(column=3, row=currRow, sticky=S+W)
        currRow += 1
        self.weekStartsLabel.grid(column=0, row=currRow, sticky=S+E)
        self.weekMondayRadio.grid(column=1, row=currRow, sticky=S+W)
        self.marginYLabel.grid(column=2, row=currRow, sticky=N+E)
        self.marginYEntry.grid(column=3, row=currRow, sticky=W)
        currRow += 1
        self.weekSundayRadio.grid(column=1, row=currRow, sticky=N+W)
        self.offsetXLabel.grid(column=2, row=currRow, sticky=S+E)
        self.offsetXEntry.grid(column=3, row=currRow, sticky=S+W)
        currRow += 1
        self.weekNrLabel.grid(column=0, row=currRow, sticky=N+E)
        self.weekNrCheck.grid(column=1, row=currRow, sticky=N+W)
        self.marginXLabel.grid(column=2, row=currRow, sticky=N+E)
        self.marginXEntry.grid(column=3, row=currRow, sticky=W)
        currRow += 1
        self.weekNrHdLabel.grid(column=0, row=currRow, sticky=N+E)
        self.weekNrHdEntry.grid(column=1, row=currRow, sticky=N+W)
        self.imageLabel.grid(column=2, row=currRow, sticky=N+E)
        self.imageCheck.grid(column=3, row=currRow, sticky=N+W)
        currRow += 1
        self.holidaysLabel.grid(column=0, row=currRow, sticky=N+E)
        self.holidaysCheck.grid(column=1, row=currRow, sticky=N+W)
        self.minicalsLabel.grid(column=2, row=currRow, sticky=N+E)
        self.minicalsCheck.grid(column=3, row=currRow, sticky=N+W)
        currRow += 1
        self.moonsLabel.grid(column=0, row=currRow, sticky=N+E)
        self.moonsCheck.grid(column=1, row=currRow, sticky=N+W)
        currRow += 1
        self.utcdiffLabel.grid(column=0, row=currRow, sticky=N+E)
        self.utcdiffEntry.grid(column=1, row=currRow, sticky=N+W)
        currRow += 1
        self.rowconfigure(currRow, pad=6)
        self.okButton.grid(column=1, row=currRow, sticky=E)
        self.cancelButton.grid(column=2, row=currRow, sticky=W)

        # fill the months values
        self.realLangChange()

    def languageChange(self):
        """ Called by Change button. Get language list value and
            call real re-filling. """
        ix = self.langListbox.curselection()
        if len(ix) == 0:
            self.statusVar.set('Select a language, please')
            return
        langX = self.langListbox.get(ix[0])
        self.lang = langX
        if os == "Windows":
            x = langX
        else: # Linux
            iy = [[x[0] for x in localization].index(self.lang)]
            x = (localization[iy[0]][2])
        try:
            locale.setlocale(locale.LC_CTYPE, x)
            locale.setlocale(locale.LC_TIME, x)
        except locale.Error:
            print("Language " + x + " is not installed on your operating system.")
            self.statusVar.set("Language '" + x + "' is not installed on your operating system")
            return
        self.realLangChange(langX)

    def realLangChange(self, langX='English'):
        """ Real widget setup. It takes values from localization list.
        [0] = months, [1] Days """
        self.lang = langX
        self.monthListbox.delete(0, END)
        self.wholeYear.set(0)
        if os == "Windows":
            ix = [[x[0] for x in localization].index(self.lang)]
            self.calUniCode = (localization[ix[0]][1]) # get unicode page for the selected language
        else: # Linux
            self.calUniCode = "UTF-8"
        for i in range (1,13):
            mt = calendar.month_name[i]
            self.monthListbox.insert(END, mt)

    def setWholeYear(self):
        """ All/none months selection. It's called after "Whole year" check button
        click. """
        if self.wholeYear.get() == 1:
            self.monthListbox.selection_set(0, END)
        else:
            self.monthListbox.selection_clear(0, END)

    def fontApply(self, chosenFont = 'Symbola Regular'):
        """ Font selection. Called by "Apply selected font" button click. """
        ix = self.fontListbox.curselection()
        if len(ix) == 0:
            self.statusVar.set('Please select a font.')
            return
        self.font = self.fontListbox.get(ix[0])

    def okButton_pressed(self):
        """ User variables testing and preparing """
        # year
        try:
            year = self.yearVar.get().strip()
            if len(year) != 4:
                raise ValueError
            year = int(year, 10)
        except ValueError:
            self.statusVar.set('Year must be in the "YYYY" format e.g. 2020.')
            return
        # inner margins
        if ((float(self.offsetXVar.get()) - float(self.marginXVar.get())) < 0 
            or (float(self.offsetYVar.get()) - float(self.marginYVar.get())) < 0):
            self.statusVar.set('Inner margins must be less than offsets.')
            return
        # fonts
        fonts = getFontNames()
        if self.font not in fonts:
            self.statusVar.set('Please select a font.')
            return
        # months
        selMonths = self.monthListbox.curselection()
        if len(selMonths) == 0:
            self.statusVar.set('At least one month must be selected.')
            return
        months = []
        for i in selMonths:
            months.append(int(i))
        # week numbers
        if self.weekNrVar.get() == 0:
            weekNr = False
        else:
            weekNr = True
        # draw images
        if self.imageVar.get() == 0:
            drawImg = False
        else:
            drawImg = True
        # show mini calendars
        if self.minicalsVar.get() == 0:
            miniCals = False
        else:
            miniCals = True
        # holidays
        if self.holidaysVar.get() == 0: 
            holidaysList = list()
        else:
            hol = calcHolidays(year)
            holidaysList = hol.importHolidays()
        # moon phases
        try:
            utcdiff = self.utcdiffVar.get().strip()
            if abs(int(utcdiff)) > 12:
                raise ValueError
            utcdiff = int(utcdiff)
        except ValueError: 
            self.statusVar.set('Time zone difference from UTC has to be \
an integer between -12 and +12.')
            return
        if self.moonsVar.get() == 0: 
            moonsList = list()
        else:
            moon = calcMoons(year, utcdiff)
            moonsList = moon.importMoons()
        # create calendar (finally)
        msg=messagebox.showinfo("INFO:", '  language=' + self.lang 
            + '\n  font=' + self.font+'\n')
        cal = ScMonthCalendar(year, months, self.weekVar.get(), weekNr, self.weekNrHdVar.get(),
                float(self.offsetXVar.get()), float(self.marginXVar.get()), float(self.offsetYVar.get()), 
                float(self.marginYVar.get()), drawImg, miniCals, self.font, self.lang, holidaysList,
                moonsList)
        self.master.withdraw()
        err = cal.createCalendar()
        if err != None:
            self.master.deiconify()
            self.statusVar.set(err)
        else:
            self.quit()

    def quit(self):
        self.master.destroy()

######################################################
def main():
    """ Application/Dialog loop with Scribus sauce around """
    try:
        statusMessage('Running script...')
        progressReset()
        original_locale1=locale.getlocale(locale.LC_CTYPE)
        original_locale2=locale.getlocale(locale.LC_TIME)
        root = Tk()
        app = TkCalendar(root)
        root.mainloop()
        locale.setlocale(locale.LC_CTYPE, original_locale1)
        locale.setlocale(locale.LC_TIME, original_locale2)
    finally:
        if haveDoc() > 0:
            redrawAll()
        statusMessage('Done.')
        progressReset()

if __name__ == '__main__':
    main()

