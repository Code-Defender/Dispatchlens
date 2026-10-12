import os
import re
import time
import logging
import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from .equipment_classifier import classify_equipment
from .fmcsa_service import FMCSAService, FMCSAServiceException

logger = logging.getLogger(__name__)

COMPANY_CENSUS_API_URL = "https://data.transportation.gov/api/v3/views/az4n-8mr2/query.json"
DEFAULT_TIMEOUT = 30  # seconds


class CompanyCensusException(Exception):
    """Base exception for Company Census Service errors."""
    pass


class InvalidMCRangeException(CompanyCensusException):
    """Raised when provided MC range or date range is invalid."""
    pass


class CompanyCensusConnectionException(CompanyCensusException):
    """Raised when connection to FMCSA SODA API fails."""
    pass


class CompanyCensusService:
    """
    Dedicated service for searching the official FMCSA Company Census dataset (az4n-8mr2)
    by MC number range or carrier registration add_date range via the SODA v3 query endpoint
    with carrier status filtering and optional controlled-concurrency QCMobile API verification enrichment.
    """

    def __init__(self, api_url=None, app_token=None, timeout=DEFAULT_TIMEOUT, fmcsa_service=None):
        self.api_url = api_url or COMPANY_CENSUS_API_URL
        self.app_token = app_token or os.getenv('SOCRATA_APP_TOKEN') or os.getenv('FMCSA_CENSUS_APP_TOKEN')
        self.timeout = timeout
        self.fmcsa_service = fmcsa_service

    def _get_fmcsa_service(self):
        if self.fmcsa_service is None:
            self.fmcsa_service = FMCSAService()
        return self.fmcsa_service

    def _get_headers(self):
        headers = {"Content-Type": "application/json"}
        if self.app_token:
            headers["X-App-Token"] = self.app_token
        return headers

    def _parse_mc_input(self, mc_val):
        """Extracts integer value from MC string or int."""
        if mc_val is None:
            return None
        digits = re.sub(r'\D', '', str(mc_val).strip())
        if not digits:
            return None
        return int(digits)

    def _parse_date_input(self, date_val):
        """
        Parses and validates a date input (YYYY-MM-DD or YYYYMMDD).
        Returns tuple: (soda_date_str "YYYYMMDD", iso_date_str "YYYY-MM-DD", datetime.date object).
        """
        if not date_val:
            return None
        val_str = str(date_val).strip()
        digits = re.sub(r'\D', '', val_str)
        if len(digits) != 8:
            raise InvalidMCRangeException(f"Invalid date format: {date_val}. Expected YYYY-MM-DD")
        try:
            dt = datetime.strptime(digits, "%Y%m%d").date()
            iso_str = dt.strftime("%Y-%m-%d")
            return digits, iso_str, dt
        except ValueError:
            raise InvalidMCRangeException(f"Invalid calendar date: {date_val}")

    def _parse_int(self, val):
        if val is None or val == '':
            return 0
        try:
            return int(val)
        except (ValueError, TypeError):
            return 0

    def search_by_mc_range(self, start_mc, end_mc, max_records=1000, active_only=True, verify_qcmobile=False, return_meta=False):
        """
        Executes a SODA v3 query for carriers within the given MC number range.
        If active_only is True, filters to return carriers with status_code='A'
        (active entity) and docket1_status_code='A' (active MC authority).
        """
        start_time = time.time()
        start_int = self._parse_mc_input(start_mc)
        end_int = self._parse_mc_input(end_mc)

        if start_int is None or end_int is None:
            raise InvalidMCRangeException(f"Invalid MC range input: start_mc={start_mc}, end_mc={end_mc}")

        if start_int > end_int:
            raise InvalidMCRangeException(f"start_mc ({start_int}) cannot be greater than end_mc ({end_int})")

        query_str = (
            f"SELECT * WHERE docket1prefix = 'MC' "
            f"AND docket1::number >= {start_int} "
            f"AND docket1::number <= {end_int} "
            f"ORDER BY docket1::number"
        )

        return self._execute_soda_query(
            query_str=query_str,
            max_records=max_records,
            active_only=active_only,
            confirmed_mc_only=active_only,
            verify_qcmobile=verify_qcmobile,
            return_meta=return_meta,
            start_time=start_time
        )

    def search_by_date_range(self, start_date, end_date, max_records=1000, active_only=True, confirmed_mc_only=True, verify_qcmobile=False, return_meta=False):
        """
        Executes a SODA v3 query for carriers added/registered within the given date range
        using the official FMCSA Census add_date field.
        If confirmed_mc_only is True (default), filters for carriers with confirmed active MC authority
        (status_code='A', docket1prefix='MC', and docket1_status_code='A').
        """
        start_time = time.time()
        start_parsed = self._parse_date_input(start_date)
        end_parsed = self._parse_date_input(end_date)

        if not start_parsed:
            raise InvalidMCRangeException("start_date parameter is required")
        if not end_parsed:
            raise InvalidMCRangeException("end_date parameter is required")

        start_soda, start_iso, start_dt = start_parsed
        end_soda, end_iso, end_dt = end_parsed

        if start_dt > end_dt:
            raise InvalidMCRangeException(f"start_date ({start_iso}) cannot be greater than end_date ({end_iso})")

        if confirmed_mc_only:
            query_str = (
                f"SELECT * WHERE status_code = 'A' "
                f"AND docket1prefix = 'MC' "
                f"AND docket1_status_code = 'A' "
                f"AND add_date >= '{start_soda}' "
                f"AND add_date <= '{end_soda}' "
                f"ORDER BY add_date DESC"
            )
        else:
            query_str = (
                f"SELECT * WHERE status_code = 'A' "
                f"AND add_date >= '{start_soda}' "
                f"AND add_date <= '{end_soda}' "
                f"ORDER BY add_date DESC"
            )

        return self._execute_soda_query(
            query_str=query_str,
            max_records=max_records,
            active_only=active_only,
            confirmed_mc_only=confirmed_mc_only,
            verify_qcmobile=verify_qcmobile,
            return_meta=return_meta,
            start_time=start_time
        )

    def _execute_soda_query(self, query_str, max_records=1000, active_only=True, confirmed_mc_only=False, verify_qcmobile=False, return_meta=False, start_time=None):
        """
        Internal execution helper for pagination, raw JSON response parsing, carrier normalization,
        active status filtering, and optional QCMobile enrichment.
        """
        if start_time is None:
            start_time = time.time()

        all_records = []
        page_number = 1
        page_size = min(100, max_records)

        census_request_count = 0
        qcmobile_request_count = 0
        qcmobile_successes = 0
        qcmobile_failures = 0

        while len(all_records) < max_records:
            payload = {
                "query": query_str,
                "page": {
                    "pageNumber": page_number,
                    "pageSize": page_size
                },
                "includeSynthetic": False
            }

            try:
                census_request_count += 1
                response = requests.post(
                    self.api_url,
                    headers=self._get_headers(),
                    json=payload,
                    timeout=self.timeout
                )
                response.raise_for_status()
                raw_data = response.json()
            except requests.exceptions.Timeout as err:
                logger.error("FMCSA Company Census request timed out")
                raise CompanyCensusConnectionException("Company Census API request timed out") from err
            except requests.exceptions.RequestException as err:
                logger.error(f"FMCSA Company Census API request failed: {err}")
                raise CompanyCensusConnectionException("Company Census API temporarily unavailable") from err
            except ValueError as err:
                logger.error("Failed to parse JSON response from Company Census API")
                raise CompanyCensusException("Invalid JSON response from Company Census API") from err

            records = []
            if isinstance(raw_data, list):
                records = raw_data
            elif isinstance(raw_data, dict):
                records = raw_data.get("results") or raw_data.get("data") or raw_data.get("rows") or []

            if not records:
                break

            all_records.extend(records)

            if len(records) < page_size:
                break

            page_number += 1

        # Normalize and filter records
        qualified_census_records = []
        for item in all_records:
            sc = (item.get("status_code") or "").strip().upper()
            dsc = (item.get("docket1_status_code") or "").strip().upper()
            docket_raw = item.get("docket1")
            has_mc = bool(docket_raw and re.sub(r'\D', '', str(docket_raw)) not in ["", "0"])

            if active_only and sc != "A":
                continue

            if confirmed_mc_only:
                if sc != "A" or dsc != "A" or not has_mc:
                    continue

            census_norm = self._normalize_census_record(item)
            qualified_census_records.append(census_norm)
            if len(qualified_census_records) >= max_records:
                break

        # Optional QCMobile verification with controlled concurrency
        final_normalized_records = []

        if verify_qcmobile and qualified_census_records:
            def verify_single_carrier(census_norm):
                dot_val = census_norm.get("dot_number")
                qc_data = None
                qc_error = None
                if dot_val and str(dot_val).isdigit() and int(dot_val) > 0:
                    try:
                        fmcsa_svc = self._get_fmcsa_service()
                        qc_data = fmcsa_svc.fetch_essential_carrier_data(dot_val)
                    except Exception as err:
                        logger.warning(f"QCMobile verification failed for DOT {dot_val}: {err}")
                        qc_error = str(err)
                else:
                    qc_error = f"Invalid DOT number: {dot_val}"

                merged = self._merge_census_and_qcmobile(census_norm, qc_data=qc_data, qc_error=qc_error)
                return merged, (qc_data is not None and not qc_error)

            qcmobile_request_count = len(qualified_census_records)

            with ThreadPoolExecutor(max_workers=min(5, len(qualified_census_records))) as executor:
                futures = [executor.submit(verify_single_carrier, rec) for rec in qualified_census_records]
                for future in futures:
                    final_rec, is_success = future.result()
                    final_normalized_records.append(final_rec)
                    if is_success:
                        qcmobile_successes += 1
                    else:
                        qcmobile_failures += 1
        else:
            final_normalized_records = qualified_census_records

        elapsed_ms = round((time.time() - start_time) * 1000, 2)

        meta = {
            "census_request_count": census_request_count,
            "qcmobile_request_count": qcmobile_request_count,
            "qcmobile_successes": qcmobile_successes,
            "qcmobile_failures": qcmobile_failures,
            "total_response_time_ms": elapsed_ms
        }

        if return_meta:
            return {
                "results": final_normalized_records,
                "meta": meta
            }

        return final_normalized_records

    def _normalize_census_record(self, item):
        """
        Normalizes a single FMCSA Company Census raw API record into a standardized dictionary.
        """
        def format_date_str(val):
            if not val:
                return None
            s = str(val).strip()
            digits = re.sub(r'\D', '', s)
            if len(digits) == 8:
                return f"{digits[:4]}-{digits[4:6]}-{digits[6:]}"
            return s

        mc_raw = item.get("docket1")
        mc_prefix = (item.get("docket1prefix") or "").strip().upper()
        if not mc_prefix or mc_prefix in ["NONE", "NULL"]:
            mc_prefix = "MC"

        mc_str = str(mc_raw).strip() if mc_raw is not None else ""
        mc_digits = re.sub(r'\D', '', mc_str)

        # Never convert missing or '0' MC number to 'MC-0'
        if mc_digits and mc_digits != "0":
            mc_number = f"{mc_prefix}{mc_digits}"
            mc_numeric = int(mc_digits)
        else:
            mc_number = None
            mc_numeric = None

        dot_raw = item.get("dot_number")
        dot_str = str(dot_raw).strip() if dot_raw is not None else ""
        dot_digits = re.sub(r'\D', '', dot_str)
        dot_number = dot_digits if dot_digits else None

        status_code = (item.get("status_code") or "").strip().upper()
        docket_status_code = (item.get("docket1_status_code") or "").strip().upper()

        classification = classify_equipment(item)

        is_active_carrier = (status_code == "A")
        # Do not set is_active_authority = True solely because status_code = 'A'
        # Confirmed active MC authority requires docket status 'A' and a valid MC number
        is_active_authority = (docket_status_code == "A" and bool(mc_number))

        if is_active_authority:
            authority_status = "ACTIVE"
            record_category = "CONFIRMED_MC"
        elif docket_status_code == "I":
            authority_status = "REVOKED"
            record_category = "REVOKED_MC"
        elif docket_status_code == "P":
            authority_status = "PENDING"
            record_category = "PENDING_MC"
        elif is_active_carrier:
            authority_status = "UNVERIFIED"
            record_category = "USDOT_ONLY"
        else:
            authority_status = "INACTIVE"
            record_category = "INACTIVE"

        return {
            "mc_number": mc_number,
            "mc_numeric": mc_numeric,
            "dot_number": dot_number,
            "company_name": (item.get("legal_name") or "").strip(),
            "phone": (item.get("phone") or "").strip(),
            "email": (item.get("email_address") or "").strip(),
            "officer_name": (item.get("company_officer_1") or "").strip(),
            "add_date": format_date_str(item.get("add_date")),
            "mcs150_date": format_date_str(item.get("mcs150_date")),
            "status": status_code,
            "docket_status": docket_status_code or None,
            "is_active_carrier": is_active_carrier,
            "is_active_authority": is_active_authority,
            "authority_status": authority_status,
            "record_category": record_category,
            "is_usdot_only": record_category == "USDOT_ONLY",
            "is_broker": classification["is_broker"],
            "business_category": classification.get("business_category", "Motor Carrier"),
            "authority_class": (item.get("classdef") or "").strip(),
            "carrier_operation": (item.get("carrier_operation") or "").strip(),
            "equipment_type": classification["equipment_type"],
            "fleet_size": classification["fleet_size"],
            "power_units": self._parse_int(item.get("power_units")),
            "drivers": self._parse_int(item.get("total_drivers")),
            "address": {
                "street": (item.get("phy_street") or "").strip(),
                "city": (item.get("phy_city") or "").strip(),
                "state": (item.get("phy_state") or "").strip(),
                "zip": (item.get("phy_zip") or "").strip(),
                "country": (item.get("phy_country") or "").strip()
            },
            "authority": {
                "common": None,
                "contract": None,
                "broker": None,
                "authorized_for_property": None,
                "authorized_for_broker": None,
                "authorized_for_household_goods": None,
                "authorized_for_passenger": None
            },
            "insurance": {
                "bipd_on_file": None,
                "bipd_required": None,
                "bipd_required_amount": None,
                "cargo_on_file": None,
                "cargo_required": None,
                "bond_on_file": None,
                "bond_required": None
            },
            "inspections": {
                "driver_insp": None,
                "driver_oos_insp": None,
                "driver_oos_rate": None,
                "driver_oos_rate_national_average": None,
                "vehicle_insp": None,
                "vehicle_oos_insp": None,
                "vehicle_oos_rate": None,
                "vehicle_oos_rate_national_average": None,
                "hazmat_insp": None,
                "hazmat_oos_insp": None,
                "hazmat_oos_rate": None,
                "hazmat_oos_rate_national_average": None
            },
            "crashes": {
                "total": None,
                "fatal": None,
                "injury": None,
                "towaway": None
            },
            "safety_rating": {
                "rating": None,
                "rating_date": None,
                "oos_date": None
            },
            "qcmobile_verified": False,
            "qcmobile_error": None
        }

    def _merge_census_and_qcmobile(self, census_record, qc_data=None, qc_error=None):
        """
        Merges Company Census normalized data with QCMobile API response following field authority rules:
        - Company Census is authoritative for: email, officer_name, mc_number, equipment_type, fleet_size
        - QCMobile is primary for: authority, insurance, inspections, crashes, safety rating, live allowed_to_operate
        - Fallbacks/shared: company_name, phone, address, power_units, drivers
        """
        has_qc = qc_data is not None and not qc_error

        mc_number = census_record.get("mc_number") or ""
        dot_number = census_record.get("dot_number") or (str(qc_data.get("dot_number")) if has_qc and qc_data.get("dot_number") else "")
        company_name = (qc_data.get("legal_name") if has_qc and qc_data.get("legal_name") else census_record.get("company_name")) or ""
        phone = (census_record.get("phone") or (qc_data.get("phone") if has_qc and qc_data.get("phone") else "")) or ""
        email = census_record.get("email") or ""  # Census authoritative
        officer_name = census_record.get("officer_name") or ""  # Census authoritative

        addr_street = (qc_data.get("phy_street") if has_qc and qc_data.get("phy_street") else census_record["address"].get("street")) or ""
        addr_city = (qc_data.get("phy_city") if has_qc and qc_data.get("phy_city") else census_record["address"].get("city")) or ""
        addr_state = (qc_data.get("phy_state") if has_qc and qc_data.get("phy_state") else census_record["address"].get("state")) or ""
        addr_zip = (qc_data.get("phy_zipcode") if has_qc and qc_data.get("phy_zipcode") else census_record["address"].get("zip")) or ""
        addr_country = (qc_data.get("phy_country") if has_qc and qc_data.get("phy_country") else census_record["address"].get("country")) or ""

        authority_info = {
            "common": qc_data.get("common_authority_status") if has_qc else None,
            "contract": qc_data.get("contract_authority_status") if has_qc else None,
            "broker": qc_data.get("broker_authority_status") if has_qc else None,
            "authorized_for_property": qc_data.get("authorized_for_property") if has_qc else None,
            "authorized_for_broker": qc_data.get("authorized_for_broker") if has_qc else None,
            "authorized_for_household_goods": qc_data.get("authorized_for_household_goods") if has_qc else None,
            "authorized_for_passenger": qc_data.get("authorized_for_passenger") if has_qc else None,
        }

        allowed_to_operate = qc_data.get("allowed_to_operate") if (has_qc and qc_data.get("allowed_to_operate") is not None) else (census_record.get("status") == "A")

        insurance_info = {
            "bipd_on_file": qc_data.get("bipd_insurance_on_file") if has_qc else None,
            "bipd_required": qc_data.get("bipd_insurance_required") if has_qc else None,
            "bipd_required_amount": qc_data.get("bipd_required_amount") if has_qc else None,
            "cargo_on_file": qc_data.get("cargo_insurance_on_file") if has_qc else None,
            "cargo_required": qc_data.get("cargo_insurance_required") if has_qc else None,
            "bond_on_file": qc_data.get("bond_insurance_on_file") if has_qc else None,
            "bond_required": qc_data.get("bond_insurance_required") if has_qc else None,
        }

        inspections_info = {
            "driver_insp": qc_data.get("driver_insp") if has_qc else None,
            "driver_oos_insp": qc_data.get("driver_oos_insp") if has_qc else None,
            "driver_oos_rate": qc_data.get("driver_oos_rate") if has_qc else None,
            "driver_oos_rate_national_average": qc_data.get("driver_oos_rate_national_average") if has_qc else None,
            "vehicle_insp": qc_data.get("vehicle_insp") if has_qc else None,
            "vehicle_oos_insp": qc_data.get("vehicle_oos_insp") if has_qc else None,
            "vehicle_oos_rate": qc_data.get("vehicle_oos_rate") if has_qc else None,
            "vehicle_oos_rate_national_average": qc_data.get("vehicle_oos_rate_national_average") if has_qc else None,
            "hazmat_insp": qc_data.get("hazmat_insp") if has_qc else None,
            "hazmat_oos_insp": qc_data.get("hazmat_oos_insp") if has_qc else None,
            "hazmat_oos_rate": qc_data.get("hazmat_oos_rate") if has_qc else None,
            "hazmat_oos_rate_national_average": qc_data.get("hazmat_oos_rate_national_average") if has_qc else None,
        }

        crashes_info = {
            "total": qc_data.get("crash_total") if has_qc else None,
            "fatal": qc_data.get("fatal_crash") if has_qc else None,
            "injury": qc_data.get("inj_crash") if has_qc else None,
            "towaway": qc_data.get("towaway_crash") if has_qc else None,
        }

        safety_rating_info = {
            "rating": qc_data.get("safety_rating") if has_qc else None,
            "rating_date": qc_data.get("safety_rating_date") if has_qc else None,
            "oos_date": qc_data.get("oos_date") if has_qc else None,
        }

        power_units = (qc_data.get("total_power_units") if has_qc and qc_data.get("total_power_units") is not None else census_record.get("power_units")) or 0
        drivers = (qc_data.get("total_drivers") if has_qc and qc_data.get("total_drivers") is not None else census_record.get("drivers")) or 0

        is_active_carrier = census_record.get("is_active_carrier", True)
        is_active_authority = census_record.get("is_active_authority", False)
        authority_status = census_record.get("authority_status", "UNVERIFIED")
        record_category = census_record.get("record_category", "USDOT_ONLY")

        if has_qc:
            common_auth = str(qc_data.get("common_authority_status") or "").strip().upper()
            contract_auth = str(qc_data.get("contract_authority_status") or "").strip().upper()
            broker_auth = str(qc_data.get("broker_authority_status") or "").strip().upper()

            qc_active_auth = (
                common_auth in ["A", "ACTIVE"] or
                contract_auth in ["A", "ACTIVE"] or
                broker_auth in ["A", "ACTIVE"]
            )
            qc_revoked = (
                common_auth in ["R", "REVOKED", "I", "INACTIVE"] or
                contract_auth in ["R", "REVOKED", "I", "INACTIVE"]
            )

            if qc_active_auth and allowed_to_operate:
                is_active_authority = True
                authority_status = "ACTIVE"
                record_category = "CONFIRMED_MC"
            elif qc_revoked or allowed_to_operate is False:
                is_active_authority = False
                authority_status = "REVOKED"
                record_category = "REVOKED_MC"
            elif not qc_active_auth and not is_active_authority:
                # Inconclusive or no active authority found
                is_active_authority = False
                authority_status = "UNVERIFIED"
                record_category = "USDOT_ONLY"

        return {
            "mc_number": mc_number,
            "dot_number": dot_number,
            "company_name": company_name,
            "phone": phone,
            "email": email,
            "officer_name": officer_name,
            "add_date": census_record.get("add_date"),
            "mcs150_date": census_record.get("mcs150_date"),
            "status": census_record.get("status"),
            "docket_status": census_record.get("docket_status"),
            "is_active_carrier": is_active_carrier,
            "is_active_authority": is_active_authority,
            "authority_status": authority_status,
            "record_category": record_category,
            "is_usdot_only": (record_category == "USDOT_ONLY"),
            "is_broker": census_record.get("is_broker", False),
            "business_category": census_record.get("business_category", "Motor Carrier"),
            "allowed_to_operate": allowed_to_operate,
            "authority_class": census_record.get("authority_class"),
            "carrier_operation": census_record.get("carrier_operation"),
            "equipment_type": census_record.get("equipment_type"),
            "fleet_size": census_record.get("fleet_size"),
            "power_units": power_units,
            "drivers": drivers,
            "address": {
                "street": addr_street,
                "city": addr_city,
                "state": addr_state,
                "zip": addr_zip,
                "country": addr_country
            },
            "authority": authority_info,
            "insurance": insurance_info,
            "inspections": inspections_info,
            "crashes": crashes_info,
            "safety_rating": safety_rating_info,
            "qcmobile_verified": has_qc,
            "qcmobile_error": qc_error
        }
