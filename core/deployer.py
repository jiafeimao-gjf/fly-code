"""Deployment automation module."""

import subprocess
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
from utils.logger import logger


@dataclass
class DeploymentTarget:
    """Represents a deployment target."""
    name: str
    type: str  # local, docker, cloud
    config: dict


class Deployer:
    """Handles deployment to various targets."""

    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root or Path.cwd()
        self.targets: dict[str, DeploymentTarget] = {}

    def register_target(self, name: str, target_type: str, config: dict) -> None:
        """Register a deployment target."""
        self.targets[name] = DeploymentTarget(name=name, type=target_type, config=config)
        logger.info(f"Registered deployment target: {name} ({target_type})")

    def deploy(self, target_name: str) -> tuple[bool, str]:
        """Deploy to the specified target."""
        if target_name not in self.targets:
            return False, f"Unknown target: {target_name}. Available: {list(self.targets.keys())}"

        target = self.targets[target_name]

        if target.type == "local":
            return self._deploy_local(target)
        elif target.type == "docker":
            return self._deploy_docker(target)
        else:
            return False, f"Unsupported target type: {target.type}"

    def _deploy_local(self, target: DeploymentTarget) -> tuple[bool, str]:
        """Deploy to local environment."""
        try:
            setup_script = target.config.get("setup_script")
            run_script = target.config.get("run_script")

            if setup_script:
                logger.info(f"Running setup: {setup_script}")
                result = subprocess.run(setup_script, shell=True, capture_output=True, text=True)
                if result.returncode != 0:
                    return False, f"Setup failed: {result.stderr}"

            if run_script:
                logger.info(f"Running: {run_script}")
                result = subprocess.run(run_script, shell=True, capture_output=True, text=True)
                if result.returncode != 0:
                    return False, f"Run failed: {result.stderr}"
                return True, f"Deployed successfully: {result.stdout}"

            return True, "Local deployment completed"

        except Exception as e:
            return False, f"Local deployment failed: {e}"

    def _deploy_docker(self, target: DeploymentTarget) -> tuple[bool, str]:
        """Deploy using Docker."""
        try:
            dockerfile = target.config.get("dockerfile", "Dockerfile")
            image_name = target.config.get("image_name", self.project_root.name)
            container_name = target.config.get("container_name", f"{image_name}_container")

            # Build image
            logger.info(f"Building Docker image: {image_name}")
            build_cmd = f"docker build -t {image_name} -f {dockerfile} {self.project_root}"
            result = subprocess.run(build_cmd, shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                return False, f"Docker build failed: {result.stderr}"

            # Stop existing container if running
            stop_cmd = f"docker stop {container_name} 2>/dev/null || true"
            subprocess.run(stop_cmd, shell=True)

            # Run new container
            run_cmd = f"docker run -d --name {container_name} {image_name}"
            result = subprocess.run(run_cmd, shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                return False, f"Docker run failed: {result.stderr}"

            return True, f"Docker deployment successful: {container_name}"

        except Exception as e:
            return False, f"Docker deployment failed: {e}"

    def rollback(self, target_name: str) -> tuple[bool, str]:
        """Rollback deployment on target."""
        if target_name not in self.targets:
            return False, f"Unknown target: {target_name}"

        target = self.targets[target_name]

        if target.type == "docker":
            container_name = target.config.get("container_name", f"{self.project_root.name}_container")
            try:
                subprocess.run(f"docker stop {container_name}", shell=True, capture_output=True)
                subprocess.run(f"docker rm {container_name}", shell=True, capture_output=True)
                return True, f"Rolled back: {container_name}"
            except Exception as e:
                return False, f"Rollback failed: {e}"

        return False, f"Rollback not supported for target type: {target.type}"

    def get_status(self, target_name: str) -> str:
        """Get deployment status for target."""
        if target_name not in self.targets:
            return f"Unknown target: {target_name}"

        target = self.targets[target_name]

        if target.type == "docker":
            container_name = target.config.get("container_name", f"{self.project_root.name}_container")
            result = subprocess.run(
                f"docker ps --filter name={container_name} --format '{{.Status}}'",
                shell=True, capture_output=True, text=True
            )
            status = result.stdout.strip() or "not running"
            return f"{target_name}: {status}"

        return f"{target_name}: status unknown"
