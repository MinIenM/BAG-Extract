#------------------------------------------------------------------------------
# Naam:         libLog.py
# Omschrijving: Generieke functies voor logging binnen BAG Extract+ 
# Auteur:       Matthijs van der Deijl
#
# Versie:       1.3
#               - foutafhandeling verbeterd
# Datum:        16 december 2009
#
# Versie:       1.2
# Datum:        24 november 2009
#
# Ministerie van Volkshuisvesting, Ruimtelijke Ordening en Milieubeheer
#------------------------------------------------------------------------------
import time, datetime
import sys
import wx

from libBAGextractPlusVersie import *
from libBAGconfiguratie import *


class LogScherm:
    def __init__(self):
        self.logStack     = []
        self.stackGrootte = -1

    def __call__(self, tekst):
        self.schrijf(tekst)
        
    def push(self, log):
        self.stackGrootte += 1
        self.logStack.append(" ")
        self.logStack[self.stackGrootte] = log

    def pop(self):
        self.stackGrootte -= 1

    def start(self):
        if self.stackGrootte >= 0:
            i = self.logStack[self.stackGrootte].GetNumberOfLines() 
            self.logStack[self.stackGrootte].Clear()
            while i > 0:
                self.logStack[self.stackGrootte].AppendText(" \n")
                i -= 1
            self.logStack[self.stackGrootte].Clear()                
            
    def schrijf(self, tekst):
        if self.stackGrootte < 0:
            print tekst
        else:        
            self.logStack[self.stackGrootte].AppendText("\n" + tekst)
            self.logStack[self.stackGrootte].Refresh()
            self.logStack[self.stackGrootte].Update()
            
# globale variabele voor gebruik van de logging        
logScherm = LogScherm()

class Log:
    def __init__(self):
        self.logfileNaam    = ""
        self.logfile        = None
        self.starttime      = 0
        self.bagextractplus = None
        self.cursor         = None

    def __call__(self, tekst):
        self.schrijf(tekst)

    def start(self, applicatie, database, actie, bestand):
        logScherm.start()
        logScherm(actie + " " + bestand)
        logScherm("")
        i = 0
        gevonden = False
        while not gevonden:
            self.logfileNaam = configuratie.logging + "BAGextract+ %s %03d.log" %(str(datetime.date.today()), i)
            try:
                self.logfile = open(self.logfileNaam, "r")
                self.logfile.close()
            except:
                gevonden = True
            i += 1
            
        try:    
            self.logfile = open(self.logfileNaam, "w")
        except Exception, foutmelding:
            logScherm("Fout - kan logfile '%s' niet openen:\n %s" %(self.logfileNaam, foutmelding))
            logScherm("")
            self.logfile = None
            self.logfileNaam = "<niet beschikbaar>"

        if self.logfile:        
            self.logfile.write(" ____    _    ____   _____      _                  _     Versie: %-13s \n" %(BAGextractPlusVersie))
            self.logfile.write("| __ )  / \  / ___| | ____|_  _| |_ _ __ __ _  ___| |_    _      %-13s \n" %(BAGextractPlusDatum))
            self.logfile.write("|  _ \ / _ \| |  _  |  _| \ \/ / __| '__/ _` |/ __| __| _|+|_                  \n")
            self.logfile.write("| |_) / ___ \ |_| | | |___ >  <| |_| | | (_| | (__| |  |+++++|                 \n")
            self.logfile.write("|____/_/   \_\VROM| |_____/_/\_\ __|_|  \__,_|\___|\__|  |+|                   \n")
            self.logfile.write("\n")
            self.logfile.write("Logfile: %s\n" %(self.logfileNaam))
            self.logfile.write("Datum:   %s\n" %(str(datetime.date.today())))
            self.logfile.write("Actie:   %s - %s\n" %(actie, bestand))
            self.logfile.write("-------------------------------------------------------------------------------\n")
            self.logfile.write("\n")
            self.logfile.flush()

        self.bagextractplus = applicatie
        self.cursor         = self.bagextractplus.GetCursor()
        self.bagextractplus.SetCursor(wx.HOURGLASS_CURSOR)
        for i in range(5):
            self.bagextractplus.menuBalk.EnableTop(i, False)
        self.bagextractplus.Refresh()
        self.bagextractplus.Update()
        self.bagextractplus.app.Yield(True)
                
        self.starttime = 0
        database.log(actie, bestand, self.logfileNaam)
        
    def sluit(self):
        if self.logfile:
            self.logfile.close()
            self.logfile = None
            logScherm("Zie logfile '%s' voor het verslag" %(self.logfileNaam))
            logScherm("")

        self.bagextractplus.SetCursor(self.cursor)
        for i in range(5):
            self.bagextractplus.menuBalk.EnableTop(i, True)
        self.bagextractplus.Refresh()
        self.bagextractplus.Update()
        self.bagextractplus.app.Yield(True)
        self.bagextractplus = None
        
    def schrijf(self, tekst):
        if self.logfile:
            self.logfile.write(tekst + "\n")
            self.logfile.flush()
        logScherm(tekst)
        if self.bagextractplus:
            self.bagextractplus.app.Yield(True)

    def startTimer(self):
        self.starttime = time.clock()

    def schrijfTimer(self, tekst):
        tijd = time.clock() - self.starttime
        if tijd < 60 :
            self.schrijf(tekst + " in %s seconden" %(tijd))
        else:
            self.schrijf(tekst + " in %s minuten" %(tijd/60))

# globale variabele voor gebruik van de logging        
log = Log()

  
