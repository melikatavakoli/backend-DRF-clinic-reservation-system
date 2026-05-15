

def pick_serializer_fields(serializer_class, fields):
    class Serializer(serializer_class):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            allowed = set(fields)
            existing = set(self.fields)
            for field in existing - allowed:
                self.fields.pop(field)
    return Serializer
