{
    "name": "StrictBase: Agent Outbound Guard",
    "version": "19.0.1.0.1",
    "category": "Tools",
    "summary": "Block agent-initiated outbound communication unless explicitly confirmed",
    "author": "StrictBase",
    "depends": ["mail", "sale", "account"],
    "data": [
        "security/strictbase_agent_guard_security.xml",
        "security/ir.model.access.csv",
    ],
    "installable": True,
    "license": "LGPL-3",
}
