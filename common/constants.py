GROUP_ADMIN = "ADMIN"
GROUP_USER = "USER"

ROLE_CHOICES = (
    (GROUP_ADMIN, "管理员"),
    (GROUP_USER, "普通用户"),
)


class AssetStatus:
    IN_STOCK = "in_stock"
    LOANED = "loaned"
    MAINTENANCE = "maintenance"
    SCRAPPED = "scrapped"

    CHOICES = (
        (IN_STOCK, "在库"),
        (LOANED, "已领用"),
        (MAINTENANCE, "维修中"),
        (SCRAPPED, "报废"),
    )


class LoanStatus:
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    RETURN_PENDING = "return_pending"
    RETURNED = "returned"

    CHOICES = (
        (PENDING, "待审批"),
        (APPROVED, "已通过"),
        (REJECTED, "已拒绝"),
        (RETURN_PENDING, "待确认归还"),
        (RETURNED, "已归还"),
    )


class MessageType:
    SYSTEM = "system"
    LOAN = "loan"
    APPROVAL = "approval"
    RETURN = "return"
    REMINDER = "reminder"
    STOCK = "stock"

    CHOICES = (
        (SYSTEM, "系统通知"),
        (LOAN, "领用申请"),
        (APPROVAL, "审批结果"),
        (RETURN, "归还"),
        (REMINDER, "到期提醒"),
        (STOCK, "库存预警"),
    )


# 菜单与按钮权限码
PERMISSION_CODES = {
    "menu.dashboard": "首页看板",
    "menu.assets": "资产管理",
    "menu.import_export": "导入导出",
    "menu.loan_apply": "领用申请",
    "menu.my_loans": "我的申请",
    "menu.my_assets": "我的资产",
    "menu.approval": "审批管理",
    "menu.messages": "消息中心",
    "menu.users": "用户管理",
    "menu.roles": "角色管理",
    "menu.reports": "统计报表",
    "menu.profile": "个人中心",
    "btn.asset_create": "新增资产",
    "btn.asset_edit": "编辑资产",
    "btn.asset_delete": "删除资产",
    "btn.asset_import": "导入资产",
    "btn.asset_export": "导出资产",
    "btn.loan_approve": "审批领用",
    "btn.user_manage": "用户管理",
}

ADMIN_DEFAULT_PERMISSIONS = list(PERMISSION_CODES.keys())

USER_DEFAULT_PERMISSIONS = [
    "menu.dashboard",
    "menu.loan_apply",
    "menu.my_loans",
    "menu.my_assets",
    "menu.messages",
    "menu.profile",
]
