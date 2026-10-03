from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from accounts.models import Department
from accounts.services import ensure_default_groups, get_or_create_profile
from assets.models import Asset, AssetCategory
from assets.services.asset_service import create_asset
from common.constants import GROUP_ADMIN, GROUP_USER, AssetStatus


class Command(BaseCommand):
    help = "初始化角色、部门、分类、测试账号与示例资产"

    def handle(self, *args, **options):
        admin_group, user_group = ensure_default_groups()
        self.stdout.write("角色与权限已初始化")

        dept_it, _ = Department.objects.get_or_create(code="IT", defaults={"name": "信息技术部"})
        dept_rd, _ = Department.objects.get_or_create(code="RD", defaults={"name": "科研管理部"})

        categories = [
            ("laptop", "笔记本电脑", 3),
            ("desktop", "台式机", 2),
            ("monitor", "显示器", 5),
            ("mouse", "鼠标", 10),
            ("keyboard", "键盘", 10),
            ("adapter", "转接头", 8),
            ("projector", "投影仪", 1),
        ]
        for code, name, threshold in categories:
            AssetCategory.objects.update_or_create(
                code=code,
                defaults={"name": name, "warning_threshold": threshold, "is_active": True},
            )
        self.stdout.write("部门与资产分类已初始化")

        admin_user, created = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@example.com",
                "first_name": "系统",
                "last_name": "管理员",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if created or not admin_user.check_password("admin123"):
            admin_user.set_password("admin123")
            admin_user.is_active = True
            admin_user.save()
        admin_user.groups.set([admin_group])
        profile = get_or_create_profile(admin_user)
        profile.department = dept_it
        profile.employee_no = "A001"
        profile.save()

        normal_user, u_created = User.objects.get_or_create(
            username="user",
            defaults={
                "email": "user@example.com",
                "first_name": "张",
                "last_name": "研究员",
            },
        )
        if u_created or not normal_user.check_password("user123"):
            normal_user.set_password("user123")
            normal_user.is_active = True
            normal_user.save()
        normal_user.groups.set([user_group])
        uprofile = get_or_create_profile(normal_user)
        uprofile.department = dept_rd
        uprofile.employee_no = "U001"
        uprofile.save()

        self.stdout.write("测试账号: admin/admin123, user/user123")

        if Asset.objects.filter(is_deleted=False).count() == 0:
            admin = admin_user
            samples = [
                ("IT-NB-001", "ThinkPad T14", "laptop", "Lenovo", "T14 Gen3", "8000"),
                ("IT-NB-002", "MacBook Pro", "laptop", "Apple", "M3 14", "12000"),
                ("IT-PC-001", "办公台式机", "desktop", "Dell", "OptiPlex", "5500"),
                ("IT-MN-001", "27寸显示器", "monitor", "Dell", "U2720Q", "3200"),
                ("IT-MS-001", "无线鼠标", "mouse", "Logitech", "MX Master", "499"),
                ("IT-KB-001", "机械键盘", "keyboard", "Keychron", "K2", "699"),
                ("IT-AD-001", "USB-C 转接头", "adapter", "Anker", "Hub", "199"),
                ("IT-PJ-001", "会议室投影", "projector", "Epson", "CB-X06", "4500"),
            ]
            for no, name, cat, brand, model, price in samples:
                category = AssetCategory.objects.get(code=cat)
                create_asset(
                    {
                        "asset_no": no,
                        "name": name,
                        "category": category,
                        "brand": brand,
                        "model": model,
                        "status": AssetStatus.IN_STOCK,
                        "location": "IT仓库",
                        "price": Decimal(price),
                    },
                    admin,
                )
            self.stdout.write("示例资产已创建")
        else:
            self.stdout.write("资产已存在，跳过示例数据")

        self.stdout.write(self.style.SUCCESS("系统初始化完成"))
