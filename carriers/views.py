import re
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Carrier
from .serializers import CarrierSerializer
from .services.fmcsa_service import (
    FMCSAService,
    InvalidDOTNumberException,
    CarrierNotFoundException,
    FMCSAConnectionException,
    FMCSAServiceException,
)
from .services.company_census_service import (
    CompanyCensusService,
    InvalidMCRangeException,
    CompanyCensusConnectionException,
    CompanyCensusException,
)

logger = logging.getLogger(__name__)


class CarrierSearchRangeView(APIView):
    """
    Public API endpoint to search FMCSA Company Census by MC number range.
    GET /api/carriers/search/?start_mc=1670008&end_mc=1670052
    """
    MAX_RANGE_LIMIT = 5000

    def get(self, request):
        start_mc_raw = request.query_params.get('start_mc')
        end_mc_raw = request.query_params.get('end_mc')

        if not start_mc_raw:
            return Response(
                {"success": False, "error": "start_mc parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not end_mc_raw:
            return Response(
                {"success": False, "error": "end_mc parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        def parse_mc(val):
            if val is None:
                return None
            digits = re.sub(r'\D', '', str(val).strip())
            if not digits:
                return None
            return int(digits)

        start_mc = parse_mc(start_mc_raw)
        end_mc = parse_mc(end_mc_raw)

        if start_mc is None:
            return Response(
                {"success": False, "error": f"Invalid start_mc format: {start_mc_raw}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if end_mc is None:
            return Response(
                {"success": False, "error": f"Invalid end_mc format: {end_mc_raw}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if start_mc > end_mc:
            return Response(
                {"success": False, "error": f"start_mc ({start_mc}) cannot be greater than end_mc ({end_mc})"},
                status=status.HTTP_400_BAD_REQUEST
            )

        range_span = end_mc - start_mc + 1
        if range_span > self.MAX_RANGE_LIMIT:
            return Response(
                {"success": False, "error": f"Requested MC range ({range_span}) exceeds maximum limit of {self.MAX_RANGE_LIMIT}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        verify_qcmobile_raw = request.query_params.get('verify_qcmobile', 'false')
        verify_qcmobile = str(verify_qcmobile_raw).lower() in ['true', '1', 'yes']

        service = CompanyCensusService()

        try:
            res_dict = service.search_by_mc_range(
                start_mc=start_mc,
                end_mc=end_mc,
                active_only=True,
                verify_qcmobile=verify_qcmobile,
                return_meta=True
            )

            results = res_dict["results"]
            meta = res_dict["meta"]

            return Response(
                {
                    "count": len(results),
                    "start_mc": start_mc,
                    "end_mc": end_mc,
                    "meta": meta,
                    "results": results
                },
                status=status.HTTP_200_OK
            )

        except InvalidMCRangeException as exc:
            return Response(
                {"success": False, "error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except CompanyCensusConnectionException as exc:
            logger.error(f"Company Census API connection error: {exc}")
            return Response(
                {"success": False, "error": "Company Census API service temporarily unavailable"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except CompanyCensusException as exc:
            logger.error(f"Company Census service error: {exc}")
            return Response(
                {"success": False, "error": "Failed to process Company Census query"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as exc:
            logger.error(f"Unexpected error in carrier search range API: {exc}")
            return Response(
                {"success": False, "error": "An internal server error occurred"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CarrierSearchDateView(APIView):
    """
    Public API endpoint to search FMCSA Company Census by carrier registration/add date range.
    GET /api/carriers/search-by-date/?start_date=2026-09-20&end_date=2026-09-24
    """

    def get(self, request):
        start_date_raw = request.query_params.get('start_date')
        end_date_raw = request.query_params.get('end_date')

        if not start_date_raw:
            return Response(
                {"success": False, "error": "start_date parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not end_date_raw:
            return Response(
                {"success": False, "error": "end_date parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        verify_qcmobile_raw = request.query_params.get('verify_qcmobile', 'false')
        verify_qcmobile = str(verify_qcmobile_raw).lower() in ['true', '1', 'yes']

        include_usdot_only_raw = request.query_params.get('include_usdot_only', 'false')
        include_usdot_only = str(include_usdot_only_raw).lower() in ['true', '1', 'yes']

        service = CompanyCensusService()

        try:
            res_dict = service.search_by_date_range(
                start_date=start_date_raw,
                end_date=end_date_raw,
                active_only=True,
                confirmed_mc_only=not include_usdot_only,
                verify_qcmobile=verify_qcmobile,
                return_meta=True
            )

            results = res_dict["results"]
            meta = res_dict["meta"]
            confirmed_mc_count = sum(1 for c in results if c.get("is_active_authority"))
            usdot_only_count = sum(1 for c in results if c.get("is_usdot_only"))

            return Response(
                {
                    "count": len(results),
                    "confirmed_mc_count": confirmed_mc_count,
                    "usdot_only_count": usdot_only_count,
                    "start_date": start_date_raw,
                    "end_date": end_date_raw,
                    "meta": meta,
                    "results": results
                },
                status=status.HTTP_200_OK
            )

        except InvalidMCRangeException as exc:
            return Response(
                {"success": False, "error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except CompanyCensusConnectionException as exc:
            logger.error(f"Company Census API connection error: {exc}")
            return Response(
                {"success": False, "error": "Company Census API service temporarily unavailable"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except CompanyCensusException as exc:
            logger.error(f"Company Census service error: {exc}")
            return Response(
                {"success": False, "error": "Failed to process Company Census date query"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as exc:
            logger.error(f"Unexpected error in carrier search date API: {exc}")
            return Response(
                {"success": False, "error": "An internal server error occurred"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CarrierDetailView(APIView):
    """
    API endpoint to retrieve and normalize FMCSA carrier details by DOT number.
    GET /api/carriers/<dot_number>/
    """

    def get(self, request, dot_number):
        dot_str = str(dot_number).strip()
        if not dot_str.isdigit() or int(dot_str) <= 0:
            return Response(
                {
                    "success": False,
                    "error": "Invalid DOT number"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        dot = int(dot_str)
        service = FMCSAService()

        try:
            normalized_data = service.fetch_carrier_data(dot)

            carrier, created = Carrier.objects.update_or_create(
                dot_number=dot,
                defaults=normalized_data
            )

            serializer = CarrierSerializer(carrier)
            return Response(
                {
                    "success": True,
                    "carrier": serializer.data
                },
                status=status.HTTP_200_OK
            )

        except InvalidDOTNumberException:
            return Response(
                {
                    "success": False,
                    "error": "Invalid DOT number"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        except CarrierNotFoundException:
            return Response(
                {
                    "success": False,
                    "error": "Carrier not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        except FMCSAConnectionException:
            return Response(
                {
                    "success": False,
                    "error": "FMCSA service temporarily unavailable"
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        except FMCSAServiceException as exc:
            logger.error(f"FMCSA Service error occurred for DOT {dot}: {exc}")
            return Response(
                {
                    "success": False,
                    "error": "FMCSA service temporarily unavailable"
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        except Exception as exc:
            logger.error(f"Unexpected error retrieving carrier for DOT {dot}: {exc}")
            return Response(
                {
                    "success": False,
                    "error": "An internal error occurred"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
