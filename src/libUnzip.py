#------------------------------------------------------------------------------
# Naam:         libUnzip.py
# Omschrijving: Generieke functies voor het uitpakken van gecomprimeerde
#               BAG Extract bestanden
# Auteur:       Matthijs van der Deijl
#
# Versie:       1.4
# Datum:        21 januari 2010
#
# Ministerie van Volkshuisvesting, Ruimtelijke Ordening en Milieubeheer
#------------------------------------------------------------------------------
import sys, zipfile, os, os.path, glob
from libLog import *

def rmgeneric(path, __func__):
    try:
        __func__(path)
    except OSError, (errno, strerror):
        pass

def removeall(path):
    if not os.path.isdir(path):
        return

    files = os.listdir(path)

    for x in files:
        fullpath=os.path.join(path, x)
        if os.path.isfile(fullpath):
            f=os.remove
            rmgeneric(fullpath, f)
        elif os.path.isdir(fullpath):
            removeall(fullpath)
            f=os.rmdir
            rmgeneric(fullpath, f)

def unzip_file_into_dir(zipfileNaam, doelDirectory):
    # Bepaal directory waarin zipbestand wordt uitgepakt.
    (zipPad, zipNaam) = os.path.split(zipfileNaam)
    (zipNaamKort, zipNaamExtensie) = os.path.splitext(zipNaam)
    extractDirectory = os.path.join(doelDirectory, zipNaamKort)
    log(extractDirectory)

    # Maak directory waarin inhoud van zipbestand wordt opgeslagen.
    if os.path.exists(extractDirectory):        
        removeall(extractDirectory)
        os.rmdir(extractDirectory)
        if os.path.exists(extractDirectory):
            log("*** FOUT *** Verwijder eerst %s om door te gaan." %extractDirectory)
            return False
    try:
        os.mkdir(extractDirectory, 0777)
    except:
        log("*** FOUT *** Kan directory %s niet maken." %extractDirectory)
        return False

    # Open het zipbestand en pak het uit            
    geopendeZipfile = zipfile.ZipFile(zipfileNaam)
    for zipOnderdeelNaam in geopendeZipfile.namelist():
        if zipOnderdeelNaam.endswith('/'):
            os.mkdir(os.path.join(extractDirectory, zipOnderdeelNaam), 0777)
        else:
            zipOnderdeelFile = open(os.path.join(extractDirectory, zipOnderdeelNaam), 'wb')
            zipOnderdeelFile.write(geopendeZipfile.read(zipOnderdeelNaam))
            zipOnderdeelFile.close()

    # Doorloop de directory met de opgeslagen bestanden en pak elk
    # opgeslagen zip-bestand op zijn beurt uit.
    for fileNaam in os.listdir(extractDirectory):
        filePad =  os.path.join(extractDirectory, fileNaam) 
        (fileNaamKort, fileNaamExtensie) = os.path.splitext(filePad)
        if fileNaamExtensie.lower() == ".zip":
            unzip_file_into_dir(filePad, extractDirectory)

    return True
