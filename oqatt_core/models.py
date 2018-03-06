from neomodel import ( StructuredNode, StringProperty, IntegerProperty,
    UniqueIdProperty, RelationshipTo, RelationshipFrom,BooleanProperty,
    EmailProperty,ArrayProperty,StructuredRel,DateTimeProperty)
from datetime import datetime


class User(StructuredNode):
    uid = UniqueIdProperty()
    fcm_id = StringProperty()
    token_bal = IntegerProperty()
    name = StringProperty()
    contact = StringProperty(unique_index=True)
    email = EmailProperty()
    knows = RelationshipTo('User', 'knows')
    create_date = DateTimeProperty(default=lambda: datetime.utcnow())
   
class Knows(StructuredRel):
    since = DateTimeProperty(default=lambda: datetime.utcnow())

# class Belongs(StructuredRel):
#     create_date = DateTimeProperty(default=lambda: datetime.utcnow())

# class Maintains(StructuredRel):
#     create_date = DateTimeProperty(default=lambda: datetime.utcnow())

# class Has(StructuredRel):
#     create_date = DateTimeProperty(default=lambda: datetime.utcnow())

# class Bucket(StructuredNode):
#     name = StringProperty()
#     create_date = DateTimeProperty(default=lambda: datetime.utcnow())
#     belongs = RelationshipTo('User', 'belongs')
#     has = RelationshipTo('Tag', 'has')

# class Tag(StructuredNode):
#     name = StringProperty()
#     create_date = DateTimeProperty(default=lambda: datetime.utcnow())
