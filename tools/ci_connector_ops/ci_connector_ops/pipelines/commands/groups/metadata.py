#
# Copyright (c) 2023 Airbyte, Inc., all rights reserved.
#
import logging

import anyio
import click
from ci_connector_ops.pipelines.contexts import CIContext
from ci_connector_ops.pipelines.pipelines.metadata import (
    run_metadata_lib_test_pipeline,
    run_metadata_orchestrator_test_pipeline,
    run_metadata_upload_pipeline,
    run_metadata_validation_pipeline,
)
from ci_connector_ops.pipelines.utils import DaggerPipelineCommand, get_all_metadata_files, get_modified_metadata_files
from rich.logging import RichHandler

logging.basicConfig(level=logging.INFO, format="%(name)s: %(message)s", datefmt="[%X]", handlers=[RichHandler(rich_tracebacks=True)])
logger = logging.getLogger(__name__)

# MAIN GROUP


@click.group(help="Commands related to the metadata service.")
@click.pass_context
def metadata(ctx: click.Context):
    pass


# VALIDATE COMMAND


@metadata.command(cls=DaggerPipelineCommand, help="Commands related to validating the metadata files.")
@click.option("--modified-only/--all", default=True)
@click.pass_context
def validate(ctx: click.Context, modified_only: bool):
    if modified_only:
        modified_files = ctx.obj["modified_files_in_branch"]
        metadata_to_validate = get_modified_metadata_files(modified_files)
        if not metadata_to_validate:
            click.secho("No modified metadata found. Skipping metadata validation.")
            return
    else:
        click.secho("Will run metadata validation on all the metadata files found in the repo.")
        metadata_to_validate = get_all_metadata_files()

    click.secho(f"Will validate {len(metadata_to_validate)} metadata files.")

    return anyio.run(
        run_metadata_validation_pipeline,
        ctx.obj["is_local"],
        ctx.obj["git_branch"],
        ctx.obj["git_revision"],
        ctx.obj.get("gha_workflow_run_url"),
        ctx.obj.get("pipeline_start_timestamp"),
        ctx.obj.get("ci_context"),
        metadata_to_validate,
    )


# UPLOAD COMMAND


@metadata.command(cls=DaggerPipelineCommand, help="Commands related to uploading the metadata files to remote storage.")
@click.argument("gcs-bucket-name", type=click.STRING)
@click.option(
    "--gcs-credentials", help="Credentials in JSON format with permission to get and upload on the GCS bucket", envvar="GCS_CREDENTIALS"
)
@click.option("--modified-only/--all", default=True)
@click.pass_context
def upload(ctx: click.Context, gcs_bucket_name: str, gcs_credentials: str, modified_only: bool):
    if modified_only:
        if ctx.obj["ci_context"] is not CIContext.MASTER and ctx.obj["git_branch"] != "master":
            click.secho("Not on the master branch. Skipping metadata upload.")
            return
        modified_files = ctx.obj["modified_files_in_commit"]
        metadata_to_upload = get_modified_metadata_files(modified_files)
        if not metadata_to_upload:
            click.secho("No modified metadata found. Skipping metadata upload.")
            return
    else:
        metadata_to_upload = get_all_metadata_files()

    click.secho(f"Will upload {len(metadata_to_upload)} metadata files.")

    return anyio.run(
        run_metadata_upload_pipeline,
        ctx.obj["is_local"],
        ctx.obj["git_branch"],
        ctx.obj["git_revision"],
        ctx.obj.get("gha_workflow_run_url"),
        ctx.obj.get("pipeline_start_timestamp"),
        ctx.obj.get("ci_context"),
        metadata_to_upload,
        gcs_bucket_name,
        gcs_credentials,
    )


# TEST GROUP


@metadata.group(help="Commands related to testing the metadata service.")
@click.pass_context
def test(ctx: click.Context):
    pass


@test.command(cls=DaggerPipelineCommand, help="Run tests for the metadata service library.")
@click.pass_context
def lib(ctx: click.Context):
    return anyio.run(
        run_metadata_lib_test_pipeline,
        ctx.obj["is_local"],
        ctx.obj["git_branch"],
        ctx.obj["git_revision"],
        ctx.obj.get("gha_workflow_run_url"),
        ctx.obj.get("pipeline_start_timestamp"),
        ctx.obj.get("ci_context"),
    )


@test.command(cls=DaggerPipelineCommand, help="Run tests for the metadata service orchestrator.")
@click.pass_context
def orchestrator(ctx: click.Context):
    return anyio.run(
        run_metadata_orchestrator_test_pipeline,
        ctx.obj["is_local"],
        ctx.obj["git_branch"],
        ctx.obj["git_revision"],
        ctx.obj.get("gha_workflow_run_url"),
        ctx.obj.get("pipeline_start_timestamp"),
        ctx.obj.get("ci_context"),
    )


if __name__ == "__main__":
    lib()
