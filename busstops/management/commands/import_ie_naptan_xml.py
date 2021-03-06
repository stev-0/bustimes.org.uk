"""Import an Irish NaPTAN XML file, obtainable from
https://data.dublinked.ie/dataset/national-public-transport-nodes/resource/6d997756-4dba-40d8-8526-7385735dc345
"""

import warnings
import zipfile
import xml.etree.cElementTree as ET
from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand
from ...models import Locality, AdminArea, StopPoint


class Command(BaseCommand):
    ns = {'naptan': 'http://www.naptan.org.uk/'}

    @staticmethod
    def add_arguments(parser):
        parser.add_argument('filenames', nargs='+', type=str)

    def handle_stop(self, element):
        stop = StopPoint(
            atco_code=element.find('naptan:AtcoCode', self.ns).text,
            locality_centre=element.find('naptan:Place/naptan:LocalityCentre', self.ns).text == 'true',
            active=element.get('Status') == 'active',
        )

        for subelement in element.find('naptan:Descriptor', self.ns):
            tag = subelement.tag[27:]
            if tag == 'CommonName':
                stop.common_name = subelement.text
            elif tag == 'Street':
                stop.street = subelement.text
            elif tag == 'Indicator':
                stop.indicator = subelement.text.lower()
            else:
                warnings.warn('Stop {} has an unexpected property: {}'.format(stop.atco_code, tag))

        stop_classification_element = element.find('naptan:StopClassification', self.ns)

        stop_type = stop_classification_element.find('naptan:StopType', self.ns).text
        if stop_type != 'class_undefined':
            stop.stop_type = stop_type

            bus_element = stop_classification_element.find('naptan:OnStreet/naptan:Bus', self.ns)

            if bus_element is not None:
                stop.bus_stop_type = bus_element.find('naptan:BusStopType', self.ns).text
                stop.timing_status = bus_element.find('naptan:TimingStatus', self.ns).text

                compass_point_element = bus_element.find(
                    'naptan:MarkedPoint/naptan:Bearing/naptan:CompassPoint', self.ns
                )
                if compass_point_element is not None:
                    stop.bearing = compass_point_element.text

        if stop.bus_stop_type == 'type_undefined':
            stop.bus_stop_type = ''

        place_element = element.find('naptan:Place', self.ns)

        location_element = place_element.find('naptan:Location', self.ns)
        longitude_element = location_element.find('naptan:Longitude', self.ns)
        latitude_element = location_element.find('naptan:Latitude', self.ns)
        if longitude_element is None:
            warnings.warn('Stop {} has no location'.format(stop.atco_code))
        else:
            stop.latlong = Point(float(longitude_element.text), float(latitude_element.text))

        admin_area_id = element.find('naptan:AdministrativeAreaRef', self.ns).text
        if not AdminArea.objects.filter(atco_code=admin_area_id).exists():
            AdminArea.objects.create(id=admin_area_id, atco_code=admin_area_id, region_id='NI')
        stop.admin_area_id = admin_area_id

        locality_element = place_element.find('naptan:NptgLocalityRef', self.ns)
        if locality_element is not None:
            if not Locality.objects.filter(id=locality_element.text).exists():
                Locality.objects.create(id=locality_element.text, admin_area_id=admin_area_id)
            stop.locality_id = locality_element.text

        stop.save()

    def handle_file(self, archive, filename):
        with archive.open(filename) as open_file:
            iterator = ET.iterparse(open_file)
            for _, element in iterator:
                tag = element.tag[27:]
                if tag == 'StopPoint':
                    self.handle_stop(element)
                    element.clear()

    def handle(self, *args, **options):
        for filename in options['filenames']:
            with zipfile.ZipFile(filename) as archive:
                for filename in archive.namelist():
                    self.handle_file(archive, filename)
