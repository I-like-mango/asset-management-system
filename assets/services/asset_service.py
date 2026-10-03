from django.utils import timezone

from assets.models import Asset, AssetStatusLog
from assets.utils.qrcode_utils import generate_qr_image
from common.constants import AssetStatus
from common.exceptions import BusinessError


def log_status_change(asset, operator, to_status, note=""):
    AssetStatusLog.objects.create(
        asset=asset,
        from_status=asset.status,
        to_status=to_status,
        operator=operator,
        note=note,
    )


def save_asset(asset: Asset, operator, *, regenerate_qr=False):
    if regenerate_qr or not asset.qr_code:
        content = f"ASSET:{asset.asset_no}"
        asset.qr_code.save(f"{asset.asset_no}.png", generate_qr_image(content), save=False)
    asset.save()
    return asset


def create_asset(data: dict, operator) -> Asset:
    asset_no = data.get("asset_no", "").strip()
    if Asset.objects.filter(asset_no=asset_no, is_deleted=False).exists():
        raise BusinessError(f"资产编号 {asset_no} 已存在")
    asset = Asset(created_by=operator, **data)
    save_asset(asset, operator, regenerate_qr=True)
    log_status_change(asset, operator, asset.status, "创建资产")
    return asset


def update_asset(asset: Asset, data: dict, operator) -> Asset:
    new_no = data.get("asset_no", asset.asset_no).strip()
    if (
        new_no != asset.asset_no
        and Asset.objects.filter(asset_no=new_no, is_deleted=False).exclude(pk=asset.pk).exists()
    ):
        raise BusinessError(f"资产编号 {new_no} 已存在")
    old_status = asset.status
    for field, value in data.items():
        setattr(asset, field, value)
    save_asset(asset, operator, regenerate_qr=(new_no != asset.asset_no))
    if old_status != asset.status:
        log_status_change(asset, operator, asset.status, "编辑资产")
    return asset


def soft_delete_asset(asset: Asset, operator):
    if asset.is_deleted:
        raise BusinessError("资产已删除")
    if asset.status == AssetStatus.LOANED:
        raise BusinessError("已领用资产不能删除，请先归还")
    log_status_change(asset, operator, asset.status, "软删除")
    asset.soft_delete()
