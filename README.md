# StrictBase Odoo Addons

Backend modules for Odoo 19.0 CE, built and maintained by [StrictBase](https://strictbase.com).

These modules address specific gaps in Odoo CE where standard functionality is insufficient for strict data integrity, correct billing workflows, or upgrade-safe architecture.

## Disclaimer

Several modules in this repository were built for StrictBase's own internal Odoo setup and are published as working reference implementations, not as general-purpose community addons. They may require adaptation before use in another environment. Read each module's README carefully before installing.

## Modules

| Module | Description |
|--------|-------------|
| `strictbase_agent_guard` | Odoo-side outbound safety guardrail for broad agent access |
| `strictbase_contact` | Base extensions to `res.partner` for downstream modules |
| `strictbase_currency_fix` | Locale-aware currency formatting across backend and frontend |
| `strictbase_employee_names` | Split firstname/lastname on `hr.employee` via `resource.resource` |
| `strictbase_fixed_price_project` | Removes bogus allocated hours on fixed-price projects from sales |
| `strictbase_invoice_template` | Custom invoice PDF with YYYYMM-XXX yearly-reset sequence |
| `strictbase_partner_names` | Split firstname/lastname on `res.partner` with CRM integration |
| `strictbase_project_portal_readonly` | Read-only support portal for client visibility into tickets and hours |
| `strictbase_support_project_overview` | Project-level support wallet balance overview |
| `strictbase_task_sol_lock` | Preserves historical timesheet SO lines when a task's wallet is switched |
| `strictbase_worked_not_invoiced_report` | List view for delivered service lines pending invoicing |

## License

GNU Lesser General Public License v3.0. See [LICENSE](LICENSE).