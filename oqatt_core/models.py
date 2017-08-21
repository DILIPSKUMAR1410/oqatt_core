from neomodel import ( StructuredNode, StringProperty, IntegerProperty,
    UniqueIdProperty, RelationshipTo, RelationshipFrom,BooleanProperty)

class User(StructuredNode):
    uid = UniqueIdProperty()
    contact = StringProperty(unique_index=True)
    name = StringProperty()
    contact_list = RelationshipTo('User', 'has_contact_of')
    claimed = BooleanProperty(default=False)