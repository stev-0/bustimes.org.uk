import xml.etree.cElementTree as ET
from datetime import time
from django.test import TestCase
from busstops.models import Service
from timetables import timetable


FIXTURES_DIR = './busstops/management/tests/fixtures/'


class TimetableTest(TestCase):
    """Tests some timetables generated directly from XML files"""
    @classmethod
    def setUpTestData(cls):
        cls.ne_service = Service.objects.create(
            pk='NE_130_PC4736_572',
            region_id='NE',
            date='2016-05-05'
        )
        cls.nw_service = Service.objects.create(
            pk='60023943',
            region_id='NW',
            date='2016-05-24'
        )
        cls.ea_service = Service.objects.create(
            pk='ea_21-13B-B-y08',
            region_id='EA',
            date='2016-05-24',
            net='ea'
        )
        cls.gb_service = Service.objects.create(
            pk='M11A_MEGA',
            region_id='GB',
            date='2016-05-24',
        )
        cls.gb_service = Service.objects.create(
            pk='swe_31-668-_-y10',
            region_id='SW',
            date='2016-05-24',
        )

    def test_get_pickle_filenames(self):
        """
        get_pickle_filenames should get filenames for a service,
        using different heuristics depending on the service's region
        """
        self.assertEqual(timetable.get_pickle_filenames(self.ne_service, None), ['NE_130_PC4736_572'])
        self.assertEqual(timetable.get_pickle_filenames(self.nw_service, None), ['SVR60023943'])

        self.assertEqual(timetable.get_pickle_filenames(self.ea_service, 'poo'), [])
        ea_filenames = timetable.get_pickle_filenames(self.ea_service, FIXTURES_DIR)
        self.assertEqual(['ea_21-13B-B-y08-1.xml'], ea_filenames)

        gb_filenames = timetable.get_pickle_filenames(self.gb_service, FIXTURES_DIR)
        self.assertEqual([], gb_filenames)

    def test_timetable_none(self):
        """timetable_from_filename should return None if there is an error"""
        none = timetable.timetable_from_filename(FIXTURES_DIR, 'ea_21-13B-B-y08-')
        self.assertIsNone(none)

    def test_timetable_ea(self):
        """Test a timetable from the East Anglia region"""
        timetable_ea = timetable.timetable_from_filename(FIXTURES_DIR, 'ea_21-13B-B-y08-1.xml')

        self.assertEqual('Monday to Sunday', str(timetable_ea.operating_profile))
        self.assertEqual('until 21 October 2016', str(timetable_ea.operating_period))

        self.assertEqual(3, len(timetable_ea.groupings[0].column_heads))
        self.assertEqual(13, len(timetable_ea.groupings[0].journeys))

        self.assertEqual(3, len(timetable_ea.groupings[1].column_heads))
        self.assertEqual(14, len(timetable_ea.groupings[1].journeys))

        self.assertTrue(timetable_ea.groupings[1].has_minor_stops())
        self.assertEqual(87, len(timetable_ea.groupings[1].rows))
        self.assertEqual('Leys Lane', timetable_ea.groupings[1].rows[0].part.stop.common_name)

    def test_timetable_megabus(self):
        """Test a timetable from the National Coach Services Database"""
        megabus = timetable.timetable_from_filename(
            FIXTURES_DIR, 'Megabus_Megabus14032016 163144_MEGA_M11A.xml'
        )
        self.assertFalse(megabus.groupings[0].has_minor_stops())
        self.assertFalse(megabus.groupings[1].has_minor_stops())
        self.assertEqual(megabus.groupings[0].rows[0].times, [
            time(13, 0), time(15, 0), time(16, 0), time(16, 30), time(18, 0), time(20, 0),
            time(23, 45)
        ])

    def test_timetable_ne(self):
        """Test timetable with some abbreviations"""
        timetable_ne = timetable.timetable_from_filename(FIXTURES_DIR, 'NE_03_SCC_X6_1.xml')
        self.assertEqual(timetable_ne.groupings[0].column_heads[0].span, 16)
        self.assertEqual(timetable_ne.groupings[0].column_heads[1].span, 14)
        self.assertEqual(timetable_ne.groupings[0].column_heads[2].span, 4)
        self.assertEqual(
            timetable_ne.groupings[0].rows[0].times[:3], [time(7, 0), time(8, 0), time(9, 0)]
        )
        # Test abbreviations (check the colspan and rowspan attributes of Cells)
        self.assertEqual(timetable_ne.groupings[0].rows[0].times[-3].colspan, 2)
        self.assertEqual(timetable_ne.groupings[0].rows[0].times[-3].rowspan, 88)
        self.assertIsNone(timetable_ne.groupings[1].rows[0].times[-12])
        self.assertEqual(timetable_ne.groupings[1].rows[0].times[-13].colspan, 2)

    def test_timetable_scotland(self):
        """Test a Scotch timetable with a 14 column wide empty foot"""
        timetable_scotland = timetable.timetable_from_filename(FIXTURES_DIR, 'SVRABBN017.xml')
        self.assertEqual(timetable_scotland.groupings[0].column_feet[0].span, 14)
        self.assertEqual(timetable_scotland.groupings[0].column_feet[0].notes, [])

    def test_timetable_deadruns(self):
        """Test a timetable with some dead runs which should be respected"""
        deadruns = timetable.timetable_from_filename(FIXTURES_DIR, 'SVRLABO024A.xml')
        self.assertEqual(
            deadruns.groupings[0].rows[-25].times[:3], [time(20, 58), time(22, 28), time(23, 53)]
        )
        self.assertEqual(
            deadruns.groupings[0].rows[-24].times[:7], ['', '', '', '', '', '', time(9, 51)]
        )
        self.assertEqual(deadruns.groupings[0].rows[-20].times[:6], ['', '', '', '', '', ''])
        self.assertEqual(deadruns.groupings[0].rows[-12].times[:6], ['', '', '', '', '', ''])
        self.assertEqual(deadruns.groupings[0].rows[-8].times[:6], ['', '', '', '', '', ''])
        self.assertEqual(deadruns.groupings[0].rows[-7].times[:6], ['', '', '', '', '', ''])
        self.assertEqual(deadruns.groupings[0].rows[-5].times[:6], ['', '', '', '', '', ''])
        self.assertEqual(deadruns.groupings[0].rows[-4].times[:6], ['', '', '', '', '', ''])
        self.assertEqual(deadruns.groupings[0].rows[-3].times[:6], ['', '', '', '', '', ''])
        self.assertEqual(
            deadruns.groupings[0].rows[-2].times[:7], ['', '', '', '', '', '', time(10, 5)]
        )
        self.assertEqual(
            deadruns.groupings[0].rows[-1].times[:7], ['', '', '', '', '', '', time(10, 7)]
        )

    def test_timetable_servicedorg(self):
        """Test a timetable with a ServicedOrganisation"""
        timetable_sw = timetable.timetable_from_filename(FIXTURES_DIR, 'swe_31-668-_-y10-1.xml')
        self.assertEqual(
            str(timetable_sw.groupings[0].column_heads[0].operatingprofile),
            'Monday to Friday\nSchool days'
        )


class DateRangeTest(TestCase):
    """Tests for DateRanges"""

    def test_single_date(self):
        """Test a DateRange starting and ending on the same date"""
        element = ET.fromstring("""
            <DateRange xmlns="http://www.transxchange.org.uk/">
                <StartDate>2001-05-01</StartDate>
                <EndDate>2001-05-01</EndDate>
            </DateRange>
        """)
        date_range = timetable.DateRange(element)
        self.assertEqual(str(date_range), '1 May 2001')
        self.assertFalse(date_range.starts_in_future())

    def test_past_range(self):
        """Test a DateRange starting and ending in the past"""
        element = ET.fromstring("""
            <OperatingPeriod xmlns="http://www.transxchange.org.uk/">
                <StartDate>2001-05-01</StartDate>
                <EndDate>2002-05-01</EndDate>
            </OperatingPeriod>
        """)
        date_range = timetable.DateRange(element)
        self.assertEqual(str(date_range), '2001-05-01 to 2002-05-01')


class OperatingPeriodTest(TestCase):
    """Tests for OperatingPeriods"""

    def test_single_date(self):
        """Test an OperatingPeriod starting and ending on the same date"""
        element = ET.fromstring("""
            <OperatingPeriod xmlns="http://www.transxchange.org.uk/">
                <StartDate>2001-05-01</StartDate>
                <EndDate>2001-05-01</EndDate>
            </OperatingPeriod>
        """)
        operating_period = timetable.OperatingPeriod(element)
        self.assertEqual(str(operating_period), 'on 1 May 2001')
        self.assertFalse(operating_period.starts_in_future())

    def test_open_ended(self):
        """Test an OperatingPeriod starting in the future, with no specified end"""
        element = ET.fromstring("""
            <OperatingPeriod xmlns="http://www.transxchange.org.uk/">
                <StartDate>2021-09-01</StartDate>
            </OperatingPeriod>
        """)
        operating_period = timetable.OperatingPeriod(element)
        self.assertEqual(str(operating_period), 'from 1 September 2021')
        self.assertTrue(operating_period.starts_in_future())

    def test_future_long_range(self):
        """Test an OperatingPeriod starting and ending in different years in the future"""
        element = ET.fromstring("""
            <OperatingPeriod xmlns="http://www.transxchange.org.uk/">
                <StartDate>2021-09-01</StartDate>
                <EndDate>2056-02-02</EndDate>
            </OperatingPeriod>
        """)
        operating_period = timetable.OperatingPeriod(element)
        self.assertEqual(str(operating_period), 'from 1 September 2021 to 2 February 2056')
        self.assertTrue(operating_period.starts_in_future())

    def test_future_medium_range(self):
        """Test an OperatingPeriod starting and ending in the same year in the future"""
        element = ET.fromstring("""
            <OperatingPeriod xmlns="http://www.transxchange.org.uk/">
                <StartDate>2056-02-01</StartDate>
                <EndDate>2056-06-02</EndDate>
            </OperatingPeriod>
        """)
        operating_period = timetable.OperatingPeriod(element)
        self.assertEqual(str(operating_period), 'from 1 February to 2 June 2056')
        self.assertTrue(operating_period.starts_in_future())

    def test_future_short_range(self):
        """Test an OperatingPeriod starting and ending in the same month in the future"""
        element = ET.fromstring("""
            <OperatingPeriod xmlns="http://www.transxchange.org.uk/">
                <StartDate>2056-02-01</StartDate>
                <EndDate>2056-02-05</EndDate>
            </OperatingPeriod>
        """)
        operating_period = timetable.OperatingPeriod(element)
        self.assertEqual(str(operating_period), 'from 1 to 5 February 2056')
        self.assertTrue(operating_period.starts_in_future())

    def test_past_range(self):
        """
        An OperatingPeriod starting and ending in the same month in the past
        should not be displayed
        """
        element = ET.fromstring("""
            <OperatingPeriod xmlns="http://www.transxchange.org.uk/">
                <StartDate>2001-05-01</StartDate>
                <EndDate>2002-05-01</EndDate>
            </OperatingPeriod>
        """)
        operating_period = timetable.OperatingPeriod(element)
        self.assertEqual(str(operating_period), '')
