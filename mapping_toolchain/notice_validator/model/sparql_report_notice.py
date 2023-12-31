from typing import Optional

from ted_sws.core.model.validation_report import ReportNotice

from mapping_toolchain.notice_validator.model.xpath_query_report import XPATHQueryReport


class SPARQLReportNotice(ReportNotice):
    xpath_query_report: Optional[XPATHQueryReport]
