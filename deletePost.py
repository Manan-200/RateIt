from app import app, db, Post
with app.app_context():
    Post.query.filter_by(id=6).delete()
    db.session.commit()