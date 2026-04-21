from flask import Blueprint, render_template

main_bp = Blueprint("main", __name__)
@main_bp.route("/")
def dashboard():
    tools = [
        {
            "id": "merge",
            "title": "Merge PDFs",
            "description": "Combine multiple PDF files into a single document.",
            "icon": "merge",
            "url": "/merge",
            "accent": "blue",
        },
        {
            "id": "split",
            "title": "Split PDF",
            "description": "Extract specific page ranges into separate files.",
            "icon": "split",
            "url": "/split",
            "accent": "blue",
        },
        {
            "id": "summarize",
            "title": "AI Summarize",
            "description": "Get page-by-page AI summaries using local NLP.",
            "icon": "summarize",
            "url": "/summarize",
            "accent": "blue",
        },
        {
            "id": "convert",
            "title": "PDF → DOCX",
            "description": "Convert PDF documents to editable Word files.",
            "icon": "convert",
            "url": "/convert",
            "accent": "blue",
        },
    ]
    student_tools = [
        {
            "id": "quiz",
            "title": "Flashcards & Quiz",
            "description": "Generate flashcards and quizzes automatically from your PDFs.",
            "icon": "brain-circuit",
            "url": "/quiz",
            "accent": "green",
        },
    ]
    return render_template("dashboard/index.html", tools=tools, student_tools=student_tools)
