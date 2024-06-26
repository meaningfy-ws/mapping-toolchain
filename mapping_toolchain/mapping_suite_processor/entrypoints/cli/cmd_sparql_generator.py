#!/usr/bin/python3

import os
import shutil
from pathlib import Path

import click

from mapping_toolchain.core.adapters.cmd_runner import CmdRunner as BaseCmdRunner, DEFAULT_MAPPINGS_PATH
from ted_sws.data_manager.adapters.mapping_suite_repository import MS_VALIDATE_FOLDER_NAME, \
    MS_SPARQL_FOLDER_NAME, MappingSuiteRepositoryInFileSystem
from ted_sws.event_manager.adapters.log import LOG_INFO_TEXT
from mapping_toolchain.mapping_suite_processor.entrypoints.cli import CONCEPTUAL_MAPPINGS_FILE_TEMPLATE
from ted_sws.mapping_suite_processor.services.conceptual_mapping_generate_sparql_queries import \
    mapping_suite_processor_generate_sparql_queries as generate_sparql_queries, DEFAULT_RQ_NAME

DEFAULT_OUTPUT_SPARQL_QUERIES_FOLDER = '{mappings_path}/{mapping_suite_id}/' + MS_VALIDATE_FOLDER_NAME + '/' + \
                                       MS_SPARQL_FOLDER_NAME + '/cm_assertions'
CMD_NAME = "CMD_SPARQL_GENERATOR"

"""
USAGE:
# sparql_generator --help
"""


class CmdRunner(BaseCmdRunner):
    """
    Keeps the logic to be used by SPARQL queries Generator
    """

    def __init__(
            self,
            conceptual_mappings_file,
            output_sparql_queries_folder,
            rq_name
    ):
        super().__init__(name=CMD_NAME)
        self.conceptual_mappings_file_path = Path(os.path.realpath(conceptual_mappings_file))
        self.output_sparql_queries_folder_path = Path(os.path.realpath(output_sparql_queries_folder))
        self.rq_name = rq_name

        if not self.conceptual_mappings_file_path.is_file():
            error_msg = f"No such file :: [{conceptual_mappings_file}]"
            self.log_failed_msg(error_msg)
            raise FileNotFoundError(error_msg)

    def run_cmd(self):
        self.generate(self.conceptual_mappings_file_path, self.output_sparql_queries_folder_path, self.rq_name)

    def generate(self, conceptual_mappings_file_path, output_sparql_queries_folder_path, rq_name):
        """
        Generates SPARQL queries from Conceptual Mappings
        """
        self.log("Running " + LOG_INFO_TEXT.format("SPARQL queries") + " generation ... ")

        error = None
        try:
            shutil.rmtree(output_sparql_queries_folder_path, ignore_errors=True)
            generate_sparql_queries(conceptual_mappings_file_path, output_sparql_queries_folder_path, rq_name)
        except Exception as e:
            error = e

        return self.run_cmd_result(error)


def run(mapping_suite_id=None, opt_conceptual_mappings_file=None, opt_output_sparql_queries_folder=None,
        opt_rq_name=DEFAULT_RQ_NAME, opt_mappings_folder=DEFAULT_MAPPINGS_PATH):
    if opt_conceptual_mappings_file:
        conceptual_mappings_file = opt_conceptual_mappings_file
    else:
        conceptual_mappings_file = CONCEPTUAL_MAPPINGS_FILE_TEMPLATE.format(
            mappings_path=opt_mappings_folder,
            mapping_suite_id=mapping_suite_id
        )

    if opt_output_sparql_queries_folder:
        output_sparql_queries_folder = opt_output_sparql_queries_folder
    else:
        output_sparql_queries_folder = DEFAULT_OUTPUT_SPARQL_QUERIES_FOLDER.format(
            mappings_path=opt_mappings_folder,
            mapping_suite_id=mapping_suite_id
        )

    cmd = CmdRunner(
        conceptual_mappings_file=conceptual_mappings_file,
        output_sparql_queries_folder=output_sparql_queries_folder,
        rq_name=opt_rq_name
    )
    cmd.run()


@click.command()
@click.argument('mapping-suite-id', nargs=1, required=False)
@click.option('-i', '--opt-conceptual-mappings-file', help="Use to overwrite default INPUT")
@click.option('-o', '--opt-output-sparql-queries-folder', help="Use to overwrite default OUTPUT")
@click.option('-rq-name', '--opt-rq-name', default=DEFAULT_RQ_NAME)
@click.option('-m', '--opt-mappings-folder', default=DEFAULT_MAPPINGS_PATH)
def main(mapping_suite_id, opt_conceptual_mappings_file, opt_output_sparql_queries_folder,
         opt_rq_name, opt_mappings_folder):
    """
    Generates SPARQL queries from Conceptual Mappings.
    """
    run(mapping_suite_id, opt_conceptual_mappings_file, opt_output_sparql_queries_folder,
        opt_rq_name, opt_mappings_folder)


if __name__ == '__main__':
    main()
