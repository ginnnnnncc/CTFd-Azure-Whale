from __future__ import division  # Use floating point for math calculations
import math
from datetime import datetime

from flask import Blueprint

from CTFd.models import db, Challenges, Flags
from CTFd.plugins.flags import FlagException, get_flag_class
from CTFd.plugins.challenges import BaseChallenge
from CTFd.utils import user as current_user
from .decay import DECAY_FUNCTIONS, logarithmic


class DynamicDockerChallenge(Challenges):
    __mapper_args__ = {"polymorphic_identity": "dynamic_docker"}
    id = db.Column(None, db.ForeignKey("challenges.id"), primary_key=True)

    dynamic_score = db.Column(db.Integer, default=0)
    function = db.Column(db.String(32), default="logarithmic")
    initial = db.Column(db.Integer, default=None)
    minimum = db.Column(db.Integer, default=None)
    decay = db.Column(db.Integer, default=None)

    yaml = db.Column(db.Text, nullable=False)
    container_name = db.Column(db.String(32), nullable=False)
    port = db.Column(db.Integer, nullable=False, default=80)
    flag = db.Column(db.String(128), nullable=False)
    cpu = db.Column(db.Float, nullable=False)
    
    def __init__(self, *args, **kwargs):
        if kwargs.get('initial', None) == '':
            kwargs["initial"] = None
        if kwargs.get('minimum', None) == '':
            kwargs["minimum"] = None
        if kwargs.get('decay', None) == '':
            kwargs["decay"] = None
        if kwargs.get('value', None) == '':
            kwargs["value"] = None
        super(DynamicDockerChallenge, self).__init__(**kwargs)


class DynamicValueDockerChallenge(BaseChallenge):
    id = "dynamic_docker"  # Unique identifier used to register challenges
    name = "dynamic_docker"  # Name of a challenge type
    templates = {  # Handlebars templates used for each aspect of challenge editing & viewing
        "create": "/plugins/ctfd-whale/assets/create.html",
        "update": "/plugins/ctfd-whale/assets/update.html",
        "view": "/plugins/ctfd-whale/assets/view.html",
    }
    scripts = {  # Scripts that are loaded when a template is loaded
        "create": "/plugins/ctfd-whale/assets/create.js",
        "update": "/plugins/ctfd-whale/assets/update.js",
        "view": "/plugins/ctfd-whale/assets/view.js",
    }
    # Route at which files are accessible. This must be registered using register_plugin_assets_directory()
    route = "/plugins/ctfd-whale/assets/"
    # Blueprint used to access the static_folder directory.
    blueprint = Blueprint(
        "ctfd-whale-challenge",
        __name__,
        template_folder="templates",
        static_folder="assets",
    )
    challenge_model = DynamicDockerChallenge

    @classmethod
    def calculate_value(cls, challenge):
        if challenge.dynamic_score == 1:
            f = DECAY_FUNCTIONS.get(challenge.function, logarithmic)
            value = f(challenge)
            challenge.value = value
        
        db.session.commit()
        return challenge

    @classmethod
    def read(cls, challenge):
        """
        This method is in used to access the data of a challenge in a format processable by the front end.

        :param challenge:
        :return: Challenge object, data dictionary to be returned to the user
        """
        challenge = DynamicDockerChallenge.query.filter_by(id=challenge.id).first()
        data = {
            "id": challenge.id,
            "name": challenge.name,
            "value": challenge.value,
            "initial": challenge.initial,
            "decay": challenge.decay,
            "minimum": challenge.minimum,
            "description": challenge.description,
            "category": challenge.category,
            "state": challenge.state,
            "max_attempts": challenge.max_attempts,
            "type": challenge.type,
            "type_data": {
                "id": DynamicValueDockerChallenge.id,
                "name": DynamicValueDockerChallenge.name,
                "templates": DynamicValueDockerChallenge.templates,
                "scripts": DynamicValueDockerChallenge.scripts,
            },
        }
        return data

    @classmethod
    def update(cls, challenge, request):
        """
        This method is used to update the information associated with a challenge. This should be kept strictly to the
        Challenges table and any child tables.

        :param challenge:
        :param request:
        :return:
        """
        data = request.form or request.get_json()

        for attr, value in data.items():
            # We need to set these to floats so that the next operations don't operate on strings
            if attr in ("initial", "minimum", "decay", "cpu"):
                value = float(value)
            setattr(challenge, attr, value)
            
        return DynamicValueDockerChallenge.calculate_value(challenge)

    @classmethod
    def attempt(cls, challenge, request):
        """
        This method is used to check whether a given input is right or wrong. It does not make any changes and should
        return a boolean for correctness and a string to be shown to the user. It is also in charge of parsing the
        user's input from the request itself.

        :param challenge: The Challenge object from the database
        :param request: The request the user submitted
        :return: (boolean, string)
        """
        data = request.form or request.get_json()
        submission = data["submission"].strip()
        
        user_id = current_user.get_current_user().id
        q = db.session.query(WhaleContainer)
        q = q.filter(WhaleContainer.user_id == user_id)
        q = q.filter(WhaleContainer.challenge_id == challenge.id)
        q = q.filter(WhaleContainer.status == 'Running')
        records = q.all()
        if len(records) == 0:
            return False, "Please solve it during the container is running"

        container = records[0]
        if container.flag == submission:
            return True, "Correct"
        return False, "Incorrect"

    @classmethod
    def solve(cls, user, team, challenge, request):
        super().solve(user, team, challenge, request)

        if challenge.dynamic_score == 1:
            DynamicValueDockerChallenge.calculate_value(challenge)


class WhaleConfig(db.Model):
    key = db.Column(db.String(length=128), primary_key=True)
    value = db.Column(db.Text)

    def __init__(self, key, value):
        self.key = key
        self.value = value

    def __repr__(self):
        return "<WhaleConfig (0) {1}>".format(self.key, self.value)


class WhaleContainer(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(None, db.ForeignKey("users.id"))
    challenge_id = db.Column(None, db.ForeignKey("challenges.id"))
    start_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    renew_count = db.Column(db.Integer, nullable=False, default=0)
    status = db.Column(db.String(32), default="Deploying")
    flag = db.Column(db.String(128), nullable=False)
    ip = db.Column(db.String(32), nullable=True)
    container_name = db.Column(db.String(64), nullable=False)
    resource_group_name = db.Column(db.String(64), nullable=False)
    visible = db.Column(db.Boolean, default=True)
    cpu = db.Column(db.Float, nullable=False)
    

    # Relationships
    user = db.relationship("Users", foreign_keys="WhaleContainer.user_id", lazy="select")
    challenge = db.relationship(
        "Challenges", foreign_keys="WhaleContainer.challenge_id", lazy="select"
    )

    def __init__(self, user_id, challenge_id, flag, container_name, resource_group_name, cpu):
        self.user_id = user_id
        self.challenge_id = challenge_id
        self.start_time = datetime.now()
        self.renew_count = 0
        self.flag = flag
        self.container_name = container_name
        self.resource_group_name = resource_group_name
        self.cpu = cpu

    def __repr__(self):
        return "<WhaleContainer ID:(0) {1} {2} {3} {4}>".format(self.id, self.user_id, self.challenge_id,
                                                                self.start_time, self.renew_count)


class ResourceGroup(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(64), nullable=False)
    region = db.Column(db.String(64), nullable=False)
    priority = db.Column(db.Integer, nullable=False, default=0)
    used = db.Column(db.Float, nullable=False, default=0)
    
    def __init__(self, name, region):
        self.name = name
        self.region = region
        
    def __repr__(self):
        return "<ResourceGroup ID:(0) {1} {2} {3}>".format(self.id, self.name, self.region, self.used)