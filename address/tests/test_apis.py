from django.test import TestCase
from address.models import Country, State, City


class AddressModelTests(TestCase):

    def setUp(self):
        self.country = Country.objects.create(label="Azerbaijan")
        self.state = State.objects.create(
            label="Baku",
            country=self.country
        )
        self.city = City.objects.create(
            label="Kesla",
            state=self.state
        )

    def test_country_soft_delete(self):
        self.country.delete()

        self.assertTrue(Country.all_objects.get(id=self.country.id)._is_deleted)
        self.assertIsNotNone(Country.all_objects.get(id=self.country.id)._deleted_at)

    def test_country_restore(self):
        self.country.delete()
        self.country.restore()

        obj = Country.objects.get(id=self.country.id)
        self.assertFalse(obj._is_deleted)

    def test_state_relation(self):
        self.assertEqual(self.state.country, self.country)

    def test_city_relation(self):
        self.assertEqual(self.city.state, self.state)

    def test_soft_delete_queryset_filtering(self):
        self.country.delete()

        self.assertEqual(Country.objects.count(), 0)
        self.assertEqual(Country.all_objects.count() >= 1, True)