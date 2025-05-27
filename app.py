from flask import Flask, render_template, request, redirect, url_for
from database import Database

app = Flask(__name__)
db = Database("gelezen_boeken.db")

@app.route("/", methods=["GET", "POST"])
def main():
    zoekterm = ""
    sorteer_op = "titel_asc"

    if request.method == "POST":
        actie = request.form.get("actie")
        boek_id = request.form.get("boek_id")

        if actie == "verwijder":
            db.delete_boek(int(boek_id))
            return redirect(url_for("main"))

        elif actie == "update":
            return redirect(url_for("update_boek", boek_id=boek_id))

        elif "zoekterm" in request.form or "sorteer" in request.form:
            zoekterm = request.form.get("zoekterm", "")
            sorteer_op = request.form.get("sorteer", "titel_asc")
            boeken = db.zoek_en_sorteer(zoekterm, sorteer_op)
            return render_template("index.html", boeken=boeken, zoekterm=zoekterm, sorteer_op=sorteer_op)

        else:
            titel = request.form["titel"]
            voornaam = request.form["voornaam"]
            achternaam = request.form["achternaam"]
            review = request.form["review"]
            db.add_boek_met_review(titel, voornaam, achternaam, review)
            return redirect(url_for("main"))

    boeken = db.get_boeken_en_reviews()
    return render_template("index.html", boeken=boeken, zoekterm=zoekterm, sorteer_op=sorteer_op)



@app.route("/update/<int:boek_id>", methods=["GET", "POST"])
def update_boek(boek_id):
    boek = db.get_boek(boek_id)

    if request.method == "POST":
        nieuwe_titel = request.form["titel"]
        nieuwe_voornaam = request.form["voornaam"]
        nieuwe_achternaam = request.form["achternaam"]
        nieuwe_review = request.form["review"]

        db.update_boek(boek_id, nieuwe_titel, nieuwe_voornaam, nieuwe_achternaam, nieuwe_review)
        return redirect(url_for("main"))
    
    

    return render_template("update.html", boek=boek)


if __name__ == "__main__":
    app.run(debug=True)