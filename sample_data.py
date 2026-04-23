from datetime import date
from models import User, Plan

def get_sample_plans() -> list[Plan]:
    day = date(2024, 8, 15)

    alice = User(name="Alice")
    bob   = User(name="Bob")
    cara  = User(name="Cara")
    dave  = User(name="Dave")
    elena = User(name="Elena")
    felix = User(name="Felix")
    grace = User(name="Grace")
    harry = User(name="Harry")
    isla  = User(name="Isla")
    jay   = User(name="Jay")

    #                                                                    max_group
    return [
        Plan(alice.id, "Alice", "bay area", day, "morning",   ["hiking", "coffee", "yoga"],          "active",       4),
        Plan(bob.id,   "Bob",   "bay area", day, "morning",   ["coffee", "bookstore"],               "chill",        2),
        Plan(cara.id,  "Cara",  "bay area", day, "afternoon", ["brunch", "coffee", "museums"],       "social",       5),
        Plan(dave.id,  "Dave",  "bay area", day, "morning",   ["hiking", "farmer's market"],         "active",       3),
        Plan(elena.id, "Elena", "bay area", day, "evening",   ["wine bar", "live music"],            "chill",        4),
        Plan(felix.id, "Felix", "bay area", day, "afternoon", ["climbing", "hiking"],                "adventurous",  3),
        Plan(grace.id, "Grace", "bay area", day, "morning",   ["yoga", "coffee", "walk"],            "chill",        4),
        Plan(harry.id, "Harry", "bay area", day, "afternoon", ["cycling", "picnic", "coffee"],       "active",       4),
        Plan(isla.id,  "Isla",  "bay area", day, "evening",   ["live music", "wine bar"],            "social",       6),
        Plan(jay.id,   "Jay",   "bay area", day, "morning",   ["hiking", "coffee", "picnic"],        "social",       4),
    ]
