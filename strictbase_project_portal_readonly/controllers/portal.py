import io

from odoo import _, http
from odoo.http import content_disposition, request

from odoo.addons.project.controllers.portal import ProjectCustomerPortal
from odoo.addons.portal.controllers.portal import CustomerPortal


class StrictBaseReadonlyPortalMixin:
    def _get_portal_brand_name(self):
        website = getattr(request, "website", None)
        if website and website.company_id:
            return website.company_id.sudo().name
        return request.env.company.name

    def _get_readonly_projects(self):
        partner = request.env.user.partner_id
        if not request.env.user._is_portal():
            return request.env["project.project"]
        return request.env["project.project"].sudo().search([
            ("is_template", "=", False),
            ("collaborator_ids", "any", [
                ("partner_id", "=", partner.id),
                ("readonly_full_access", "=", True),
            ]),
        ], order="name, id")

    def _is_readonly_project_user(self):
        return bool(self._get_readonly_projects())

    def _support_overview_url(self, project=None):
        if project:
            return f"/my?project_id={project.id}"
        return "/my"

    def _format_hours(self, hours):
        if hours is False or hours is None:
            return False
        value = f"{hours:.2f}".rstrip("0").rstrip(".")
        return _("%s h", value)

    def _prepare_export_task_rows(self, project, tasks):
        timesheets = request.env["account.analytic.line"].sudo().search([
            ("task_id", "in", tasks.ids),
        ], order="task_id, date desc, id desc")
        timesheets_by_task = {task.id: [] for task in tasks}
        for line in timesheets:
            timesheets_by_task.setdefault(line.task_id.id, []).append({
                "date": str(line.date or ""),
                "description": line.name or "",
                "hours": self._format_hours(line.unit_amount or 0.0),
            })

        rows = []
        for task in tasks:
            rows.append({
                "project_name": project.name,
                "task_name": task.name,
                "status": task.stage_id.name or ("Done" if task.is_closed else "Open"),
                "category": "Past" if task.is_closed else "Current",
                "time_spent_label": self._format_hours(task.total_hours_spent or 0.0),
                "worklogs": timesheets_by_task.get(task.id, []),
            })
        return rows

    def _prepare_support_overview_values(self, project_id=None):
        brand_name = self._get_portal_brand_name()
        readonly_projects = self._get_readonly_projects()
        selected_project = readonly_projects.filtered(lambda project: project.id == project_id)[:1] if project_id else readonly_projects[:1]
        projects = selected_project or readonly_projects
        project_sections = []

        for project in projects:
            tasks = request.env["project.task"].sudo().search([
                ("project_id", "=", project.id),
                ("active", "=", True),
            ], order="write_date desc, id desc")
            open_tasks = tasks.filtered(lambda task: not task.is_closed)
            closed_tasks = tasks.filtered("is_closed")
            project_sections.append({
                "project": project,
                "open_tasks": open_tasks,
                "closed_tasks": closed_tasks,
                "export_task_rows": self._prepare_export_task_rows(project, tasks),
                "remaining_hours": project.sale_line_id.remaining_hours if project.sale_line_id else False,
                "remaining_hours_label": self._format_hours(project.sale_line_id.remaining_hours) if project.sale_line_id else False,
            })

        values = {
            **self._prepare_portal_layout_values(),
            "page_name": "support_overview",
            "page_title": _("%(brand)s Support Overview", brand=brand_name),
            "support_overview_brand_name": brand_name,
            "projects": readonly_projects,
            "project_sections": project_sections,
            "selected_project": projects[:1],
        }
        return values

    def _prepare_support_task_values(self, project, task):
        timesheets = request.env["account.analytic.line"].sudo().search([
            ("task_id", "=", task.id),
        ], order="date desc, id desc")
        return {
            **self._prepare_portal_layout_values(),
            "page_name": "support_ticket",
            "page_title": task.name,
            "project": project,
            "task": task,
            "timesheets": timesheets,
            "time_spent_label": self._format_hours(task.total_hours_spent or 0.0),
            "remaining_hours_label": self._format_hours(project.sale_line_id.remaining_hours) if project.sale_line_id else False,
        }

    def _get_support_export_projects(self, project_id=None):
        readonly_projects = self._get_readonly_projects()
        if project_id:
            selected_project = readonly_projects.filtered(lambda project: project.id == project_id)[:1]
            return selected_project
        return readonly_projects

    def _make_xlsx_response(self, projects):
        import xlsxwriter  # noqa: PLC0415

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})

        header = workbook.add_format({"bold": True, "bg_color": "#D9E2F3", "border": 1})
        text = workbook.add_format({"text_wrap": True, "valign": "top"})
        hour = workbook.add_format({"num_format": "0.00", "valign": "top"})
        date = workbook.add_format({"num_format": "yyyy-mm-dd", "valign": "top"})

        overview_sheet = workbook.add_worksheet("Overview")
        overview_headers = ["Project", "Open Tickets", "Past Tickets", "Remaining Hours"]
        for column, label in enumerate(overview_headers):
            overview_sheet.write(0, column, label, header)
        overview_sheet.set_column(0, 0, 28)
        overview_sheet.set_column(1, 3, 16)

        tickets_sheet = workbook.add_worksheet("Tickets")
        ticket_headers = ["Project", "Ticket", "Status", "Category", "Time Spent", "Remaining Hours"]
        for column, label in enumerate(ticket_headers):
            tickets_sheet.write(0, column, label, header)
        tickets_sheet.set_column(0, 1, 32)
        tickets_sheet.set_column(2, 3, 14)
        tickets_sheet.set_column(4, 5, 16)

        worklog_sheet = workbook.add_worksheet("Work Log")
        worklog_headers = ["Project", "Ticket", "Date", "Description", "Hours"]
        for column, label in enumerate(worklog_headers):
            worklog_sheet.write(0, column, label, header)
        worklog_sheet.set_column(0, 1, 28)
        worklog_sheet.set_column(2, 2, 14)
        worklog_sheet.set_column(3, 3, 48)
        worklog_sheet.set_column(4, 4, 12)

        overview_row = 1
        ticket_row = 1
        worklog_row = 1

        for project in projects:
            tasks = request.env["project.task"].sudo().search([
                ("project_id", "=", project.id),
                ("active", "=", True),
            ], order="write_date desc, id desc")
            open_tasks = tasks.filtered(lambda task: not task.is_closed)
            closed_tasks = tasks.filtered("is_closed")
            remaining_hours = project.sale_line_id.remaining_hours if project.sale_line_id else False

            overview_sheet.write(overview_row, 0, project.name, text)
            overview_sheet.write_number(overview_row, 1, len(open_tasks))
            overview_sheet.write_number(overview_row, 2, len(closed_tasks))
            if remaining_hours is not False:
                overview_sheet.write_number(overview_row, 3, remaining_hours, hour)
            overview_row += 1

            for task in tasks:
                tickets_sheet.write(ticket_row, 0, project.name, text)
                tickets_sheet.write(ticket_row, 1, task.name, text)
                tickets_sheet.write(ticket_row, 2, task.stage_id.name or ("Done" if task.is_closed else "Open"), text)
                tickets_sheet.write(ticket_row, 3, "Past" if task.is_closed else "Current", text)
                tickets_sheet.write_number(ticket_row, 4, task.total_hours_spent or 0.0, hour)
                if remaining_hours is not False:
                    tickets_sheet.write_number(ticket_row, 5, remaining_hours, hour)
                ticket_row += 1

                timesheets = request.env["account.analytic.line"].sudo().search([
                    ("task_id", "=", task.id),
                ], order="date desc, id desc")
                for line in timesheets:
                    worklog_sheet.write(worklog_row, 0, project.name, text)
                    worklog_sheet.write(worklog_row, 1, task.name, text)
                    if line.date:
                        worklog_sheet.write_datetime(worklog_row, 2, line.date, date)
                    worklog_sheet.write(worklog_row, 3, line.name or "", text)
                    worklog_sheet.write_number(worklog_row, 4, line.unit_amount or 0.0, hour)
                    worklog_row += 1

        workbook.close()
        filename = "support-overview.xlsx" if len(projects) != 1 else f"{projects.name}-support.xlsx"
        return request.make_response(
            output.getvalue(),
            headers=[
                ("Content-Type", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
                ("Content-Disposition", content_disposition(filename)),
            ],
        )


class StrictBaseReadonlyCustomerPortal(StrictBaseReadonlyPortalMixin, CustomerPortal):
    @http.route(['/my', '/my/home'], type='http', auth="user", website=True, list_as_website_content="User Dashboard")
    def home(self, **kw):
        if self._is_readonly_project_user():
            args = request.httprequest.args
            project_id = args.get("project_id")
            project_id = int(project_id) if project_id and str(project_id).isdigit() else None
            values = self._prepare_support_overview_values(project_id=project_id)
            return request.render("strictbase_project_portal_readonly.portal_my_support", values)
        return super().home(**kw)


class StrictBaseReadonlyProjectPortal(StrictBaseReadonlyPortalMixin, ProjectCustomerPortal):
    @http.route(['/my/projects', '/my/projects/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_projects(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        if self._is_readonly_project_user():
            return request.redirect(self._support_overview_url(self._get_readonly_projects()[:1]))
        return super().portal_my_projects(page=page, date_begin=date_begin, date_end=date_end, sortby=sortby, **kw)

    @http.route(['/my/projects/<int:project_id>', '/my/projects/<int:project_id>/page/<int:page>'], type='http', auth="public", website=True)
    def portal_my_project(self, project_id=None, access_token=None, page=1, date_begin=None, date_end=None, sortby=None, search=None, search_in='content', groupby=None, task_id=None, **kw):
        readonly_projects = self._get_readonly_projects()
        if project_id in readonly_projects.ids:
            return request.redirect(self._support_overview_url(request.env["project.project"].browse(project_id)))
        return super().portal_my_project(
            project_id=project_id,
            access_token=access_token,
            page=page,
            date_begin=date_begin,
            date_end=date_end,
            sortby=sortby,
            search=search,
            search_in=search_in,
            groupby=groupby,
            task_id=task_id,
            **kw,
        )

    @http.route(['/my/projects/<int:project_id>/project_sharing', '/my/projects/<int:project_id>/project_sharing/<path:subpath>'], type='http', auth='user', methods=['GET'])
    def render_project_backend_view(self, project_id, subpath=None):
        readonly_projects = self._get_readonly_projects()
        if project_id in readonly_projects.ids:
            return request.redirect(self._support_overview_url(request.env["project.project"].browse(project_id)))
        return super().render_project_backend_view(project_id=project_id, subpath=subpath)

    @http.route('/my/projects/<int:project_id>/task/<int:task_id>', type='http', auth='public', website=True)
    def portal_my_project_task(self, project_id=None, task_id=None, access_token=None, **kw):
        readonly_projects = self._get_readonly_projects()
        if project_id in readonly_projects.ids:
            project = request.env["project.project"].sudo().browse(project_id)
            task = request.env["project.task"].sudo().search([
                ("project_id", "=", project_id),
                ("id", "=", task_id),
                ("active", "=", True),
            ], limit=1)
            if not task:
                return request.redirect(self._support_overview_url(project))
            values = self._prepare_support_task_values(project, task)
            return request.render("strictbase_project_portal_readonly.portal_my_support_task", values)
        return super().portal_my_project_task(project_id=project_id, task_id=task_id, access_token=access_token, **kw)
