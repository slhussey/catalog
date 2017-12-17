""" Populate the database with data so that the website has something to display """

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import DATABASE, User, Category, Item

# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DATABASE_SESSION instance
ENGINE = create_engine('sqlite:///catalog.db')
DATABASE.metadata.bind = ENGINE

# A DATABASE_SESSION_FACTORY() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
DATABASE_SESSION_FACTORY = sessionmaker(bind=ENGINE)
DATABASE_SESSION = DATABASE_SESSION_FACTORY()

#Create initial user (me)
USER1 = User(username="Stephen Hussey", picture="", email="stephen.hussey2@gmail.com")

#Populate all the categories
CATEGORY1 = Category(name="Soccer")
DATABASE_SESSION.add(CATEGORY1)

CATEGORY2 = Category(name="Basketball")
DATABASE_SESSION.add(CATEGORY2)

CATEGORY3 = Category(name="Baseball")
DATABASE_SESSION.add(CATEGORY3)

CATEGORY4 = Category(name="Frisbee")
DATABASE_SESSION.add(CATEGORY4)

CATEGORY5 = Category(name="Snowboarding")
DATABASE_SESSION.add(CATEGORY5)

CATEGORY6 = Category(name="Rock Climbing")
DATABASE_SESSION.add(CATEGORY6)

CATEGORY7 = Category(name="Foosball")
DATABASE_SESSION.add(CATEGORY7)

CATEGORY8 = Category(name="Skating")
DATABASE_SESSION.add(CATEGORY8)

CATEGORY9 = Category(name="Hockey")
DATABASE_SESSION.add(CATEGORY9)

DATABASE_SESSION.commit()

ITEM1 = Item(name="Stick", desc="", category=CATEGORY9, user=USER1)
DATABASE_SESSION.add(ITEM1)

ITEM2 = Item(name="Goggles", desc="", category=CATEGORY5, user=USER1)
DATABASE_SESSION.add(ITEM2)

ITEM3 = Item(name="Snowboard", category=CATEGORY5, user=USER1,
             desc="Best for any terrain and conditions. All-mountain snowboards perform " \
                "anywhere on a mountain--groomed runs, backcountry, even park and pipe. They "\
                "may be directional (meaning downhill only) or twin-tip (for riding switch, " \
                "meaning either direction). Most boarders ride all-mountain boards. Because "\
                "of their versatility, all-mountain boards are god for beginners who are still "\
                "learning what terrain they like.")
DATABASE_SESSION.add(ITEM3)

ITEM4 = Item(name="Two Shin Guards", desc="", category=CATEGORY1, user=USER1)
DATABASE_SESSION.add(ITEM4)

ITEM5 = Item(name="Shin Guards", desc="", category=CATEGORY1, user=USER1)
DATABASE_SESSION.add(ITEM5)

ITEM6 = Item(name="Frisbee", desc="", category=CATEGORY4, user=USER1)
DATABASE_SESSION.add(ITEM6)

ITEM7 = Item(name="Bat", desc="", category=CATEGORY3, user=USER1)
DATABASE_SESSION.add(ITEM7)

ITEM8 = Item(name="Jersey", desc="", category=CATEGORY1, user=USER1)
DATABASE_SESSION.add(ITEM8)

ITEM9 = Item(name="Soccer Cleats", desc="", category=CATEGORY1, user=USER1)
DATABASE_SESSION.add(ITEM9)

DATABASE_SESSION.commit()
