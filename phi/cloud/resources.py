from typing import List, Optional, Union, Tuple

from phi.app.group import AppGroup
from phi.resource.group import ResourceGroup
from phi.cloud.app.base import CloudApp
from phi.cloud.resource.base import CloudResource
from phi.infra.resources import InfraResources
from phi.utils.log import logger


class CloudResources(InfraResources):
    env: str = "prd"

    apps: Optional[List[Union[CloudApp, AppGroup]]] = None
    resources: Optional[List[Union[CloudResource, ResourceGroup]]] = None

    def create_resources(
        self,
        group_filter: Optional[str] = None,
        name_filter: Optional[str] = None,
        type_filter: Optional[str] = None,
        dry_run: Optional[bool] = False,
        auto_confirm: Optional[bool] = False,
        force: Optional[bool] = None,
        pull: Optional[bool] = None,
    ) -> Tuple[int, int]:
        logger.info("-*- Creating CloudResources")

    def delete_resources(
        self,
        group_filter: Optional[str] = None,
        name_filter: Optional[str] = None,
        type_filter: Optional[str] = None,
        dry_run: Optional[bool] = False,
        auto_confirm: Optional[bool] = False,
        force: Optional[bool] = None,
    ) -> Tuple[int, int]:
        logger.info("-*- Deleting CloudResources")

    def update_resources(
        self,
        group_filter: Optional[str] = None,
        name_filter: Optional[str] = None,
        type_filter: Optional[str] = None,
        dry_run: Optional[bool] = False,
        auto_confirm: Optional[bool] = False,
        force: Optional[bool] = None,
        pull: Optional[bool] = None,
    ) -> Tuple[int, int]:
        logger.info("-*- Updating CloudResources")
