import base64
import json
from pathlib import Path
from typing import List
from urllib.parse import urljoin, urlparse

import click
from mapping_toolchain.core.adapters.cmd_runner import CmdRunnerForMappingSuite as BaseCmdRunner, DEFAULT_MAPPINGS_PATH
from ted_sws.core.model.manifestation import RDFManifestation
from ted_sws.data_manager.services.mapping_suite_resource_manager import read_flat_file_resources, \
    file_resource_output_path
from ted_sws.event_manager.adapters.log import LOG_INFO_TEXT, LOG_WARN_TEXT
from ted_sws.notice_publisher.adapters.s3_notice_publisher import S3Publisher
from ted_sws.notice_publisher.services.notice_publisher import publish_notice_rdf_content_into_s3
from ted_sws.notice_transformer.services.notice_transformer import DEFAULT_TRANSFORMATION_FILE_EXTENSION

from mapping_toolchain.mapping_suite_processor import OUTPUT_FOLDER

CMD_NAME = "CMD_S3_RDF_PUBLISHER"
DEFAULT_NOTICE_RDF_S3_BUCKET_NAME = "notice-rdf"

"""
USAGE:
# s3_rdf_publisher --help
"""


class CmdRunner(BaseCmdRunner):
    """
    Publish RDF content to S3 bucket
    """

    def __init__(
            self,
            rdf_files: List[str],
            mapping_suite_id,
            notice_ids: List[str],
            skip_notice_ids: List[str],
            bucket_name: str,
            object_names: List[str],
            mappings_path,
            s3_publisher: S3Publisher = None
    ):
        super().__init__(name=CMD_NAME)
        self.rdf_files = []
        self.mapping_suite_id = mapping_suite_id
        if self.mapping_suite_id:
            self.notice_ids = self._init_list_input_opts_split(notice_ids)
            self.skip_notice_ids = self._init_list_input_opts_split(skip_notice_ids)
            self.mappings_path = mappings_path
            self.output_folder = OUTPUT_FOLDER.format(mappings_path=self.mappings_path,
                                                      mapping_suite_id=self.mapping_suite_id)
            output_path = Path(self.output_folder)
            file_resources = read_flat_file_resources(output_path, extension=DEFAULT_TRANSFORMATION_FILE_EXTENSION)

            if not self.notice_ids and self.skip_notice_ids:
                for file_resource in file_resources:
                    notice_id = file_resource.parents[-1]
                    if notice_id not in self.skip_notice_ids:
                        self.notice_ids.append(notice_id)

            for file_resource in file_resources:
                notice_id = file_resource.parents[-1]
                if notice_id in self.notice_ids:
                    rdf_file_name = notice_id + DEFAULT_TRANSFORMATION_FILE_EXTENSION
                    rdf_path = file_resource_output_path(file_resource, output_path) / rdf_file_name
                    if rdf_path.is_file():
                        self.rdf_files.append(str(rdf_path))

        self.rdf_files += self._init_list_input_opts_split(rdf_files)

        self.bucket_name = bucket_name
        self.object_names = self._init_list_input_opts_split(object_names)

        self.s3_publisher = s3_publisher

    def set_policy(self):
        self.s3_publisher.create_bucket_if_not_exists(self.bucket_name)
        policy = self.s3_publisher.rdf_bucket_policy(self.bucket_name)
        self.s3_publisher.client.set_bucket_policy(self.bucket_name, json.dumps(policy))

    def object_url(self, bucket_name: str, object_name: str) -> str:
        url = self.s3_publisher.client.get_presigned_url("GET", self.bucket_name, object_name)
        return urljoin(url, urlparse(url).path)

    def run_cmd(self):
        self.set_policy()
        self.log(LOG_WARN_TEXT.format("---"))
        for idx, rdf_file_name in enumerate(self.rdf_files):
            rdf_file_path = Path(rdf_file_name)
            with open(rdf_file_path, "rb") as rdf_file:
                rdf_content = rdf_file.read()

            object_name = self.object_names[idx] if idx < len(self.object_names) else rdf_file_path.name

            self.log(f"Publishing RDF({rdf_file_name}) to {self.bucket_name}/{object_name} .")

            publish_notice_rdf_content_into_s3(
                rdf_manifestation=RDFManifestation(object_data=base64.b64encode(rdf_content)),
                bucket_name=self.bucket_name,
                object_name=object_name,
                s3_publisher=self.s3_publisher
            )

            self.log(LOG_INFO_TEXT.format(f"URL :: {self.object_url(self.bucket_name, object_name)}"))
            self.log(LOG_WARN_TEXT.format("---"))

        return self.run_cmd_result()


def run(rdf_file=None, mapping_suite_id=None, notice_id=None, skip_notice_id=None,
        bucket_name=DEFAULT_NOTICE_RDF_S3_BUCKET_NAME, object_name=None, mappings_folder=DEFAULT_MAPPINGS_PATH
        , s3_publisher: S3Publisher = S3Publisher()
        ):
    cmd = CmdRunner(
        rdf_files=list(rdf_file or []),
        mapping_suite_id=mapping_suite_id,
        notice_ids=list(notice_id or []),
        skip_notice_ids=list(skip_notice_id or []),
        bucket_name=bucket_name,
        object_names=list(object_name or []),
        mappings_path=mappings_folder,
        s3_publisher=s3_publisher
    )
    cmd.run()


@click.command()
@click.option('-f', '--rdf-file', required=False, multiple=True,
              help="'--rdf-file=RDF_FILE' or '-f RDF_FILE1,RDF_FILE2'")
@click.option('-ms-id', '--mapping-suite-id', required=False)
@click.option('-n', '--notice-id', required=False, multiple=True,
              help="'--notice-id=NOTICE_ID' or '-n NOTICE_ID1,NOTICE_ID2'")
@click.option('-no-n', '--skip-notice-id', required=False, multiple=True,
              help="notices to be skipped when only --mapping-suite-id is provided")
@click.option('-b', '--bucket-name', default=DEFAULT_NOTICE_RDF_S3_BUCKET_NAME, help="S3 Bucket")
@click.option('-o', '--object-name', required=False, multiple=True, default=None,
              help="'--object-name=OBJECT_NAME' or '-o OBJECT_NAME1,OBJECT_NAME2'")
@click.option('-m', '--mappings-folder', default=DEFAULT_MAPPINGS_PATH)
def main(rdf_file, mapping_suite_id, notice_id, skip_notice_id, bucket_name, object_name, mappings_folder):
    """
    Publish RDF content to S3 bucket.
    --rdf-file[list] OR --mapping-suite-id[value] OR (--mapping-suite-id[value] AND --notice-id[list]) must be provided!

    Make sure to have set up these variables.code-text-area.module.scss in .env file:\n
    S3_PUBLISH_HOST,
    S3_PUBLISH_NOTICE_RDF_BUCKET (this will be overwritten by CLI option, if provided),
    S3_PUBLISH_USER,
    S3_PUBLISH_PASSWORD,
    S3_PUBLISH_REGION=eu-central-1,
    S3_PUBLISH_SECURE=1,
    S3_PUBLISH_SSL_VERIFY=0
    """
    run(rdf_file, mapping_suite_id, notice_id, skip_notice_id, bucket_name, object_name, mappings_folder)


if __name__ == '__main__':
    main()
