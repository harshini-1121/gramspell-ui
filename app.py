from flask import Flask, render_template, request
from gramspell import correct_text_for_web
import docx

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    corrected_text = ""
    user_text = ""
    spell_issues = []
    grammar_issues = []

    if request.method == "POST":
        action = request.form.get("action")

        # Text input
        if action == "check":
            user_text = request.form.get("text", "")
            if user_text.strip():
                result = correct_text_for_web(user_text, auto_spell=True, auto_grammar=True)
                corrected_text = result['corrected']
                spell_issues = result['spell_issues']
                grammar_issues = result['grammar_issues']

        # Word file upload
        elif action == "upload":
            file = request.files.get("file")
            if file and file.filename.endswith(".docx"):
                doc = docx.Document(file)
                text = "\n".join([para.text for para in doc.paragraphs])
                user_text = text
                if text.strip():
                    result = correct_text_for_web(text, auto_spell=True, auto_grammar=True)
                    corrected_text = result['corrected']
                    spell_issues = result['spell_issues']
                    grammar_issues = result['grammar_issues']

    return render_template(
        "index.html",
        original=user_text,
        corrected=corrected_text,
        spell_issues=spell_issues,
        grammar_issues=grammar_issues
    )


if __name__ == "__main__":
    app.run(debug=True)