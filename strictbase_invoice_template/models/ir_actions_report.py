import os
import subprocess
import tempfile
from contextlib import ExitStack, closing
from urllib.parse import urlparse

import lxml.html

import odoo.addons.base.models.ir_actions_report as _base_report
from odoo import _, models
from odoo.exceptions import UserError
from odoo.http import request, root
from odoo.service import security
from odoo.tools import config as _odoo_config


def _strictbase_wkhtmltopdf_bin():
    bin_path = _odoo_config.get("bin_path")
    if bin_path and bin_path != "None":
        exe = os.path.join(bin_path, "wkhtmltopdf")
        if os.path.isfile(exe) and os.access(exe, os.X_OK):
            return exe
    return _base_report._wkhtml().bin


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    def _build_wkhtmltopdf_args(
        self,
        paperformat_id,
        landscape,
        specific_paperformat_args=None,
        set_viewport_size=False,
    ):
        args = super()._build_wkhtmltopdf_args(
            paperformat_id,
            landscape,
            specific_paperformat_args=specific_paperformat_args,
            set_viewport_size=set_viewport_size,
        )
        if "--encoding" not in args:
            args.extend(["--encoding", "utf-8"])
        return args

    def _run_wkhtmltopdf(
        self,
        bodies,
        report_ref=False,
        header=None,
        footer=None,
        landscape=False,
        specific_paperformat_args=None,
        set_viewport_size=False,
    ):
        paperformat_id = self._get_report(report_ref).get_paperformat() if report_ref else self.get_paperformat()
        command_args = self._build_wkhtmltopdf_args(
            paperformat_id,
            landscape,
            specific_paperformat_args=specific_paperformat_args,
            set_viewport_size=set_viewport_size,
        )
        files_command_args = []
        wkhtmltopdf_bin = _strictbase_wkhtmltopdf_bin()

        def delete_file(file_path):
            try:
                os.unlink(file_path)
            except OSError:
                _base_report._logger.error("Error when trying to remove file %s", file_path)

        with ExitStack() as stack:
            if request and request.db:
                temp_session = root.session_store.new()
                temp_session.update({
                    **request.session,
                    "debug": "",
                    "_trace_disable": True,
                })
                if temp_session.uid:
                    temp_session.session_token = security.compute_session_token(temp_session, self.env)
                root.session_store.save(temp_session)
                stack.callback(root.session_store.delete, temp_session)

                base_url = self._get_report_url()
                domain = urlparse(base_url).hostname
                cookie = f"session_id={temp_session.sid}; HttpOnly; domain={domain}; path=/;"
                cookie_jar_file_fd, cookie_jar_file_path = tempfile.mkstemp(suffix=".txt", prefix="report.cookie_jar.tmp.")
                stack.callback(delete_file, cookie_jar_file_path)
                with closing(os.fdopen(cookie_jar_file_fd, "wb")) as cookie_jar_file:
                    cookie_jar_file.write(cookie.encode())
                command_args.extend(["--cookie-jar", cookie_jar_file_path])

            if header:
                head_file_fd, head_file_path = tempfile.mkstemp(suffix=".html", prefix="report.header.tmp.")
                with closing(os.fdopen(head_file_fd, "wb")) as head_file:
                    head_file.write(header.encode())
                stack.callback(delete_file, head_file_path)
                files_command_args.extend(["--header-html", head_file_path])
            if footer:
                foot_file_fd, foot_file_path = tempfile.mkstemp(suffix=".html", prefix="report.footer.tmp.")
                with closing(os.fdopen(foot_file_fd, "wb")) as foot_file:
                    foot_file.write(footer.encode())
                stack.callback(delete_file, foot_file_path)
                files_command_args.extend(["--footer-html", foot_file_path])

            paths = []
            for body_idx, body in enumerate(bodies):
                prefix = f"report.body.tmp.{body_idx}."
                body_file_fd, body_file_path = tempfile.mkstemp(suffix=".html", prefix=prefix)
                with closing(os.fdopen(body_file_fd, "wb")) as body_file:
                    if len(body) < 4 * 1024 * 1024:
                        body_file.write(body.encode())
                    else:
                        tree = lxml.html.fromstring(body)
                        _base_report._split_table(tree, 500)
                        body_file.write(lxml.html.tostring(tree))
                paths.append(body_file_path)
                stack.callback(delete_file, body_file_path)

            pdf_report_fd, pdf_report_path = tempfile.mkstemp(suffix=".pdf", prefix="report.tmp.")
            os.close(pdf_report_fd)
            stack.callback(delete_file, pdf_report_path)

            process = subprocess.run(
                [wkhtmltopdf_bin, *command_args, *files_command_args, *paths, pdf_report_path],
                capture_output=True,
                encoding="utf-8",
                check=False,
            )
            err = process.stderr

            match process.returncode:
                case 0:
                    with open(pdf_report_path, "rb") as pdf_file:
                        return pdf_file.read()
                case -11:
                    raise UserError(_("Wkhtmltopdf failed (error code: -11). Memory limit too low or maximum file number of subprocess reached."))
                case -6:
                    raise UserError(_("Wkhtmltopdf failed (error code: -6). Message: %s", err[-1000:]))
                case -1:
                    if any(msg in err for msg in ["cannot connect to X server", "Need a way to run Xvfb"]):
                        raise UserError(_("Wkhtmltopdf failed because it needs an X server to run."))
                    raise UserError(_("Wkhtmltopdf failed (error code: -1). Message: %s", err[-1000:]))
                case _:
                    raise UserError(_("Wkhtmltopdf failed (error code: %s). Message: %s", process.returncode, err[-1000:]))
