import os
import re
import logging
import requests

logger = logging.getLogger(__name__)

FMCSA_BASE_URL = "https://mobile.fmcsa.dot.gov/qc/services"
DEFAULT_TIMEOUT = 10  # seconds


class FMCSAServiceException(Exception):
    """Base exception for FMCSA Service errors."""
    pass


class CarrierNotFoundException(FMCSAServiceException):
    """Raised when FMCSA returns no carrier data for given DOT number."""
    pass


class InvalidDOTNumberException(FMCSAServiceException):
    """Raised when the provided DOT number is invalid."""
    pass


class FMCSAConnectionException(FMCSAServiceException):
    """Raised when connection to FMCSA times out or fails."""
    pass


class FMCSAService:
    """
    Dedicated service for retrieving and normalizing carrier data
    from the official FMCSA QCMobile API.
    """

    def __init__(self, web_key=None, base_url=None, timeout=DEFAULT_TIMEOUT):
        self.web_key = web_key or os.getenv('FMCSA_WEB_KEY')
        self.base_url = (base_url or FMCSA_BASE_URL).rstrip('/')
        self.timeout = timeout

    def _get_web_key(self):
        if not self.web_key or self.web_key == 'your_web_key_here':
            raise FMCSAServiceException("FMCSA_WEB_KEY environment variable is not configured.")
        return self.web_key

    def _make_request(self, endpoint_path):
        """
        Executes an HTTP GET request to the specified FMCSA endpoint.
        Ensures WebKey is never leaked in exceptions or logs.
        """
        web_key = self._get_web_key()
        url = f"{self.base_url}/{endpoint_path.lstrip('/')}"
        params = {'webKey': web_key}

        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout as err:
            logger.error(f"FMCSA request timeout for endpoint: {endpoint_path}")
            raise FMCSAConnectionException("FMCSA service connection timed out") from err
        except requests.exceptions.HTTPError as err:
            status_code = err.response.status_code if err.response is not None else 'Unknown'
            logger.error(f"FMCSA HTTP error {status_code} for endpoint: {endpoint_path}")
            if err.response is not None and err.response.status_code == 404:
                raise CarrierNotFoundException("Carrier not found") from err
            raise FMCSAServiceException("FMCSA service returned an HTTP error") from err
        except requests.exceptions.RequestException as err:
            logger.error(f"FMCSA request failed for endpoint: {endpoint_path}")
            raise FMCSAConnectionException("FMCSA service temporarily unavailable") from err
        except ValueError as err:
            logger.error(f"Failed to parse JSON response from endpoint: {endpoint_path}")
            raise FMCSAServiceException("Invalid JSON response from FMCSA service") from err

    def fetch_carrier_data(self, dot_number):
        """
        Fetches carrier details from official FMCSA endpoints and normalizes the output.
        """
        # Validate dot_number
        dot_str = str(dot_number).strip()
        if not dot_str.isdigit() or int(dot_str) <= 0:
            raise InvalidDOTNumberException(f"Invalid DOT number: {dot_number}")

        dot = int(dot_str)

        # 1. Main carrier endpoint (required)
        carrier_resp = self._make_request(f"carriers/{dot}")
        carrier_obj = self._extract_carrier_object(carrier_resp)

        if not carrier_obj:
            raise CarrierNotFoundException(f"Carrier with DOT {dot} not found")

        # 2. Additional optional endpoints
        basics_resp = self._safe_fetch(f"carriers/{dot}/basics")
        cargo_resp = self._safe_fetch(f"carriers/{dot}/cargo-carried")
        operation_resp = self._safe_fetch(f"carriers/{dot}/operation-classification")
        docket_resp = self._safe_fetch(f"carriers/{dot}/docket-numbers")
        authority_resp = self._safe_fetch(f"carriers/{dot}/authority")

        # 3. Combine and normalize
        return self._normalize(
            dot_number=dot,
            carrier_obj=carrier_obj,
            basics_resp=basics_resp,
            cargo_resp=cargo_resp,
            operation_resp=operation_resp,
            docket_resp=docket_resp,
            authority_resp=authority_resp
        )

    def fetch_essential_carrier_data(self, dot_number):
        """
        Lightweight essential fetch for range search enrichment.
        Only requests main carrier details and authority status (2 endpoints total),
        skipping optional basics/cargo/operation endpoints.
        """
        dot_str = str(dot_number).strip()
        if not dot_str.isdigit() or int(dot_str) <= 0:
            raise InvalidDOTNumberException(f"Invalid DOT number: {dot_number}")

        dot = int(dot_str)

        # 1. Main carrier endpoint
        carrier_resp = self._make_request(f"carriers/{dot}")
        carrier_obj = self._extract_carrier_object(carrier_resp)

        if not carrier_obj:
            raise CarrierNotFoundException(f"Carrier with DOT {dot} not found")

        # 2. Authority endpoint
        authority_resp = self._safe_fetch(f"carriers/{dot}/authority")

        # 3. Normalize essential fields
        return self._normalize(
            dot_number=dot,
            carrier_obj=carrier_obj,
            basics_resp=None,
            cargo_resp=None,
            operation_resp=None,
            docket_resp=None,
            authority_resp=authority_resp
        )


    def _safe_fetch(self, endpoint):
        try:
            return self._make_request(endpoint)
        except CarrierNotFoundException:
            raise
        except FMCSAServiceException as e:
            logger.warning(f"Optional endpoint {endpoint} failed or returned error: {e}")
            return None

    def _extract_content_list(self, resp_data):
        if not resp_data or not isinstance(resp_data, dict):
            return []
        content = resp_data.get('content', [])
        if isinstance(content, list):
            return content
        elif isinstance(content, dict):
            return [content]
        return []

    def _extract_carrier_object(self, resp_data):
        content = self._extract_content_list(resp_data)
        if not content:
            # Check if root dict has carrier
            if isinstance(resp_data, dict) and 'carrier' in resp_data:
                return resp_data['carrier']
            return None

        first_item = content[0]
        if isinstance(first_item, dict):
            if 'carrier' in first_item:
                return first_item['carrier']
            return first_item
        return None

    def _parse_bool(self, val):
        if val is None:
            return None
        if isinstance(val, bool):
            return val
        s = str(val).strip().upper()
        if s in ('Y', 'YES', 'TRUE', '1', 'ACTIVE', 'ALLOWED'):
            return True
        if s in ('N', 'NO', 'FALSE', '0', 'INACTIVE', 'NOT ALLOWED'):
            return False
        return None

    def _parse_int(self, val):
        if val is None or val == '':
            return None
        try:
            return int(val)
        except (ValueError, TypeError):
            return None

    def _parse_float(self, val):
        if val is None or val == '':
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None

    def _parse_mc_info(self, docket_resp, carrier_obj):
        """
        Extracts mc_prefix and mc_number from docket response or carrier_obj.
        """
        docket_content = self._extract_content_list(docket_resp)
        mc_prefix = None
        mc_number = None

        # Try docket endpoint response first
        for item in docket_content:
            if isinstance(item, dict):
                prefix = item.get('prefix') or item.get('icdPrefix') or item.get('docketPrefix')
                docket_num = item.get('docketNumber') or item.get('docketId') or item.get('icdDocketNumber')

                if prefix or docket_num:
                    mc_prefix = str(prefix).strip() if prefix else "MC"
                    if docket_num:
                        # docket_num could be "MC1670397" or "1670397" or "MC 1670397"
                        digits = re.sub(r'\D', '', str(docket_num))
                        if digits:
                            mc_number = int(digits)
                            return mc_prefix, mc_number

        # Fallback to carrier_obj fields if present
        docket_val = carrier_obj.get('docketNumber') or carrier_obj.get('mcNumber') or carrier_obj.get('docket_number')
        if docket_val:
            prefix_match = re.search(r'([A-Za-z]+)', str(docket_val))
            if prefix_match:
                mc_prefix = prefix_match.group(1).upper()
            else:
                mc_prefix = "MC"

            digits = re.sub(r'\D', '', str(docket_val))
            if digits:
                mc_number = int(digits)

        return mc_prefix, mc_number

    def _normalize(self, dot_number, carrier_obj, basics_resp, cargo_resp, operation_resp, docket_resp, authority_resp):
        carrier = carrier_obj or {}

        # 1. Operation classification
        op_class_list = []
        op_content = self._extract_content_list(operation_resp)
        for item in op_content:
            if isinstance(item, dict):
                desc = item.get('operationClassificationDesc') or item.get('desc') or item.get('description')
                if desc:
                    op_class_list.append(str(desc).strip())
            elif isinstance(item, str):
                op_class_list.append(item.strip())

        # 2. Cargo carried
        cargo_list = []
        cargo_content = self._extract_content_list(cargo_resp)
        for item in cargo_content:
            if isinstance(item, dict):
                desc = item.get('cargoCarriedDesc') or item.get('desc') or item.get('description')
                if desc:
                    cargo_list.append(str(desc).strip())
            elif isinstance(item, str):
                cargo_list.append(item.strip())

        # 3. MC Info
        mc_prefix, mc_number = self._parse_mc_info(docket_resp, carrier)

        # 4. Operation classification codes
        op_code_dict = carrier.get('carrierOperation', {}) if isinstance(carrier.get('carrierOperation'), dict) else {}
        op_code = op_code_dict.get('carrierOperationCode') or carrier.get('carrierOperationCode')
        op_desc = op_code_dict.get('carrierOperationDesc') or carrier.get('carrierOperationDesc')

        # 5. Authority info
        auth_content = self._extract_content_list(authority_resp)
        auth_item = auth_content[0] if (auth_content and isinstance(auth_content[0], dict)) else {}
        auth_obj = auth_item.get('carrierAuthority') if isinstance(auth_item.get('carrierAuthority'), dict) else auth_item

        common_auth = auth_obj.get('commonAuthorityStatus') or carrier.get('commonAuthorityStatus')
        contract_auth = auth_obj.get('contractAuthorityStatus') or carrier.get('contractAuthorityStatus')
        broker_auth = auth_obj.get('brokerAuthorityStatus') or carrier.get('brokerAuthorityStatus')

        auth_prop = self._parse_bool(auth_obj.get('authorizedForProperty') or carrier.get('authorizedForProperty'))
        auth_broker = self._parse_bool(auth_obj.get('authorizedForBroker') or carrier.get('authorizedForBroker'))
        auth_hhg = self._parse_bool(auth_obj.get('authorizedForHouseholdGoods') or carrier.get('authorizedForHouseholdGoods'))
        auth_pass = self._parse_bool(auth_obj.get('authorizedForPassenger') or carrier.get('authorizedForPassenger'))


        # 6. Basics / Safety data
        basics_content = self._extract_content_list(basics_resp)
        basics_dict = {}
        for item in basics_content:
            if isinstance(item, dict):
                basics_dict.update(item)

        # Crash totals
        crash_total = self._parse_int(basics_dict.get('crashTotal') or carrier.get('crashTotal'))
        fatal_crash = self._parse_int(basics_dict.get('fatalCrash') or carrier.get('fatalCrashCount') or carrier.get('fatalCrash'))
        inj_crash = self._parse_int(basics_dict.get('injCrash') or carrier.get('injCrashCount') or carrier.get('injCrash'))
        towaway_crash = self._parse_int(basics_dict.get('towawayCrash') or carrier.get('towawayCrashCount') or carrier.get('towawayCrash'))

        # Driver inspection metrics
        driver_insp = self._parse_int(basics_dict.get('driverInsp') or basics_dict.get('driverInspCount') or carrier.get('driverInsp'))
        driver_oos_insp = self._parse_int(basics_dict.get('driverOosInsp') or basics_dict.get('driverOosInspCount') or carrier.get('driverOosInsp'))
        driver_oos_rate = self._parse_float(basics_dict.get('driverOosRate') or carrier.get('driverOosRate'))
        driver_oos_rate_avg = self._parse_float(basics_dict.get('driverOosRateNationalAverage') or basics_dict.get('driverOosRateNatAvg'))

        # Vehicle inspection metrics
        vehicle_insp = self._parse_int(basics_dict.get('vehicleInsp') or basics_dict.get('vehicleInspCount') or carrier.get('vehicleInsp'))
        vehicle_oos_insp = self._parse_int(basics_dict.get('vehicleOosInsp') or basics_dict.get('vehicleOosInspCount') or carrier.get('vehicleOosInsp'))
        vehicle_oos_rate = self._parse_float(basics_dict.get('vehicleOosRate') or carrier.get('vehicleOosRate'))
        vehicle_oos_rate_avg = self._parse_float(basics_dict.get('vehicleOosRateNationalAverage') or basics_dict.get('vehicleOosRateNatAvg'))

        # Hazmat inspection metrics
        hazmat_insp = self._parse_int(basics_dict.get('hazmatInsp') or basics_dict.get('hazmatInspCount') or carrier.get('hazmatInsp'))
        hazmat_oos_insp = self._parse_int(basics_dict.get('hazmatOosInsp') or basics_dict.get('hazmatOosInspCount') or carrier.get('hazmatOosInsp'))
        hazmat_oos_rate = self._parse_float(basics_dict.get('hazmatOosRate') or carrier.get('hazmatOosRate'))
        hazmat_oos_rate_avg = self._parse_float(basics_dict.get('hazmatOosRateNationalAverage') or basics_dict.get('hazmatOosRateNatAvg'))

        # Construct normalized dictionary strictly following specification
        normalized = {
            "dot_number": dot_number,
            "mc_number": mc_number,
            "mc_prefix": mc_prefix,
            "legal_name": carrier.get('legalName'),
            "dba_name": carrier.get('dbaName'),
            "allowed_to_operate": self._parse_bool(carrier.get('allowedToOperate')),
            "carrier_operation_code": op_code,
            "carrier_operation_description": op_desc,
            "common_authority_status": common_auth,
            "contract_authority_status": contract_auth,
            "broker_authority_status": broker_auth,
            "authorized_for_property": auth_prop,
            "authorized_for_broker": auth_broker,
            "authorized_for_household_goods": auth_hhg,
            "authorized_for_passenger": auth_pass,
            "phy_street": carrier.get('phyStreet'),
            "phy_city": carrier.get('phyCity'),
            "phy_state": carrier.get('phyState'),
            "phy_zipcode": carrier.get('phyZipcode'),
            "phy_country": carrier.get('phyCountry'),
            "total_drivers": self._parse_int(carrier.get('totalDrivers')),
            "total_power_units": self._parse_int(carrier.get('totalPowerUnits')),
            "bipd_insurance_on_file": carrier.get('bipdInsuranceOnFile'),
            "bipd_insurance_required": carrier.get('bipdInsuranceRequired'),
            "bipd_required_amount": self._parse_int(carrier.get('bipdRequiredAmount')),
            "cargo_insurance_on_file": carrier.get('cargoInsuranceOnFile'),
            "cargo_insurance_required": carrier.get('cargoInsuranceRequired'),
            "bond_insurance_on_file": carrier.get('bondInsuranceOnFile'),
            "bond_insurance_required": carrier.get('bondInsuranceRequired'),
            "crash_total": crash_total,
            "fatal_crash": fatal_crash,
            "inj_crash": inj_crash,
            "towaway_crash": towaway_crash,
            "driver_insp": driver_insp,
            "driver_oos_insp": driver_oos_insp,
            "driver_oos_rate": driver_oos_rate,
            "driver_oos_rate_national_average": driver_oos_rate_avg,
            "vehicle_insp": vehicle_insp,
            "vehicle_oos_insp": vehicle_oos_insp,
            "vehicle_oos_rate": vehicle_oos_rate,
            "vehicle_oos_rate_national_average": vehicle_oos_rate_avg,
            "hazmat_insp": hazmat_insp,
            "hazmat_oos_insp": hazmat_oos_insp,
            "hazmat_oos_rate": hazmat_oos_rate,
            "hazmat_oos_rate_national_average": hazmat_oos_rate_avg,
            "safety_rating": carrier.get('safetyRating'),
            "safety_rating_date": carrier.get('safetyRatingDate'),
            "oos_date": carrier.get('oosDate'),
            "status_code": carrier.get('statusCode'),
            "operation_classification": op_class_list,
            "cargo_carried": cargo_list,
        }

        return normalized
