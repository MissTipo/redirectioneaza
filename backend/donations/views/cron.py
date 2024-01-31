import csv
import logging
import operator
from datetime import datetime

from django.http import HttpResponse
from django.utils import timezone

from donations.models.main import Donor, Ngo
from .base import Handler


logger = logging.getLogger(__name__)


# TODO: The cron URLs should not be accessible by the public


class Stats(Handler):
    def get(self, request):
        now = timezone.now()
        start_of_year = datetime(now.year, 1, 1, 0, 0)
        # TODO: use aggregations for counting the totals in one step
        donations = Donor.objects.filter(date_created__gte=start_of_year).values("ngo_id", "has_signed")

        ngos = {}
        signed = 0
        for d in donations:
            ngos[d["ngo_id"]] = ngos.get(d["ngo_id"], 0)

            ngos[d["ngo_id"]] += 1

            if d["has_signed"]:
                signed += 1

        sorted_x = sorted(ngos.items(), key=operator.itemgetter(1))

        res = """
        Formulare semnate: {} <br>
        Top ngos: {}
        """.format(
            signed, sorted_x[len(sorted_x) - 10 :]
        )

        return HttpResponse(res)


class CustomExport(Handler):
    def get(self, request):
        current_year = timezone.now().year
        start_arg = request.GET.get("start")
        end_arg = request.GET.get("end")

        if not start_arg or not end_arg:
            return HttpResponse("Missing start and end from URL. Format: ?start=23-1&end=19-5")

        start_arg = start_arg.split("-")
        end_arg = end_arg.split("-")
        query_start = datetime(current_year, int(start_arg[1]), int(start_arg[0]), 0, 0, 59)
        query_end = datetime(current_year, int(end_arg[1]), int(end_arg[0]), 23, 59, 59)

        donors = (
            Donor.objects.filter(date_created__gte=query_start, date_created__lte=query_end).select_related("ngo").all()
        )

        fields = (
            "id",
            "last_name",
            "first_name",
            "email",
            "has_signed",
            "pdf_file",
            "ngo__name",
            "ngo__email",
            "ngo__is_accepting_forms",
        )

        logger.info("Found {} donations".format(len(donors)))

        response = HttpResponse(
            content_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="export_donor.csv"'},
        )

        writer = csv.writer(response, quoting=csv.QUOTE_ALL)
        writer.writerow(fields)

        for donor in donors:
            if donor.ngo:
                writer.writerow(
                    [
                        donor.id,
                        donor.first_name,
                        donor.last_name,
                        donor.email,
                        donor.has_signed,
                        donor.pdf_file.url if donor.pdf_file else donor.pdf_url,
                        donor.ngo.name,
                        donor.ngo.email,
                        donor.ngo.is_accepting_forms,
                    ]
                )
            else:
                logger.warn("Could not find ngo for donation, ID: {}".format(donor.id))

        return response


class NgoExport(Handler):
    def get(self, request):
        fields = (
            "id",
            "name",
            "registration_number",
            "county",
            "active_region",
            "email",
            "website",
            "address",
        )

        response = HttpResponse(
            content_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="export_ngo.csv"'},
        )

        writer = csv.writer(response, quoting=csv.QUOTE_ALL)
        writer.writerow(fields)

        for ngo in Ngo.objects.all().values(*fields):
            writer.writerow([ngo[field_name] for field_name in fields])

        return response


class NgoRemoveForms(Handler):
    def get(self, request):

        # get all the ngos
        ngos = Ngo.objects.all()

        logger.info("Removing form_url and custom_form from {0} ngos.".format(len(ngos)))

        # loop through them and remove the form_url
        # this will force an update on it when downloaded again
        for ngo in ngos:
            ngo.form_url = ""
            ngo.custom_form.delete()

        return HttpResponse("ok")
