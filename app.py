from flask import Flask, render_template, request, redirect, make_response
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

linking_table = db.Table("linking_table",
                         db.Column("post_id", db.Integer, db.ForeignKey("post.id")),
                         db.Column("tag_id", db.Integer, db.ForeignKey("tag.id"))
                        )

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    desc = db.Column(db.String(500), nullable=False)
    tags = db.relationship("Tag", secondary=linking_table, backref="Posts")

    def __repr__(self) -> str:
        return f"{self.id} - {self.title}"

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    value = db.Column(db.Integer, nullable=True)

    def __repr__(self) -> str:
        return f"{self.id} - {self.name}"

def getRaterTags(post: Post) -> list:
    raterTags = []
    for tag in post.tags:
        if tag.value != None:
            raterTags.append(tag)
    return raterTags

def getMaxRating(post: Post) -> Tag:
    ratings = []
    raterTags = getRaterTags(post)
    if len(raterTags) % 2 == 0:
        midIndex = int(len(raterTags)/2) - 1
    else:
        midIndex = int((len(raterTags) + 1)/2) - 1
    for i in range(len(raterTags)):
        if i != midIndex:
            weight = abs(midIndex - i) * raterTags[i].value
        else:
            weight = raterTags[i].value
        for j in range(weight):
            ratings.append(raterTags[i])
    if len(ratings) == 0: return raterTags[midIndex]
    return(ratings[int(len(ratings)/2)])

@app.route("/")
def about():
    return render_template("about.html")

@app.route("/post", methods=["GET", "POST"])
def post():
    if request.method== "POST":
        blankPostError = False
        title = request.form["title"]
        desc = request.form["desc"]
        tags = request.form["tags"].split()
        # raterTags = request.form["raterTags"].split()
        raterTags = ["easy", "medium", "hard"]
        post = Post(title=title, desc=desc)
        if title == "" or desc == "" or tags == "" or raterTags == "":
            blankPostError = True
        else:
            for tag_name in tags + raterTags:
                if tag_name in raterTags:
                    tag = Tag(name=tag_name, value=0)
                else:
                    tag = Tag.query.filter_by(name=tag_name).first()
                    if tag is None:
                        tag = Tag(name=tag_name, value=None)

                post.tags.append(tag)
                db.session.add(tag)

            db.session.add(post)
            db.session.commit()
        return render_template("post.html", blankPostError=blankPostError)

    return render_template("post.html")

@app.route("/discover", methods=["GET", "POST"])
def discover():
    posts = Post.query.all()
    if request.method == "POST":
        tags = request.form["tags"].split()
        for tag_name in tags:
            tag = Tag.query.filter_by(name=tag_name).first()
            if tag == None:
                return render_template("discover.html", posts=[])
            search_results = tag.Posts
            posts = list(set(search_results).intersection(posts))
        
        if request.form["raterTag"] != "":
            i = 0
            while i < len(posts):
                if request.form["raterTag"] != getMaxRating(posts[i]).name:
                    posts.pop(i)
                    i -= 1
                i += 1
        try:
            ratedPostsIds = eval(request.cookies.get("ratedPostsIds"))
        except:
            ratedPostsIds = None

        if request.form.get("ratedRadioBtn") == "unratedRadio":
            if ratedPostsIds is not None:
                i = 0
                while i < len(posts):
                    if posts[i].id in ratedPostsIds:
                        posts.pop(i)
                        i -= 1
                    i += 1
        elif request.form.get("ratedRadioBtn") == "ratedRadio":
            if ratedPostsIds == None:
                posts = []
            else:
                i = 0
                while i < len(posts):
                    if posts[i].id not in ratedPostsIds:
                        posts.pop(i)
                        i -= 1
                    i += 1
    return render_template("discover.html", posts=posts, getMaxRating=getMaxRating)

@app.route("/discover/<int:id>", methods=["GET", "POST"])
def postDesc(id):
    post = Post.query.filter_by(id=id).first()
    totalRatings = 0
    raterTags = getRaterTags(post)
    for tag in raterTags:
        totalRatings += tag.value
    totalVal = totalRatings
    if totalVal == 0: totalVal += 1
    if request.method == "POST":
        for raterTag in raterTags:
            if request.form.get("ratingOptions") == str(raterTag.id):
                try:
                    ratedPostsIds = eval(request.cookies.get("ratedPostsIds"))
                except:
                    ratedPostsIds = []
                if post.id not in ratedPostsIds:
                    raterTag.value += 1
                    db.session.commit()
                    resp = make_response(redirect(f"/discover/{post.id}"))
                    ratedPostsIds.append(post.id)
                    resp.set_cookie("ratedPostsIds", str(ratedPostsIds))
                    return resp
                return redirect(f"/discover/{post.id}")
    return render_template("postDescription.html", post=post, raterTags=raterTags, totalVal=totalVal)

if __name__ == "__main__":
    app.run(debug=True)
