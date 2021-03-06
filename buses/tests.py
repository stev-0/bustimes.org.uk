"""Tests for the buses app
"""
from django.test import TestCase
from busstops.models import Operator
from . import utils


class UtilsTests(TestCase):
    """Tests for the buses.utils module
    """
    def test_minify(self):
        """Test that the minify function minifies (while preserving some characters) as expected
        """
        self.assertEqual(utils.minify("""
                   \n
            <marquee>
                {% if foo %}\n     \n                    {% if bar %}
                        <strong>Golf sale</strong>  \n
                    {% endif %}
                {% endif %}
            </marquee>
            """), """
<marquee>
{% if foo %}{% if bar %}<strong>Golf sale</strong>  \n{% endif %}{% endif %}</marquee>
""")

    def test_get_identifier(self):
        self.assertEqual(utils.get_identifier('Chutney'), 'Chutney')
        operator = Operator(id='CHUT')
        self.assertEqual(utils.get_identifier(operator),
                         'busstops.operator.CHUT')
