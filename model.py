import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

pd.set_option('display.max_columns', None)
data = pd.read_csv("internship.csv")
print(data)
skills = data["Skills"]
print(skills)
vectorizer = TfidfVectorizer()
skill_matrix = vectorizer.fit_transform(skills)
print(skill_matrix)
similarity = cosine_similarity(skill_matrix)
print(similarity)
student_skills = input("Enter your skills: ")
all_skills = skills.tolist()
all_skills.append(student_skills)
print(all_skills)
all_vectors = vectorizer.fit_transform(all_skills)
student_vector = all_vectors[-1]
internship_vectors = all_vectors[:-1]
scores = cosine_similarity(student_vector, internship_vectors)
print(scores)
best_match_index = scores.argmax()
recommended = data.iloc[best_match_index]
print("\n🎯 Best Internship Recommendation")
print("Internship :", recommended["Internship_Title"])
print("Company    :", recommended["Company"])
print("Location   :", recommended["Location"])
print("Stipend    :", recommended["Stipend"])
print("Duration   :", recommended["Duration"])