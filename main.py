from app import app, db
from app.models import User, ForumCategory, ForumTopic, ForumPost, RulesSection, Rule

@app.shell_context_processor
def make_shell_context():
    """Stellt Kontext für die Flask-Shell bereit."""
    return {'db': db, 'User': User, 'ForumCategory': ForumCategory, 
            'ForumTopic': ForumTopic, 'ForumPost': ForumPost,
            'RulesSection': RulesSection, 'Rule': Rule}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)