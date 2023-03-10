"""Convert OWL to FHIR"""
import os
import subprocess
from argparse import ArgumentParser
from typing import Dict, List

SRC_DIR = os.path.realpath(os.path.dirname(__file__))
PROJECT_DIR = os.path.realpath(os.path.join(SRC_DIR, '..'))
CONTENT_DIR = os.path.realpath(os.path.join(PROJECT_DIR, 'content'))


def _run_shell_command(command: str, cwd: str = None) -> subprocess.CompletedProcess:
    """Runs a command in the shell, and handles some common errors"""
    args = command.split(' ')
    if cwd:
        result = subprocess.run(args, capture_output=True, text=True, cwd=cwd)
    else:
        result = subprocess.run(args, capture_output=True, text=True)
    stderr, stdout = result.stderr, result.stdout
    if stdout and 'error' in stdout or 'ERROR' in stdout:
        raise RuntimeError(stdout)
    if stderr:
        raise RuntimeError(stderr)
    return result


def sssom_to_fhir(
    inpath: str, outpath: str, dev_sssom_path: str = None, dev_sssom_interpreter_path: str = None,
) -> str:
    """Run conversion"""
    # Validate args
    if (dev_sssom_path and not dev_sssom_interpreter_path) or (not dev_sssom_path and dev_sssom_interpreter_path):
        raise ValueError('If you specify a `dev_sssom_path` or `dev_sssom_interpreter_path`, you must specify both.')

    # Run conversion
    dev_sssom_path = dev_sssom_path if dev_sssom_path is None or not dev_sssom_path.endswith('sssom-py') \
        else os.path.join(dev_sssom_path, 'sssom', 'cli.py')
    cwd = os.path.realpath(os.path.join(os.path.dirname(dev_sssom_path), '..')) if dev_sssom_path else PROJECT_DIR
    lead_cmd = 'sssom' if not dev_sssom_path else f'{dev_sssom_interpreter_path} {dev_sssom_path}'
    command = f'{lead_cmd} convert {inpath} --output-format fhir_json --output {outpath}'
    _run_shell_command(command, cwd=cwd)

    return outpath


def convert_from_content_dir():
    """Convert all the latest versions from the content/ dir

    This will go to the content/ dir look for all "content module" directories there and, within each, look at tsv/, get
    the highest "v#", and convert any tsv files there, placing them in the content module\'s corresponding fhir/ dir."""
    # todo: temporarily skip icd10cm_snomed_from_omop and minimal_example
    content_modules: List[str] = os.listdir(CONTENT_DIR)
    print()


def cli():
    """Command line interface."""
    package_description = 'Convert SSSOM to FHIR.'
    parser = ArgumentParser(description=package_description)
    parser.add_argument('-i', '--inpath', required=False, help='Path to input SSSOM TSV.')
    parser.add_argument('-o', '--outpath', required=False, help='Where FHIR ConceptMap JSON should be saved.')
    parser.add_argument(
        '-c', '--convert-from-content-dir', action='store_true', required=False,
        help='If this option is used, other CLI flags are ignored. This will go to the content/ dir look for all '
             '"content module" directories there and, within each, look at tsv/, get the highest "v#", and convert any '
             'tsv files there, placing them in the content module\'s corresponding fhir/ dir.')
    parser.add_argument(
        '-d', '--dev-sssom-path', default=None, required=False,
        help='If you want to use a local development version of SSSOM, specify the path to the OAK directory here. '
             'Must be used with --dev-sssom-interpreter-path.')
    parser.add_argument(
        '-D', '--dev-sssom-interpreter-path', default=None, required=False,
        help='If you want to use a local development version of SSSOM, specify the path to the Python interpreter '
             'where its dependencies are installed (i.e. its virtual environment). Must be used with --dev-sssom-path.')

    d: Dict = vars(parser.parse_args())
    if d['convert_from_content_dir']:
        convert_from_content_dir()
    else:
        del d['convert_from_content_dir']
        if not (d['inpath'] and d['outpath']):
            raise RuntimeError('Required params missing: --inpath, --outpath')
        sssom_to_fhir(**d)


if __name__ == '__main__':
    cli()
