# coding=utf-8
import os
import json
import vcr
from django.test import TestCase
from django.core import mail
from django.contrib.gis.geos import Point
from django.shortcuts import render
from .models import Region, AdminArea, District, Locality, StopPoint, StopUsage, Operator, Service, Note


DIR = os.path.dirname(os.path.abspath(__file__))


class ContactTests(TestCase):
    """Tests for the contact form and view"""

    def test_contact_get(self):
        response = self.client.get('/contact')
        self.assertEqual(response.status_code, 200)

    def test_empty_contact_post(self):
        response = self.client.post('/contact')
        self.assertFalse(response.context['form'].is_valid())

    def test_contact_post(self):
        response = self.client.post('/contact', {
            'name': 'Rufus Herring',
            'email': 'rufus@example.com',
            'message': 'Dear John,\r\n\r\nHow are you?\r\n\r\nAll the best,\r\nRufus',
            'referrer': 'https://www.yahoo.com'
        })
        self.assertContains(response, '<h1>Thank you</h1>', html=True)
        self.assertEqual('Dear John,', mail.outbox[0].subject)
        self.assertEqual('"Rufus Herring" <robot@bustimes.org.uk>', mail.outbox[0].from_email)
        self.assertEqual(['rufus@example.com'], mail.outbox[0].reply_to)
        self.assertEqual(['contact@bustimes.org.uk'], mail.outbox[0].to)

    def test_awin_post(self):
        self.client.post('/awin-transaction', {
            'AwinTransactionPush': json.dumps({
                'transactionId': '244231459',
                'transactionDate': '2016-12-06 18:35:28',
                'transactionAmount': '33.7',
                'commission': '0.67',
                'affiliateId': '242611',
                'merchantId': '2678',
                'groupId': '0',
                'bannerId': '0',
                'clickRef': '',
                'clickThroughTime': '2016-12-06 07:15:24',
                'clickTime': '2016-12-06 07:15:24',
                'url': 'https://bustimes.org.uk/services/swe_33-FLC-_-y10',
                'transactionCurrency': 'GBP',
                'commissionGroups': [
                    {
                        'id': '15250',
                        'name': 'Default Commission',
                        'code': 'DEFAULT',
                        'description': ' You will receive 2% commission '
                    }
                ]
            })
        })
        self.assertEqual('💷 67p on a £33.70 transaction', mail.outbox[0].subject)
        self.assertEqual('🚌⏰🤖 <robot@bustimes.org.uk>', mail.outbox[0].from_email)


class ViewsTests(TestCase):
    """Boring tests for various views"""

    @classmethod
    def setUpTestData(cls):
        cls.north = Region.objects.create(pk='N', name='North')
        cls.norfolk = AdminArea.objects.create(
            id=91, atco_code=91, region=cls.north, name='Norfolk'
        )
        cls.north_norfolk = District.objects.create(
            id=91, admin_area=cls.norfolk, name='North Norfolk'
        )
        cls.melton_constable = Locality.objects.create(
            id='E0048689', admin_area=cls.norfolk, name='Melton Constable'
        )
        cls.inactive_stop = StopPoint.objects.create(
            pk='2900M115',
            common_name='Bus Shelter',
            active=False,
            admin_area=cls.norfolk,
            locality=cls.melton_constable,
            locality_centre=False,
            indicator='adj',
            bearing='E'
        )
        cls.stop = StopPoint.objects.create(
            pk='2900M114',
            common_name='Bus Shelter',
            active=True,
            admin_area=cls.norfolk,
            locality=cls.melton_constable,
            locality_centre=False,
            indicator='opp',
            bearing='W',
            latlong=Point(52.8566019427, 1.0331935468)
        )
        cls.inactive_service = Service.objects.create(
            pk='45A',
            line_name='45A',
            date='1984-01-01',
            region=cls.north,
            current=False
        )
        StopUsage.objects.create(service=cls.inactive_service, stop=cls.stop, order=0)
        cls.inactive_service_with_alternative = Service.objects.create(
            pk='45B',
            line_name='45B',
            description='Holt - Norwich',
            date='1984-01-01',
            region=cls.north,
            current=False
        )
        cls.service = Service.objects.create(
            pk='ea_21-45-A-y08',
            line_name='45A',
            description='Holt - Norwich',
            date='1984-01-01',
            region=cls.north
        )

        cls.chariots = Operator.objects.create(
            pk='AINS',
            name='Ainsley\'s Chariots',
            vehicle_mode='airline',
            region_id='N',
            address='10 King Road\nIpswich',
            phone='0800 1111',
            email='ainsley@example.com',
            url='http://isyourgirlfriendahorse.com'
        )
        cls.nuventure = Operator.objects.create(
            pk='VENT', name='Nu-Venture', vehicle_mode='bus', region_id='N'
        )
        cls.natx = Operator.objects.create(
            pk='NXAP', name='National Express Airport', vehicle_mode='bus', region_id='N', url='nationalexpress.com'
        )
        cls.flixbus = Operator.objects.create(
            pk='FLIXBUS', name='FlixBus', vehicle_mode='coach', region_id='N', url='http://www.flixbus.com'
        )
        cls.service.operator.add(cls.chariots)
        cls.inactive_service.operator.add(cls.chariots)

        cls.note = Note.objects.create(
            text='Mind your head'
        )
        cls.note.operators.set((cls.chariots,))

    def test_index(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['regions'][0], self.north)

    def test_offline(self):
        response = self.client.get('/offline')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sorry, you don’t seem to be connected to the Internet.')

    def test_not_found(self):
        response = self.client.get('/fff')
        self.assertEqual(response.status_code, 404)

    def test_static(self):
        for route in ('/cookies', '/data', '/map'):
            response = self.client.get(route)
            self.assertEqual(response.status_code, 200)

    def test_region(self):
        response = self.client.get('/regions/N')
        self.assertContains(response, 'North')
        self.assertContains(response, '<h1>North</h1>')
        self.assertContains(response, '<a href="/areas/91">Norfolk</a>')
        self.assertContains(response, 'Chariots')
        self.assertNotContains(response, 'Nu-Venture')

    def test_lowercase_region(self):
        response = self.client.get('/regions/n')
        self.assertContains(
            response, '<link rel="canonical" href="https://bustimes.org.uk/regions/N" />'
        )
        self.assertEqual(response.status_code, 200)

    def test_search(self):
        response = self.client.get('/search?q=melton')
        self.assertContains(response, '1 result found for')
        self.assertContains(response, 'Melton Constable')

        response = self.client.get('/search?q=mlton')
        self.assertContains(response, '0 results found for')

        response = render(None, 'search/search.html', {
            'query': True,
            'suggestion': 'bordeaux'
        })
        self.assertContains(response, '<p>Did you mean <a href="/search?q=bordeaux">bordeaux</a>?</p>')

    def test_admin_area(self):
        """Admin area containing just one child should redirect to that child"""
        response = self.client.get('/areas/91')
        self.assertRedirects(response, '/localities/E0048689')

    def test_district(self):
        """Admin area containing just one child should redirect to that child"""
        response = self.client.get('/districts/91')
        self.assertEqual(response.status_code, 200)

    def test_locality(self):
        response = self.client.get('/localities/E0048689')
        self.assertContains(response, '<h1>Melton Constable</h1>')

    def test_stops(self):
        response = self.client.get('/stops.json')
        self.assertEqual(response.status_code, 400)

        response = self.client.get('/stops.json', {
            'ymax': '52.9',
            'xmax': '1.1',
            'ymin': '52.8',
            'xmin': '1.0',
        })
        self.assertEqual('FeatureCollection', response.json()['type'])
        self.assertIn('features', response.json())

    def test_stop(self):
        with vcr.use_cassette(os.path.join(DIR, '..', 'data', 'vcr', '2900M114.yaml')):
            response = self.client.get('/stops/2900M114')
        self.assertContains(response, 'North')
        self.assertContains(response, 'Norfolk')
        self.assertContains(response, 'Melton Constable, opp Bus Shelter')
        self.assertContains(response, 'heading=270')
        self.assertContains(response, '/static/js/map.')

    def test_stop_json(self):
        response = self.client.get('/stops/2900M114.json')
        data = response.json()
        self.assertTrue(data['active'])
        self.assertEqual(data['admin_area'], 91)
        self.assertEqual(data['atco_code'], '2900M114')
        self.assertEqual(data['latlong'], [52.8566019427, 1.0331935468])
        self.assertEqual(data['live_sources'], [])
        self.assertIsNone(data['heading'])
        self.assertIsNone(data['stop_area'])

    def test_inactive_stop(self):
        response = self.client.get('/stops/2900M115')
        self.assertEqual(response.status_code, 404)

    def test_operator_found(self):
        """The normal and Accelerated Mobile pages versions should be mostly the same
        (but slightly different)
        """
        for url in ('/operators/AINS', '/operators/ainsleys-chariots', '/operators/AINS?amp'):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'An airline operating company in')
            self.assertContains(response, 'Contact Ainsley&#39;s Chariots')
            self.assertContains(response, '10 King Road<br />Ipswich')
            self.assertContains(response, '&#109;&#97;&#105;&#108;&#116;&#111;&#58;&#97;&#105;' +
                                '&#110;&#115;&#108;&#101;&#121;&#64;&#101;&#120;&#97;&#109;' +
                                '&#112;&#108;&#101;&#46;&#99;&#111;&#109;')
            self.assertContains(response, 'http://isyourgirlfriendahorse.com')
            self.assertContains(response, 'Mind your head')  # Note

        self.assertContains(response, '<style amp-custom>')
        self.assertContains(response, "\"data:image/svg+xml;charset=utf8,%3Csvg xmlns='http://www.w3.org/2000")

    def test_operator_not_found(self):
        """An operator with no services should should return a 404 response"""
        response = self.client.get('/operators/VENT')
        self.assertEqual(response.status_code, 404)

    def test_service(self):
        response = self.client.get('/services/ea_21-45-A-y08')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'http://isyourgirlfriendahorse.com')
        self.assertContains(response, 'Mind your head')  # Note
        self.assertEqual(self.note.get_absolute_url(), '/operators/ainsleys-chariots')

    def test_service_natx(self):
        self.service.operator.set([self.natx])

        response = self.client.get('/services/ea_21-45-A-y08')
        self.assertContains(response, 'Buy tickets from National Express')

        response = self.client.get('/operators/NXAP')
        self.assertContains(response, 'viglink')

    def test_service_flixbus(self):
        self.service.operator.set([self.flixbus])

        response = self.client.get('/services/ea_21-45-A-y08')
        self.assertContains(response, 'Buy tickets from FlixBus')
        self.assertContains(response, 'viglink')

        response = self.client.get('/operators/FLIXBUS')
        self.assertContains(response, 'viglink')

    def test_service_redirect(self):
        response = self.client.get('/services/45B')
        self.assertEqual(response.status_code, 302)

    def test_service_not_found(self):
        response = self.client.get('/services/45A')
        self.assertEqual(response.status_code, 404)
        self.assertContains(
            response,
            'Sorry, it looks like the  service <strong>45A</strong> no longer exists. It might have',
            status_code=404
        )
        self.assertContains(response, 'Services operated by Ainsley', status_code=404)
        self.assertContains(response, '<li><a href="/localities/E0048689">Melton Constable</a></li>', status_code=404)

    def test_service_xml(self):
        response = self.client.get('/services/ea_21-45-A-y08.xml')
        self.assertEqual(response['Content-Type'], 'text/plain')
        self.assertEqual(response.status_code, 200)

    def test_modes(self):
        self.assertContains(render(None, 'modes.html', {
            'modes': ['bus'],
            'noun': 'services'
        }), 'Bus services')
        self.assertContains(render(None, 'modes.html', {
            'noun': 'services'
        }), 'Services')
        self.assertContains(render(None, 'modes.html', {
            'modes': ['bus', 'coach'],
            'noun': 'services'
        }), 'Bus and coach services')
        self.assertContains(render(None, 'modes.html', {
            'modes': ['bus', 'coach', 'tram'],
            'noun': 'services'
        }), 'Bus, coach and tram services')
        self.assertContains(render(None, 'modes.html', {
            'modes': ['bus', 'coach', 'tram', 'cable car'],
            'noun': 'operators'
        }), 'Bus, coach, tram and cable car operators')
