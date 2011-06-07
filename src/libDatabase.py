#------------------------------------------------------------------------------
# Naam:         libDatabase.py
# Omschrijving: Generieke functies voor databasegebruik binnen BAG Extract+
# Auteur:       Matthijs van der Deijl
#
# Versie:       1.3
#               - functie controleerTabellen toegevoegd
#               - selectie van logregels gesorteerd op datum
# Datum:        9 december 2009
#
# Versie:       1.2
# Datum:        24 november 2009
#
# Ministerie van Volkshuisvesting, Ruimtelijke Ordening en Milieubeheer
#------------------------------------------------------------------------------
import psycopg2

from libBAGconfiguratie import *
from libLog import *

class Database:
    def __init__(self):
        self.database = configuratie.database
        self.host     = configuratie.host 
        self.user     = configuratie.user
        self.password = configuratie.password
         
        try:
            self.connection = psycopg2.connect("dbname='%s' user='%s' host='%s' password='%s'" %(self.database,
                                                                                                 self.user,
                                                                                                 self.host,
                                                                                                 self.password));
            self.cursor = self.connection.cursor()
            print("Verbinding met database %s geslaagd." %(self.database))
        except:
            print("*** FOUT *** Verbinding met database %s niet geslaagd." %(self.database))
            print("")
            raw_input("Druk <enter> om af te sluiten")
            sys.exit()

    # Maak van de datum/tijdstip string in de BAG een datumwaarde voor in de database 
    def datum(self, tekst):
        if tekst == '':
            return "2299-12-31"
        else:
            return "%s%s%s%s-%s%s-%s%s" %(tekst[0],tekst[1],tekst[2],tekst[3],tekst[4],tekst[5],tekst[6],tekst[7])

    # Geef de waarde in de vorm waarin het kan worden ingevoegd in de database
    def string(self, tekst):
        # Vervang een ' in een string door ''
        # Vervang een \n door een spatie
        # Vervang een \ door \\
        return tekst.replace("'", "''").replace("\n", " ").replace("\\", "\\\\")

    def maakObject(self, soort, naam, dropSQL, createSQL):
        # Probeer eerst het oude object weg te gooien. 
        try:
            self.connection.set_isolation_level(0)
            self.cursor.execute(dropSQL)
            log("%s %s verwijderd" %(soort, naam))
        except:
            pass

        # Maak het object nieuw aan.
        try:
            self.connection.set_isolation_level(0)
            self.cursor.execute(createSQL)    
            log("%s %s nieuw aangemaakt" %(soort, naam))
            self.connection.commit()
            return True
        except (psycopg2.Error,), foutmelding:
            log("*** FOUT *** Kan %s %s niet maken:\n %s" %(soort, naam, foutmelding))
            return False
        
    def maakTabel(self, naam, createSQL):
        return self.maakObject("Tabel", naam, "DROP TABLE %s CASCADE" %(naam), createSQL)

    def maakView(self, naam, createSQL):
        return self.maakObject("View", naam, "DROP VIEW %s" %(naam), createSQL)

    def maakIndex(self, naam, createSQL):
        return self.maakObject("Index", naam, "DROP INDEX %s" %(naam), createSQL)

    def insert(self, sql, identificatie):
        try:
            self.cursor.execute(sql)
        except (psycopg2.IntegrityError,), foutmelding:
            log("* Waarschuwing * Object %s niet opgeslagen: %s" %(identificatie, str(foutmelding)))
        except (psycopg2.Error,), foutmelding:
            log("*** FOUT *** Object %s niet opgeslagen: %s - %s" %(identificatie, str(foutmelding), sql))
        self.connection.commit()

    def execute(self, sql):
        try:
            self.cursor.execute(sql)
            self.connection.commit()
            return self.cursor.rowcount
        except (psycopg2.Error,), foutmelding:
            log("*** FOUT *** Kan SQL-statement '%s' niet uitvoeren:\n %s" %(sql, foutmelding))
            return False

    def select(self, sql):
        try:
            self.cursor.execute(sql)
            rows = self.cursor.fetchall()
            self.connection.commit()
            return rows
        except (psycopg2.Error,), foutmelding:
            log("*** FOUT *** Kan SQL-statement '%s' niet uitvoeren:\n %s" %(sql, foutmelding))
            return []
    
    def controleerOfMaakLog(self):
        try:
            self.cursor.execute("SELECT * FROM BAGextractpluslog")
        except:
            sql  = "CREATE TABLE BAGextractpluslog"
            sql += "(datum   DATE"
            sql += ",actie   VARCHAR(1000)"
            sql += ",bestand VARCHAR(1000)"
            sql += ",logfile VARCHAR(1000))"
            self.maakTabel("BAGextractpluslog", sql)
            
    def log(self, actie, bestand, logfile):
        self.controleerOfMaakLog()
        sql  = "INSERT INTO BAGextractpluslog (datum, actie, bestand, logfile)"
        sql += " VALUES ('now', '%s', '%s', '%s')" %(actie, self.string(bestand), self.string(logfile))
        self.execute(sql)
        
    def getLog(self):
        self.controleerOfMaakLog()
        self.cursor.execute("SELECT * FROM BAGextractpluslog ORDER BY datum, logfile")
        rows = self.cursor.fetchall()
        self.connection.commit()
        return rows

    def controleerTabel(self, tabel):
        self.cursor.execute("SELECT tablename FROM pg_tables WHERE tablename = '%s'" %tabel)
        rows = self.cursor.fetchall()
        self.connection.commit()
        if len(rows) == 0:
            return False
        return True
        
# Globale variabele
database = Database()
