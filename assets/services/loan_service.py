from django.utils import timezone

from assets.models import Asset, AssetLoan, ApprovalRecord
from assets.services.asset_service import log_status_change
from common.constants import AssetStatus, LoanStatus, MessageType
from common.decorators import is_admin
from common.exceptions import BusinessError
from notifications.services import message_service


def apply_loan(user, asset_id, purpose, expected_return_at):
    asset = Asset.objects.filter(pk=asset_id, is_deleted=False).first()
    if not asset:
        raise BusinessError("资产不存在")
    if asset.status != AssetStatus.IN_STOCK:
        raise BusinessError("仅可选择在库资产")
    if expected_return_at <= timezone.now():
        raise BusinessError("预计归还时间必须晚于当前时间")
    if AssetLoan.objects.filter(
        asset=asset,
        status__in=[LoanStatus.PENDING, LoanStatus.APPROVED, LoanStatus.RETURN_PENDING],
    ).exists():
        raise BusinessError("该资产已有进行中的领用/归还流程")

    loan = AssetLoan.objects.create(
        asset=asset,
        applicant=user,
        purpose=purpose,
        expected_return_at=expected_return_at,
        status=LoanStatus.PENDING,
    )
    from django.contrib.auth.models import User

    admins = User.objects.filter(groups__name="ADMIN", is_active=True).distinct()
    for admin in admins:
        message_service.send_message(
            admin,
            title=f"新的领用申请：{asset.asset_no}",
            content=f"{user.get_full_name() or user.username} 申请领用 {asset.name}，请及时审批。",
            msg_type=MessageType.LOAN,
            related_key=f"loan:{loan.pk}",
        )
    return loan


def approve_loan(loan: AssetLoan, approver, approved: bool, comment: str = ""):
    if loan.status != LoanStatus.PENDING:
        raise BusinessError("该申请已处理")
    ApprovalRecord.objects.create(
        loan=loan,
        approver=approver,
        approved=approved,
        comment=comment,
    )
    asset = loan.asset
    if approved:
        loan.status = LoanStatus.APPROVED
        loan.approved_at = timezone.now()
        loan.admin_remark = comment
        loan.save()
        asset.status = AssetStatus.LOANED
        asset.current_holder = loan.applicant
        asset.loaned_at = timezone.now()
        asset.due_at = loan.expected_return_at
        asset.save()
        log_status_change(asset, approver, AssetStatus.LOANED, "审批通过领用")
        message_service.send_message(
            loan.applicant,
            title=f"领用申请已通过：{asset.asset_no}",
            content=f"您申请领用的资产 {asset.name} 已通过审批。{comment}",
            msg_type=MessageType.APPROVAL,
            related_key=f"loan_approved:{loan.pk}",
            send_email=True,
        )
    else:
        loan.status = LoanStatus.REJECTED
        loan.admin_remark = comment
        loan.save()
        message_service.send_message(
            loan.applicant,
            title=f"领用申请已拒绝：{asset.asset_no}",
            content=f"拒绝原因：{comment or '无'}",
            msg_type=MessageType.APPROVAL,
            related_key=f"loan_rejected:{loan.pk}",
            send_email=True,
        )
    return loan


def request_return(user, loan_id):
    loan = AssetLoan.objects.select_related("asset").filter(pk=loan_id, applicant=user).first()
    if not loan:
        raise BusinessError("申请不存在")
    if loan.status != LoanStatus.APPROVED:
        raise BusinessError("仅已通过领用的申请可发起归还")
    loan.status = LoanStatus.RETURN_PENDING
    loan.save(update_fields=["status"])
    from django.contrib.auth.models import User

    for admin in User.objects.filter(groups__name="ADMIN", is_active=True).distinct():
        message_service.send_message(
            admin,
            title=f"归还待确认：{loan.asset.asset_no}",
            content=f"{user.username} 发起归还，请确认。",
            msg_type=MessageType.RETURN,
            related_key=f"return:{loan.pk}",
        )
    return loan


def confirm_return(loan: AssetLoan, operator):
    if loan.status != LoanStatus.RETURN_PENDING:
        raise BusinessError("当前状态不可确认归还")
    asset = loan.asset
    loan.status = LoanStatus.RETURNED
    loan.actual_return_at = timezone.now()
    loan.save()
    asset.status = AssetStatus.IN_STOCK
    asset.current_holder = None
    asset.loaned_at = None
    asset.due_at = None
    asset.save()
    log_status_change(asset, operator, AssetStatus.IN_STOCK, "确认归还")
    message_service.send_message(
        loan.applicant,
        title=f"归还已确认：{asset.asset_no}",
        content=f"资产 {asset.name} 已归还入库。",
        msg_type=MessageType.RETURN,
        related_key=f"return_done:{loan.pk}",
        send_email=True,
    )
    return loan


def user_can_view_asset(user, asset: Asset) -> bool:
    if is_admin(user):
        return True
    return asset.current_holder_id == user.id and not asset.is_deleted
