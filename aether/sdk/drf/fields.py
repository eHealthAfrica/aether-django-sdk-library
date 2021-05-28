from django.db.models import JSONField


class AetherJSONField(JSONField):
    '''
    Avoids ``TypeError: the JSON object must be str, bytes or bytearray, not dict``

    See:
        - https://stackoverflow.com/questions/65721477/
            django-3-1-jsonfield-attempts-to-deserialized-dict

        - https://code.djangoproject.com/ticket/32135
    '''

    def from_db_value(self, value, expression, connection):
        try:
            return super(AetherJSONField, self).from_db_value(value, expression, connection)

        except Exception as e:
            if 'the JSON object must be str, bytes or bytearray, not dict' in str(e):
                return value
            raise e
