from unittest.mock import patch, MagicMock
import requests
from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from carriers.models import Carrier
from carriers.services.fmcsa_service import (
    FMCSAService,
    InvalidDOTNumberException,
    CarrierNotFoundException,
    FMCSAConnectionException,
    FMCSAServiceException,
)
from carriers.services.company_census_service import (
    CompanyCensusService,
    InvalidMCRangeException,
    CompanyCensusConnectionException,
    CompanyCensusException,
)
from carriers.services.equipment_classifier import classify_equipment




class FMCSAServiceTestCase(TestCase):
    """Unit test suite for FMCSAService."""

    def setUp(self):
        self.service = FMCSAService(web_key="test_web_key")
        self.dot = 4202109

        # Mock sample responses
        self.carrier_sample = {
            "content": [
                {
                    "carrier": {
                        "dotNumber": 4202109,
                        "legalName": "RP TRANSPORT LLC",
                        "dbaName": None,
                        "allowedToOperate": "Y",
                        "phyStreet": "123 MAIN ST",
                        "phyCity": "MISSION",
                        "phyState": "TX",
                        "phyZipcode": "78573",
                        "phyCountry": "US",
                        "totalDrivers": 5,
                        "totalPowerUnits": 3,
                        "carrierOperation": {
                            "carrierOperationCode": "C",
                            "carrierOperationDesc": "Interstate"
                        },
                        "bipdInsuranceOnFile": "Y",
                        "bipdInsuranceRequired": "Y",
                        "bipdRequiredAmount": 750000,
                        "cargoInsuranceOnFile": "N",
                        "cargoInsuranceRequired": "N",
                        "bondInsuranceOnFile": "N",
                        "bondInsuranceRequired": "N",
                        "safetyRating": "SATISFACTORY",
                        "safetyRatingDate": "2022-01-15",
                        "statusCode": "A"
                    }
                }
            ]
        }

        self.docket_sample = {
            "content": [
                {
                    "prefix": "MC",
                    "docketNumber": "1670397",
                    "icdDocketNumber": 1670397
                }
            ]
        }

        self.authority_sample = {
            "content": [
                {
                    "commonAuthorityStatus": "A",
                    "contractAuthorityStatus": "N",
                    "brokerAuthorityStatus": "N",
                    "authorizedForProperty": "Y",
                    "authorizedForBroker": "N",
                    "authorizedForHouseholdGoods": "N",
                    "authorizedForPassenger": "N"
                }
            ]
        }

        self.cargo_sample = {
            "content": [
                {"cargoCarriedDesc": "General Freight"},
                {"cargoCarriedDesc": "Household Goods"}
            ]
        }

        self.op_sample = {
            "content": [
                {"operationClassificationDesc": "Authorized For Hire"}
            ]
        }

        self.basics_sample = {
            "content": [
                {
                    "crashTotal": 2,
                    "fatalCrash": 0,
                    "injCrash": 1,
                    "towawayCrash": 1,
                    "driverInspCount": 10,
                    "driverOosInspCount": 1,
                    "driverOosRate": 10.0,
                    "driverOosRateNatAvg": 5.5,
                    "vehicleInspCount": 15,
                    "vehicleOosInspCount": 2,
                    "vehicleOosRate": 13.3,
                    "vehicleOosRateNatAvg": 20.1,
                    "hazmatInspCount": 0,
                    "hazmatOosInspCount": 0,
                    "hazmatOosRate": None,
                    "hazmatOosRateNatAvg": None
                }
            ]
        }

    @patch('requests.get')
    def test_successful_carrier_lookup_and_normalization(self, mock_get):
        def side_effect(url, params, timeout):
            mock_resp = MagicMock()
            mock_resp.raise_for_status.return_value = None

            if 'docket-numbers' in url:
                mock_resp.json.return_value = self.docket_sample
            elif 'authority' in url:
                mock_resp.json.return_value = self.authority_sample
            elif 'cargo-carried' in url:
                mock_resp.json.return_value = self.cargo_sample
            elif 'operation-classification' in url:
                mock_resp.json.return_value = self.op_sample
            elif 'basics' in url:
                mock_resp.json.return_value = self.basics_sample
            else:
                mock_resp.json.return_value = self.carrier_sample
            return mock_resp

        mock_get.side_effect = side_effect

        normalized = self.service.fetch_carrier_data(self.dot)

        self.assertEqual(normalized['dot_number'], 4202109)
        self.assertEqual(normalized['mc_number'], 1670397)
        self.assertEqual(normalized['mc_prefix'], "MC")
        self.assertEqual(normalized['legal_name'], "RP TRANSPORT LLC")
        self.assertTrue(normalized['allowed_to_operate'])
        self.assertEqual(normalized['phy_city'], "MISSION")
        self.assertEqual(normalized['phy_state'], "TX")
        self.assertEqual(normalized['common_authority_status'], "A")
        self.assertTrue(normalized['authorized_for_property'])
        self.assertEqual(normalized['cargo_carried'], ["General Freight", "Household Goods"])
        self.assertEqual(normalized['operation_classification'], ["Authorized For Hire"])

    @patch('requests.get')
    def test_carrier_with_empty_optional_endpoints(self, mock_get):
        def side_effect(url, params, timeout):
            mock_resp = MagicMock()
            mock_resp.raise_for_status.return_value = None

            if f"carriers/{self.dot}" in url and not any(sub in url for sub in ['basics', 'cargo', 'operation', 'docket', 'authority']):
                mock_resp.json.return_value = self.carrier_sample
            else:
                # Return empty content for optional endpoints
                mock_resp.json.return_value = {"content": []}
            return mock_resp

        mock_get.side_effect = side_effect

        normalized = self.service.fetch_carrier_data(self.dot)

        self.assertEqual(normalized['dot_number'], 4202109)
        self.assertIsNone(normalized['mc_number'])
        self.assertEqual(normalized['cargo_carried'], [])
        self.assertEqual(normalized['operation_classification'], [])
        self.assertIsNone(normalized['common_authority_status'])

    def test_invalid_dot_number(self):
        with self.assertRaises(InvalidDOTNumberException):
            self.service.fetch_carrier_data("INVALID_DOT")

        with self.assertRaises(InvalidDOTNumberException):
            self.service.fetch_carrier_data("-123")

    @patch('requests.get')
    def test_fmcsa_api_error(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=MagicMock(status_code=500)
        )
        mock_get.return_value = mock_resp

        with self.assertRaises(FMCSAServiceException):
            self.service.fetch_carrier_data(self.dot)

    @patch('requests.get')
    def test_fmcsa_timeout(self, mock_get):
        mock_get.side_effect = requests.exceptions.Timeout()

        with self.assertRaises(FMCSAConnectionException):
            self.service.fetch_carrier_data(self.dot)

    def test_mc_number_extraction(self):
        # Case 1: Prefix MC and digits
        prefix, num = self.service._parse_mc_info(
            {"content": [{"prefix": "MC", "docketNumber": "MC 1670397"}]}, {}
        )
        self.assertEqual(prefix, "MC")
        self.assertEqual(num, 1670397)

        # Case 2: String in carrier object
        prefix, num = self.service._parse_mc_info(
            {"content": []}, {"docketNumber": "FF-987654"}
        )
        self.assertEqual(prefix, "FF")
        self.assertEqual(num, 987654)


class CarrierAPIViewTestCase(TestCase):
    """Integration test suite for Carrier GET API View."""

    def setUp(self):
        self.url = f"/api/carriers/4202109/"

    @patch.object(FMCSAService, 'fetch_carrier_data')
    def test_api_successful_lookup(self, mock_fetch):
        mock_fetch.return_value = {
            "dot_number": 4202109,
            "mc_number": 1670397,
            "mc_prefix": "MC",
            "legal_name": "RP TRANSPORT LLC",
            "dba_name": None,
            "allowed_to_operate": True,
            "carrier_operation_code": "C",
            "carrier_operation_description": "Interstate",
            "common_authority_status": "A",
            "contract_authority_status": "N",
            "broker_authority_status": "N",
            "authorized_for_property": True,
            "authorized_for_broker": False,
            "authorized_for_household_goods": False,
            "authorized_for_passenger": False,
            "phy_street": "123 MAIN ST",
            "phy_city": "MISSION",
            "phy_state": "TX",
            "phy_zipcode": "78573",
            "phy_country": "US",
            "total_drivers": 5,
            "total_power_units": 3,
            "bipd_insurance_on_file": "Y",
            "bipd_insurance_required": "Y",
            "bipd_required_amount": 750000,
            "cargo_insurance_on_file": "N",
            "cargo_insurance_required": "N",
            "bond_insurance_on_file": "N",
            "bond_insurance_required": "N",
            "crash_total": 0,
            "fatal_crash": 0,
            "inj_crash": 0,
            "towaway_crash": 0,
            "driver_insp": 10,
            "driver_oos_insp": 1,
            "driver_oos_rate": 10.0,
            "driver_oos_rate_national_average": 5.5,
            "vehicle_insp": 15,
            "vehicle_oos_insp": 2,
            "vehicle_oos_rate": 13.3,
            "vehicle_oos_rate_national_average": 20.1,
            "hazmat_insp": 0,
            "hazmat_oos_insp": 0,
            "hazmat_oos_rate": None,
            "hazmat_oos_rate_national_average": None,
            "safety_rating": "SATISFACTORY",
            "safety_rating_date": "2022-01-15",
            "oos_date": None,
            "status_code": "A",
            "operation_classification": ["Authorized For Hire"],
            "cargo_carried": ["General Freight"]
        }

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['carrier']['dot_number'], 4202109)
        self.assertEqual(response.data['carrier']['legal_name'], "RP TRANSPORT LLC")
        
        # Verify saved in database
        self.assertTrue(Carrier.objects.filter(dot_number=4202109).exists())

    def test_api_invalid_dot_number(self):
        response = self.client.get('/api/carriers/invalid_dot/')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['error'], "Invalid DOT number")

    @patch.object(FMCSAService, 'fetch_carrier_data')
    def test_api_carrier_not_found(self, mock_fetch):
        mock_fetch.side_effect = CarrierNotFoundException("Carrier not found")

        response = self.client.get('/api/carriers/999999999/')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['error'], "Carrier not found")

    @patch.object(FMCSAService, 'fetch_carrier_data')
    def test_api_fmcsa_unavailable(self, mock_fetch):
        mock_fetch.side_effect = FMCSAConnectionException("Service unavailable")

        response = self.client.get('/api/carriers/4202109/')

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['error'], "FMCSA service temporarily unavailable")


class CompanyCensusServiceTestCase(TestCase):
    """Unit test suite for CompanyCensusService."""

    def setUp(self):
        self.service = CompanyCensusService()

    @patch('requests.post')
    def test_search_by_mc_range_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "docket1prefix": "MC",
                "docket1": "1670008",
                "dot_number": "4202109",
                "legal_name": "RP TRANSPORT LLC",
                "phone": "9569971090",
                "email_address": "rptransport3399@yahoo.com",
                "company_officer_1": "RAUL PEREZ",
                "status_code": "A",
                "docket1_status_code": "A",
                "classdef": "AUTHORIZED FOR HIRE",
                "power_units": "3",
                "total_drivers": "5",
                "phy_street": "123 MAIN ST",
                "phy_city": "MISSION",
                "phy_state": "TX",
                "phy_zip": "78573",
                "phy_country": "US"
            },

            {
                "docket1prefix": "MC",
                "docket1": "1670009",
                "dot_number": "3074232",
                "legal_name": "ROLANDO BARRIENTES",
                "phone": "9563783115",
                "email_address": "rct2truckingllc@yahoo.com",
                "company_officer_1": "ROLANDO BARRIENTES",
                "status_code": "A",
                "docket1_status_code": "A",
                "classdef": "AUTHORIZED FOR HIRE",
                "power_units": "1",
                "total_drivers": "1",
                "phy_street": "456 OAK AVE",
                "phy_city": "MCALLEN",
                "phy_state": "TX",
                "phy_zip": "78501",
                "phy_country": "US"
            }
        ]
        mock_post.return_value = mock_response

        results = self.service.search_by_mc_range(1670008, 1670009)

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["mc_number"], "MC1670008")
        self.assertEqual(results[0]["dot_number"], "4202109")
        self.assertEqual(results[0]["company_name"], "RP TRANSPORT LLC")
        self.assertEqual(results[0]["phone"], "9569971090")
        self.assertEqual(results[0]["email"], "rptransport3399@yahoo.com")
        self.assertEqual(results[0]["officer_name"], "RAUL PEREZ")
        self.assertEqual(results[0]["power_units"], 3)
        self.assertEqual(results[0]["drivers"], 5)
        self.assertEqual(results[0]["address"]["city"], "MISSION")
        self.assertEqual(results[0]["address"]["state"], "TX")
        self.assertTrue(results[0]["is_active_carrier"])
        self.assertTrue(results[0]["is_active_authority"])

    @patch('requests.post')
    def test_search_by_mc_range_active_only_filtering(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "docket1prefix": "MC",
                "docket1": "1670008",
                "dot_number": "4202109",
                "legal_name": "ACTIVE CARRIER LLC",
                "status_code": "A",
                "docket1_status_code": "A"
            },
            {
                "docket1prefix": "MC",
                "docket1": "1670009",
                "dot_number": "3074232",
                "legal_name": "INACTIVE DOCKET CARRIER",
                "status_code": "A",
                "docket1_status_code": "I"
            },
            {
                "docket1prefix": "MC",
                "docket1": "1670012",
                "dot_number": "4291686",
                "legal_name": "INACTIVE USDOT CARRIER",
                "status_code": "I",
                "docket1_status_code": "A"
            }
        ]
        mock_post.return_value = mock_response

        # Active only (default)
        active_results = self.service.search_by_mc_range(1670008, 1670012, active_only=True)
        self.assertEqual(len(active_results), 1)
        self.assertEqual(active_results[0]["company_name"], "ACTIVE CARRIER LLC")
        self.assertEqual(active_results[0]["mc_number"], "MC1670008")

        # All records (active_only=False)
        all_results = self.service.search_by_mc_range(1670008, 1670012, active_only=False)
        self.assertEqual(len(all_results), 3)

    def test_invalid_mc_range(self):
        with self.assertRaises(InvalidMCRangeException):
            self.service.search_by_mc_range(1670050, 1670008)

        with self.assertRaises(InvalidMCRangeException):
            self.service.search_by_mc_range("invalid", "1670008")

    @patch('requests.post')
    def test_connection_error(self, mock_post):
        mock_post.side_effect = requests.exceptions.Timeout("Timed out")
        with self.assertRaises(CompanyCensusConnectionException):
            self.service.search_by_mc_range(1670008, 1670052)

    @patch.object(FMCSAService, 'fetch_essential_carrier_data')
    @patch('requests.post')
    def test_qcmobile_verification_success(self, mock_post, mock_qc_fetch):
        # Mock Census SODA POST response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "docket1prefix": "MC",
                "docket1": "1670008",
                "dot_number": "4202109",
                "legal_name": "RP TRANSPORT LLC",
                "phone": "9569971090",
                "email_address": "rptransport3399@yahoo.com",
                "company_officer_1": "RAUL PEREZ",
                "status_code": "A",
                "docket1_status_code": "A",
                "classdef": "AUTHORIZED FOR HIRE",
                "power_units": "3",
                "total_drivers": "5",
                "owntract": "3",
                "owntrail": "3"
            }
        ]
        mock_post.return_value = mock_response

        # Mock QCMobile response
        mock_qc_fetch.return_value = {
            "dot_number": 4202109,
            "legal_name": "RP TRANSPORT LLC",
            "allowed_to_operate": True,
            "common_authority_status": "A",
            "contract_authority_status": "N",
            "broker_authority_status": "N",
            "authorized_for_property": True,
            "bipd_insurance_on_file": "Y",
            "bipd_insurance_required": "Y",
            "bipd_required_amount": 750000,
            "safety_rating": "SATISFACTORY",
            "safety_rating_date": "2022-01-15",
            "total_power_units": 3,
            "total_drivers": 5
        }

        results = self.service.search_by_mc_range(1670008, 1670008, active_only=True, verify_qcmobile=True)

        self.assertEqual(len(results), 1)
        res = results[0]

        # Verify QCMobile verified flag
        self.assertTrue(res["qcmobile_verified"])
        self.assertIsNone(res["qcmobile_error"])

        # Verify Census authoritative fields preserved
        self.assertEqual(res["email"], "rptransport3399@yahoo.com")
        self.assertEqual(res["officer_name"], "RAUL PEREZ")
        self.assertEqual(res["mc_number"], "MC1670008")
        self.assertEqual(res["equipment_type"], "Tractor-Trailer")

        # Verify QCMobile enriched fields
        self.assertEqual(res["authority"]["common"], "A")
        self.assertTrue(res["authority"]["authorized_for_property"])
        self.assertEqual(res["insurance"]["bipd_on_file"], "Y")
        self.assertEqual(res["insurance"]["bipd_required_amount"], 750000)

    @patch.object(FMCSAService, 'fetch_essential_carrier_data')
    @patch('requests.post')
    def test_qcmobile_verification_failure_preserves_census(self, mock_post, mock_qc_fetch):
        # Mock Census SODA POST response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "docket1prefix": "MC",
                "docket1": "1670008",
                "dot_number": "4202109",
                "legal_name": "RP TRANSPORT LLC",
                "phone": "9569971090",
                "email_address": "rptransport3399@yahoo.com",
                "company_officer_1": "RAUL PEREZ",
                "status_code": "A",
                "docket1_status_code": "A",
                "power_units": "3",
                "total_drivers": "5",
                "owntract": "3",
                "owntrail": "3"
            }
        ]

        mock_post.return_value = mock_response

        # Mock QCMobile failing with timeout
        mock_qc_fetch.side_effect = FMCSAConnectionException("FMCSA service connection timed out")

        results = self.service.search_by_mc_range(1670008, 1670008, active_only=True, verify_qcmobile=True)

        self.assertEqual(len(results), 1)
        res = results[0]

        # Verification failed flag & error recorded
        self.assertFalse(res["qcmobile_verified"])
        self.assertEqual(res["qcmobile_error"], "FMCSA service connection timed out")

        # ALL Company Census data remains completely intact
        self.assertEqual(res["mc_number"], "MC1670008")
        self.assertEqual(res["dot_number"], "4202109")
        self.assertEqual(res["company_name"], "RP TRANSPORT LLC")
        self.assertEqual(res["email"], "rptransport3399@yahoo.com")
        self.assertEqual(res["officer_name"], "RAUL PEREZ")
        self.assertEqual(res["phone"], "9569971090")
        self.assertEqual(res["equipment_type"], "Tractor-Trailer")
        self.assertEqual(res["fleet_size"], "Multi Trucks")
        self.assertEqual(res["power_units"], 3)
        self.assertEqual(res["drivers"], 5)



class EquipmentClassificationTestCase(TestCase):
    """Unit test suite for DispatchLens Equipment & Fleet Classification logic."""

    def test_rule1_broker_dispatch(self):
        # Case A: Official FMCSA carship 'B' indicates broker
        item_carship = {"carship": "B", "power_units": 0}
        res_carship = classify_equipment(item_carship)
        self.assertEqual(res_carship["equipment_type"], "Broker / Dispatch")
        self.assertTrue(res_carship["is_broker"])
        self.assertEqual(res_carship["fleet_size"], "Zero Units")

        # Case B: Broker keyword in legal name
        item_name = {"legal_name": "APEX FREIGHT BROKERAGE LLC", "power_units": 0}
        res_name = classify_equipment(item_name)
        self.assertEqual(res_name["equipment_type"], "Broker / Dispatch")
        self.assertTrue(res_name["is_broker"])

        # Case C: Zero power units ALONE does not prove broker or dispatcher
        item_carrier = {"legal_name": "SMITH TRUCKING LLC", "power_units": 0, "owntract": 0, "owntruck": 0}
        res_carrier = classify_equipment(item_carrier)
        self.assertEqual(res_carrier["equipment_type"], "General Carrier")
        self.assertFalse(res_carrier["is_broker"])
        self.assertEqual(res_carrier["fleet_size"], "Zero Units")

    def test_rule2_hotshot(self):
        # Case A: Keyword in name
        item1 = {"legal_name": "ABC HOTSHOT LLC", "power_units": 1, "owntract": 1, "owntrail": 1}
        res1 = classify_equipment(item1)
        self.assertEqual(res1["equipment_type"], "Hotshot")
        self.assertEqual(res1["fleet_size"], "Single Unit")

        # Case B: Straight truck + trailer + no tractors
        item2 = {"legal_name": "S&K HAULING LLC", "power_units": 1, "owntruck": 1, "owntrail": 1, "owntract": 0}
        res2 = classify_equipment(item2)
        self.assertEqual(res2["equipment_type"], "Hotshot")
        self.assertEqual(res2["fleet_size"], "Single Unit")

    def test_rule3_power_only(self):
        item = {"legal_name": "GSA TRANSPORT LLC", "power_units": 1, "owntract": 1, "owntrail": 0}
        res = classify_equipment(item)
        self.assertEqual(res["equipment_type"], "Power Only")
        self.assertEqual(res["fleet_size"], "Single Unit")

    def test_rule4_box_truck(self):
        item = {"legal_name": "JARHEAD TRANSPORT LLC", "power_units": 1, "owntruck": 1, "owntract": 0, "owntrail": 0}
        res = classify_equipment(item)
        self.assertEqual(res["equipment_type"], "Box Truck")
        self.assertEqual(res["fleet_size"], "Single Unit")

    def test_rule5_big_equipment(self):
        # Case A: Cargo flag active with "X" or "Y"
        item1 = {"legal_name": "HEAVY MOVING LLC", "power_units": 3, "owntract": 3, "owntrail": 3, "crgo_machlrg": "X"}
        res1 = classify_equipment(item1)
        self.assertEqual(res1["equipment_type"], "Big Equipment")
        self.assertEqual(res1["fleet_size"], "Multi Trucks")

        # Case B: Cargo description keyword
        item2 = {"legal_name": "RP TRANSPORT LLC", "power_units": 3, "owntract": 3, "owntrail": 3, "crgo_cargoothr_desc": "OIL FIELD EQUIPMENT"}
        res2 = classify_equipment(item2)
        self.assertEqual(res2["equipment_type"], "Big Equipment")
        self.assertEqual(res2["fleet_size"], "Multi Trucks")

    def test_rule6_tractor_trailer(self):
        item = {"legal_name": "DDP CARGO INC", "power_units": 2, "owntract": 2, "owntrail": 2}
        res = classify_equipment(item)
        self.assertEqual(res["equipment_type"], "Tractor-Trailer")
        self.assertEqual(res["fleet_size"], "Multi Trucks")

    def test_rule7_general_carrier(self):
        item = {"legal_name": "ROZSCO TOURS LLC", "power_units": 3, "owntract": 0, "owntrail": 0, "owntruck": 0}
        res = classify_equipment(item)
        self.assertEqual(res["equipment_type"], "General Carrier")
        self.assertEqual(res["fleet_size"], "Multi Trucks")


class CarrierSearchRangeAPIViewTestCase(TestCase):
    """Unit test suite for public GET /api/carriers/search/ REST API Endpoint."""

    def setUp(self):
        self.url = '/api/carriers/search/'

    @patch.object(CompanyCensusService, 'search_by_mc_range')
    def test_valid_search_range(self, mock_search):
        mock_search.return_value = {
            "results": [
                {
                    "mc_number": "MC1670008",
                    "dot_number": "4202109",
                    "company_name": "RP TRANSPORT LLC",
                    "phone": "9569971090",
                    "email": "rptransport3399@yahoo.com",
                    "officer_name": "RAUL PEREZ",
                    "status": "A",
                    "docket_status": "A",
                    "is_active_carrier": True,
                    "is_active_authority": True,
                    "allowed_to_operate": True,
                    "equipment_type": "Big Equipment",
                    "fleet_size": "Multi Trucks",
                    "power_units": 3,
                    "drivers": 5,
                    "address": {
                        "street": "908 W LA POINTE AVE APT 4",
                        "city": "MISSION",
                        "state": "TX",
                        "zip": "78573",
                        "country": "US"
                    },
                    "authority": {},
                    "insurance": {},
                    "inspections": {},
                    "crashes": {},
                    "safety_rating": {},
                    "qcmobile_verified": False,
                    "qcmobile_error": None
                }
            ],
            "meta": {
                "census_request_count": 1,
                "qcmobile_request_count": 0,
                "qcmobile_successes": 0,
                "qcmobile_failures": 0,
                "total_response_time_ms": 50.0
            }
        }

        response = self.client.get(f"{self.url}?start_mc=1670008&end_mc=1670052")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["start_mc"], 1670008)
        self.assertEqual(response.data["end_mc"], 1670052)
        self.assertIn("meta", response.data)
        self.assertEqual(response.data["meta"]["census_request_count"], 1)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["mc_number"], "MC1670008")
        mock_search.assert_called_once_with(start_mc=1670008, end_mc=1670052, active_only=True, verify_qcmobile=False, return_meta=True)

    @patch.object(CompanyCensusService, 'search_by_mc_range')
    def test_mc_prefix_normalization(self, mock_search):
        mock_search.return_value = {"results": [], "meta": {"census_request_count": 1, "qcmobile_request_count": 0, "qcmobile_successes": 0, "qcmobile_failures": 0, "total_response_time_ms": 10.0}}
        response = self.client.get(f"{self.url}?start_mc=MC1670008&end_mc=MC1670052")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["start_mc"], 1670008)
        self.assertEqual(response.data["end_mc"], 1670052)
        mock_search.assert_called_once_with(start_mc=1670008, end_mc=1670052, active_only=True, verify_qcmobile=False, return_meta=True)

    @patch.object(CompanyCensusService, 'search_by_mc_range')
    def test_mc_hyphen_prefix_normalization(self, mock_search):
        mock_search.return_value = {"results": [], "meta": {"census_request_count": 1, "qcmobile_request_count": 0, "qcmobile_successes": 0, "qcmobile_failures": 0, "total_response_time_ms": 10.0}}
        response = self.client.get(f"{self.url}?start_mc=MC-1670008&end_mc=MC-1670052")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["start_mc"], 1670008)
        self.assertEqual(response.data["end_mc"], 1670052)
        mock_search.assert_called_once_with(start_mc=1670008, end_mc=1670052, active_only=True, verify_qcmobile=False, return_meta=True)


    def test_missing_start_mc(self):
        response = self.client.get(f"{self.url}?end_mc=1670052")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])
        self.assertEqual(response.data["error"], "start_mc parameter is required")

    def test_missing_end_mc(self):
        response = self.client.get(f"{self.url}?start_mc=1670008")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])
        self.assertEqual(response.data["error"], "end_mc parameter is required")

    def test_invalid_mc_format(self):
        response = self.client.get(f"{self.url}?start_mc=abc&end_mc=1670052")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])

    def test_start_greater_than_end(self):
        response = self.client.get(f"{self.url}?start_mc=1670050&end_mc=1670008")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])

    def test_exceeds_max_range_limit(self):
        response = self.client.get(f"{self.url}?start_mc=1&end_mc=6000")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])
        self.assertIn("exceeds maximum limit", response.data["error"])


class CompanyCensusServiceDateSearchTestCase(TestCase):
    """Unit test suite for CompanyCensusService date range search functionality."""

    def setUp(self):
        self.service = CompanyCensusService()

    @patch('requests.post')
    def test_search_by_date_range_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "docket1prefix": "MC",
                "docket1": "1674851",
                "dot_number": "4202109",
                "legal_name": "START DATE CARRIER LLC",
                "phone": "9569971090",
                "email_address": "startdate@example.com",
                "company_officer_1": "JOHN START",
                "status_code": "A",
                "docket1_status_code": "A",
                "add_date": "20260920",
                "power_units": "2",
                "total_drivers": "2",
                "phy_street": "100 START ST",
                "phy_city": "DALLAS",
                "phy_state": "TX",
                "phy_zip": "75201",
                "phy_country": "US"
            },
            {
                "docket1prefix": "MC",
                "docket1": "1674852",
                "dot_number": "4202110",
                "legal_name": "END DATE BROKER LLC",
                "phone": "9569971091",
                "email_address": "enddate@example.com",
                "company_officer_1": "JANE END",
                "status_code": "A",
                "docket1_status_code": "A",
                "add_date": "20260924",
                "power_units": "0",
                "total_drivers": "0",
                "phy_street": "200 END AVE",
                "phy_city": "AUSTIN",
                "phy_state": "TX",
                "phy_zip": "78701",
                "phy_country": "US"
            }
        ]
        mock_post.return_value = mock_response

        results = self.service.search_by_date_range("2026-09-20", "2026-09-24")

        self.assertEqual(len(results), 2)
        
        # Start date record check
        self.assertEqual(results[0]["add_date"], "2026-09-20")
        self.assertEqual(results[0]["company_name"], "START DATE CARRIER LLC")
        self.assertEqual(results[0]["mc_number"], "MC1674851")
        self.assertEqual(results[0]["address"]["city"], "DALLAS")

        # End date broker record check (zero power units included)
        self.assertEqual(results[1]["add_date"], "2026-09-24")
        self.assertEqual(results[1]["company_name"], "END DATE BROKER LLC")
        self.assertEqual(results[1]["equipment_type"], "Broker / Dispatch")
        self.assertEqual(results[1]["fleet_size"], "Zero Units")
        self.assertEqual(results[1]["power_units"], 0)

    @patch('requests.post')
    def test_search_by_date_active_only_filtering(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "docket1prefix": "MC",
                "docket1": "1674851",
                "dot_number": "4202109",
                "legal_name": "ACTIVE BOTH LLC",
                "status_code": "A",
                "docket1_status_code": "A",
                "add_date": "20260920"
            },
            {
                "docket1prefix": "MC",
                "docket1": "1674852",
                "dot_number": "4202110",
                "legal_name": "INACTIVE DOCKET LLC",
                "status_code": "A",
                "docket1_status_code": "I",
                "add_date": "20260921"
            },
            {
                "docket1prefix": "MC",
                "docket1": "1674853",
                "dot_number": "4202111",
                "legal_name": "INACTIVE USDOT LLC",
                "status_code": "I",
                "docket1_status_code": "A",
                "add_date": "20260922"
            }
        ]
        mock_post.return_value = mock_response

        # Active only
        active_results = self.service.search_by_date_range("2026-09-20", "2026-09-24", active_only=True)
        self.assertEqual(len(active_results), 1)
        self.assertEqual(active_results[0]["company_name"], "ACTIVE BOTH LLC")

    def test_invalid_date_formats_and_order(self):
        with self.assertRaises(InvalidMCRangeException):
            self.service.search_by_date_range("invalid-date", "2026-09-24")

        with self.assertRaises(InvalidMCRangeException):
            self.service.search_by_date_range("2026-13-45", "2026-09-24")

        with self.assertRaises(InvalidMCRangeException):
            self.service.search_by_date_range("2026-09-25", "2026-09-20")

    @patch('requests.post')
    def test_no_matching_date_records(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_post.return_value = mock_response

        results = self.service.search_by_date_range("2026-09-01", "2026-09-02")
        self.assertEqual(len(results), 0)


class CarrierSearchDateAPIViewTestCase(TestCase):
    """Unit test suite for GET /api/carriers/search-by-date/ endpoint."""

    def setUp(self):
        self.url = '/api/carriers/search-by-date/'

    @patch.object(CompanyCensusService, 'search_by_date_range')
    def test_valid_date_range_api(self, mock_search):
        mock_search.return_value = {
            "results": [
                {
                    "mc_number": "MC1674851",
                    "dot_number": "4202109",
                    "company_name": "TEST DATE CARRIER LLC",
                    "phone": "9569971090",
                    "email": "test@example.com",
                    "officer_name": "TEST OFFICER",
                    "status": "A",
                    "docket_status": "A",
                    "is_active_carrier": True,
                    "is_active_authority": True,
                    "allowed_to_operate": True,
                    "equipment_type": "Broker / Dispatch",
                    "fleet_size": "Zero Units",
                    "power_units": 0,
                    "drivers": 0,
                    "add_date": "2026-09-20",
                    "address": {"street": "100 ST", "city": "DALLAS", "state": "TX", "zip": "75201", "country": "US"}
                }
            ],
            "meta": {
                "census_request_count": 1,
                "total_response_time_ms": 10.0
            }
        }

        response = self.client.get(f"{self.url}?start_date=2026-09-20&end_date=2026-09-24")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["start_date"], "2026-09-20")
        self.assertEqual(response.data["end_date"], "2026-09-24")
        self.assertEqual(response.data["results"][0]["company_name"], "TEST DATE CARRIER LLC")
        self.assertEqual(response.data["results"][0]["equipment_type"], "Broker / Dispatch")
        # Ensure confirmed_mc_only defaults to True
        mock_search.assert_called_with(
            start_date="2026-09-20",
            end_date="2026-09-24",
            active_only=True,
            confirmed_mc_only=True,
            verify_qcmobile=False,
            return_meta=True
        )

    @patch.object(CompanyCensusService, 'search_by_date_range')
    def test_date_range_api_with_include_usdot_only(self, mock_search):
        mock_search.return_value = {
            "results": [
                {
                    "mc_number": None,
                    "dot_number": "4202109",
                    "company_name": "USDOT ONLY LLC",
                    "status": "A",
                    "docket_status": None,
                    "is_active_carrier": True,
                    "is_active_authority": False,
                    "is_usdot_only": True,
                    "authority_status": "UNVERIFIED"
                }
            ],
            "meta": {"census_request_count": 1, "total_response_time_ms": 10.0}
        }

        response = self.client.get(f"{self.url}?start_date=2026-09-20&end_date=2026-09-24&include_usdot_only=true")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["confirmed_mc_count"], 0)
        self.assertEqual(response.data["usdot_only_count"], 1)
        mock_search.assert_called_with(
            start_date="2026-09-20",
            end_date="2026-09-24",
            active_only=True,
            confirmed_mc_only=False,
            verify_qcmobile=False,
            return_meta=True
        )

    def test_missing_start_date(self):
        response = self.client.get(f"{self.url}?end_date=2026-09-24")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "start_date parameter is required")

    def test_missing_end_date(self):
        response = self.client.get(f"{self.url}?start_date=2026-09-20")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "end_date parameter is required")

    def test_invalid_date_format(self):
        response = self.client.get(f"{self.url}?start_date=09-20-2026&end_date=2026-09-24")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid calendar date", response.data["error"])

    def test_end_date_earlier_than_start_date(self):
        response = self.client.get(f"{self.url}?start_date=2026-09-25&end_date=2026-09-20")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("cannot be greater than end_date", response.data["error"])

    @patch.object(CompanyCensusService, 'search_by_date_range')
    def test_backend_error_handling(self, mock_search):
        mock_search.side_effect = CompanyCensusConnectionException("FMCSA SODA service connection error")
        response = self.client.get(f"{self.url}?start_date=2026-09-20&end_date=2026-09-24")
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertIn("unavailable", response.data["error"])


class RegressionAuthorityAndAccuracyTestCase(TestCase):
    """
    Regression test suite specifically verifying:
    1. Missing MC numbers are never normalized as 'MC-0'
    2. Null docket status does not produce active authority
    3. Revoked authority is correctly labeled REVOKED
    4. Active USDOT without confirmed MC authority is labeled UNVERIFIED/USDOT_ONLY and excluded from confirmed results
    5. Verified active MC authority is properly identified
    6. Date search accurately separates confirmed MC carriers from USDOT-only records
    """

    def setUp(self):
        self.service = CompanyCensusService()

    def test_missing_mc_number_never_produces_mc0(self):
        # Case 1: docket1 is None
        item_none = {
            "status_code": "A",
            "docket1": None,
            "docket1prefix": "MC",
            "docket1_status_code": "A",
            "dot_number": "4001001",
            "legal_name": "NO MC CARRIER LLC"
        }
        res_none = self.service._normalize_census_record(item_none)
        self.assertIsNone(res_none["mc_number"])
        self.assertIsNone(res_none["mc_numeric"])
        self.assertNotEqual(res_none["mc_number"], "MC-0")
        self.assertNotEqual(res_none["mc_number"], "MC0")
        self.assertFalse(res_none["is_active_authority"])

        # Case 2: docket1 is string '0'
        item_zero = {
            "status_code": "A",
            "docket1": "0",
            "docket1prefix": "MC",
            "docket1_status_code": "A",
            "dot_number": "4001002",
            "legal_name": "ZERO MC CARRIER LLC"
        }
        res_zero = self.service._normalize_census_record(item_zero)
        self.assertIsNone(res_zero["mc_number"])
        self.assertIsNone(res_zero["mc_numeric"])
        self.assertNotEqual(res_zero["mc_number"], "MC-0")
        self.assertFalse(res_zero["is_active_authority"])

    def test_null_docket_status_is_unverified(self):
        item = {
            "status_code": "A",
            "docket1": "1674851",
            "docket1prefix": "MC",
            "docket1_status_code": None,
            "dot_number": "4001003",
            "legal_name": "NULL DOCKET CARRIER LLC"
        }
        res = self.service._normalize_census_record(item)
        self.assertFalse(res["is_active_authority"])
        self.assertEqual(res["authority_status"], "UNVERIFIED")
        self.assertEqual(res["record_category"], "USDOT_ONLY")
        self.assertTrue(res["is_usdot_only"])

    def test_revoked_authority_is_revoked(self):
        item = {
            "status_code": "A",
            "docket1": "1674851",
            "docket1prefix": "MC",
            "docket1_status_code": "I",
            "dot_number": "4001004",
            "legal_name": "REVOKED CARRIER LLC"
        }
        res = self.service._normalize_census_record(item)
        self.assertFalse(res["is_active_authority"])
        self.assertEqual(res["authority_status"], "REVOKED")
        self.assertEqual(res["record_category"], "REVOKED_MC")

    def test_active_usdot_without_confirmed_mc_authority(self):
        # A carrier with active USDOT but no MC operating docket (e.g. private carrier)
        item = {
            "status_code": "A",
            "docket1": None,
            "docket1prefix": None,
            "docket1_status_code": None,
            "dot_number": "4001005",
            "legal_name": "PRIVATE PROPERTY HAULER LLC"
        }
        res = self.service._normalize_census_record(item)
        self.assertTrue(res["is_active_carrier"])
        self.assertFalse(res["is_active_authority"])
        self.assertEqual(res["authority_status"], "UNVERIFIED")
        self.assertEqual(res["record_category"], "USDOT_ONLY")
        self.assertTrue(res["is_usdot_only"])
        self.assertIsNone(res["mc_number"])

    def test_verified_active_mc_authority(self):
        item = {
            "status_code": "A",
            "docket1": "1674851",
            "docket1prefix": "MC",
            "docket1_status_code": "A",
            "dot_number": "4001006",
            "legal_name": "VERIFIED MC CARRIER LLC"
        }
        res = self.service._normalize_census_record(item)
        self.assertTrue(res["is_active_carrier"])
        self.assertTrue(res["is_active_authority"])
        self.assertEqual(res["authority_status"], "ACTIVE")
        self.assertEqual(res["record_category"], "CONFIRMED_MC")
        self.assertFalse(res["is_usdot_only"])
        self.assertEqual(res["mc_number"], "MC1674851")

    @patch('requests.post')
    def test_date_search_confirmed_mc_only_filtering(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "status_code": "A",
                "docket1prefix": "MC",
                "docket1": "1674851",
                "docket1_status_code": "A",
                "dot_number": "4001001",
                "legal_name": "CONFIRMED MC 1",
                "add_date": "20260920"
            },
            {
                "status_code": "A",
                "docket1prefix": None,
                "docket1": None,
                "docket1_status_code": None,
                "dot_number": "4001002",
                "legal_name": "USDOT ONLY 1",
                "add_date": "20260920"
            }
        ]
        mock_post.return_value = mock_response

        # When confirmed_mc_only=True (default), USDOT-only record with no MC is excluded
        results = self.service.search_by_date_range("2026-09-20", "2026-09-24", confirmed_mc_only=True)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["company_name"], "CONFIRMED MC 1")
        self.assertEqual(results[0]["mc_number"], "MC1674851")
        self.assertTrue(results[0]["is_active_authority"])

        # When confirmed_mc_only=False, both are returned with proper categorization
        all_results = self.service.search_by_date_range("2026-09-20", "2026-09-24", confirmed_mc_only=False)
        self.assertEqual(len(all_results), 2)
        self.assertTrue(all_results[0]["is_active_authority"])
        self.assertFalse(all_results[1]["is_active_authority"])
        self.assertIsNone(all_results[1]["mc_number"])
        self.assertEqual(all_results[1]["authority_status"], "UNVERIFIED")





