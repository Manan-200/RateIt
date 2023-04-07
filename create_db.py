from app import app, db, Post, Tag
with app.app_context():
    db.create_all()