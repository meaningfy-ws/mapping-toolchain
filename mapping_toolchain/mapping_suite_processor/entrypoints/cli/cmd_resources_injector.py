import os
import shutil
from pathlib import Path

import click

from mapping_toolchain.core.adapters.cmd_runner import CmdRunner as BaseCmdRunner, DEFAULT_MAPPINGS_PATH
from ted_sws.data_manager.adapters.mapping_suite_repository import MS_TRANSFORM_FOLDER_NAME, \
    MS_RESOURCES_FOLDER_NAME, MS_VALIDATE_FOLDER_NAME, MS_SHACL_FOLDER_NAME
from mapping_toolchain.mapping_suite_processor.entrypoints.cli import CONCEPTUAL_MAPPINGS_FILE_TEMPLATE
from ted_sws.mapping_suite_processor.services.conceptual_mapping_files_injection import \
    mapping_suite_processor_inject_resources as inject_resources, \
    mapping_suite_processor_inject_shacl_shapes as inject_shacl_shapes

from ted_sws.resources import MAPPING_FILES_PATH, SHACL_SHAPES_PATH

DEFAULT_OUTPUT_PATH = '{mappings_path}/{mapping_suite_id}'
DEFAULT_RESOURCES_PATH = MAPPING_FILES_PATH
DEFAULT_SHACL_SHAPES_PATH = SHACL_SHAPES_PATH
CMD_NAME = "CMD_RESOURCES_INJECTOR"

"""
USAGE:
# resources_injector --help
"""


class CmdRunner(BaseCmdRunner):
    """
    Keeps the logic to be used by Resources Injector CMD
    """

    def __init__(
            self,
            conceptual_mappings_file,
            resources_folder,
            shacl_folder,
            output_folder
    ):
        super().__init__(name=CMD_NAME)
        self.conceptual_mappings_file_path = Path(os.path.realpath(conceptual_mappings_file))
        self.resources_folder_path = Path(os.path.realpath(resources_folder))
        self.shacl_folder_path = Path(os.path.realpath(shacl_folder))
        self.output_folder_path = Path(os.path.realpath(output_folder))
        self.output_resources_folder_path = self.output_folder_path / MS_TRANSFORM_FOLDER_NAME / MS_RESOURCES_FOLDER_NAME
        self.output_shacl_folder_path = self.output_folder_path / MS_VALIDATE_FOLDER_NAME / MS_SHACL_FOLDER_NAME

        if not self.conceptual_mappings_file_path.is_file():
            error_msg = f"No such file :: [{conceptual_mappings_file}]"
            self.log_failed_msg(error_msg)
            raise FileNotFoundError(error_msg)

    def run_cmd(self):
        error = None
        try:
            self.log(f"Importing resources from {self.resources_folder_path} ...")
            shutil.rmtree(self.output_resources_folder_path, ignore_errors=True)
            self.output_resources_folder_path.mkdir(parents=True, exist_ok=True)
            inject_resources(conceptual_mappings_file_path=self.conceptual_mappings_file_path,
                             resources_folder_path=self.resources_folder_path,
                             output_resources_folder_path=self.output_resources_folder_path
                             )

            self.log(f"Importing SHACL shapes from {self.shacl_folder_path} to {self.output_shacl_folder_path}")
            shutil.rmtree(self.output_shacl_folder_path, ignore_errors=True)
            self.output_shacl_folder_path.mkdir(parents=True, exist_ok=True)
            inject_shacl_shapes(
                shacl_shape_folder_path=self.shacl_folder_path,
                output_shacl_shape_folder_path=self.output_shacl_folder_path
            )
        except Exception as e:
            error = e

        return self.run_cmd_result(error)


def run(mapping_suite_id=None,
        opt_conceptual_mappings_file: str = None,
        opt_output_folder: str = None,
        opt_resources_folder: str = str(DEFAULT_RESOURCES_PATH),
        opt_shacl_folder: str = str(DEFAULT_SHACL_SHAPES_PATH),
        opt_mappings_folder=DEFAULT_MAPPINGS_PATH
        ):
    """
    This method will inject the requested resources into the MappingSuite
    :param mapping_suite_id:
    :param opt_conceptual_mappings_file:
    :param opt_output_folder:
    :param opt_resources_folder:
    :param opt_shacl_folder:
    :param opt_mappings_folder:
    :return:
    """
    if opt_conceptual_mappings_file:
        conceptual_mappings_file = opt_conceptual_mappings_file
    else:
        conceptual_mappings_file = CONCEPTUAL_MAPPINGS_FILE_TEMPLATE.format(
            mappings_path=opt_mappings_folder,
            mapping_suite_id=mapping_suite_id
        )

    resources_folder = opt_resources_folder

    if opt_output_folder and not mapping_suite_id:
        output_folder = opt_output_folder
    else:
        output_folder = DEFAULT_OUTPUT_PATH.format(
            mappings_path=opt_mappings_folder,
            mapping_suite_id=mapping_suite_id
        )

    cmd = CmdRunner(
        conceptual_mappings_file=conceptual_mappings_file,
        resources_folder=resources_folder,
        shacl_folder=opt_shacl_folder,
        output_folder=output_folder
    )
    cmd.run()


@click.command()
@click.argument('mapping-suite-id', nargs=1, required=False)
@click.option('-i', '--opt-conceptual-mappings-file', help="Use to overwrite default INPUT")
@click.option('-o', '--opt-output-folder', help="Use to overwrite default OUTPUT")
@click.option('-r', '--opt-resources-folder', default=str(DEFAULT_RESOURCES_PATH))
@click.option('-s', '--opt-shacl-folder', default=str(DEFAULT_SHACL_SHAPES_PATH))
@click.option('-m', '--opt-mappings-folder', default=DEFAULT_MAPPINGS_PATH)
def main(mapping_suite_id, opt_conceptual_mappings_file, opt_output_folder, opt_resources_folder, opt_shacl_folder,
         opt_mappings_folder):
    """
    Injects the requested resources from Conceptual Mappings into the MappingSuite.
    """
    run(mapping_suite_id, opt_conceptual_mappings_file, opt_output_folder, opt_resources_folder, opt_shacl_folder,
        opt_mappings_folder)


if __name__ == '__main__':
    main()
