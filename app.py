from flask import Flask, render_template, request, session, redirect
import os
import sqlite3
import pandas as pd
import pdfplumber
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)

app.secret_key = "internship_project_secret"

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Load dataset
data = pd.read_csv("internship.csv", index_col=False)

# TF-IDF Vectorizer
vectorizer = TfidfVectorizer()
def extract_skills(pdf_path):

    skills_list = [
        "Python",
        "Java",
        "SQL",
        "HTML",
        "CSS",
        "JavaScript",
        "Flask",
        "Machine Learning",
        "Deep Learning",
        "TensorFlow",
        "Pandas",
        "NumPy",
        "Power BI",
        "Excel",
        "C",
        "C++"
    ]

    extracted_skills = []

    with pdfplumber.open(pdf_path) as pdf:

        text = ""

        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text

    text = text.lower()

    for skill in skills_list:
        if skill.lower() in text:
            extracted_skills.append(skill)

    return ", ".join(extracted_skills)


@app.route("/")
def home():

    if "username" in session:
        return render_template("index.html", username=session["username"])

    return render_template("login.html")


@app.route("/recommend", methods=["POST"])
def recommend():

    # User Inputs
    student_skills = request.form["skills"]
    selected_state = request.form["state"]
    selected_district = request.form["district"]
    resume = request.files["resume"]

    if resume.filename != "":
      filepath = os.path.join(app.config["UPLOAD_FOLDER"], resume.filename)
      resume.save(filepath)
      student_skills = extract_skills(filepath)

    # Filter by State
    filtered_data = data[data["State"] == selected_state]

    # Filter by District
    district_data = filtered_data[
        filtered_data["District"] == selected_district
    ]

    # If district has companies, use district data
    if not district_data.empty:
        filtered_data = district_data

    # If state has no companies, use all companies
    if filtered_data.empty:
        filtered_data = data

    # Prepare skills
    skills = filtered_data["Skills"]

    all_skills = skills.tolist()
    all_skills.append(student_skills)

    # TF-IDF
    all_vectors = vectorizer.fit_transform(all_skills)

    student_vector = all_vectors[-1]
    internship_vectors = all_vectors[:-1]

    # Similarity
    scores = cosine_similarity(student_vector, internship_vectors)
    scores_list = scores[0]

    # Best Match
    best_match = scores_list.argmax()

    recommendation = filtered_data.iloc[best_match]

    match_percentage = round(scores_list[best_match] * 100, 2)

    # Top 3 Matches
    top_matches = scores_list.argsort()[-3:][::-1]

    top_recommendations = []

    for index in top_matches:

        internship = filtered_data.iloc[index]

        top_recommendations.append({
            "title": internship["Internship_Title"],
            "company": internship["Company"],
            "logo": internship["Logo"],
            "location": internship["Location"],
            "stipend": internship["Stipend"],
            "duration": internship["Duration"],
            "type": internship["Internship_Type"],
            "rating": internship["Rating"],
            "percentage": round(scores_list[index] * 100, 2),
            "map_link": internship["Map_Link"],
            "apply_link": internship["Apply_Link"]
        })

    return render_template(
        "result.html",
        internship=recommendation["Internship_Title"],
        company=recommendation["Company"],
        logo=recommendation["Logo"],
        location=recommendation["Location"],
        stipend=recommendation["Stipend"],
        duration=recommendation["Duration"],
        internship_type=recommendation["Internship_Type"],
        rating=recommendation["Rating"],
        match=match_percentage,
        map_link=recommendation["Map_Link"],
        apply_link=recommendation["Apply_Link"],
        extracted_skills=student_skills,
        top_recommendations=top_recommendations
    )
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("students.db")
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO users(name, email, password) VALUES (?, ?, ?)",
            (name, email, password)
        )

        conn.commit()
        conn.close()

        return "Registration Successful!"

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("students.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE email=? AND password=?",
            (email, password)
        )

        user = cursor.fetchone()

        conn.close()

        if user:
            session["username"] = user[1]
            session["email"] = user[2]
            return redirect("/")
        else:
            return "Invalid Email or Password"

    return render_template("login.html")

@app.route("/save", methods=["POST"])
def save():

    company = request.form["company"]
    internship = request.form["internship"]
    location = request.form["location"]
    stipend = request.form["stipend"]

    student_email = session.get("email")

    if not student_email:
      return redirect("/login")
    conn = sqlite3.connect("students.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO favourites
        (student_email, company, internship, location, stipend)
        VALUES (?, ?, ?, ?, ?)
        """,
        (student_email, company, internship, location, stipend)
    )

    conn.commit()
    conn.close()

    return "Internship Saved Successfully ❤️"

@app.route("/favourites")
def favourites():

    if "email" not in session:
        return render_template("login.html")

    conn = sqlite3.connect("students.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM favourites WHERE student_email=?",
        (session["email"],)
    )

    data = cursor.fetchall()

    conn.close()

    return render_template(
        "favourites.html",
        favourites=data
    )

@app.route("/admin")
def admin():
    return render_template("admin_login.html")


@app.route("/admin_login", methods=["POST"])
def admin_login():

    email = request.form["email"]
    password = request.form["password"]

    if email == "admin@gmail.com" and password == "admin123":
        return render_template("admin_dashboard.html")

    return "Invalid Admin Login"

@app.route("/add_internship", methods=["GET", "POST"])
def add_internship():

    if request.method == "POST":

        new_data = {
            "Internship_Title": request.form["title"],
            "Company": request.form["company"],
            "State": request.form["state"],
            "District": request.form["district"],
            "Skills": request.form["skills"],
            "Location": request.form["location"],
            "Stipend": request.form["stipend"],
            "Duration": request.form["duration"],
            "Internship_Type": request.form["internship_type"],
            "Rating": request.form["rating"],
            "Logo": request.form["logo"],
            "Map_Link": request.form["map_link"],
            "Apply_Link": request.form["apply_link"]
        }

        global data

        data.loc[len(data)] = new_data

        data.to_csv("internship.csv", index=False)

        return "✅ Internship Added Successfully"

    return render_template("add_internship.html")

@app.route("/view_internships")
def view_internships():

    global data

    internships = data.to_dict(orient="records")

    return render_template(
        "view_internships.html",
        internships=internships
    )

@app.route("/delete/<int:index>")
def delete(index):

    global data

    data = data.drop(index).reset_index(drop=True)

    data.to_csv("internship.csv", index=False)

    return redirect("/view_internships")

@app.route("/edit/<int:index>", methods=["GET", "POST"])
def edit(index):

    global data

    if request.method == "POST":

        data.loc[index, "Internship_Title"] = request.form["title"]
        data.loc[index, "Company"] = request.form["company"]
        data.loc[index, "State"] = request.form["state"]
        data.loc[index, "District"] = request.form["district"]
        data.loc[index, "Skills"] = request.form["skills"]
        data.loc[index, "Location"] = request.form["location"]
        data.loc[index, "Stipend"] = request.form["stipend"]
        data.loc[index, "Duration"] = request.form["duration"]
        data.loc[index, "Internship_Type"] = request.form["internship_type"]
        data.loc[index, "Rating"] = request.form["rating"]
        data.loc[index, "Map_Link"] = request.form["map_link"]
        data.loc[index, "Apply_Link"] = request.form["apply_link"]

        data.to_csv("internship.csv", index=False)

        return redirect("/view_internships")

    internship = data.iloc[index]

    return render_template(
        "edit_internship.html",
        internship=internship,
        index=index
    )
    
if __name__ == "__main__":
    app.run(debug=True)