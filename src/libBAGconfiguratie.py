#------------------------------------------------------------------------------
# Naam:         libBAGconfiguratie.py
# Omschrijving: Generieke functies het lezen van BAG.conf
# Auteur:       Matthijs van der Deijl
#
# Versie:       1.2
# Datum:        24 november 2009
#
# Ministerie van Volkshuisvesting, Ruimtelijke Ordening en Milieubeheer
#------------------------------------------------------------------------------
import sys, os, os.path

from ConfigParser import ConfigParser

class BAGconfiguratie:
    def __init__(self):
        if not os.path.exists('BAG.conf'):
            print "*** FOUT *** Kan configuratiebestand 'BAG.conf' niet openen."
            print ""
            raw_input("Druk <enter> om af te sluiten")
            sys.exit()
            
        configdict = ConfigParser()
        configdict.read('BAG.conf')
        try:
            self.database = configdict.defaults()['database']
            self.host     = configdict.defaults()['host']
            self.user     = configdict.defaults()['user']
            self.password = configdict.defaults()['password']
            self.download = configdict.defaults()['download']
            self.extract  = configdict.defaults()['extract']
            self.logging  = configdict.defaults()['logging']
        except:
            print "*** FOUT *** Inhoud van configuratiebestand 'BAG.conf' is niet volledig."
            print ""
            raw_input("Druk <enter> om af te sluiten")
            sys.exit()
        try:               
            self.bestand  = configdict.defaults()['bestand']
        except:
            pass

# Globale variabele voor toegang tot BAG.conf
configuratie = BAGconfiguratie()
