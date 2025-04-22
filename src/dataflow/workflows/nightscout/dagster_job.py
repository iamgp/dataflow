"""Dagster job definition for the Nightscout workflow."""

from dagster import ConfigurableResource, job, op
from pydantic import Field

from dataflow.shared.config import load_workflow_config
from dataflow.workflows.nightscout.ingestion import NightscoutConfig, run_nightscout_ingestion
from dataflow.workflows.registry import register_workflow


class NightscoutResource(ConfigurableResource):
    """Resource representing Nightscout workflow configuration."""

    base_url: str = Field(..., description="Base URL for the Nightscout API")
    api_secret: str | None = Field(None, description="API secret for authenticated access")
    entries_count: int = Field(100, description="Number of entries to fetch")
    treatments_days: int = Field(7, description="Number of days of treatments to fetch")
    profile_enabled: bool = Field(True, description="Whether to fetch profile data")
    bucket_name: str = Field("nightscout-raw", description="Minio bucket for raw data storage")
    local_save_path: str | None = Field(None, description="Local path to save data (optional)")


@op(
    name="nightscout_ingestion",
    description="Ingests data from Nightscout API and stores it in Minio",
    required_resource_keys={"nightscout_config"},
)
def nightscout_ingestion_op(context):
    """Dagster operation for ingesting data from Nightscout API.

    Args:
        context: The Dagster execution context

    Returns:
        Dict with status summary
    """
    context.log.info("Starting Nightscout ingestion operation")

    # Get configuration from resource
    config_dict = context.resources.nightscout_config.dict()
    context.log.debug("Using Nightscout configuration", **config_dict)

    # Run the ingestion process
    try:
        run_nightscout_ingestion(config_dict)
        context.log.info("Nightscout ingestion completed successfully")
        return {"status": "success", "message": "Nightscout data ingested successfully"}
    except Exception as e:
        context.log.error("Nightscout ingestion failed", error=str(e))
        return {"status": "failure", "message": f"Nightscout ingestion failed: {e}"}


@register_workflow(
    name="nightscout",
    metadata={
        "description": "Ingests data from Nightscout diabetes management API",
        "author": "DataFlow Team",
        "tags": ["diabetes", "health", "api"],
    },
)
@job(
    name="nightscout_job",
    description="Job for ingesting Nightscout data",
    resource_defs={
        "nightscout_config": NightscoutResource.configure_at_launch(),
    },
)
def nightscout_job():
    """Dagster job for ingesting and processing Nightscout data."""
    nightscout_ingestion_op()


def load_nightscout_job():
    """Load the Nightscout job with default configuration.

    Returns:
        Configured Nightscout job
    """
    # Load configuration from file
    config = load_workflow_config("nightscout")
    validated_config = NightscoutConfig(**config)

    # Create the job with resources
    return nightscout_job.with_resources(
        resource_defs={
            "nightscout_config": NightscoutResource(
                base_url=validated_config.base_url,
                api_secret=validated_config.api_secret,
                entries_count=validated_config.entries_count,
                treatments_days=validated_config.treatments_days,
                profile_enabled=validated_config.profile_enabled,
                bucket_name=validated_config.bucket_name,
                local_save_path=validated_config.local_save_path,
            ),
        }
    )
