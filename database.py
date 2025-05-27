import sqlite3

class Database:
    def __init__(self, db_path):
        self.db_path = db_path
        self.init_db()

    def connect(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        """Maak alle benodigde tabellen aan als ze nog niet bestaan."""
        conn = self.connect()
        cur = conn.cursor()

        # Maak tabellen aan
        cur.execute("""
        CREATE TABLE IF NOT EXISTS boek (
            id INTEGER PRIMARY KEY,
            titel TEXT NOT NULL,
            jaar_van_uitgave INTEGER,
            plaats_van_uitgave TEXT,
            uitgever TEXT,
            aantal_paginas INTEGER,
            originele_taal TEXT,
            samenvatting TEXT
        )
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS auteur (
            id INTEGER PRIMARY KEY,
            voornaam TEXT,
            achternaam TEXT,
            leeftijd INTEGER,
            nationaliteit TEXT,
            geboortedatum DATE,
            geslacht TEXT
        )
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS genre (
            id INTEGER PRIMARY KEY,
            naam TEXT,
            beschrijving TEXT
        )
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS review (
            id INTEGER PRIMARY KEY,
            boek_id INTEGER,
            reviewtekst TEXT,
            datum_review DATE DEFAULT (DATE('now')),
            beoordeling INTEGER,
            leesdatum DATE,
            aantal_keren_gelezen INTEGER,
            FOREIGN KEY (boek_id) REFERENCES boek(id) ON DELETE CASCADE
        )
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS boek_auteur (
            boek_id INTEGER,
            auteur_id INTEGER,
            PRIMARY KEY (boek_id, auteur_id),
            FOREIGN KEY (boek_id) REFERENCES boek(id) ON DELETE CASCADE,
            FOREIGN KEY (auteur_id) REFERENCES auteur(id) ON DELETE CASCADE
        )
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS boek_genre (
            boek_id INTEGER,
            genre_id INTEGER,
            PRIMARY KEY (boek_id, genre_id),
            FOREIGN KEY (boek_id) REFERENCES boek(id) ON DELETE CASCADE,
            FOREIGN KEY (genre_id) REFERENCES genre(id) ON DELETE CASCADE
        )
        """)

        conn.commit()
        conn.close()

    def add_boek_met_review(self, titel, auteur_voornaam, auteur_achternaam, reviewtekst):
        """Voeg een boek, auteur en review toe en koppel auteur aan boek."""
        conn = self.connect()
        cur = conn.cursor()

        # Voeg boek toe
        cur.execute("INSERT INTO boek (titel) VALUES (?)", (titel,))
        boek_id = cur.lastrowid

        # Voeg auteur toe (zonder check, kan uitgebreid worden)
        cur.execute("INSERT INTO auteur (voornaam, achternaam) VALUES (?, ?)", (auteur_voornaam, auteur_achternaam))
        auteur_id = cur.lastrowid

        # Koppel boek aan auteur
        cur.execute("INSERT INTO boek_auteur (boek_id, auteur_id) VALUES (?, ?)", (boek_id, auteur_id))

        # Voeg review toe (datum wordt automatisch gezet)
        cur.execute("INSERT INTO review (boek_id, reviewtekst) VALUES (?, ?)", (boek_id, reviewtekst))

        conn.commit()
        conn.close()

    def get_boeken_en_reviews(self):
        """Haal alle boeken op met auteurs en reviews."""
        conn = self.connect()
        cur = conn.cursor()

        cur.execute("""
            SELECT boek.id, boek.titel, auteur.voornaam, auteur.achternaam, review.reviewtekst
            FROM boek
            JOIN boek_auteur ON boek.id = boek_auteur.boek_id
            JOIN auteur ON boek_auteur.auteur_id = auteur.id
            LEFT JOIN review ON boek.id = review.boek_id
            ORDER BY boek.titel ASC
        """)
        result = cur.fetchall()
        conn.close()
        return result

    def zoek_en_sorteer(self, zoekterm, sorteer_op):
        """Zoek boeken en auteurs op naam en sorteer resultaten."""
        conn = self.connect()
        cur = conn.cursor()

        zoekterm = f"%{zoekterm.lower()}%"

        sorteer_query = {
            "titel_asc": "ORDER BY boek.titel ASC",
            "titel_desc": "ORDER BY boek.titel DESC",
            "datum_nieuwste": "ORDER BY review.datum_review DESC",
            "datum_oudste": "ORDER BY review.datum_review ASC"
        }.get(sorteer_op, "ORDER BY boek.titel ASC")

        query = f"""
            SELECT boek.id, boek.titel, auteur.voornaam, auteur.achternaam, review.reviewtekst
            FROM boek
            JOIN boek_auteur ON boek.id = boek_auteur.boek_id
            JOIN auteur ON boek_auteur.auteur_id = auteur.id
            LEFT JOIN review ON boek.id = review.boek_id
            WHERE LOWER(boek.titel) LIKE ? OR LOWER(auteur.voornaam) LIKE ? OR LOWER(auteur.achternaam) LIKE ?
            {sorteer_query}
        """

        cur.execute(query, (zoekterm, zoekterm, zoekterm))
        result = cur.fetchall()
        conn.close()
        return result

    def delete_boek(self, boek_id):
        """Verwijder een boek en alle gekoppelde records op basis van boek_id."""
        conn = self.connect()
        cur = conn.cursor()

        # Verwijder gekoppelde data
        cur.execute("DELETE FROM boek_genre WHERE boek_id = ?", (boek_id,))
        cur.execute("DELETE FROM boek_auteur WHERE boek_id = ?", (boek_id,))
        cur.execute("DELETE FROM review WHERE boek_id = ?", (boek_id,))
        # Verwijder het boek zelf
        cur.execute("DELETE FROM boek WHERE id = ?", (boek_id,))

        conn.commit()
        conn.close()

    def update_boek(self, boek_id, nieuwe_titel, nieuwe_voornaam, nieuwe_achternaam, nieuwe_review):
        conn = self.connect()
        cur = conn.cursor()

        # Update boek titel
        cur.execute("UPDATE boek SET titel = ? WHERE id = ?", (nieuwe_titel, boek_id))

        # Update auteur
        cur.execute("""
            UPDATE auteur
            SET voornaam = ?, achternaam = ?
            WHERE id = (SELECT auteur_id FROM boek_auteur WHERE boek_id = ?)
        """, (nieuwe_voornaam, nieuwe_achternaam, boek_id))

        # Update review
        cur.execute("UPDATE review SET reviewtekst = ? WHERE boek_id = ?", (nieuwe_review, boek_id))

        conn.commit()
        conn.close()


    def get_boek(self, boek_id):
        conn = self.connect()
        cur = conn.cursor()
        cur.execute("""
            SELECT boek.id, boek.titel, auteur.voornaam, auteur.achternaam, review.reviewtekst
            FROM boek
            JOIN boek_auteur ON boek.id = boek_auteur.boek_id
            JOIN auteur ON auteur.id = boek_auteur.auteur_id
            LEFT JOIN review ON boek.id = review.boek_id
            WHERE boek.id = ?
        """, (boek_id,))
        boek = cur.fetchone()
        conn.close()
        return boek

    def update_review(self, boek_id, nieuwe_review):
        conn = self.connect()
        cur = conn.cursor()
        cur.execute("UPDATE review SET reviewtekst = ? WHERE boek_id = ?", (nieuwe_review, boek_id))
        conn.commit()
        conn.close()