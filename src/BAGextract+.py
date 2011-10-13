#------------------------------------------------------------------------------
# Naam:         BAGextract+.py
# Omschrijving: Hoofdmodule van de BAG Extract+ tools.
# Auteur:       Matthijs van der Deijl
#
# Versie:       1.8
#               - Controle en waarschuwing bij inladen GML-extract toegevoegd.
#               13 oktober 2011
#
# Versie:       1.7
#               - objecttype LPL vervangen door LIG
#               - objecttype SPL vervangen door STA
#               - Controle op levenscyclus in verwerking mutaties uitgeschakeld wegens ongedefinieerde
#                 volgorde in wijziging bestaand voorkomen en opvoer niet voorkomen.
#               11 maart 2011
#
# Versie:       1.5
#               - Bug (objectType not defined) gefixt in verwerking mutatiebestanden
#               9 septembver 2010
#
# Versie:       1.3
#               - Verwerking mutatiebestanden robuuster gemaakt voor geval van lege Mutatie-producten
#               - GeomFromText vervangen door GeomFromEWKT
#                 (dit voorkomt Warnings in de database logging)
#               - Controle op database toegevoegd voorafgaand aan het laden van extract of mutatiebestand
#               - Foutafhandeling verbeterd
# Datum:        28 december 2009
#
# Versie:       1.2
#               - Grafische user interface toegevoegd
# Datum:        24 november 2009
#
# Ministerie van Volkshuisvesting, Ruimtelijke Ordening en Milieubeheer
#------------------------------------------------------------------------------
import wx
import wx.richtext as rt
import sys, os, os.path
import datetime
import csv
from xml.dom import minidom
from ConfigParser import ConfigParser

from libBAGextractPlusVersie import *
from libBAGconfiguratie import *
from libLog import *
from libUnzip import *
from libDatabase import *
from libBAG import *

from BAGraadpleeg import *

# Globale variabele
bagObjecten = []

#------------------------------------------------------------------------------
# BAGExtractPlus toont het hoofdscherm van de BAG Extract+ tool
#------------------------------------------------------------------------------    
class BAGExtractPlus(wx.Frame):
    # Constructor
    # Maakt het logscherm voor het tonen van de voortgang en resultaten van diverse acties en
    # initialiseert de menu's van waaruit alle functies worden aangeroepen.
    def __init__(self, app):
        wx.Frame.__init__(self, None, -1, 'BAG Extract+', size=(1000, 500))
        self.app = app
        
        self.CenterOnScreen()
        self.CreateStatusBar()

        self.menuBalk = wx.MenuBar()
        menu1 = wx.Menu()
        menu1.Append(101, "&Unzip bestand", "Pakt een gedownload BAG-extract of -mutatiebestand uit in de 'extractdirectory'")
        menu1.Append(102, "Laad &Extract bestand", "Laadt een uitgepakt BAG-extractbestand in de database")
        menu1.Append(103, "Laad &Mutatiebestand", "Laadt een uitgepakt mutatiebestand in de database")
        menu1.AppendSeparator()
        menu1.Append(104, "&Toon configuratie", "Toon instellingen in BAG.conf")
        menu1.AppendSeparator()
        menu1.Append(105, "&Afsluiten", "Sluit BAG Extract+ af")
        self.menuBalk.Append(menu1, "&Bestand")

        menu2 = wx.Menu()
        menu2.Append(201, "Zoek BAG-object", "Zoekt en toont de gegevens van een BAG-object")
        self.menuBalk.Append(menu2, "&Raadpleeg database")
        self.SetMenuBar(self.menuBalk)

        menu3 = wx.Menu()
        menu3.Append(301, "&Laad mijn data", "Laadt een bestand met eigen gegevens uit")
        menu3.Append(302, "&Maak view op mijn data", "Laadt een bestand met de view-definitie op de eigen gegevens")
        menu3.Append(303, "&Initialiseer mappingtabel", "Maakt tabel voor mapping van BAG-objecten op eigen gegevens")
        menu3.Append(304, "&Zoek BAG-objecten bij mijn data", "Zoekt BAG-objecten bij eigen gegevens")
        menu3.Append(305, "&Vergelijk BAG-data met mijn data", "Vergelijkt gegevens van de gevonden BAG-objecten met eigen gegevens")
        self.menuBalk.Append(menu3, "&Vergelijk")

        menu4 = wx.Menu()
        menu4.Append(401, "&Initialiseer database", "Maakt database gereed (en leeg) voor gebruik van BAG Extract+")
        menu4.Append(402, "&Onderhoud indexen", "Ververst zoek-indices op tabel")
        menu4.Append(403, "&Toon logging", "Toont de logging in de database")
        self.menuBalk.Append(menu4, "&Database")

        menu5 = wx.Menu()
        menu5.Append(501, "&Over BAG Extract+", "Informatie over BAG Extract+")
        self.menuBalk.Append(menu5, "&Info")
        
        self.Bind(wx.EVT_MENU, self.bestandUnzipExtract,          id=101)
        self.Bind(wx.EVT_MENU, self.bestandLaadExtractBestand,    id=102)
        self.Bind(wx.EVT_MENU, self.bestandLaadMutatieBestand,    id=103)
        self.Bind(wx.EVT_MENU, self.bestandToonConfiguratie,      id=104)
        self.Bind(wx.EVT_MENU, self.bestandSluitBAGExtractplus,   id=105)

        self.Bind(wx.EVT_MENU, self.raadpleeg,                    id=201)

        self.Bind(wx.EVT_MENU, self.vergelijkLaadMijnData,        id=301)
        self.Bind(wx.EVT_MENU, self.vergelijkMaakView,            id=302)
        self.Bind(wx.EVT_MENU, self.vergelijkInitialiseerMapping, id=303)
        self.Bind(wx.EVT_MENU, self.vergelijkZoekBAGobjecten,     id=304)
        self.Bind(wx.EVT_MENU, self.vergelijkVergelijkGegevens,   id=305)

        self.Bind(wx.EVT_MENU, self.databaseInitialiseer,         id=401)
        self.Bind(wx.EVT_MENU, self.databaseOnderhoudIndexen,     id=402)
        self.Bind(wx.EVT_MENU, self.databaseToonLogging,          id=403)

        self.Bind(wx.EVT_MENU, self.infoBAGExtractPlus,           id=501)
      
        self.log  = wx.TextCtrl(self, -1, "Welkom bij BAG Extract+\n\n", style=wx.TE_READONLY|wx.TE_MULTILINE)
        self.font = wx.Font(8, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.log.SetFont(self.font)
        logScherm.push(self.log)

        self.Show(True)

    #------------------------------------------------------------------------------    
    # Pak een extract of mutatiebestand uit.
    #------------------------------------------------------------------------------    
    def bestandUnzipExtract(self, event):
        fileDialoog = wx.FileDialog(self,
                                    "Selecteer bestand",
                                    configuratie.download,
                                    "",
                                    "*.zip",
                                    wx.OPEN|wx.CHANGE_DIR)
        if fileDialoog.ShowModal() == wx.ID_OK:
            log.start(self, database, "Uitpakken extract bestand", fileDialoog.GetPath())
            log("Unzip " + fileDialoog.GetPath())
            log(" naar " + configuratie.extract)
            log("")
            if not unzip_file_into_dir(fileDialoog.GetPath(), configuratie.extract):
                log("Uitpakken mislukt")
            log("")
            log.sluit()
        
    #------------------------------------------------------------------------------    
    # Laad een BAG Extract in de database.
    #------------------------------------------------------------------------------    
    def bestandLaadExtractBestand(self, event):
        for obj in bagObjecten:
            if not obj.controleerTabel():
                dialoog = wx.MessageDialog(self,
                                           "1 of meerdere tabellen ontbreken in de database. Initialiseer eerst de database (zie database-menu).",
                                           "",
                                           wx.OK|wx.ICON_EXCLAMATION)
                dialoog.ShowModal()
                return
            
        dirDialoog = wx.DirDialog(self,
                                  "Selecteer directory met extract bestanden",
                                  configuratie.extract,
                                  wx.OPEN|wx.DD_DIR_MUST_EXIST)
        if dirDialoog.ShowModal() == wx.ID_OK:
            logging = database.getLog()
            for regel in logging:
                if regel[2] == dirDialoog.GetPath():
                    dialoog = wx.MessageDialog(self,
                                               "WAARSCHUWING: Dit extractbestand is eerder verwerkt op %s (zie logging). Wilt u doorgaan?" %(regel[0]),
                                               "",
                                               wx.YES_NO|wx.ICON_QUESTION)
                    if dialoog.ShowModal() == wx.ID_NO:
                        return
                    break

            log.start(self, database, "Laad extract bestand", dirDialoog.GetPath())
            verwerkteBestanden = 0
            start = time.clock()
            # Loop door alle bestanden binnen de gekozen directory en verwerk deze
            for (root, subdirectories, files) in os.walk(dirDialoog.GetPath()):
                for subdirectoryNaam in subdirectories:
                    # Sla de mutatiebestanden over in deze verwerking. Deze zijn
                    # herkenbaar aan de aanduiding MUT in de naam.
                    if not "MUT" in subdirectoryNaam:
                        subdirectory = os.path.join(root, subdirectoryNaam)
                        log(subdirectory)
                        for xmlFileNaam in os.listdir(subdirectory):
                            if xmlFileNaam == ".":
                                break
                            (naam,extensie) = os.path.splitext(xmlFileNaam)
                            if extensie.upper() == ".XML":
                                xmlFile = os.path.join(subdirectory, xmlFileNaam)
                                log(xmlFileNaam + "...")
                                log.startTimer()
                                
                                try:
                                    xml = minidom.parse(xmlFile)
                                    teller = 0
                                    for bagObject in bagObjecten:
                                        for xmlObject in xml.getElementsByTagName(bagObject.tag()):
                                            bagObject.leesUitXML(xmlObject)
                                            bagObject.voegToeInDatabase()
                                            teller += 1
                                            self.app.Yield(True)
                                    log.schrijfTimer("=> %d objecten toegevoegd" %(teller))
                                    if teller == 0:
                                        for xmlObject in xml.getElementsByTagName("product_LVC_gml:LVC-GML-product"):
                                            teller += 1
                                        if teller > 0:
                                            log("*** Waarschuwing *** Bestand is een BAG-extact in GML-formaat; BAG Extract+ verwerkt alleen BAG-extracten in XML-formaat!")
                                    xml.unlink()
                                    verwerkteBestanden += 1
                                except Exception, foutmelding:
                                    log("*** FOUT *** Fout in verwerking xml-bestand '%s':\n %s" %(xmlFileNaam, foutmelding))
                        log("")                    
            if verwerkteBestanden == 0:
                log("")
                log("%s bevat geen extractbestanden" %(dirDialoog.GetPath()))
                log("")
            else:
                tijd = time.clock() - start
                log("")
                log("%s bestanden verwerkt" %(str(verwerkteBestanden)))
                log("")
                log("Einde verwerking - verwerkingstijd: %s minuten " %(str(tijd/60)))
                log("")
            log.sluit()
            
    #------------------------------------------------------------------------------    
    # Laad een BAG mutatiebestand in de database.
    #------------------------------------------------------------------------------    
    def bestandLaadMutatieBestand(self, event):
        for obj in bagObjecten:
            if not obj.controleerTabel():
                dialoog = wx.MessageDialog(self,
                                           "1 of meerdere tabellen ontbreken in de database. Initialiseer eerst de database (zie database-menu).",
                                           "",
                                           wx.OK|wx.ICON_EXCLAMATION)
                dialoog.ShowModal()
                return

        dirDialoog = wx.DirDialog(self,
                                  "Selecteer directory met mutatiebestand",
                                  configuratie.extract,
                                  wx.OPEN|wx.DD_DIR_MUST_EXIST)
        if dirDialoog.ShowModal() == wx.ID_OK:
            logging = database.getLog()
            for regel in logging:
                if regel[2] == dirDialoog.GetPath():
                    dialoog = wx.MessageDialog(self,
                                               "WAARSCHUWING: Dit mutatiebestand is eerder verwerkt op %s (zie logging). Wilt u doorgaan?" %(regel[0]),
                                               "", wx.YES_NO|wx.ICON_QUESTION)
                    if dialoog.ShowModal() == wx.ID_NO:
                        return
                    break

            log.start(self, database, "Laad mutatiebestand ", dirDialoog.GetPath())
            verwerkteBestanden = 0
            start = time.clock()
            wWPL = 0
            wOPR = 0
            wNUM = 0
            wLIG = 0
            wSTA = 0
            wVBO = 0
            wPND = 0
            nWPL = 0
            nOPR = 0
            nNUM = 0
            nLIG = 0
            nSTA = 0
            nVBO = 0
            nPND = 0
            tellerFout = 0
            # Loop door alle mutatiebestanden binnen de gekozen directory en verwerk deze
            for (root, subdirectories, files) in os.walk(dirDialoog.GetPath()):
                for subdirectoryNaam in subdirectories:
                    # De mutatiebestanden zijn herkenbaar aan de aanduiding MUT in de naam
                    if "MUT" in subdirectoryNaam:
                        subdirectory = os.path.join(root, subdirectoryNaam)
                        log(subdirectory)
                        for xmlFileNaam in os.listdir(subdirectory):
                            if xmlFileNaam == ".":
                                break
                            (naam,extensie) = os.path.splitext(xmlFileNaam)
                            if extensie.upper() == ".XML":
                                xmlFile = os.path.join(subdirectory, xmlFileNaam)
                                log(xmlFileNaam + "...")
                                log.startTimer()
                                
                                try:
                                    xml = minidom.parse(xmlFile)
                                    tellerNieuw  = 0
                                    tellerWijzig = 0
                                    for xmlMutatie in xml.getElementsByTagName("product_LVC:Mutatie-product"):
                                        xmlObjectType = xmlMutatie.getElementsByTagName("product_LVC:ObjectType")
                                        if len(xmlObjectType) > 0:
                                            bagObjectOrigineel = getBAGobjectBijType(getText(xmlObjectType[0].childNodes))
                                            bagObjectWijziging = getBAGobjectBijType(getText(xmlObjectType[0].childNodes))
                                            bagObjectNieuw     = getBAGobjectBijType(getText(xmlObjectType[0].childNodes))

                                            xmlOrigineel = xmlMutatie.getElementsByTagName("product_LVC:Origineel")
                                            xmlWijziging = xmlMutatie.getElementsByTagName("product_LVC:Wijziging")
                                            xmlNieuw     = xmlMutatie.getElementsByTagName("product_LVC:Nieuw")
                                            if len(xmlOrigineel) > 0 and bagObjectOrigineel and len(xmlWijziging) > 0 and bagObjectWijziging:
                                                bagObjectOrigineel.leesUitXML(xmlOrigineel[0].getElementsByTagName(bagObjectOrigineel.tag())[0])
                                                bagObjectWijziging.leesUitXML(xmlWijziging[0].getElementsByTagName(bagObjectWijziging.tag())[0])
                                                bagObjectOrigineel.wijzigInDatabase(bagObjectWijziging)
                                                tellerWijzig += 1
                                                if bagObjectOrigineel.objectType() == "WPL":
                                                    wWPL += 1
                                                if bagObjectOrigineel.objectType() == "OPR":
                                                    wOPR += 1
                                                if bagObjectOrigineel.objectType() == "NUM":
                                                    wNUM += 1
                                                if bagObjectOrigineel.objectType() == "LIG":
                                                    wLIG += 1
                                                if bagObjectOrigineel.objectType() == "STA":
                                                    wSTA += 1
                                                if bagObjectOrigineel.objectType() == "VBO":
                                                    wVBO += 1
                                                if bagObjectOrigineel.objectType() == "PND":
                                                    wPND += 1
                                            if len(xmlNieuw) > 0:
                                                bagObjectNieuw.leesUitXML(xmlNieuw[0].getElementsByTagName(bagObjectNieuw.tag())[0])
                                                bagObjectNieuw.voegToeInDatabase()
                                                #bagObjectNieuw.controleerLevenscyclus(toonResultaat=True)
                                                #if not bagObjectNieuw.levenscyclusCorrect:
                                                #    tellerFout += 1
                                                tellerNieuw += 1
                                                if bagObjectNieuw.objectType() == "WPL":
                                                    nWPL += 1
                                                if bagObjectNieuw.objectType() == "OPR":
                                                    nOPR += 1
                                                if bagObjectNieuw.objectType() == "NUM":
                                                    nNUM += 1
                                                if bagObjectNieuw.objectType() == "LIG":
                                                    nLIG += 1
                                                if bagObjectNieuw.objectType() == "STA":
                                                    nSTA += 1
                                                if bagObjectNieuw.objectType() == "VBO":
                                                    nVBO += 1
                                                if bagObjectNieuw.objectType() == "PND":
                                                    nPND += 1
                                        self.app.Yield(True)
                                    log.schrijfTimer("=> %d objecten toegevoegd, %d objecten gewijzigd" %(tellerNieuw, tellerWijzig))
                                    xml.unlink()
                                    verwerkteBestanden += 1
                                except Exception, foutmelding:
                                    log("*** FOUT *** Fout in verwerking xml-bestand '%s':\n %s" %(xmlFileNaam, foutmelding))
                        log("")

            if verwerkteBestanden == 0:
                log("")
                log("%s bevat geen mutatiebestanden" %(dirDialoog.GetPath()))
                log("")
            else:
                tijd = time.clock() - start
                log("")
                log("%s bestanden verwerkt" %(str(verwerkteBestanden)))
                log("")
                log("Einde verwerking - verwerkingstijd: %s minuten " %(str(tijd/60)))
                log("")
                log("                     +------------+----------------+")
                log("                     |    nieuw   |  gewijzigd     |")
                log("+--------------------+------------+----------------+")
                log("| woonplaats         |  %7s   |    %7s     |" %(nWPL, wWPL))
                log("| openbare ruimte    |  %7s   |    %7s     |" %(nOPR, wOPR))
                log("| nummeraanduiding   |  %7s   |    %7s     |" %(nNUM, wNUM))
                log("| pand               |  %7s   |    %7s     |" %(nPND, wPND))
                log("| verblijfsobject    |  %7s   |    %7s     |" %(nVBO, wVBO))
                log("| ligplaats          |  %7s   |    %7s     |" %(nLIG, wLIG))
                log("| standplaats        |  %7s   |    %7s     |" %(nSTA, wSTA))
                log("+--------------------+------------+----------------+")
                if tellerFout > 0:
                    log("")
                    log("Van %s gewijzigde objecten is de levenscyclus in de database corrupt geraakt." %(tellerFout))
            log("")
            log.sluit()

    #------------------------------------------------------------------------------    
    # Toon configuratiegegevens uit BAG.conf.
    #------------------------------------------------------------------------------    
    def bestandToonConfiguratie(self, event):
        logScherm.start()
        logScherm("Inhoud van 'BAG.conf'")
        logScherm("+-----------------------------------------------------------------------------+")
        logScherm(" Databasegegevens:")
        logScherm(" - Database = " + configuratie.database)
        logScherm(" - Host     = " + configuratie.host)
        logScherm(" - User     = " + configuratie.user)
        logScherm(" - Password = " + configuratie.password)
        logScherm("")
        logScherm(" Bestandslocatiegegevens:")
        logScherm(" - Download = " + configuratie.download)
        logScherm(" - Extract  = " + configuratie.extract)
        logScherm(" - Logging  = " + configuratie.logging)
        logScherm("+-----------------------------------------------------------------------------+")
        logScherm("")
            
    #------------------------------------------------------------------------------    
    # Sluit de applicatie.
    #------------------------------------------------------------------------------    
    def bestandSluitBAGExtractplus(self, event):
        self.Close()

    #------------------------------------------------------------------------------    
    # Start het raadpleeg scherm voor het zoeken en raadplegen van BAG objecten.
    #------------------------------------------------------------------------------    
    def raadpleeg(self, event):
        raadpleeg = BAGRaadpleeg(self)
        logScherm.push(raadpleeg.log)        
        raadpleeg.ShowModal()
        logScherm.pop()

    #------------------------------------------------------------------------------    
    # Laad een bestand met afnemersdata in de database.
    #------------------------------------------------------------------------------    
    def vergelijkLaadMijnData(self, event):
        fileDialoog = wx.FileDialog(self,
                                    "Selecteer bestand met mijn data",
                                    os.getcwd(),
                                    "",
                                    "*.csv;*.txt",
                                    wx.OPEN|wx.CHANGE_DIR)
        if fileDialoog.ShowModal() == wx.ID_OK:
            # Open het in te laden bestand
            try:
                csvFile = open(fileDialoog.GetPath(),"rU")
            except:
                dialoog = wx.MessageDialog(self,
                           "Kan invoerbestand '%s' niet openen" %(fileDialoog.GetPath()),
                           "",
                           wx.OK|wx.ICON_EXCLAMATION)
                dialoog.ShowModal()
                logScherm("Kan invoerbestand '%s' niet openen" %(fileDialoog.GetPath()))
                return

            # Lees het eerste stukje om te bepalen of het CSV-bestand een header bevat.
            try:
                sample  = csvFile.read(1024)
                dialect = csv.Sniffer().sniff(sample)
                header  = csv.Sniffer().has_header(sample)
            except csv.Error, foutmelding:
                logScherm("*** FOUT *** Fout bij het inladen van invoerbestand '%s'" %(fileDialoog.GetPath()))
                dialoog = wx.MessageDialog(self,
                           "Fout bij het inladen van invoerbestand '%s':\n %s" %(fileDialoog.GetPath(), foutmelding),
                           "",
                           wx.OK|wx.ICON_EXCLAMATION)
                dialoog.ShowModal()
                csvFile.close()
                return
            
            # Ga weer terug naar het begin van het bestand
            csvFile.seek(0)

            # Lees het hele CSV-bestand
            try:
                reader = csv.reader(csvFile, dialect)
            except csv.Error, foutmelding:
                logScherm("*** FOUT *** Fout bij het inladen van invoerbestand '%s'" %(fileDialoog.GetPath()))
                dialoog = wx.MessageDialog(self,
                           "Fout bij het inladen van invoerbestand '%s' op regel %d:\n %s" %(fileDialoog.GetPath(), reader.line_num, foutmelding),
                           "",
                           wx.OK|wx.ICON_EXCLAMATION)
                dialoog.ShowModal()
                csvFile.close()
                return

            log.start(self, database, "Laad bestand met mijn data", fileDialoog.GetPath())
                
            # Maak in de database de tabel met de gegevens uit het CSV-bestand.
            # De tabel krijgt de naam van het CSV-bestand.
            # Als het bestand een header heeft, dan worden de kolomnamen uit de header
            # gebruikt als kolomnamen in de tabel. Als er geen header is, dan worden de
            # kolommen genummer kolom1, kolom2, enz.
            pad, filenaam = os.path.split(fileDialoog.GetPath())
            tabelnaam, extensie = os.path.splitext(filenaam)
            tabelnaam = tabelnaam.replace(' ', '_')
            kolommen  = ""
            sqlCreate = "CREATE TABLE %s (" %(tabelnaam)
            sqlInsert = "INSERT INTO %s (" %(tabelnaam)
            rij = reader.next()
            aantalKolommen = len(rij)
            for i in range(0, aantalKolommen):
                if i > 0:
                    sqlCreate += ", "
                    sqlInsert += ", "
                    kolommen  += "\n   - "
                if header:
                    sqlCreate += rij[i]
                    sqlInsert += rij[i]
                    kolommen  += rij[i]
                else:
                    sqlCreate += "kolom%s" %(i)
                    sqlInsert += "kolom%s" %(i)
                    kolommen  += "kolom%s" %(i)
                sqlCreate += " VARCHAR(100)" 
            sqlCreate += ")"
            sqlInsert += ") VALUES "

            # Maak de tabel in de database
            log("Maak tabel %s met de kolommen:\n   - %s" %(tabelnaam, kolommen))
            database.maakTabel(tabelnaam, sqlCreate)
            log("")
            
            # Voeg elke regel in het CSV-bestand toe in de tabel
            log("Laad data uit %s ..." %(fileDialoog.GetPath()))
            teller = 0
            for rij in reader:
                sqlValues = "("
                for i in range(0, aantalKolommen):
                    if i > 0:
                        sqlValues += ","
                    if i < len(rij):
                        sqlValues += "'%s'" %(database.string(rij[i]))
                    else:
                        sqlValues += "''"
                sqlValues += ")"
                try:
                    database.execute(sqlInsert + sqlValues)
                    teller += 1
                except:
                    log("Regel genegeerd wegens onleesbare data: %s" %(sqlValues))
                self.app.Yield(True)
            log("")
            log("%d rijen geladen in tabel %s" %(teller, tabelnaam))
            log("")
            log.sluit()
            csvFile.close()

    #------------------------------------------------------------------------------    
    # Maak een view 'mijn_data' op de ingeladen afnemersdata in de database.
    #------------------------------------------------------------------------------    
    def vergelijkMaakView(self, event):
        fileDialoog = wx.FileDialog(self,
                                    "Selecteer bestand met de view-definitie op mijn data",
                                    os.getcwd(),
                                    "",
                                    "*.txt",
                                    wx.OPEN|wx.CHANGE_DIR)
        if fileDialoog.ShowModal() == wx.ID_OK:
            try:
                viewFile = open(fileDialoog.GetPath(),'rU')
            except:
                dialoog = wx.MessageDialog(self,
                           "Kan invoerbestand '%s' niet openen" %(fileDialoog.GetPath()),
                           "",
                           wx.OK|wx.ICON_EXCLAMATION)
                dialoog.ShowModal()
                logScherm("Kan invoerbestand '%s' niet openen" %(fileDialoog.GetPath()))
                return
            
            log.start(self, database, "Laad bestand met viewdefinitie op mijn data ", fileDialoog.GetPath())

            sql = viewFile.read(1024)
            log(sql)
            log("")
            if not database.maakView("mijn_data", sql):
                dialoog = wx.MessageDialog(self,
                           "Kan view 'mijn_data' niet maken",
                           "",
                           wx.OK|wx.ICON_EXCLAMATION)
                dialoog.ShowModal()
            
            log("")
            log.sluit()
            viewFile.close()
            
    #------------------------------------------------------------------------------    
    # Maak en initialiseer de mappingtabel voor de mapping van BAG objecten op mijn_data
    #------------------------------------------------------------------------------    
    def vergelijkInitialiseerMapping(self, event):
        # BAGvergelijk+ maakt een mappingtabel met daarin de sleutelgegevens
        # van mijn_data en de sleutelgegevens van de BAG-data.
        # Desgewenst kunt u hier zelf kolommen aan toevoegen. Bijvoorbeeld om
        # ook pandgegevens te vergelijken.
        log.start(self, database, "Maak mappingtabel mijn_bag_data", "")
        sql =  "CREATE TABLE mijn_bag_data "
        sql += "(mijn_identificatie                   VARCHAR(100)"
        sql += ",mijn_woonplaatsnaam                  VARCHAR(100)"
        sql += ",mijn_openbareruimtenaam              VARCHAR(100)"
        sql += ",mijn_postcode                        VARCHAR(100)"
        sql += ",mijn_huisnummer                      VARCHAR(100)"
        sql += ",mijn_huisletter                      VARCHAR(100)"
        sql += ",mijn_huisnummertoevoeging            VARCHAR(100)"
        sql += ",mijn_geometrie                       VARCHAR(100)"
        sql += ",mijn_bouwjaarvan                     VARCHAR(100)"
        sql += ",mijn_bouwjaartot                     VARCHAR(100)"   
        sql += ",bag_woonplaatsnaam                   VARCHAR(80)"
        sql += ",bag_openbareruimtenaam               VARCHAR(80)"
        sql += ",bag_postcode                         VARCHAR(6)"
        sql += ",bag_huisnummer                       VARCHAR(5)"
        sql += ",bag_huisletter                       VARCHAR(5)"
        sql += ",bag_huisnummertoevoeging             VARCHAR(4)"
        sql += ",bag_nummeraanduidingidentificatie    VARCHAR(16)"
        sql += ",bag_adresseerbaarobjectidentificatie VARCHAR(16)"
        sql += ",bag_pandidentificatie                VARCHAR(16)"
        sql += ",bag_bouwjaar                         VARCHAR(6)"
        sql += ",opmerking                            VARCHAR(1000)"
        sql += ")"
        sql += " WITH (OIDS=TRUE)"
        database.maakTabel("mijn_bag_data", sql)

        # Vul de mappingtabel met de sleutelgegevens uit mijn_data.
        log("")
        log("Vul mappingtabel met gegevens uit mijn_bag_data...")
        sql =  "INSERT INTO mijn_bag_data "
        sql += "(mijn_identificatie"
        sql += ",mijn_woonplaatsnaam"
        sql += ",mijn_openbareruimtenaam"
        sql += ",mijn_postcode"
        sql += ",mijn_huisnummer"
        sql += ",mijn_huisletter"
        sql += ",mijn_huisnummertoevoeging"
        sql += ",mijn_geometrie"
        sql += ",mijn_bouwjaarvan"
        sql += ",mijn_bouwjaartot"
        sql += ",bag_adresseerbaarobjectidentificatie"
        sql += ",bag_nummeraanduidingidentificatie"
        sql += ",bag_pandidentificatie"
        sql += ",opmerking"
        sql += ")"
        sql += " SELECT mijn_data.mijn_identificatie"
        sql += "      , mijn_data.mijn_woonplaatsnaam"
        sql += "      , mijn_data.mijn_openbareruimtenaam"
        sql += "      , mijn_data.mijn_postcode"
        sql += "      , mijn_data.mijn_huisnummer"
        sql += "      , mijn_data.mijn_huisletter"
        sql += "      , mijn_data.mijn_huisnummertoevoeging"
        sql += "      , replace(replace('POINT(x.0 y.0 0.0)', 'x', mijn_data.mijn_x), 'y', mijn_data.mijn_y)"
        sql += "      , mijn_data.mijn_bouwjaarvan"
        sql += "      , mijn_data.mijn_bouwjaartot"
        sql += "      , ''"
        sql += "      , ''"
        sql += "      , ''"
        sql += "      , ''"
        sql += "   FROM mijn_data"
        database.execute(sql)
        log(" ==> %s rijen toegevoegd" %(database.cursor.rowcount))
        log("Voeg geometrie toe...")
        database.execute("SELECT AddGeometryColumn('public', 'mijn_bag_data', 'geometrie', 28992, 'POINT', 3)")
        database.execute("UPDATE mijn_bag_data SET geometrie = GeomFromEWKT('SRID=28992;' || mijn_geometrie)")
        log(" ==> %s rijen gewijzigd" %(database.cursor.rowcount))
        log("")
        log.sluit()
        
    #------------------------------------------------------------------------------    
    # Zoek de BAG-objecten bij de afnemersdata in de mappingtabel 
    #------------------------------------------------------------------------------    
    def vergelijkZoekBAGobjecten(self, event):
        log.start(self, database, "Zoek BAG-gegevens bij mijn data", "")

        aantalMijn_data_bag = 0

        log("")
        log("Zoek panden waarvan de geometrie een element van mijn_data overlapt...")
        sql  = "UPDATE mijn_bag_data"
        sql += "   SET bag_pandidentificatie = PND.identificatie"
        sql += "     , bag_bouwjaar          = PND.bouwjaar"
        sql += "  FROM pandActueelBestaand PND"
        sql += " WHERE PND.geometrie && mijn_bag_data.geometrie"   # a && b betekent a OVERLAPS b
        aantalMijn_data_bag += database.execute(sql)
        log(" ==> %s panden verwerkt" %(database.cursor.rowcount))
        
        log("")
        log("Zoek verblijfsobjecten bij de panden...")
        sql  = "UPDATE mijn_bag_data"
        sql += "   SET bag_adresseerbaarobjectidentificatie = VP.identificatie"
        sql += "  FROM verblijfsobjectpand VP"
        sql += " WHERE VP.gerelateerdpand = mijn_bag_data.bag_pandidentificatie"
        database.execute(sql)
        log(" ==> %s verblijfsobjecten verwerkt" %(database.cursor.rowcount))

        log("")
        log("Zoek nummeraanduidingen (hoofdadres) bij de verblijfsobjecten...")
        sql  = "UPDATE mijn_bag_data"
        sql += "   SET bag_nummeraanduidingidentificatie = VBO.hoofdadres"
        sql += "  FROM verblijfsobjectActueelBestaand VBO"
        sql += " WHERE VBO.identificatie = mijn_bag_data.bag_adresseerbaarobjectidentificatie"
        database.execute(sql)
        log(" ==> %s nummeraanduidingen verwerkt" %(database.cursor.rowcount))

        log("")
        log("Zoek gegevens bij nummeraanduidingen...")
        sql  = "UPDATE mijn_bag_data"
        sql += "   SET bag_nummeraanduidingidentificatie = nummeraanduidingidentificatie"
        sql += "     , bag_woonplaatsnaam                = woonplaatsnaam"
        sql += "     , bag_openbareruimtenaam            = openbareruimtenaam"
        sql += "     , bag_postcode                      = postcode"
        sql += "     , bag_huisnummer                    = huisnummer"
        sql += "     , bag_huisletter                    = huisletter"
        sql += "     , bag_huisnummertoevoeging          = huisnummertoevoeging"
        sql += "  FROM adresActueelBestaand"
        sql += " WHERE nummeraanduidingidentificatie = mijn_bag_data.bag_nummeraanduidingidentificatie"
        database.execute(sql)
        log(" ==> %s nummeraanduidingen verwerkt" %(database.cursor.rowcount))

        # Zoek eerst op postcode, huisnummer, huisletter en huisnummertoevoeging
        log("")
        log("Zoek nummeraanduidingen op basis van postcode, huisnummer, huisletter en huisnummertoevoeging...")
        sql =  "UPDATE mijn_bag_data"
        sql += "   SET bag_nummeraanduidingidentificatie = nummeraanduidingidentificatie"
        sql += "     , bag_woonplaatsnaam                = woonplaatsnaam"
        sql += "     , bag_openbareruimtenaam            = openbareruimtenaam"
        sql += "     , bag_postcode                      = postcode"
        sql += "     , bag_huisnummer                    = huisnummer"
        sql += "     , bag_huisletter                    = huisletter"
        sql += "     , bag_huisnummertoevoeging          = huisnummertoevoeging"
        sql += "  FROM adresActueelBestaand"
        sql += " WHERE bag_nummeraanduidingidentificatie = ''"
        sql += "   AND upper(postcode)                   = upper(mijn_bag_data.mijn_postcode)"
        sql += "   AND huisnummer                        = mijn_bag_data.mijn_huisnummer"
        sql += "   AND upper(huisletter)                 = upper(mijn_bag_data.mijn_huisletter)"
        sql += "   AND upper(huisnummertoevoeging)       = upper(mijn_bag_data.mijn_huisnummertoevoeging)"
        aantalMijn_data_bag += database.execute(sql)
        log(" ==> %s nummeraanduidingen verwerkt" %(database.cursor.rowcount))

        # Voor het geval dat in mijn_data huisletter en huisnummertoevoeging door
        # elkaar zijn gebruikt, zoeken we vervolgens met omgewisselde huisletter
        # en huisnummertoevoeging
        log("")
        log("Zoek nummeraanduidingen op basis van postcode, huisnummer, huisletter en huisnummertoevoeging," +
            " maar nu met huisletter en huisnummertoevoeging omgewisseld...")
        sql =  "UPDATE mijn_bag_data"
        sql += "   SET bag_nummeraanduidingidentificatie = nummeraanduidingidentificatie"
        sql += "     , bag_woonplaatsnaam                = woonplaatsnaam"
        sql += "     , bag_openbareruimtenaam            = openbareruimtenaam"
        sql += "     , bag_postcode                      = postcode"
        sql += "     , bag_huisnummer                    = huisnummer"
        sql += "     , bag_huisletter                    = huisletter"
        sql += "     , bag_huisnummertoevoeging          = huisnummertoevoeging"
        sql += "  FROM adresActueelBestaand"
        sql += " WHERE bag_nummeraanduidingidentificatie = ''"
        sql += "   AND upper(postcode)                   = upper(mijn_bag_data.mijn_postcode)"
        sql += "   AND huisnummer                        = mijn_bag_data.mijn_huisnummer"
        sql += "   AND upper(huisletter)                 = upper(mijn_bag_data.mijn_huisnummertoevoeging)"
        sql += "   AND upper(huisnummertoevoeging)       = upper(mijn_bag_data.mijn_huisletter)"
        aantalMijn_data_bag += database.execute(sql)
        log(" ==> %s nummeraanduidingen verwerkt" %(database.cursor.rowcount))

        # Zoek vervolgens op woonplaats, straatnaam en huisnummergegevens
        log("")
        log("Zoek nummeraanduidingen op basis van woonplaats, straatnaam, huisnummer, huisletter en huisnummertoevoeging...")
        sql =  "UPDATE mijn_bag_data"
        sql += "   SET bag_nummeraanduidingidentificatie = nummeraanduidingidentificatie"
        sql += "     , bag_woonplaatsnaam                = woonplaatsnaam"
        sql += "     , bag_openbareruimtenaam            = openbareruimtenaam"
        sql += "     , bag_postcode                      = postcode"
        sql += "     , bag_huisnummer                    = huisnummer"
        sql += "     , bag_huisletter                    = huisletter"
        sql += "     , bag_huisnummertoevoeging          = huisnummertoevoeging"
        sql += "  FROM adresActueelBestaand"
        sql += " WHERE bag_nummeraanduidingidentificatie = ''"
        sql += "   AND upper(woonplaatsnaam)             = upper(mijn_bag_data.mijn_woonplaatsnaam)"
        sql += "   AND upper(openbareruimtenaam)         = upper(mijn_bag_data.mijn_openbareruimtenaam)"
        sql += "   AND huisnummer                        = mijn_bag_data.mijn_huisnummer"
        sql += "   AND upper(huisletter)                 = upper(mijn_bag_data.mijn_huisletter)"
        sql += "   AND upper(huisnummertoevoeging)       = upper(mijn_bag_data.mijn_huisnummertoevoeging)"
        aantalMijn_data_bag += database.execute(sql)
        log(" ==> %s nummeraanduidingen verwerkt" %(database.cursor.rowcount))

        # Zoek vervolgens op woonplaats, straatnaam en huisnummergegevens met
        # omgewisselde huisletter en huisnummertoevoeging
        log("")
        log("Zoek nummeraanduidingen op basis van woonplaats, straatnaam, huisnummer, huisletter en huisnummertoevoeging," +
            " maar nu met huisletter en huisnummertoevoeging omgewisseld...")
        sql =  "UPDATE mijn_bag_data"
        sql += "   SET bag_nummeraanduidingidentificatie = nummeraanduidingidentificatie"
        sql += "     , bag_woonplaatsnaam                = woonplaatsnaam"
        sql += "     , bag_openbareruimtenaam            = openbareruimtenaam"
        sql += "     , bag_postcode                      = postcode"
        sql += "     , bag_huisnummer                    = huisnummer"
        sql += "     , bag_huisletter                    = huisletter"
        sql += "     , bag_huisnummertoevoeging          = huisnummertoevoeging"
        sql += "  FROM adresActueelBestaand"
        sql += " WHERE bag_nummeraanduidingidentificatie = ''"
        sql += "   AND upper(woonplaatsnaam)             = upper(mijn_bag_data.mijn_woonplaatsnaam)"
        sql += "   AND upper(openbareruimtenaam)         = upper(mijn_bag_data.mijn_openbareruimtenaam)"
        sql += "   AND huisnummer                        = mijn_bag_data.mijn_huisnummer"
        sql += "   AND upper(huisletter)                 = upper(mijn_bag_data.mijn_huisnummertoevoeging)"
        sql += "   AND upper(huisnummertoevoeging)       = upper(mijn_bag_data.mijn_huisletter)"
        aantalMijn_data_bag += database.execute(sql)
        log(" ==> %s nummeraanduidingen verwerkt" %(database.cursor.rowcount))

        # Zoek nu vervolgens de verblijfsobjecten bij de gevonden nummeraanduidingen
        # op basis van de hoofdadres-relatie
        log("")
        log("Zoek verblijfsobjecten bij de nummeraanduidingen op basis van hoofdadres...")
        sql =  "UPDATE mijn_bag_data"
        sql += "   SET bag_adresseerbaarobjectidentificatie = VBO.identificatie"
        sql += "  FROM verblijfsobjectActueelBestaand VBO"
        sql += " WHERE VBO.hoofdadres = mijn_bag_data.bag_nummeraanduidingidentificatie"
        sql += "   AND bag_adresseerbaarobjectidentificatie = ''"
        database.execute(sql)
        log(" ==> %s verblijfsobjecten verwerkt" %(database.cursor.rowcount))

        # Zoek nu vervolgens de ligplaatsen bij de gevonden nummeraanduidingen
        # op basis van de hoofdadres-relatie
        log("")
        log("Zoek ligplaatsen bij de nummeraanduidingen op basis van hoofdadres...")
        sql =  "UPDATE mijn_bag_data"
        sql += "   SET bag_adresseerbaarobjectidentificatie = LIG.identificatie"
        sql += "  FROM ligplaatsActueelBestaand LIG"
        sql += " WHERE LIG.hoofdadres = mijn_bag_data.bag_nummeraanduidingidentificatie"
        sql += "   AND bag_adresseerbaarobjectidentificatie = ''"
        database.execute(sql)
        log(" ==> %s ligplaatsen verwerkt" %(database.cursor.rowcount))

        # Zoek nu vervolgens de standplaatsen bij de gevonden nummeraanduidingen
        # op basis van de hoofdadres-relatie
        log("")
        log("Zoek standplaatsen bij de nummeraanduidingen op basis van hoofdadres...")
        sql =  "UPDATE mijn_bag_data"
        sql += "   SET bag_adresseerbaarobjectidentificatie = STA.identificatie"
        sql += "  FROM standplaatsActueelBestaand STA"
        sql += " WHERE STA.hoofdadres = mijn_bag_data.bag_nummeraanduidingidentificatie"
        sql += "   AND bag_adresseerbaarobjectidentificatie = ''"
        database.execute(sql)
        log(" ==> %s standplaatsen verwerkt" %(database.cursor.rowcount))

        # Zoek nu vervolgens de adresseerbareobjecten bij de gevonden nummeraanduidingen
        # op basis van de nevenadres-relatie
        log("")
        log("Zoek adresseerbare objecten bij de nummeraanduidingen op basis van nevenadres...")
        sql =  "UPDATE mijn_bag_data"
        sql += "   SET bag_adresseerbaarobjectidentificatie = adresseerbaarobjectnevenadres.identificatie"
        sql += "  FROM adresseerbaarobjectnevenadres"
        sql += " WHERE adresseerbaarobjectnevenadres.nevenadres = mijn_bag_data.bag_nummeraanduidingidentificatie"
        sql += "   AND bag_adresseerbaarobjectidentificatie = ''"
        database.execute(sql)
        log(" ==> %s adresseerbare objecten verwerkt" %(database.cursor.rowcount))
 
        # Zoek nu vervolgens de panden bij de gevonden verblijfsobjecten
        log("")
        log("Zoek panden bij de verblijfsobjecten...")
        sql =  "UPDATE mijn_bag_data"
        sql += "   SET bag_pandidentificatie = PND.identificatie"
        sql += "     , bag_bouwjaar          = PND.bouwjaar"
        sql += "  FROM verblijfsobjectActueelBestaand VBO"
        sql += "     , verblijfsobjectpand            VP"
        sql += "     , pandActueelBestaand            PND"
        sql += " WHERE bag_pandidentificatie = ''"
        sql += "   AND VBO.identificatie = mijn_bag_data.bag_adresseerbaarobjectidentificatie"
        sql += "   AND VP.identificatie = VBO.identificatie"
        sql += "   AND VP.aanduidingrecordinactief = VP.aanduidingrecordinactief"
        sql += "   AND VP.aanduidingrecordcorrectie = VP.aanduidingrecordcorrectie"
        sql += "   AND VP.begindatumtijdvakgeldigheid = VP.begindatumtijdvakgeldigheid"
        sql += "   AND PND.identificatie = VP.gerelateerdpand"
        database.execute(sql)
        log(" ==> %s verblijfsobjecten verwerkt" %(database.cursor.rowcount))

        log("")
        log("----- Analyse gereed -----")
        log("")
        log("Resultaat: %d BAG-objecten gevonden bij mijn data" %(aantalMijn_data_bag))
        log("")
        log("Zie de tabel 'mijn_bag_data' in de database voor de resultaten.")
        log("")
        log.sluit()
        
    #------------------------------------------------------------------------------    
    # Vergelijk de gegevens van de gevonden BAG-objecten met de afnemersdata in de mappingtabel 
    #------------------------------------------------------------------------------    
    def vergelijkVergelijkGegevens(self, event):
        log.start(self, database, "Vergelijk BAG-data met mijn data", "")

        aantalVerschillen = 0
        
        # Zoek eerst de verschillen in postcode.
        log("")
        log("Zoek verschillen in postcode...")
        sql =  "UPDATE mijn_bag_data"
        sql += "   SET opmerking = replace('* - Postcode verschilt','*'::text, opmerking::text)"
        sql += " WHERE mijn_postcode <> bag_postcode"
        aantalVerschillen += database.execute(sql)
        log(" ==> %s postcodes zijn verschillend" %(database.cursor.rowcount))

        # Zoek de verschillen in huisletter.
        log("")
        log("Zoek verschillen in huisletter ...")
        sql =  "UPDATE mijn_bag_data"
        sql += "   SET opmerking = replace('* - Huisletter verschilt','*'::text, opmerking::text)"
        sql += " WHERE mijn_huisletter <> bag_huisletter"
        aantalVerschillen += database.execute(sql)
        log(" ==> %s huisletters zijn verschillend" %(database.cursor.rowcount))

        # Zoek de verschillen in huisnummertoevoeging.
        log("")
        log("Zoek verschillen in huisnummertoevoeging ...")
        sql =  "UPDATE mijn_bag_data"
        sql += "   SET opmerking = replace('* - Huisnummertoevoeging verschilt','*'::text, opmerking::text)"
        sql += " WHERE mijn_huisnummertoevoeging <> bag_huisnummertoevoeging"
        aantalVerschillen += database.execute(sql)
        log(" ==> %s huisnummertoevoegingen zijn verschillend" %(database.cursor.rowcount))

        # Zoek de verschillen in openbare ruimte naam.
        log("")
        log("Zoek verschillen in openbare ruimte naam...")
        sql =  "UPDATE mijn_bag_data"
        sql += "   SET opmerking = replace('* - Openbare ruimte naam verschilt','*'::text, opmerking::text)"
        sql += " WHERE mijn_openbareruimtenaam <> bag_openbareruimtenaam"
        aantalVerschillen += database.execute(sql)
        log(" ==> %s openbare ruimte namen zijn verschillend" %(database.cursor.rowcount))

        # Zoek de verschillen in woonplaatsnaam.
        log("")
        log("Zoek verschillen in woonplaatsnaam...")
        sql =  "UPDATE mijn_bag_data"
        sql += "   SET opmerking = replace('* - Woonplaatsnaam verschilt','*'::text, opmerking::text)"
        sql += " WHERE mijn_woonplaatsnaam <> bag_woonplaatsnaam"
        aantalVerschillen += database.execute(sql)
        log(" ==> %s woonplaatsnamen zijn verschillend" %(database.cursor.rowcount))

        log("")
        log("Zoek verschillen in bouwjaren...")
        sql =  "UPDATE mijn_bag_data"
        sql += "   SET opmerking = replace('* - Bouwjaar verschilt','*'::text, opmerking::text)"
        sql += " WHERE mijn_bouwjaarvan > bag_bouwjaar"
        sql += "    OR mijn_bouwjaartot < bag_bouwjaar"
        aantalVerschillen += database.execute(sql)
        log(" ==> %s bouwjaren zijn verschillend" %(database.cursor.rowcount))
       
        # Geef een eindverslag met de aantallen gevonden objecten en verschillen
        log("")
        log("----- Analyse gereed -----")
        log("")
        log("Resultaat: %d verschillen gevonden tussen uw gegevens en BAG-gegevens" %(aantalVerschillen))
        log("")
        log("Zie de tabel 'mijn_bag_data' in de database voor de resultaten.")
        log("")
        log.sluit()
        
    #------------------------------------------------------------------------------    
    # Initialiseer de BAG Extract+ database. Eerst vragen we of de gebruiker echt
    # wil dat de eventuele huidige inhoud van de database wordt gewist.
    #------------------------------------------------------------------------------    
    def databaseInitialiseer(self, event):
        dialoog = wx.MessageDialog(self,
                                   "WAARSCHUWING: Deze actie verwijdert de gehele huidige inhoud van de database. Wilt u doorgaan?",
                                   "",
                                   wx.YES_NO|wx.ICON_QUESTION)
        if dialoog.ShowModal() == wx.ID_YES:
            log.start(self, database, "Initialiseren van de BAG Extract+ database", "")
            database.log("Initialiseren van de BAG Extract+ database", "", log.logfileNaam)
            log("")
            for bagObject in bagObjecten:
                bagObject.maakTabel()
                bagObject.maakIndex()
                bagObject.maakViews()
            log("")
            log.sluit()

    #------------------------------------------------------------------------------    
    # Maak de indexen op de tabellen in de database
    #------------------------------------------------------------------------------    
    def databaseOnderhoudIndexen(self, event):
        log.start(self, database, "Opnieuw aanmaken van de indexen in de BAG Extract+ database", "")
        for bagObject in bagObjecten:
            bagObject.maakIndex()
        log("")
        log.sluit()
        
    #------------------------------------------------------------------------------    
    # Toon de logging van uitgevoerde BAG Extract+ acties in de database
    #------------------------------------------------------------------------------    
    def databaseToonLogging(self, event):
        logScherm.start()
        logScherm("Toon de logging in de database\n")
        logging = database.getLog()
        if len(logging) == 0:
            logScherm("Logging is leeg\n")
        else:
            for regel in logging:
                logScherm("+-----------------------------------------------------------------------------+")
                logScherm(" Datum:   %s" %(str(regel[0])))
                logScherm(" Actie:   %s" %(regel[1]))
                if regel[2] <> "":
                    logScherm(" Bestand: %s" %(regel[2]))
                if regel[3] <> "":
                    logScherm(" Logfile: %s" %(regel[3]))
            logScherm("+-----------------------------------------------------------------------------+\n")

    #------------------------------------------------------------------------------    
    # Toon informatie over de BAG Extract+ applicatie 
    #------------------------------------------------------------------------------    
    def infoBAGExtractPlus(self, event):
        info = wx.AboutDialogInfo()
        info.Name = "BAG Extract+"
        info.Version = BAGextractPlusVersie
        info.Description  = "BAG Extract+ is een set hulpmiddelen voor het maken   \n"
        info.Description += "en vullen van een lokale BAG-database.                \n" 
        info.Description += "Deze database wordt gevuld met gegevens uit de BAG    \n"
        info.Description += "(Basisregisratie Adressen en Gebouwen). Deze gegevens \n"
        info.Description += "worden vanuit de Landelijke Voorziening van de BAG    \n"
        info.Description += "geleverd door de dienst 'BAG Extract'.                \n"
        info.Description += "Dit extract en de daaropvolgende mutatiebestanden     \n"
        info.Description += "kunnen worden ingeladen in de database, waarna deze   \n"
        info.Description += "gegevens lokaal beschikbaar zijn voor raadplegen      \n"
        info.Description += "en voor het vergelijken met eigen gegevens.           \n"
        info.Description += "\n"
        info.Copyright    = "BAG Extract+ is ontwikkeld door VROM en wordt vrij    \n"
        info.Copyright   += "beschikbaar gesteld voor gebruik en aanpassing aan    \n"
        info.Copyright   += "eigen behoeften.                                      \n"
        info.WebSite = ("http://bag.vrom.nl", "Basisregistratie Adressen en Gebouwen")
        wx.AboutBox(info)

app = wx.App(0)
bagObjecten.append(Woonplaats())
bagObjecten.append(OpenbareRuimte())
bagObjecten.append(Nummeraanduiding())
bagObjecten.append(Ligplaats())
bagObjecten.append(Standplaats())
bagObjecten.append(Verblijfsobject())
bagObjecten.append(Pand())
BAGExtractPlus(app)
app.MainLoop()
