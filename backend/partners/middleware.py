import logging

from django.conf import settings
from django.http import Http404

from .models import Partner

logger = logging.getLogger(__name__)


class InvalidSubdomain(Exception):
    pass


class PartnerDomainMiddleware:
    """
    Add the `request.partner` property based on the requested subdomain
    """

    @staticmethod
    def extract_subdomain(host: str, apex: str) -> str:
        apex = apex.strip().lower()
        dot_apex = "." + apex
        host = host.strip().lower()

        # Drop the port number (if present)
        host = host.split(":", maxsplit=1)[0]

        # Drop the `www.` prefix (if present)
        if host[:4] == "www.":
            host = host[4:]

        # Extract the subdomain name
        if host == apex:
            subdomain = ""
        elif host.endswith(dot_apex):
            subdomain = host.split(dot_apex, maxsplit=1)[0]
        else:
            raise InvalidSubdomain

        return subdomain

    def _get_partner_from_subdomain(self, request):
        if settings.FORCE_PARTNER:
            return Partner.active.first()

        try:
            subdomain = PartnerDomainMiddleware.extract_subdomain(request.get_host(), settings.APEX_DOMAIN)
        except InvalidSubdomain:
            raise Http404(f"Invalid APEX_DOMAIN: {settings.APEX_DOMAIN}")

        logger.debug("Subdomain %s", subdomain or "None")

        if not subdomain:
            partner = None
        else:
            try:
                partner = Partner.active.get(subdomain=subdomain)
            except Partner.DoesNotExist:
                partner = None

        return partner

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == "/health/":
            logger.debug("Healthcheck: Skipping PartnerDomainMiddleware")
            return self.get_response(request)

        logger.debug("Request host %s", request.get_host())
        partner = self._get_partner_from_subdomain(request)

        request.partner = partner
        logger.debug("Request partner %s", request.partner or "None")

        # Code to be executed for each request before
        # the view (and later middleware) are called.

        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        if hasattr(response, "status_code"):
            logger.info(
                "Response status %s for domain %s corresponding to partner %s",
                response.status_code,
                request.get_host(),
                request.partner or "None",
            )
        else:
            logger.info(
                "Response for domain %s corresponding to partner %s",
                request.get_host(),
                request.partner or "None",
            )

        return response
