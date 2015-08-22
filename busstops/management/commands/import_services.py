"""
Command for importing transport services.

So far, all services in the SE, EA, Y and NCSD regions can be imported without
known errors.
"""

from django.core.management.base import BaseCommand, CommandError
from busstops.models import Operator, StopPoint, Service, ServiceVersion

import os
import re
import csv
import xml.etree.ElementTree as ET
from datetime import datetime


class Command(BaseCommand):

    # see https://docs.python.org/2/library/xml.etree.elementtree.html#parsing-xml-with-namespaces
    ns = {'txc': 'http://www.transxchange.org.uk/'}

    now = datetime.today()

    serviceversion_regex = re.compile(r'(SVR|Snapshot[^ _]+_TXC_|[a-z]+_|.*_atco_)(.+).xml$')
    net_regex = re.compile(r'([a-z]+)_$')

    # map TradingNames to operator IDs where there is no correspondence between the NOC DB and TNDS:
    SPECIAL_OPERATOR_TRADINGNAMES = {
        'Southwold Town Council': 'SWTC',
        'H.C.Chambers & Son': 'CHMB',
        'Bungay and Beccles Area CT': 'BBCT',
        'Stowmarket Minibus & Coach Hire': 'MBCH',
        'Harwich Harbour Ferry': 'HHFS',
        'Halesworth Area Community Transport': 'HACT',
        'Dartmouth Steam Railway And River Boat Company': 'DRMR',
        'Borderbus': 'BDRB',
    }
    # map OperatorCodes to operator IDs (ditto):
    SPECIAL_OPERATOR_CODES = {
        'HIB':  'HIMB',  # Holy Island Minibus
        '1866': 'BPTR',  # Burnley & Pendle
        '2152': 'RSTY',  # R S Tyrer & Sons
        '2916': 'SPCT',  # South Pennine Community Transport
        'RB1':  'RBRO',  # Richards Bros
        'ACY':  'ACYM',  # Arriva Cymru/Wales
        'RMB':  'RMBL',  # Routemaster Buses Ltd
        'JO1':  'JTMT',  # John's Travel (Merthyr Tydfil)
        'CO':   'CFSV',  # Coniston Launch/Ferry
        'MN': 'ALNO',  # Arriva London North
        'ME': 'METR',  # Metrobus
        'IF': 'ELBG',  # East London Bus & Coach/Stagecoach London
        'SK': 'SELK',  # South East London & Kent Bus Co
        'TCL': 'TRAM',  # Croydon Tram
        'SL': 'ALSO',  # Arriva London South
        'WPS': 'WPSA',  # Westminster Passenger Service Association
        'SV': 'LSOV',  # London Sovereign
        'KE': 'AMTM',  # Arriva Kent Thameside
        'TE': 'ABLO',  # Abellio London (West)
        'TN': 'TOTR',  # Tower Transit/Transportr
        'UN': 'UNOE',  # Uno
        'HY': 'NCTP',  # CT Plus
        'LD': 'ASES',  # Arriva Shires
    }

    # @staticmethod
    # def parse_duration(string):
    #     """
    #     Given a TransXChange RunTime string, e.g. 'PT180S',
    #     returns a timedelta, e.g. 180 seconds.

    #     Thanks to http://stackoverflow.com/a/4628148
    #     """
    #     regex = re.compile(r'PT((?P<hours>\d+?)H)?((?P<minutes>\d+?)M)?((?P<seconds>\d+?)S)?')
    #     matches = regex.match(string).groupdict()
    #     time_params = {}
    #     for (name, param) in matches.iteritems():
    #         if param:
    #             time_params[name] = int(param)
    #     return timedelta(**time_params)

    # @staticmethod
    # def weekday_to_int(weekday):
    #     weekdays = ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')
    #     for i, day in enumerate(weekdays):
    #         if weekday == day:
    #             return i

    # @staticmethod
    # def get_operating_profile(element):
    #     """
    #     Given an OperatingProfile element,
    #     returns an OperatingProfile object that is (now) in the database
    #     """
    #     regular_days = ','.join(
    #         map(
    #             lambda e: weekday_to_int(e.tag[33:]), # tag name with namespace prefix removed
    #             element.find('txc:RegularDayType', ns).find('txc:DaysOfWeek', ns) # iterable containing children of DaysOfWeek element
    #             )
    #         )
    #     print regular_days
    #     profile, created = OperatingProfile.objects.get_or_create(
    #         regular_days=regular_days,
    #         )
    #     print profile

    def get_service_version_name(self, file_name):
        matches = self.serviceversion_regex.match(file_name)

        if matches is not None:
            return matches.group(2)
        else:
            return file_name[:-4]

    def get_net(self, file_name):
        """
        Get the service 'net' (for services in the EA, EM, L, WM, SE and SW regions).
        """
        matches = self.serviceversion_regex.match(file_name)

        if matches is not None:
            net_matches = self.net_regex.match(matches.group(1))
            if net_matches is not None:
                return net_matches.group(1)
        return ''

    def get_operator(self, operator_element):
        "Given an Operator element, returns an Operator object."

        try:
            national_code_element = operator_element.find('txc:NationalOperatorCode', self.ns)
            trading_name_element = operator_element.find('txc:TradingName', self.ns)
            name_on_license_element = operator_element.find('txc:OperatorNameOnLicence', self.ns)

            if national_code_element is not None:
                return Operator.objects.get(id=national_code_element.text)

            if trading_name_element is not None:
                operator_name = str.replace(
                    operator_element.find('txc:TradingName', self.ns).text,
                    '&amp;',
                    '&'
                    )
                if operator_name in self.SPECIAL_OPERATOR_TRADINGNAMES:
                    return Operator.objects.get(id=self.SPECIAL_OPERATOR_TRADINGNAMES[operator_name])

                return Operator.objects.get(name__iexact=operator_name)

            operator_code = operator_element.find('txc:OperatorCode', self.ns).text
            if operator_code in self.SPECIAL_OPERATOR_CODES:
                return Operator.objects.get(id=self.SPECIAL_OPERATOR_CODES[operator_code])

            possible_operators = Operator.objects.filter(id=operator_code)
            if len(possible_operators) == 1:
                return possible_operators[0]

            return Operator.objects.get(name=name_on_license_element.text)

        except Exception, error:
            print str(error)
            print ET.tostring(operator_element)
            return None

    def do_operators(self, operators_element):
        "Given an Operators element, returns a dict mapping local codes to Operator objects."

        operators = {}

        for operator_element in operators_element:
            if 'id' in operator_element.attrib:
                local_code = operator_element.attrib['id']
            else:
                local_code = operator_element.find('txc:OperatorCode', self.ns).text

            operator = self.get_operator(operator_element)
            operators[local_code] = operator

        return operators

    def do_service(self, services_element, file_name, root,
                   service_descriptions=None):

        for service_element in services_element:

            # service:

            line_name = service_element.find('txc:Lines', self.ns)[0][0].text[:24]

            mode_element = service_element.find('txc:Mode', self.ns)
            if mode_element is not None:
                mode = mode_element.text[:10]
            else:
                mode = ''

            # service operators:
            # (doing this preliminary bit now, to make getting NCSD descriptions possible)

            operators_element = root.find('txc:Operators', self.ns)
            operators = self.do_operators(operators_element)

            # service description:

            description_element = service_element.find('txc:Description', self.ns)
            if description_element is not None:
                description = description_element.text[:100]
            elif service_descriptions is not None:
                description = service_descriptions[operators.values()[0].id + line_name]
            else:
                description = ''

            # service:

            service = Service.objects.update_or_create(
                service_code=service_element.find('txc:ServiceCode', self.ns).text,
                defaults=dict(
                    line_name=line_name,
                    mode=mode,
                    description=description,
                    net=self.get_net(file_name),
                    )
                )[0]

            # service operators (part 2):

            for operator in operators.values():
                if operator is not None:
                    service.operator.add(operator)

            # service stops:

            for stop_element in root.find('txc:StopPoints', self.ns):
                try:
                    stop_atco_code = stop_element.find('txc:StopPointRef', self.ns).text
                    stop = StopPoint.objects.get(atco_code=stop_atco_code)
                    service.stops.add(stop)
                except:
                    print 'Problem adding stop %s to service %s' % (stop_atco_code, service.service_code)

            # service version:

            service_version = ServiceVersion(
                name=self.get_service_version_name(file_name),
                service=service,
                description=description
                )

            if len(service_version.name) > 24:
                print '%s (from %s) is too long, skipping' % (service_version.name, file_name)
                break

            date_element = service_element.find('txc:OperatingPeriod', self.ns)
            start_date_element = date_element.find('txc:StartDate', self.ns)
            end_date_element = date_element.find('txc:EndDate', self.ns)

            if end_date_element is not None:
                end_date = datetime.strptime(end_date_element.text, '%Y-%m-%d')
                if end_date < self.now:
                    break
                service_version.end_date = end_date

            service_version.start_date = datetime.strptime(start_date_element.text, '%Y-%m-%d')
            service_version.save()


    def handle(self, *args, **options):

        service_descriptions = None

        for root, dirs, files in os.walk('../TNDS/'):

            for i, file_name in enumerate(files):
                if (i - 1) % 1000 == 0:
                    print i

                file_path = os.path.join(root, file_name)

                # the NCSD has service descriptions are in a separate file:
                if file_name == 'IncludedServices.csv':
                    with open(file_path) as csv_file:
                        reader = csv.DictReader(csv_file)
                        service_descriptions = {}
                        for row in reader:
                            # e.g. {'NATX323': 'Cardiff - Liverpool'}
                            service_descriptions[row['Operator'] + row['LineName']] = row['Description']

                elif file_name[-4:] == '.xml':
                    e = ET.parse(file_path).getroot()

                    self.do_service(e.find('txc:Services', self.ns), file_name, e, service_descriptions=service_descriptions)
