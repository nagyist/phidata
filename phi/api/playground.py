from os import getenv
from pathlib import Path
from typing import Union, Dict, List, Any

from httpx import Response, Client as HttpxClient

from phi.constants import PHI_API_KEY_ENV_VAR
from phi.cli.settings import phi_cli_settings
from phi.cli.credentials import read_auth_token
from phi.api.api import api, invalid_response
from phi.api.routes import ApiRoutes
from phi.api.schemas.playground import PlaygroundEndpointCreate
from phi.utils.log import logger


def create_playground_endpoint(playground: PlaygroundEndpointCreate) -> bool:
    logger.debug("--**-- Creating Playground Endpoint")
    with api.AuthenticatedClient() as api_client:
        try:
            r: Response = api_client.post(
                ApiRoutes.PLAYGROUND_ENDPOINT_CREATE,
                json={"playground": playground.model_dump(exclude_none=True)},
            )
            if invalid_response(r):
                return False

            response_json: Union[Dict, List] = r.json()
            if response_json is None:
                return False

            # logger.debug(f"Response: {response_json}")
            return True
        except Exception as e:
            logger.debug(f"Could not create Playground Endpoint: {e}")
    return False


def start_playground_app_deploy(app: str, name: str, artifact_path: Path, dockerfile: str) -> bool:
    """Start a deployment of a playground artifact.

    Args:
        name (str): Name of the artifact
        artifact_path (Path): Path to the artifacttar file

    Returns:
        bool: True if deployment was successful

    Raises:
        ValueError: If artifact_path is invalid or file is too large
        RuntimeError: If deployment fails
    """
    logger.debug("--**-- Deploying Playground App")

    # Validate input
    if not artifact_path.exists():
        raise ValueError(f"Artifact not found: {artifact_path}")

    # Check file size (e.g., 100MB limit)
    max_size = 100 * 1024 * 1024  # 100MB
    if artifact_path.stat().st_size > max_size:
        raise ValueError(f"Artifact exceeds size limit: {artifact_path.stat().st_size} bytes (max {max_size} bytes)")

    # Build headers
    headers = {}
    if token := read_auth_token():
        headers[phi_cli_settings.auth_token_header] = token
    if phi_api_key := getenv(PHI_API_KEY_ENV_VAR):
        headers["Authorization"] = f"Bearer {phi_api_key}"

    try:
        with (
            HttpxClient(base_url=phi_cli_settings.api_url, headers=headers, timeout=120) as api_client,
            open(artifact_path, "rb") as file,
        ):
            files = {"file": (artifact_path.name, file, "application/gzip")}
            r: Response = api_client.post(
                ApiRoutes.START_PLAYGROUND_APP_DEPLOY,
                files=files,
                data={"app": app, "name": name, "dockerfile": dockerfile},
            )

            if invalid_response(r):
                raise RuntimeError(f"Deployment failed with status {r.status_code}: {r.text}")

            response_json: Dict = r.json()
            logger.debug(f"Response: {response_json}")
            return True

    except Exception as e:
        raise RuntimeError(f"Failed to deploy playground app: {str(e)}") from e
