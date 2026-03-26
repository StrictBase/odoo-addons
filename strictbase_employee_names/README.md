# StrictBase Employee Names

Adds `firstname` and `lastname` for employees in Odoo 19.0 CE.

See the explanator article: <https://strictbase.com/guides/odoo-partner-names.html>.

## Data model

- `resource.resource` gets `firstname` + `lastname` and remains the single source of truth for the display name (`name`) for human resources.
- `hr.employee.firstname`, `hr.employee.lastname`, and `hr.employee.name` are related fields to the linked resource (`resource_id.*`).

## Notes

- `resource.resource.name` is mandatory. This module ensures a value exists at create time, even if first/last name is not provided yet.
- The employee form replaces the single Name field with First Name + Last Name.
