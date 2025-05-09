import os
import sqlite3

from flask import Flask, flash, g, redirect, render_template, request, session, url_for

app = Flask(__name__)
app.config["DATABASE"] = "auta.db"
app.config["SECRET_KEY"] = "tajny-klic"  # bude potřeba pro sessions

# ====== Funkce pro práci s databází ======


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(error):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS auta (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nazev TEXT NOT NULL,
            popis TEXT NOT NULL,
            datum_uvedeni TEXT NOT NULL,
            cena REAL,
            barva TEXT
        )
    """)
    db.commit()


# ====== ROUTES ======


@app.route("/auta")
def index():
    db = get_db()
    auta = db.execute("SELECT * FROM auta").fetchall()
    posledni_auto = session.get("posledni_auto")
    return render_template("index.html", auta=auta, posledni_auto=posledni_auto)


@app.route("/create", methods=["GET", "POST"])
def create():
    if request.method == "POST":
        nazev = request.form.get("nazev", "").strip()
        popis = request.form.get("popis", "").strip()
        datum = request.form.get("datum", "").strip()
        cena = request.form.get("cena", "").strip()
        barva = request.form.get("barva", "").strip()

        errors = []

        if not nazev or len(nazev) > 30:
            errors.append("Název je povinný a max. 30 znaků.")
        if not popis or len(popis) > 500:
            errors.append("Popis je povinný a max. 500 znaků.")
        if not datum:
            errors.append("Datum je povinné.")
        if cena and not cena.replace(".", "", 1).isdigit():
            errors.append("Cena musí být číslo.")
        if barva and not barva.startswith("#"):
            errors.append("Barva musí být v hex formátu (např. #ff0000).")

        if errors:
            for err in errors:
                flash(err)
            return render_template("create.html")

        db = get_db()
        db.execute(
            "INSERT INTO auta (nazev, popis, datum_uvedeni, cena, barva) VALUES (?, ?, ?, ?, ?)",
            (nazev, popis, datum, cena or None, barva or None),
        )
        db.commit()

        # Uložení do session
        session["posledni_auto"] = nazev

        flash("Auto bylo úspěšně přidáno.")
        return redirect(url_for("index"))

    return render_template("create.html")


@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    db = get_db()
    auto = db.execute("SELECT * FROM auta WHERE id = ?", (id,)).fetchone()
    if auto is None:
        return "Auto nenalezeno", 404

    if request.method == "POST":
        nazev = request.form.get("nazev", "").strip()
        popis = request.form.get("popis", "").strip()
        datum = request.form.get("datum", "").strip()
        cena = request.form.get("cena", "").strip()
        barva = request.form.get("barva", "").strip()

        errors = []

        if not nazev or len(nazev) > 30:
            errors.append("Název je povinný a max. 30 znaků.")
        if not popis or len(popis) > 500:
            errors.append("Popis je povinný a max. 500 znaků.")
        if not datum:
            errors.append("Datum je povinné.")
        if cena and not cena.replace(".", "", 1).isdigit():
            errors.append("Cena musí být číslo.")
        if barva and not barva.startswith("#"):
            errors.append("Barva musí být v hex formátu.")

        if errors:
            for err in errors:
                flash(err)
            return render_template("edit.html", auto=auto)

        db.execute(
            "UPDATE auta SET nazev = ?, popis = ?, datum_uvedeni = ?, cena = ?, barva = ? WHERE id = ?",
            (nazev, popis, datum, cena or None, barva or None, id),
        )
        db.commit()
        flash("Auto bylo aktualizováno.")
        return redirect(url_for("index"))

    return render_template("edit.html", auto=auto)


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/delete/<int:id>")
def delete(id):
    db = get_db()
    auto = db.execute("SELECT * FROM auta WHERE id = ?", (id,)).fetchone()
    if auto is None:
        flash("Auto nebylo nalezeno.")
        return redirect(url_for("index"))

    db.execute("DELETE FROM auta WHERE id = ?", (id,))
    db.commit()
    flash("Auto bylo smazáno.")
    return redirect(url_for("index"))


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


# ====== Spuštění ======

if __name__ == "__main__":
    if not os.path.exists("auta.db"):
        with app.app_context():
            init_db()
            print("Databáze byla vytvořena.")
    app.run(debug=True)
