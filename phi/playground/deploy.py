import time
import tarfile
from pathlib import Path
from typing import Optional, List, cast

from rich import box
from rich.text import Text
from rich.panel import Panel

from phi.cli.settings import phi_cli_settings
from phi.api.playground import start_playground_app_deploy
from phi.utils.log import logger


def create_deployment_info(
    app: str, root: Path, elapsed_time: str = "[waiting...]", status: Optional[str] = None, error: Optional[str] = None
) -> Text:
    """Create a formatted text display showing deployment information.

    Args:
        app (str): The name of the application being deployed
        root (Path): The path to the root directory
        elapsed_time (str): The elapsed deployment time. Defaults to "[waiting...]"
        status (Optional[str]): The current deployment status. Defaults to None
        error (Optional[str]): The deployment error message. Defaults to None

    Returns:
        Text: A Rich Text object containing formatted deployment information
    """
    # Base info always shown
    elements = [
        ("📦 App: ", "bold"),
        (f"{app}\n", "cyan"),
        ("📂 Root: ", "bold"),
        (f"{root}\n", "cyan"),
        ("⏱️  Time: ", "bold"),
        (f"{elapsed_time}\n", "yellow"),
    ]

    # Add either status or error, not both
    if error is not None:
        elements.extend(
            [
                ("🚨 Error: ", "bold"),
                (f"{error}", "red"),
            ]
        )
    elif status is not None:
        elements.extend(
            [
                ("🚧 Status: ", "bold"),
                (f"{status}", "yellow"),
            ]
        )

    return Text.assemble(*elements)


def create_info_panel(deployment_info: Text) -> Panel:
    """Create a formatted panel to display deployment information.

    Args:
        deployment_info (Text): The Rich Text object containing deployment information

    Returns:
        Panel: A Rich Panel object containing the formatted deployment information
    """
    return Panel(
        deployment_info,
        title="[bold green]🚀 Deploying Playground App[/bold green]",
        border_style="cyan",
        box=box.HEAVY,
        padding=(1, 2),
    )


def create_error_panel(deployment_info: Text) -> Panel:
    """Create a formatted panel to display deployment error information.

    Args:
        deployment_info (Text): The Rich Text object containing deployment error information

    Returns:
        Panel: A Rich Panel object containing the formatted deployment error information
    """
    return Panel(
        deployment_info,
        title="[bold red]🚨 Deployment Failed[/bold red]",
        border_style="red",
        box=box.HEAVY,
        padding=(1, 2),
    )


def create_tar_artifact(root: Path) -> Path:
    """Create a gzipped tar artifact of the playground files.

    Args:
        root (Path): The path to the directory to be artifactd

    Returns:
        Path: The path to the created tar artifact

    Raises:
        Exception: If artifact creation fails
    """
    artifact_path = root.with_suffix(".tar.gz")
    try:
        logger.debug(f"Creating playground artifact: {artifact_path.name}")
        with tarfile.open(artifact_path, "w:gz") as tar:
            tar.add(root, arcname="workspace")
        logger.debug(f"Successfully created playground artifact: {artifact_path.name}")
        return artifact_path
    except Exception as e:
        logger.error(f"Failed to create playground artifact: {e}")
        raise


def start_deploy(name: str, artifact_path: Path) -> None:
    """Start the deployment of the tar artifact to phi-cloud.

    Args:
        name (str): The name of the playground app
        artifact_path (Path): The path to the tar artifact to be deployed

    Raises:
        Exception: If the deployment process fails
    """
    try:
        logger.debug(f"Deploying playground artifact: {artifact_path.name}")
        start_playground_app_deploy(name=name, artifact_path=artifact_path)
        logger.debug(f"Successfully deployed playground artifact: {artifact_path.name}")
    except Exception:
        raise


def cleanup_artifact(artifact_path: Path) -> None:
    """Delete the temporary tar artifact after deployment.

    Args:
        artifact_path (Path): The path to the tar artifact to be deleted

    Raises:
        Exception: If the deletion process fails
    """
    try:
        logger.debug(f"Deleting playground artifact: {artifact_path.name}")
        # artifact_path.unlink()
        logger.debug(f"Successfully deleted playground artifact: {artifact_path.name}")
    except Exception as e:
        logger.error(f"Failed to delete playground artifact: {e}")
        raise


def deploy_playground_app(
    app: str,
    name: str,
    root: Optional[Path] = None,
) -> None:
    """Deploy a playground application to phi-cloud.

    This function:
    1. Creates a tar artifact of the root directory.
    2. Uploades the artifact to phi-cloud.
    3. Cleaning up temporary files.
    4. Displaying real-time progress updates.

    Args:
        app (str): The application to deploy as a string identifier.
                It should be the name of the module containing the Playground app from the root path.
        name (str): The name of the playground app.
        root (Optional[Path]): The root path containing the application files. Defaults to the current working directory.

    Raises:
        Exception: If any step of the deployment process fails
    """

    phi_cli_settings.gate_alpha_feature()

    from rich.live import Live
    from rich.console import Group
    from rich.status import Status
    from phi.utils.timer import Timer

    if app is None:
        raise ValueError("PlaygroundApp is required")

    if name is None:
        raise ValueError("PlaygroundApp name is required")

    with Live(refresh_per_second=4) as live_display:
        response_timer = Timer()
        response_timer.start()
        root = root or Path.cwd()
        root = cast(Path, root)
        if not root.exists() and not root.is_dir():
            raise ValueError(f"Directory does not exist: {root}")

        try:
            deployment_info = create_deployment_info(app=app, root=root, status="Initializing...")
            panels: List[Panel] = [create_info_panel(deployment_info=deployment_info)]
            status = Status(
                "[bold blue]Initializing playground...[/bold blue]",
                spinner="aesthetic",
                speed=2,
            )
            panels.append(status)  # type: ignore
            live_display.update(Group(*panels))

            # Step 1: Create artifact
            status.update("[bold blue]Creating playground app...[/bold blue]")
            panels[0] = create_info_panel(
                create_deployment_info(
                    app=app, root=root, elapsed_time=f"{response_timer.elapsed:.1f}s", status="Creating artifact..."
                )
            )
            live_display.update(Group(*panels))
            artifact_path = create_tar_artifact(root=root)

            # Step 2: Deploy artifact
            status.update("[bold blue]Uploading playground app...[/bold blue]")
            panels[0] = create_info_panel(
                create_deployment_info(
                    app=app, root=root, elapsed_time=f"{response_timer.elapsed:.1f}s", status="Uploading artifact..."
                )
            )
            live_display.update(Group(*panels))
            start_deploy(name=name, artifact_path=artifact_path)

            # Step 3: Wait for deployment to complete
            status.update("[bold blue]Deploying playground app...[/bold blue]")
            deploy_complete = False
            num_runs = 0
            while not deploy_complete:
                panels[0] = create_info_panel(
                    create_deployment_info(
                        app=app, root=root, elapsed_time=f"{response_timer.elapsed:.1f}s", status="Deploying..."
                    )
                )
                live_display.update(Group(*panels))
                time.sleep(0.5)  # Sleep for 0.5 seconds
                num_runs += 1
                if num_runs > 10:
                    deploy_complete = True

            # Step 4: Cleanup
            status.update("[bold blue]Deleting playground artifact...[/bold blue]")
            panels[0] = create_info_panel(
                create_deployment_info(
                    app=app, root=root, elapsed_time=f"{response_timer.elapsed:.1f}s", status="Deleting artifact..."
                )
            )
            live_display.update(Group(*panels))
            cleanup_artifact(artifact_path)

            # Final display update
            status.stop()
            panels.pop()
            panels[0] = create_info_panel(
                create_deployment_info(
                    app=app, root=root, elapsed_time=f"{response_timer.elapsed:.1f}s", status="Playground app deployed!"
                )
            )
            live_display.update(Group(*panels))
        except Exception as e:
            status.update(f"[bold red]Deployment failed: {str(e)}[/bold red]")
            panels[0] = create_error_panel(
                create_deployment_info(app=app, root=root, elapsed_time=f"{response_timer.elapsed:.1f}s", error=str(e))
            )
            status.stop()
            panels.pop()
            live_display.update(Group(*panels))
