from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func

db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), nullable=False, unique=True)
    password = db.Column(db.String(128), nullable=False)
    create_at = db.Column(db.DateTime(), nullable=False, server_default=func.now())

    def __repr__(self):
        return "<User %r>" % self.id


class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    user = db.relationship(
        User, lazy=True, backref=db.backref("groups", lazy=True, cascade="all,delete")
    )
    create_at = db.Column(db.DateTime(), nullable=False, server_default=func.now())

    def __repr__(self):
        return "<Group %r>" % self.id


class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(
        db.LargeBinary(length=2**24 - 1), nullable=False
    )  # max size: 16MB
    type = db.Column(db.String(64), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey(Group.id))
    group = db.relationship(
        Group,
        lazy="joined",
        backref=db.backref("images", lazy=True, cascade="all,delete"),
    )
    user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    user = db.relationship(
        User, lazy=True, backref=db.backref("images", lazy=True, cascade="all,delete")
    )
    create_at = db.Column(db.DateTime(), nullable=False, server_default=func.now())

    def readyToJSON(self, keys, datetime_format):
        """
        Params:
            keys [Iterable[str]]
            datetime_format [str]: 同 datetime.strptime() 的格式声明
        """
        d = {}
        for k in keys:
            if k == "create_at":
                v = getattr(self, k).strftime(datetime_format)
            elif k == "group":
                v = self.group.name if self.group else None
            else:
                v = getattr(self, k)
            d[k] = v
        return d

    def __repr__(self):
        return "<Image %r>" % self.id


class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(64), nullable=False)
    # eager join load
    image_id = db.Column(db.Integer, db.ForeignKey(Image.id), nullable=False)
    image = db.relationship(
        Image, backref=db.backref("tags", lazy="joined", cascade="all,delete")
    )
    user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    user = db.relationship(
        User, lazy=True, backref=db.backref("tags", lazy=True, cascade="all,delete")
    )
    create_at = db.Column(db.DateTime(), nullable=False, server_default=func.now())

    def __repr__(self):
        return "<Tag %r>" % self.id


class Passcode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(64), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    user = db.relationship(
        User,
        lazy=True,
        backref=db.backref("passcodes", lazy=True, cascade="all,delete"),
    )
    create_at = db.Column(db.DateTime(), nullable=False, server_default=func.now())

    def __repr__(self):
        return "<Passcode %r>" % self.id


class ResetAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    user = db.relationship(
        User,
        lazy=True,
        backref=db.backref("reset_attempts", lazy=True, cascade="all,delete"),
    )
    create_at = db.Column(db.DateTime(), nullable=False, server_default=func.now())

    def __repr__(self):
        return "<ResetAttempt %r>" % self.id
