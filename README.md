# IT 办公设备资产管理系统

面向研究机构、事业单位的 IT 办公设备（笔记本、台式机、显示器、外设等）全生命周期管理演示系统。

## 技术栈

- Python 3.11+ / Django 5
- Django Templates + Bootstrap 5 + ECharts
- SQLite（默认）/ MySQL（可选）
- django-apscheduler、django-import-export、openpyxl、qrcode、Pillow

## 环境要求

- Python 3.11 及以上
- 可选：MySQL 5.7+（配置见 `.env.example`）

## 快速启动

```bash
cd it_asset_mgmt
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/macOS
# source venv/bin/activate

pip install -r requirements.txt
copy .env.example .env   # Windows
# cp .env.example .env   # Linux/macOS

python manage.py migrate
python manage.py init_system
python manage.py runserver
```

浏览器访问：<http://127.0.0.1:8000/accounts/login/>

### 测试账号

| 角色 | 用户名 | 密码 | 说明 |
|------|--------|------|------|
| 管理员 | admin | admin123 | 全部管理功能 |
| 普通用户 | user | user123 | 领用、我的资产、消息 |

## 功能说明

- **资产管理**：增删改查、软删除、筛选、分页、二维码、附件
- **导入导出**：Excel 模板、校验与错误报告、按筛选导出可选字段
- **领用/审批/归还**：普通用户申请，管理员审批，归还确认，状态与历史记录
- **通知**：站内信；用户侧邮件（默认控制台后端）；到期提醒（7/3/1/当天/逾期每3天）；库存预警
- **定时任务**：每日 8:00 扫描（django-apscheduler）；可手动 `python manage.py run_reminders`
- **权限**：Django Groups（ADMIN / USER）+ 菜单/按钮权限码
- **统计**：首页 ECharts 看板、报表页
- **用户与角色**：用户管理、角色权限分配、操作日志、邮件日志

## 演示流程建议

1. 使用 **admin** 登录，查看首页统计与库存预警。
2. 在 **资产列表** 新增或导入资产，查看详情与二维码。
3. 使用 **user** 登录，提交 **领用申请**。
4. 切回 **admin**，在 **审批管理** 通过申请；user 查看 **我的资产** 与站内信/邮件日志。
5. user 发起 **归还**，admin **确认归还**，资产回到在库。
6. 可选：执行 `python manage.py run_reminders` 测试到期提醒逻辑。

## 配置说明

- 敏感项通过 `.env` 或 `config/settings_local.py` 覆盖，勿提交真实密钥。
- 生产环境请设置 `DJANGO_DEBUG=False`、强 `DJANGO_SECRET_KEY`，并配置 SMTP。

## 项目结构

```
accounts/     用户、部门、角色权限、登录与个人中心
assets/       资产、领用、审批、导入导出、统计
notifications/ 站内信、邮件、定时提醒
audit/        操作日志
common/       常量、装饰器、异常中间件
templates/    页面模板
static/       静态资源
```

## 常用命令

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py init_system
python manage.py run_reminders
python manage.py createsuperuser
```
